import subprocess
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
import re
from shutil import copyfile
from ipamd.public.models.sequence import *
configure = {
    "schema": 'io',
}
def func(
    protein_sequence : ProteinSequence,
    working_dir : str
):
    fasta_path = os.path.join(working_dir, protein_sequence.name + '.fasta')
    output_dir = os.path.join(working_dir, protein_sequence.name + '-af')
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    seq = Seq(protein_sequence.sequence)
    seq_record = SeqRecord(seq,
                           id=protein_sequence.name,
                           name=protein_sequence.name,
                           description='')
    with open(fasta_path, "w") as output_handle:
        SeqIO.write(seq_record, output_handle, "fasta")
    info(f'running alphafold2 on sequence {protein_sequence.sequence}')
    subprocess.run(
        [
            'colabfold_batch',
            fasta_path,
            output_dir,
            '--amber'
        ],
        capture_output=True
    )
    info('Alphafold2 finished')
    files = os.listdir(output_dir)
    for file in files:
        pattern = re.compile(rf'^{protein_sequence.name}_relaxed.*001.*.pdb$')
        if pattern.match(file):
            pdb_path = os.path.join(output_dir, file)
            new_pdb_path = os.path.join(working_dir, f"{protein_sequence.name}.pdb")
            copyfile(pdb_path, new_pdb_path)
