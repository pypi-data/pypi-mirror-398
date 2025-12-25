from ipamd.public.utils.plugin_manager import PluginBase
from ipamd.public.models.md import Molecule, Atom
from ipamd.public.utils.output import warning, info
import numpy as np
configure = {
    "schema": 'frame',
    "apply": ['ff']
}
def func(frame, ff):
    atom_definition = ff.atom_definition
    if 'NA' not in atom_definition or 'CL' not in atom_definition:
        warning('neutral system is not needed')
        return

    props = frame.properties()
    charge = 0

    for molecule_properties in props['molecules']:
        charge_prop = molecule_properties['charge']
        charge += sum(charge_prop)
    if charge == 0:
        info('system is already neutral')
        return
    elif charge > 0:
        target_ion_name = 'CL'
    else:
        target_ion_name = 'NA'
    n, d = divmod(np.abs(charge), 1)
    mol = Molecule(target_ion_name, cg='CA')
    mol.add_atom(
        Atom(
            velocity=(0, 0, 0),
            atom_type=target_ion_name,
            ff=ff
        ),
        (0, 0, 0)
    )
    PluginBase.call('place_molecule_randomly',  mol, n, strict=True)
    mol1 = Molecule(target_ion_name, cg='CA')
    mol1.add_atom(
        Atom(
            velocity=(0, 0, 0),
            atom_type=target_ion_name,
            ff=ff,
            charge=d
        ),
        (0, 0, 0)
    )
    PluginBase.call('place_molecule_randomly',  mol1, 1, strict=True)
    info('enneutral system completed')