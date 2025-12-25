import numpy as np
from numba import cuda
from ipamd.public.constant import na
def func(frame, x0=0, y0=0, z0=0, lx=0, ly=0, lz=0):
    prop = frame.properties(ignoring_image=False)
    box_size = prop['size']
    molecules = prop['molecules']
    molecule_of_different_types = {}
    for molecule in molecules:
        name = molecule['molecule_type']
        if name not in molecule_of_different_types:
            molecule_of_different_types[name] = []
        molecule_of_different_types[name].append(molecule)
    if lx == 0:
        lx = box_size[0]
    if ly == 0:
        ly = box_size[1]
    if lz == 0:
        lz = box_size[2]

    x0 = x0 - box_size[0] / 2
    y0 = y0 - box_size[1] / 2
    z0 = z0 - box_size[2] / 2
    @cuda.jit
    def calculate_density(mass_list, pos_list, res_list):
        i = cuda.grid(1)
        if i < res_list.size:
            positions = pos_list[i]
            mass = mass_list[i]
            total_mass = 0
            molecule_length = len(mass)
            for j in range(molecule_length):

                if (positions[j][0] > x0 and positions[j][0] < x0 + lx and
                    positions[j][1] > y0 and positions[j][1] < y0 + ly and
                    positions[j][2] > z0 and positions[j][2] < z0 + lz):
                    total_mass += mass[j]
            res_list[i] = total_mass

    mass_in_box = 0
    for typ in molecule_of_different_types.keys():
        molecules_single_type = molecule_of_different_types[typ]
        n_molecules = len(molecules_single_type)
        molecule_mass_list = []
        molecule_pos_list = []
        for molecule in molecules_single_type:
            molecule_mass_list.append(molecule['mass'])
            molecule_pos_list.append(molecule['position'])
        molecule_mass_list_device = cuda.to_device(molecule_mass_list)
        molecule_pos_list_device = cuda.to_device(molecule_pos_list)
        for i in range(n_molecules):
            molecule_mass_list[i] = np.array(molecule_mass_list[i])
            molecule_pos_list[i] = np.array(molecule_pos_list[i])
        res_list = np.zeros(n_molecules)
        res_list_device = cuda.to_device(res_list)
        calculate_density[1024, 128](molecule_mass_list_device, molecule_pos_list_device, res_list_device)
        res_list_device.copy_to_host(res_list)
        for mass in res_list:
            mass_in_box += mass
    volume = lx * ly * lz
    if volume == 0:
        density = 0
    else:
        density = mass_in_box / volume / 1000 / na * 1e24
    return density