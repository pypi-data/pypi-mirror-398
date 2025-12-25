import numpy as np
from numba import cuda
import math

def func(frame, type_=''):
    prop = frame.properties(ignoring_image=True)
    molecules = prop['molecules']
    if type_ == '':
        type_ = molecules[0]['molecule_type']
    target_molecules = []
    for molecule in molecules:
        if molecule['molecule_type'] == type_:
            target_molecules.append(molecule)

    n_molecules = len(target_molecules)
    molecule_mass_list = []
    molecule_pos_list = []
    for molecule in target_molecules:
        molecule_mass_list.append(molecule['mass'])
        molecule_pos_list.append(molecule['position'])
    molecule_mass_list_device = cuda.to_device(molecule_mass_list)
    molecule_pos_list_device = cuda.to_device(molecule_pos_list)
    rg_list = np.zeros(n_molecules)
    rg_list_device = cuda.to_device(rg_list)
    @cuda.jit
    def calculate_rg(mass_list, pos_list, res_list):
        i = cuda.grid(1)
        if i < res_list.size:
            positions = pos_list[i]
            mass = mass_list[i]
            mass_center_x = 0
            mass_center_y = 0
            mass_center_z = 0
            total_mass = 0
            molecule_length = len(mass)
            for j in range(molecule_length):
                total_mass += mass[j]
                mass_center_x += mass[j] * positions[j][0]
                mass_center_y += mass[j] * positions[j][1]
                mass_center_z += mass[j] * positions[j][2]
            mass_center_x /= total_mass
            mass_center_y /= total_mass
            mass_center_z /= total_mass
            rg2 = 0
            for j in range(molecule_length):
                distance2 = ((positions[j][0] - mass_center_x) ** 2 +
                             (positions[j][1] - mass_center_y) ** 2 +
                             (positions[j][2] - mass_center_z) ** 2)
                rg2 += mass[j] * distance2 / total_mass
            res_list[i] = rg2
    calculate_rg[1024, 128](molecule_mass_list_device, molecule_pos_list_device, rg_list_device)
    rg_list_device.copy_to_host(rg_list)
    data = {}
    for i in range(n_molecules):
        data[str(i)] = math.sqrt(rg_list[i])
    return data