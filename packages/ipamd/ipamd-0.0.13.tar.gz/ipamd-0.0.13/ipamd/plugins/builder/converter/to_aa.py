import os
from ipamd.public.utils.plugin_manager import PluginBase
import subprocess
configure = {
    "apply": ['persistency_dir']
}
def func(filename, persistency_dir):
    PluginBase.call('to_pdb', 'temp_cg', atom_type_override='CA')
    subprocess.run(
        [
            'convert_cg2all',
            '-p',
            f'{persistency_dir}/temp_cg.pdb',
            '-o',
            f'{persistency_dir}/{filename}.pdb'
        ],
        capture_output=True
    )
    os.remove(f'{persistency_dir}/temp_cg.pdb')
