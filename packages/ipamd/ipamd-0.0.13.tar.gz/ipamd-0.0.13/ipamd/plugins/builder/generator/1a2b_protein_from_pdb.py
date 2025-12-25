from Bio import PDB
from Bio.PDB import PDBParser
from Bio.SeqUtils import seq1
from ipamd.public.models.md import Molecule, Atom
from ipamd.public.utils.output import *
from ipamd.public.utils.parser import range_to_list

configure = {
    "schema": 'io',
    'apply': ['ff']
}
def func(file_name, working_dir, ff, ignoring_h=True, cg='mass_center', rigid_range='', rigid_from_plddt=False, threshold=70, max_gap=4):
    parser = PDBParser(PERMISSIVE=1)
    position_of_last_dot = file_name.rfind('.')
    protein_name = file_name[:position_of_last_dot]
    cg = 'CA' if cg == 'alpha' else 'MC'
    molecule = Molecule(protein_name, cg=cg)
    structure = parser.get_structure(protein_name, working_dir + '/' + file_name)
    model = structure[0]
    #determine the rigid atoms
    rigid_atoms_index = []
    if rigid_range != '':
        tmp = range_to_list(rigid_range)
        for i in tmp:
            rigid_atoms_index.append(i - 1)
    elif rigid_from_plddt:
        for chain_id, chain in enumerate(model):
            for residue_id, residue in enumerate(chain):
                plddt = residue.child_list[0].bfactor
                if plddt > threshold:
                    rigid_atoms_index.append(residue_id)
    else:
        pass

    rigid_groups = []
    for i in rigid_atoms_index:
        if len(rigid_groups) == 0:
            rigid_groups.append([i])
        else:
            if i - rigid_groups[-1][-1] <= max_gap + 1:
                rigid_groups[-1].append(i)
            else:
                rigid_groups.append([i])

    rigid_groups_filtered = []
    for group in rigid_groups:
        if len(group) >= 2:
            rigid_groups_filtered.append(group)
    rigid_groups = rigid_groups_filtered

    for chain_id, chain in enumerate(model):
        sequence = ''
        if chain_id > 0:
            warning('more than one chain detected, only the first chain will be used')
            break
        chain_length = 0
        for residue in chain:
            if PDB.is_aa(residue):
                chain_length += 1

        residue_id = 0
        for residue in chain:
            residue_name = residue.get_resname()
            if PDB.is_aa(residue):
                residue_id += 1
                sequence += seq1(residue_name)
            else:
                if residue_name == 'HOH':
                    continue
                else:
                    error('meet a unknown residue: ' + residue_name)
                    raise ValueError
            ca_coordinate = [0, 0, 0]
            mc_coordinate = [0, 0, 0]
            total_mass = 0
            for atom in residue:
                if atom.name == 'CA':
                    ca_coordinate = [atom.coord[0] / 10, atom.coord[1] / 10, atom.coord[2] / 10]
                if atom.element != 'H':
                    total_mass += atom.mass
                    mc_coordinate[0] += atom.mass * atom.coord[0] / 10
                    mc_coordinate[1] += atom.mass * atom.coord[1] / 10
                    mc_coordinate[2] += atom.mass * atom.coord[2] / 10
                else:
                    if ignoring_h == False:
                        total_mass += atom.mass
                        mc_coordinate[0] += atom.mass * atom.coord[0] / 10
                        mc_coordinate[1] += atom.mass * atom.coord[1] / 10
                        mc_coordinate[2] += atom.mass * atom.coord[2] / 10

            mc_coordinate[0] /= total_mass
            mc_coordinate[1] /= total_mass
            mc_coordinate[2] /= total_mass

            rigid_group = -1
            for group_id, group in enumerate(rigid_groups):
                if residue_id in group:
                    rigid_group = group_id
                    break

            if rigid_group != -1 and cg == 'MC':
                coordinate = mc_coordinate
            else:
                coordinate = ca_coordinate

            res_name_one_word = seq1(residue_name)
            if residue_id == 0:
                custom_mass = f'compute:{ff.atom_definition[res_name_one_word]["mass"]}+1.008'
            elif residue_id == chain_length - 1:
                custom_mass = f'compute:{ff.atom_definition[res_name_one_word]["mass"]}+17.007'
            else:
                custom_mass = None

            molecule.add_atom(
                atom=Atom(
                    velocity=[0, 0, 0],
                    atom_type=res_name_one_word,
                    mass=custom_mass,
                    ff = ff
                ),
                coordinate=coordinate,
                rigid_group=rigid_group,
                bond='B-B'
            )

        info('processed protein with sequence: ' + sequence)
    return molecule