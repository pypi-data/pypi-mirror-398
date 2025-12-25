import copy
import json
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from importlib import import_module
from ipamd.public.utils.parser import value_of
from ipamd.public.utils.plugin_manager import PluginBase
from ipamd.public.utils.output import *
from ipamd.public import shared_data
from multiprocessing import Process, Pipe
import re
from numba import cuda

class Simulation:
    class __Parser(PluginBase):
        def __init__(self):
            extra_plugin_dir = config.get('simulation_plugin_dir')
            plugin_dir = ([
                shared_data.module_installation_dir + '/plugins/simulation/integrator',
                shared_data.module_installation_dir + '/plugins/simulation/force'
            ] + extra_plugin_dir)
            super().__init__(plugin_dir)
            self.load_all()

    def __init__(self, app):
        self.__app = app
        self.__parser = self.__Parser()
        @captured
        def f():
            return import_module('ipamd.app.lib.galamost')

        self.__gala_core, _ = f()

    @property
    def working_dir(self):
        return self.__app.working_dir

    def new_simulation(self,
                       simulation_box,
                       job_name='simulation',
                       dt=0.01,
                       total_time=0,
                       snap_shot=0,
                       run_step=0, period=0,
                       thermo_bath='langevin_nvt',
                       res_auto_read=True,
                       minimize_energy=True):
        if total_time != 0 and snap_shot!=0:
            run_step = int(total_time / dt)
            period = int(run_step / snap_shot)

        simulation = self.__Simulation_Job(
            simulation_box=simulation_box,
            job_name=job_name,
            run_step=run_step,
            dt=dt,
            period=period,
            parser=self.__parser,
            working_dir=self.working_dir,
            gala_core=self.__gala_core,
            gpu_id=self.__app.gpu_id,
            thermo_bath=thermo_bath,
            force_field=self.__app.force_field,
            res_auto_read=res_auto_read,
            minimize_energy=minimize_energy
        )
        return simulation

    class __Simulation_Job:
        def __init__(self, simulation_box, job_name, run_step, dt, parser, period, working_dir, gala_core, gpu_id, thermo_bath, force_field, res_auto_read, minimize_energy):
            self.__total_step = run_step
            self.__target_step = run_step
            self.__gpu_id = 0
            self.__dt = dt
            self.__simulation_box = simulation_box
            self.job_name = job_name
            self.__parser = parser
            self.__working_dir = working_dir
            self.__gala_core = gala_core
            self.__gpu_id = gpu_id
            self.period = period
            self.__thermo_bath = thermo_bath
            self.__force_field = force_field
            self.__res_auto_read = res_auto_read
            self.__should_minimize_energy = minimize_energy

            prop = simulation_box.current_frame().properties()
            self.__rigid_body = False
            for molecule in prop['molecules']:
                for rigid in molecule['rigid_group']:
                    if rigid != -1:
                        self.__rigid_body = True
                        break

        def __parse_force(self, all_info, force, param):
            parser = getattr(self.__parser, force)
            return parser(param, all_info, self.__gala_core)

        def __parse_integrator(self, all_info, integrator, param):
            parser = getattr(self.__parser, integrator)
            return parser(param, all_info, self.__gala_core)

        @staticmethod
        def __parse_gala_output(text):
            lines = text.split('\n')
            for line in lines:
                if line.startswith('INFO : '):
                    info(line[7:])
                elif line.startswith('***Warning!'):
                    warning(line[12:])
                elif line.startswith('***Error!'):
                    error(line[10:])
                else:
                    verbose(line)

        def __outputs(self):
            files = os.listdir(self.__working_dir)
            pattern = '^' + self.job_name + r'\.\d+\.xml$'
            file_list = [f for f in files if re.match(pattern, f)]
            sorted_list = sorted(file_list, key=lambda x: int(x.split('.')[-2]))
            return sorted_list

        def __latest(self, file_list):
            max_step = 0
            latest_output = self.job_name
            for file in file_list:
                digit = int(re.findall(r'\d+', file)[-1])
                if digit > max_step:
                    max_step = digit
                    latest_output = file[:-4]
            return max_step, latest_output

        def clean_cache(self, remove_info=True):
            matching_files = self.__outputs()
            for file in matching_files:
                os.remove(os.path.join(self.__working_dir, file))
            log_filename = os.path.join(self.__working_dir, self.job_name + '.log')
            if os.path.exists(log_filename):
                os.remove(log_filename)
            if os.path.exists(os.path.join(self.__working_dir, self.job_name + '.xml')):
                os.remove(os.path.join(self.__working_dir, self.job_name + '.xml'))
            if os.path.exists(os.path.join(self.__working_dir, self.job_name + '.map')):
                os.remove(os.path.join(self.__working_dir, self.job_name + '.map'))
            if remove_info and os.path.exists(os.path.join(self.__working_dir, self.job_name + '.info')):
                os.remove(os.path.join(self.__working_dir, self.job_name + '.info'))

        def run(self, yes=''):
            ready_to_run = True
            input_file_path = os.path.join(self.__working_dir, self.job_name + '.xml')
            new_simulation = False
            if os.path.exists(os.path.join(self.__working_dir, self.job_name + '.info')):
                with open(os.path.join(self.__working_dir, self.job_name + '.info'), 'r') as f:
                    simulation_info = json.load(f)
                    run_step = simulation_info['run_step']
                    matching_files = self.__outputs()
                    max_step, latest_output = self.__latest(matching_files)
                    if max_step < run_step and max_step != 0:
                        if yes=='y' or (yes != 'n' and input('Previous simulation not finished, continue? (y/n)') == 'y'):
                            input_file_path = os.path.join(self.__working_dir, latest_output + '.xml')
                            remaining_step = run_step - max_step
                            self.__total_step = remaining_step
                            self.__target_step = run_step
                        else:
                            self.clean_cache()
                            new_simulation = True
                    else:
                        if yes=='y' or (yes != 'n' and input('Find previous simulation, rerun? (y/n)') == 'y'):
                            self.clean_cache()
                            new_simulation = True
                        else:
                            ready_to_run = False
            else:
                new_simulation = True

            if new_simulation:
                with open(os.path.join(self.__working_dir, self.job_name + '.info'), 'w') as f:
                    data = {
                        'job_name': self.job_name,
                        'run_step': self.__total_step,
                        'dt': self.__dt,
                        'period': self.period
                    }
                    json.dump(data, f, indent=4)

            if ready_to_run:
                cuda.close()
                self.__simulation_box.to_xml(self.job_name)
                if new_simulation and self.__should_minimize_energy:
                    self.__minimize_energy(input_file_path)
                    info('overwriting ' + input_file_path + ' with energy minimized configuration')
                    matching_files = self.__outputs()
                    max_step, latest_output = self.__latest(matching_files)
                    self.__simulation_box.clean()
                    self.__simulation_box.new_frame()
                    self.__simulation_box.read_xml(latest_output)
                    self.__simulation_box.to_xml(self.job_name)
                    for old_file in matching_files:
                        os.remove(os.path.join(self.__working_dir, old_file))
                self.__run_simulation(str(input_file_path))

            if self.__res_auto_read:
                self.__simulation_box.clean()
                matching_files = self.__outputs()
                for file in matching_files:
                    self.__simulation_box.new_frame()
                    self.__simulation_box.read_xml(file[:-4])

            info('Simulation finished')

        @captured
        def __init_info(self, path):
            build_method = self.__gala_core.XMLReader(path)
            perform_config = self.__gala_core.PerformConfig(str(self.__gpu_id))
            return self.__gala_core.AllInfo(build_method, perform_config)

        @captured
        def __init_app(self, all_info):
            return self.__gala_core.Application(all_info, 0.002)

        @captured
        def __init_force(self, all_info, target_app):
            lookup_table = self.__simulation_box.env.values
            for force in self.__force_field.ff_param:
                params = copy.deepcopy(self.__force_field.ff_param[force])
                for key in params.keys():
                    if type(params[key]) is dict:
                        for sub_key in params[key].keys():
                            params[key][sub_key] = value_of(params[key][sub_key], lookup_table)
                    else:
                        params[key] = value_of(params[key], lookup_table)
                f = self.__parse_force(all_info, force, params)
                if type(f) is list:
                    for sf in f:
                        target_app.add(sf)
                else:
                    target_app.add(f)

            return 0 #in order to avoid warning

        @captured
        def __init_essentials(self, all_info, target_app):
            sort_method = self.__gala_core.Sort(all_info)
            sort_method.setPeriod(500)
            target_app.add(sort_method)

            zero_momentum = self.__gala_core.ZeroMomentum(all_info)
            zero_momentum.setPeriod(100)
            target_app.add(zero_momentum)
            return 0  # in order to avoid warning

        @captured
        def __init_log(self, all_info, target_app, period):
            group = self.__gala_core.ParticleSet(all_info, "all")
            comp_info = self.__gala_core.ComputeInfo(all_info, group)
            d_info = self.__gala_core.DumpInfo(all_info, comp_info,
                                               self.__working_dir + '/' + self.job_name + '.log')
            d_info.setPeriod(int(period))
            target_app.add(d_info)

        @captured
        def __init_snapshot(self, all_info, target_app, period):
            xml = self.__gala_core.XMLDump(all_info, self.__working_dir + '/' + self.job_name)
            xml.setPeriod(int(period))
            xml.setOutput(
                [
                    'bond',
                    'image',
                    'molecule',
                    'velocity',
                    'mass',
                    'charge',
                    'body'
                ]
            )
            target_app.add(xml)

        @captured
        def __init_integrator(self, all_info, target_app, type_='langevin_nvt'):
            integrator, integrator_b = self.__parse_integrator(all_info, type_, {
                'temperature': self.__simulation_box.env.values['temperature'],
                'pressure': self.__simulation_box.env.values['pressure'],
                'rigid': self.__rigid_body
            })
            target_app.add(integrator)
            if integrator_b is not None:
                target_app.add(integrator_b)

        def __minimize_energy(self, input_file_path):
            verbose('reading input file ' + input_file_path)
            em_step = 1e4
            all_info, _ = self.__init_info(input_file_path)
            app, _ = self.__init_app(all_info)
            self.__init_integrator(all_info, app, type_='em')
            self.__init_essentials(all_info, app)
            self.__init_snapshot(all_info, app, em_step)
            verbose('minimizing energy')

            @captured
            def run_md():
                app.run(int(em_step))
            run_md()

        def __run_simulation(self, input_file_path):
            all_info, _ = self.__init_info(input_file_path)
            app, _ = self.__init_app(all_info)
            self.__init_force(all_info, app)
            self.__init_essentials(all_info, app)
            self.__init_log(all_info, app, self.period)
            self.__init_snapshot(all_info, app, self.period)
            self.__init_integrator(all_info, app, type_=self.__thermo_bath)

            parent_conn, child_conn = Pipe()

            printer_process = Process(target=self.__printer, args=(child_conn,))
            printer_process.start()
            @captured_async(parent_conn, timeout=0.1)
            def run_md():
                app.run(self.__total_step)
            run_md()
            printer_process.join()

        def __printer(self, conn):
            def exit_(signum, frame):
                os.kill(os.getppid(), signal.SIGKILL)

            signal.signal(signal.SIGINT, exit_)
            signal.signal(signal.SIGTERM, exit_)


            with Progress(
                    '[progress.description]{task.description}',
                    BarColumn(),
                    "[progress.percentage]{task.percentage:>3.2f}%",
                    "[yellow]⏱",
                    TimeElapsedColumn(),
                    "[cyan]⏳",
                    TimeRemainingColumn(),
                    refresh_per_second=1) as progress:

                task = None
                simulation_finished = False
                while not simulation_finished:
                    message = conn.recv()
                    for line in message.split('\n'):
                        if '--start--' in line:
                            start_time = time.time()
                            task = progress.add_task(self.job_name, total=self.__target_step)
                            progress.update(task,
                                            description=f'{self.job_name}(TPS: *)',
                                            completed=200)
                        elif 'STATUS RUNNING' in line:
                            numbers = list(map(str, re.findall(r'\d+\.?\d*', line)))
                            tps = float(numbers[0])
                            current = int(numbers[1])
                            progress.update(task,
                                            description=f'{self.job_name}(TPS: {int(round(tps))})',
                                            completed=current)
                        elif '--end--' in line:
                            progress.update(task, completed=self.__total_step)
                            simulation_finished = True
                        elif 'Error' in line:
                            simulation_finished = True
                            error(f'{line[10:]}')
                    time.sleep(0.1)
                conn.close()