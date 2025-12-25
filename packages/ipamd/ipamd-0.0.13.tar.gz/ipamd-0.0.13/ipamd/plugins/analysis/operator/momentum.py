from ipamd.public.constant import *
def func(frame):
    prop = frame.properties(ignoring_image=False)
    molecules = prop['molecules']
    px = 0
    py = 0
    pz = 0
    for molecule in molecules:
        mass_list = molecule['mass']
        vel_list = molecule['velocity']
        n_atoms = len(mass_list)
        for i in range(n_atoms):
            mass_kg = mass_list[i] / na / 1000
            velocity_m_s = [v * 1000 for v in vel_list[i]]
            px += mass_kg * velocity_m_s[0]
            py += mass_kg * velocity_m_s[1]
            pz += mass_kg * velocity_m_s[2]

    data = {
        'px': px,
        'py': py,
        'pz': pz
    }
    return data