import os.path
import numpy as np
from Bio.PDB import Structure, Model, Chain, Residue, Atom, MMCIFIO
from Bio.SeqUtils import seq3
configure = {
    'type': 'function',
    "schema": 'frame',
    "apply": ['persistency_dir']
}

def func(filename, persistency_dir, frame, ignoring_pbc = True):
    prop = frame.properties(ignoring_image=ignoring_pbc)
    molecules = prop['molecules']

    structure = Structure.Structure("structure")
    model = Model.Model(0)
    structure.add(model)
    n_total = 0
    for i_molecule, molecule in enumerate(molecules):
        chain = Chain.Chain(str(i_molecule + 1))
        model.add(chain)
        for i, type_ in enumerate(molecule['type']):
            residue = Residue.Residue((' ', i + 1, ' '), seq3(type_), ' ')
            atom = Atom.Atom(
                name=type_,
                coord=np.multiply(molecule['position'][i], 10),
                bfactor=0.0,
                occupancy=1.0,
                altloc=' ',
                fullname=type_,
                element='N',
                serial_number=i + n_total +1,
            )
            residue.add(atom)
            chain.add(residue)
        n_total += len(molecule['type'])
    io = MMCIFIO()
    io.set_structure(structure)

    cif_filename = os.path.join(persistency_dir, filename)
    io.save(cif_filename)