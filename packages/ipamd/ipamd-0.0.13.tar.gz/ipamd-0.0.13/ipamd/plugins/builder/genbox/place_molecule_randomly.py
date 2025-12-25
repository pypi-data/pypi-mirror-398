import random

import numpy as np
from numba import cuda

from ipamd.public.utils.output import warning, verbose
configure = {
    "type": 'function',
    "schema": 'frame'
}
@cuda.jit
def overlap(pre_positions, new_position, box_size, threshold, result):
    i = cuda.grid(1)
    while i < len(pre_positions):
        for position in new_position:
            dx = min(abs(pre_positions[i][0] - position[0]), box_size[0] - abs(pre_positions[i][0] - position[0]))
            dy = min(abs(pre_positions[i][1] - position[1]), box_size[1] - abs(pre_positions[i][1] - position[1]))
            dz = min(abs(pre_positions[i][2] - position[2]), box_size[2] - abs(pre_positions[i][2] - position[2]))
            distance_square = (dx ** 2 + dy ** 2 + dz ** 2)
            if distance_square < threshold ** 2:
                result[i] = 1
                return
        i += cuda.gridsize(1)


def func(molecule, n, frame, threshold = 1, max_tries=5, strict=False, allow_out_of_box=True):
    for i in range(int(n)):
        prop = frame.properties()
        size = prop['size']
        molecules = prop['molecules']
        pre_positions = []
        for pre_molecule in molecules:
            for position in pre_molecule['position']:
                pre_positions.append(position)

        tries = 0
        while True:
            success = False
            tries += 1
            offset = [random.random() * size[0], random.random() * size[1], random.random() * size[2]]
            rotation = [random.random() * 360, random.random() * 360, random.random() * 360]
            molecule.rotate(rotation[0], rotation[1], rotation[2])

            new_positions = []
            out_of_box = False
            pos_prop = molecule.properties()['position']
            for position in pos_prop:
                abs_pos_x = position[0] + offset[0]
                abs_pos_y = position[1] + offset[1]
                abs_pos_z = position[2] + offset[2]
                if allow_out_of_box == False:
                    if abs_pos_x < 0 or abs_pos_x > size[0]:
                        out_of_box = True
                        break
                    if abs_pos_y < 0 or abs_pos_y > size[1]:
                        out_of_box = True
                        break
                    if abs_pos_z < 0 or abs_pos_z > size[2]:
                        out_of_box = True
                        break
                new_x = (abs_pos_x) % size[0] - size[0] / 2
                new_y = (abs_pos_y) % size[1] - size[1] / 2
                new_z = (abs_pos_z) % size[2] - size[2] / 2
                new_positions.append([
                    new_x,
                    new_y,
                    new_z
                ])
            if out_of_box:
                continue
            if len(pre_positions) == 0:
                success = True
            else:
                result = np.zeros(len(pre_positions), dtype=np.int32)
                new_molecule_device = cuda.to_device(new_positions)
                pre_molecule_device = cuda.to_device(pre_positions)
                result_device = cuda.to_device(result)

                overlap[1024, 128](pre_molecule_device, new_molecule_device, size, threshold, result_device)
                result = result_device.copy_to_host()
                if sum(result) == 0:
                    success = True
            if success:
                frame.add_molecule(molecule, offset=offset)
                verbose(f'Molecule {i + 1} of type {molecule.type_} was placed after {tries} tries')
                break
            if tries == max_tries and strict == False:
                warning(f'Failed to place molecule {i} of type {molecule.type_} after {max_tries} tries')
                break