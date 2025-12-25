import math
from ipamd.public.utils.parser import value_of
configure = {
    'type': 'function',
    "schema": 'frame',
    "apply": []
}

def func(frame):
    x = frame.x
    y = frame.y
    z = frame.z
    threshold_2 = 0.1 * (x ** 2 + y ** 2 + z ** 2)
    drop_list = []
    env = frame.box.env

    def mass_center(molecule):
        m_total = 0
        x_dot_m = 0
        y_dot_m = 0
        z_dot_m = 0
        for atom in molecule.atoms:
            mass = value_of(atom["prototype"].get('mass'), env)
            m_total += mass
            pos = atom['offset']
            x_dot_m += pos[0] * mass
            y_dot_m += pos[1] * mass
            z_dot_m += pos[2] * mass
        return x_dot_m / m_total, y_dot_m / m_total, z_dot_m / m_total

    for molecule in frame.molecules:
        owned = False
        for i, drop in enumerate(drop_list):
            for m in drop:
                position1 = mass_center(m['prototype'])
                position2 = mass_center(molecule['prototype'])
                dx = position1[0] + m['offset'][0] - position2[0] - molecule['offset'][0]
                dy = position1[1] + m['offset'][1] - position2[1] - molecule['offset'][1]
                dz = position1[2] + m['offset'][2] - position2[2] - molecule['offset'][2]
                dx_in_box = dx - round(dx / x) * x
                dy_in_box = dy - round(dy / y) * y
                dz_in_box = dz - round(dz / z) * z
                d_2 = dx_in_box ** 2 + dy_in_box ** 2 + dz_in_box ** 2
                if d_2 < threshold_2:
                    owned = True
                    drop.append(molecule)
                    break
            if owned:
                break
        if not owned:
            drop_list.append([molecule])

    min_x = math.inf
    min_y = math.inf
    min_z = math.inf
    for drop in drop_list:
        mol_ref = drop[0]
        mol_other = drop[1:]
        coordinate = mass_center(mol_ref['prototype'])
        ref_cor = (
            coordinate[0] + mol_ref['offset'][0],
            coordinate[1] + mol_ref['offset'][1],
            coordinate[2] + mol_ref['offset'][2]
        )

        for m in mol_other:
            molecule = m['prototype']
            new_coordinate = mass_center(molecule)
            new_cor = (
                new_coordinate[0] + m['offset'][0],
                new_coordinate[1] + m['offset'][1],
                new_coordinate[2] + m['offset'][2]
            )
            #x
            ref_x = ref_cor[0]
            new_x = new_cor[0]
            delta_x = new_x - ref_x
            delta_image_x = round(delta_x / x)
            #y
            ref_y = ref_cor[1]
            new_y = new_cor[1]
            delta_y = new_y - ref_y
            delta_image_y = round(delta_y / y)
            #z
            ref_z = ref_cor[2]
            new_z = new_cor[2]
            delta_z = new_z - ref_z
            delta_image_z = round(delta_z / z)

            m['offset'] = (
                m['offset'][0] - delta_image_x * x,
                m['offset'][1] - delta_image_y * y,
                m['offset'][2] - delta_image_z * z
            )

        for m in drop:
            molecule = m['prototype']
            offset = m['offset']
            for atom in molecule.atoms:
                atom_position = atom['offset']
                new_position = [
                    atom_position[0] + offset[0] * x,
                    atom_position[1] + offset[1] * y,
                    atom_position[2] + offset[2] * z
                ]
                if new_position[0] < min_x:
                    min_x = new_position[0]
                if new_position[1] < min_y:
                    min_y = new_position[1]
                if new_position[2] < min_z:
                    min_z = new_position[2]

    for drop in drop_list:
        for molecule in drop:
            molecule['offset'] = (
                molecule['offset'][0] - min_x // x,
                molecule['offset'][1] - min_y // y,
                molecule['offset'][2] - min_z // z
            )