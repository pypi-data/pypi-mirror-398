import os

from ipamd.public.utils.output import error

configure = {
    "schema": "io"
}
def func(frame, working_dir, simulation):
    frame_no = frame.no
    simulation_name = simulation.job_name
    log_file = os.path.join(working_dir, simulation_name + '.log')
    with open(log_file, 'r') as f:
        lines = f.readlines()[1:]
    time_step = frame_no * simulation.period
    data = {}
    for line in lines:
        time_step_of_line = float(line.split()[0])
        if time_step_of_line == time_step:
            data = float(line.split()[3])
    if data == {}:
        error('simulation should be run first')
        raise NotImplementedError
    return data