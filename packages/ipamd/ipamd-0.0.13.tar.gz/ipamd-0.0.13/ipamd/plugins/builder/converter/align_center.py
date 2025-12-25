from ipamd.public.utils.parser import value_of

configure = {
    'type': 'function',
    "schema": 'frame',
    "apply": []
}

def func(frame):
    x_center = frame.x / 2
    y_center = frame.y / 2
    z_center = frame.z / 2

    env = frame.box.env

    total_mass = 0
    x_mass = 0
    y_mass = 0
    z_mass = 0
    for m in frame.molecules:
        molecule = m['prototype']
        offset = m['offset']
        for atom in molecule.atoms:
            atom_position = atom['offset']
            atom_mass = value_of(atom['prototype'].get('mass'), env)
            total_mass += atom_mass
            x_mass += atom_mass * (atom_position[0] + offset[0])
            y_mass += atom_mass * (atom_position[1] + offset[1])
            z_mass += atom_mass * (atom_position[2] + offset[2])
    x_m_center = x_mass / total_mass
    y_m_center = y_mass / total_mass
    z_m_center = z_mass / total_mass

    delta_x = x_center - x_m_center
    delta_y = y_center - y_m_center
    delta_z = z_center - z_m_center

    for m in frame.molecules:
        offset = m['offset']
        m['offset'] = [
            offset[0] + delta_x,
            offset[1] + delta_y,
            offset[2] + delta_z
        ]