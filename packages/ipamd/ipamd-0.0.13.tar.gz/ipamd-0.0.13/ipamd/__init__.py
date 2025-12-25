import multiprocessing
from ipamd.public import shared_data
from ipamd.public.utils.hardware import available_gpus
from ipamd.public.utils.parser import range_to_list
import uuid
from ipamd.public.utils.output import warning, output, error, info
from ipamd.public.utils.xml import read_xml
from ipamd.app import Simulation, Analysis, Builder, Sakuanna
import os
from Bio import SeqIO
import csv
import shutil
from numba import cuda
from ipamd.public.models.md import ForceField

config = shared_data.config

class App():
    def __init__(self, name=None, init_working_dir=True, gpu_id=0):
        if gpu_id < len(shared_data.gpu_list):
            self.gpu_id = gpu_id
        else:
            warning('GPU id out of range')
            self.gpu_id = 0
        cuda.select_device(self.gpu_id)
        self.cuda = cuda
        self.working_dir = None
        self.name = None

        self.force_field = ForceField(atom_definition={}, ff_param={})


        if init_working_dir:
            self.switch(name)

        data_path = os.path.join(shared_data.module_installation_dir, 'data')
        self.__ff_dir = os.path.join(data_path, 'forcefield')
        file_list = os.listdir(self.__ff_dir)
        for file in file_list:
            filename, extend_name = os.path.splitext(file)
            if extend_name == '.xml':
                shared_data.available_ff.append(filename)
        self.use('default')
        self.builder = Builder(self)
        self.analysis = Analysis(self)
        self.simulation = Simulation(self)
        self.sakuanna = Sakuanna(self)

    def gen_link(self):
        cwd = os.getcwd()
        link_path = os.path.join(cwd, self.name)
        if self.working_dir == cwd:
            warning('The working directory is the current directory, no link created.')
        else:
            if not os.path.exists(link_path):
                os.symlink(self.working_dir, link_path)

    def available_ff(self):
        return shared_data.available_ff

    def switch(self, name):
        if name is None:
            random_string = uuid.uuid1().hex[0:8]
            self.name = random_string
            warning('No name provided, use random name: ' + random_string)
        else:
            self.name = name
        result_dir = config.get('result_dir')
        if result_dir == '$decentralized':
            self.working_dir = os.getcwd()
        else:
            self.working_dir = os.path.join(result_dir, self.name)
            if not os.path.exists(self.working_dir):
                os.makedirs(self.working_dir)

    def use(self, ff=None):
        if type(ff) is str:
            if ff == 'default' or ff is None:
                ff_name = config.get('default_ff')
            else:
                ff_name = ff
            ff_file = os.path.join(self.__ff_dir, ff_name + '.xml')
            ff = read_xml(ff_file)['ff']
            self.force_field.atom_definition = ff['atom_definition']
            self.force_field.ff_param = ff['ff_param']
        else:
            ff_param = ff['ff_param']
            atom_definition = ff['atom_definition']
            for key in atom_definition.keys():
                self.force_field.atom_definition[key] = atom_definition[key]
            for key in ff_param.keys():
                if key not in self.force_field.ff_param.keys():
                    self.force_field.ff_param[key] = ff_param[key]
                else:
                    for type_ in ff_param[key].keys():
                        self.force_field.ff_param[key][type_] = ff_param[key][type_]
        return self

    def load_file(self, *paths):
        for path in paths:
            if not os.path.exists(path):
                error(f'File {path} not found')
                continue
            filename = path.split("/")[-1]
            shutil.copyfile(path, os.path.join(self.working_dir, filename))

    def export_file(self, filename, dest_dir_path=None):
        full_origin_path = os.path.join(self.working_dir, filename)

        if dest_dir_path is not None:
            if not os.path.exists(dest_dir_path):
                os.makedirs(dest_dir_path)
            full_dest_path = os.path.join(dest_dir_path, filename)
        else:
            full_dest_path = os.path.join(os.getcwd(), filename)
        shutil.copyfile(full_origin_path, full_dest_path)

class OmicsLoader:
    def __init__(self, path, condition=()):
        self.__path = path
        self.__files = os.listdir(self.__path)
        self.__condition = condition

    def __iter__(self):

        for full_name in self.__files:
            filename, extend_name = os.path.splitext(full_name)
            data = {
                'type': None,
                'path': os.path.join(self.__path, full_name),
                'name': filename,
                'sequence': None
            }
            if extend_name == '.fasta':
                for record in SeqIO.parse(os.path.join(self.__path, full_name), "fasta"):
                    data['sequence'] = str(record.seq)
                    data['type'] = 'sequence'
                    data['path'] = None
                    break
            elif extend_name == '.pdb':
                data['type'] = 'structure'
            elif extend_name == '.csv':
                with open(os.path.join(self.__path, full_name), 'r') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        protein_name = row[0].strip()
                        sequence = row[1].strip()
                        data['sequence'] = sequence
                        data['name'] = protein_name
                        data['type'] = 'sequence'
                        data['path'] = None

                        yield data
                continue
            else:
                data['type'] = 'structure'
            for condition in self.__condition:
                if condition in filename:
                    data['name'] = filename
                    break
            yield data

def batch_run(loader, task, gpus='', *args, **kwargs):
    gpu_list = available_gpus()
    total_gpus = len(gpu_list)
    if gpus == '':
        free_gpu_list = [i for i in range(total_gpus)]
    else:
        free_gpu_list = range_to_list(gpus)

    semaphore = multiprocessing.Semaphore(len(free_gpu_list))
    mutex_lock = multiprocessing.Lock()

    manager = multiprocessing.Manager()
    gpu_occupy = manager.list([-1 for _ in range(total_gpus)])# 0 for free, 1 for occupied, -1 for not allocated
    task_list = [None for _ in range(total_gpus)]
    for i in free_gpu_list:
        gpu_occupy[i] = 1

    for data in loader:
        semaphore.acquire()
        output(f'[--{data['name']}--]')
        index = -1
        with mutex_lock:
            for i in range(total_gpus):
                if gpu_occupy[i] == 1:
                    gpu_occupy[i] = 0
                    index = i
                    break

        def func(data, index, lock, worker_list, semaphore):
            app = App(gpu_id=index, name=data['name'])
            info(f'Using GPU {index}: {gpu_list[index]["model"]}')
            if data['type'] == 'structure':
                app.load_file(data['path'])
            task(app, data, *args, **kwargs)
            semaphore.release()
            with lock:
                worker_list[index] = 1

        p = multiprocessing.Process(target=func, args=(data, index, mutex_lock, gpu_occupy, semaphore))
        p.start()
        task_list[index] = p

    for p in task_list:
        if p is not None:
            p.join()