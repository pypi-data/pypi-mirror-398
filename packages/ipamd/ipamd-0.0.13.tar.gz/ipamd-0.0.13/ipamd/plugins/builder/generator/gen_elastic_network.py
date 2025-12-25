import math

def func(molecule, max_gap=4):
    ff_param = {
        'bond_harmonic': {}
    }

    folded_groups = []
    last_rigid_index = -1
    for index, atom in enumerate(molecule.atoms):
        if atom['rigid_group'] >= 0:
            if last_rigid_index == -1 or index - last_rigid_index > max_gap + 1:
                folded_groups.append([])
            folded_groups[-1].append(index)
            last_rigid_index = index
    for group in folded_groups:
        n = len(group)
        for i in range(n):
            index_i = group[i]
            molecule.atoms[index_i]['rigid_group'] = -1
            coordinate_i = molecule.atoms[index_i]['offset']
            for j in range(i + 1, n):
                index_j = group[j]
                coordinate_j = molecule.atoms[index_j]['offset']
                distance = math.sqrt(
                    (coordinate_i[0] - coordinate_j[0]) ** 2 +
                    (coordinate_i[1] - coordinate_j[1]) ** 2 +
                    (coordinate_i[2] - coordinate_j[2]) ** 2)
                if index_j - index_i == 1:
                    molecule.link(index_i, index_j, f'B-B-{index_i}-{index_j}')
                    ff_param['bond_harmonic'][f'B-B-{index_i}-{index_j}'] = {
                        'k': 8033.28,
                        'r0': distance
                    }
                else:
                    if distance < 0.9:
                        molecule.link(index_i, index_j, f'en-{index_i}-{index_j}')
                        ff_param['bond_harmonic'][f'en-{index_i}-{index_j}'] = {
                            'k': 700,
                            'r0': distance
                        }

    extra_ff_data = {
        'atom_definition': {},
        'ff_param': ff_param
    }
    return molecule, extra_ff_data