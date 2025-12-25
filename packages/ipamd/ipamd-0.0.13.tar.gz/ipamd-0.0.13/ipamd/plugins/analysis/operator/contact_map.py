import numpy as np
from numba import cuda
def func(frame, type1, threshold=4, type2=''):
    prop = frame.properties(ignoring_image=False)
    molecules = prop['molecules']
    box_size = prop['size']
    threshold_square = threshold ** 2
    molecule1_list = []
    monomer = type1 == type2
    for molecule in molecules:
        if molecule['molecule_type'] == type1:
            molecule1_list.append(molecule)
    if type2 == '':
        molecule2_list = molecule1_list
        monomer = True
    else:
        molecule2_list = []
        for molecule in molecules:
            if molecule['molecule_type'] == type2:
                molecule2_list.append(molecule)

    position_list_type1 = []
    position_list_type2 = []
    for molecule in molecule1_list:
        position_list_type1.append(molecule['position'])
    for molecule in molecule2_list:
        position_list_type2.append(molecule['position'])
    n_atoms_type1 = len(position_list_type1[0])
    n_atoms_type2 = len(position_list_type2[0])
    contact_map = np.zeros((n_atoms_type1, n_atoms_type2))
    contact_map_device = cuda.to_device(contact_map)
    @cuda.jit
    def cm(monomer, threshold_square, box_size, pos1, pos2, res):
        n_atoms_type1 = len(pos1[0])
        n_atoms_type2 = len(pos2[0])
        grids = n_atoms_type1 * n_atoms_type2
        i = cuda.grid(1)
        while i < grids:
            col = i % n_atoms_type2
            row = i // n_atoms_type2
            if row >= n_atoms_type1:
                return
            index_in_molecule1 = row
            index_in_molecule2 = col
            for index_molecule_type1 in range(len(pos1)):
                for index_molecule_type2 in range(len(pos2)):
                    if monomer and index_molecule_type1 == index_molecule_type2:
                        continue
                    distance_square = 0
                    for direction in range(3):
                        delta = pos1[index_molecule_type1][index_in_molecule1][direction] - pos2[index_molecule_type2][index_in_molecule2][direction]
                        distance = min(abs(delta), box_size[direction] - abs(delta))
                        distance_square += distance ** 2

                    if distance_square < threshold_square:
                        res[row][col] += 1
            i += cuda.gridsize(1)

    cm[1024, 128](
        monomer,
        threshold_square,
        box_size,
        cuda.to_device(position_list_type1),
        cuda.to_device(position_list_type2),
        contact_map_device
    )
    contact_map_device.copy_to_host(contact_map)
    data = {}
    for i in range(n_atoms_type1 - 1, -1, -1):
        value_row = {}
        for j in range(n_atoms_type2):
            value_row[str(j + 1)] = contact_map[i][j]
        data[str(i + 1)] = value_row
    return data