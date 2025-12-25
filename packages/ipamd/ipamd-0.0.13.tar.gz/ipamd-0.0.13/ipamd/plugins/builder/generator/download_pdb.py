import pypdbio
from ipamd.public.utils.output import *
configure = {
    "schema": 'io',
}
def func(id, working_dir):
    try:
        pypdbio.fetch(
            id,
            working_dir + '/' + id + '.pdb',
        )
    except Exception:
        error('Failed to download ' + id + ' from RCSB.')
        return
    info('Downloaded ' + id + ' from RCSB.')