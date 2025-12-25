import numpy as np
from numba import cuda
import math

def func(frame, start_d=1, step=1, end_d=10, l=False, ref=False):
    @cuda.jit
    def f(pos_list, box_size, max_d, res_list):
        i = cuda.grid(1)
        n_atoms = len(pos_list)
        while i < n_atoms:
            position_i = pos_list[i]
            neighbor_count = 0
            for j in range(n_atoms):
                if i == j:
                    continue
                position_j = pos_list[j]
                max_image_x = max_d * 2 // box_size[0] + 1
                max_image_y = max_d * 2 // box_size[1] + 1
                max_image_z = max_d * 2 // box_size[2] + 1
                for image_x in range(-max_image_x, max_image_x + 1):
                    for image_y in range(-max_image_y, max_image_y + 1):
                        for image_z in range(-max_image_z, max_image_z + 1):
                            delta_x = abs(position_i[0] - position_j[0] - image_x * box_size[0])
                            delta_y = abs(position_i[1] - position_j[1] - image_y * box_size[1])
                            delta_z = abs(position_i[2] - position_j[2] - image_z * box_size[2])
                            distance_square = delta_x ** 2 + delta_y ** 2 + delta_z ** 2
                            if distance_square < max_d ** 2:
                                neighbor_count += 1

            res_list[i] = neighbor_count

            i += cuda.gridsize(1)


    prop = frame.properties(ignoring_image=False)
    molecules = prop['molecules']
    box_size = prop['size']
    position_list = []
    for molecule in molecules:
        for position in molecule['position']:
            position_list.append(position)
    n_atoms = len(position_list)

    position_list_device = cuda.to_device(position_list)


    data = {}
    for d in range(start_d, end_d + 1, step):
        if ref:
            if l:
                data[str(d)] = 0
            else:
                ref_k = 4 / 3 * d ** 3 * np.pi
                data[str(d)] = ref_k
        else:
            res_list = np.zeros(n_atoms)
            res_list_device = cuda.to_device(res_list)
            f[1024, 128](position_list_device, box_size, d, res_list_device)
            res_list_device.copy_to_host(res_list)
            n = 0
            for i in res_list:
                n += i
            V = box_size[0] * box_size[1] * box_size[2]
            k = n * V / (n_atoms ** 2)
            if l:
                data[str(d)] = math.pow(k / math.pi / 4 * 3, 1 / 3) - d
            else:
                data[str(d)] =k

    return data