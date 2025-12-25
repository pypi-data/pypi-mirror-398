configure = {
    'type': 'function',
    "schema": 'frame',
    "apply": []
}

def func(frame):
    x = int(frame.x)
    y = int(frame.y)
    z = int(frame.z)
    for m in frame.molecule_list:
        molecule = m['molecule']
        offset = m['offset']
        image={
            'x': [],
            'y': [],
            'z': []
        }
        for atom in molecule.atoms:
            atom_position = atom['offset']
            img_x, new_position_x = divmod(atom_position[0] + offset[0], x)
            img_y, new_position_y = divmod(atom_position[1] + offset[1], y)
            img_z, new_position_z = divmod(atom_position[2] + offset[2], z)
            image['x'].append(img_x)
            image['y'].append(img_y)
            image['z'].append(img_z)

        min_img_x = min(image['x'])
        min_img_y = min(image['y'])
        min_img_z = min(image['z'])
        m['offset'] = (
            offset[0] - min_img_x * x,
            offset[1] - min_img_y * y,
            offset[2] - min_img_z * z
        )