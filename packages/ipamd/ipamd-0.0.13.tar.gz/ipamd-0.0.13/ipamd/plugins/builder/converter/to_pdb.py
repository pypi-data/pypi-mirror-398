import os.path
from ipamd.public.utils.output import warning
from ipamd.public.utils.pdb import PdbWriter
from Bio.SeqUtils import seq3
configure = {
    'type': 'function',
    "schema": 'frame',
    "apply": ['persistency_dir']
}

def func(filename, persistency_dir, frame, ignoring_pbc = True, atom_type_override=''):
    prop = frame.properties(ignoring_image=ignoring_pbc)
    molecules = prop['molecules']
    n_molecules = len(molecules)
    if n_molecules >= 26:
        warning('Chain number exceeds the limit of pdb file. Use cif instead.')

    writer = PdbWriter(os.path.join(persistency_dir, filename + '.pdb'))

    n_total = 0
    for i_molecule, molecule in enumerate(molecules):
        chain_id = chr(65 + i_molecule % 26)
        for i, type_ in enumerate(molecule['type']):
            atom_info = {
                'type': 'ATOM',
                "atom_no": i + 1 + n_total,
                "atom_name": type_ if atom_type_override == '' else atom_type_override,
                "residue_name": seq3(type_).upper(),
                "chain_id": chain_id,
                "residue_id": i + 1,
                "coord_x": molecule['position'][i][0],
                "coord_y": molecule['position'][i][1],
                "coord_z": molecule['position'][i][2],
                "temp_factor": 1.0,
                "element": 'CA',
                "charge": molecule['charge'][i]
            }
            writer.write_line(atom_info)
        writer.write_ter()
        n_total += len(molecule['type'])
    writer.end()