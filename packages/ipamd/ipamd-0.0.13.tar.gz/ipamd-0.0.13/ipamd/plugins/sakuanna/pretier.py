from Bio.SeqUtils import seq3
from ipamd.public.utils.output import *

configure = {
    "type": 'function',
}

def func(protein, word3=True, ter=True):
    output_str = 'H-' if ter else ''
    seq_length = len(protein)
    seperator = '-' if word3 else ' '
    for idx, res in enumerate(protein.__sequence__):
        if word3:
            output_str += seq3(res)
        else:
            output_str += res
        output_str += seperator if idx < seq_length - 1 else ''
    output_str += '-OH' if ter else ''
    output(f'Protein {protein.__seq_name__}:')
    output(output_str)