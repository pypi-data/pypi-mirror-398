import copy
import numpy as np
from ipamd.public.models.md import Molecule
from ipamd.public.utils.output import warning
configure = {
            'attr': {
                'target': 'multi'
            }
        }

def func(frames, n=None):

    for frame in frames:
        n_molecules = len(frame.molecule_list)
        if n_molecules == 1:
            n = 0
        if n_molecules > 1 and n is None:
            n = 0
            warning('More than one molecule in the frame, only the first molecule will be used for RMSD calculation')
        break

    res = {}
    ref_prop = None
    for index, frame in enumerate(frames):
        frame_tmp = copy.deepcopy(frame)
        if index == 0:
            ref_prop = frame_tmp.properties(filter=str(n), ignoring_image=True)
        prop = frame_tmp.properties(filter=str(n), ignoring_image=True)
        t, R = Molecule.align(prop['molecules'][0], ref_prop['molecules'][0])
        mol0 = frame_tmp.molecule_list[n]['molecule']

        mol0.transform(R, by='center')
        frame_tmp.move_molecule(n, t)
        new_prop = frame_tmp.properties(filter=str(n), ignoring_image=True)
        delta = np.array(new_prop['molecules'][0]['position']) - np.array(ref_prop['molecules'][0]['position'])

        squares_sum = np.sum(delta ** 2, axis=1)
        rmsd = np.sqrt(np.mean(squares_sum))
        res[str(new_prop['no'])] = rmsd

    return res