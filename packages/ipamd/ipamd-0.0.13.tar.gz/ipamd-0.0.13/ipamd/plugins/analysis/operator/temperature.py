from ipamd.public.constant import *
def func(frame):
    prop = frame.properties(ignoring_image=False)
    molecules = prop['molecules']
    ek = 0
    freedom = 0
    for molecule in molecules:
        mass_list = molecule['mass']
        vel_list = molecule['velocity']
        n_atoms = len(mass_list)

        rigid_of_last_atom = -1
        for i in range(n_atoms):
            mass_kg = mass_list[i] / na / 1000
            velocity_m_s = [v * 1000 for v in vel_list[i]]

            ek += 0.5 * mass_kg * (velocity_m_s[0] ** 2 + velocity_m_s[1] ** 2 + velocity_m_s[2] ** 2)
            rigid = molecule['rigid_body'][i]
            if rigid == 0:
                if rigid_of_last_atom == -1:
                    freedom += 3
                    rigid_of_last_atom = 0
            else:
                if rigid_of_last_atom == 0:
                    freedom += 3
                    rigid_of_last_atom = -1
                freedom += 3


    temperature = 2 * ek / (freedom * kb)
    return temperature