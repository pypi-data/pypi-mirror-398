from ipamd.public.utils.output import warning
import numpy as np
import math
from matplotlib import pyplot as plt

configure = {
    'attr': {
        'target': 'multi'
    }
}
def func(frames):
    if type(frames) is not list:
        frames = [frames]

    n_frames = len(frames)
    if n_frames <= 5:
        warning("Small number of frames may lead to inaccurate results.")
    n_list = []
    r_list = []

    for frame in frames:
        prop = frame.properties(ignoring_image=True)
        molecules = prop['molecules']
        for molecule in molecules:
            molecule_length = molecule['n_atoms']
            total_mass = 0
            p_m = np.array([0, 0, 0], dtype=float)
            for i in range(0, molecule_length):
                total_mass += molecule['mass'][i]
                p_m += molecule['mass'][i] * np.array(molecule['position'][i])
            p_m /= total_mass

            r2_m = 0
            for i in range(0, molecule_length):
                distance2 = np.linalg.norm(np.array(molecule['position'][i]) - p_m) ** 2
                r2_m += distance2 * molecule['mass'][i]
            rg2 = r2_m / total_mass
            n_list.append(math.log2(molecule_length))
            r_list.append(math.log2(rg2)/2)
    plt.scatter(n_list, r_list)
    plt.show()

    A = np.vstack([n_list, np.ones(len(n_list))]).T
    m, b = np.linalg.lstsq(A, r_list, rcond=None)[0]
    print(m, b)
    return m