from ipamd.public.models.md import Box
configure = {
    "schema": 'io',
    "apply": ["ff"]
}

def func(filename, ff, working_dir):
    box = Box(0, 0, 0, ff, working_dir)
    box.new_frame()
    box.read_xml(filename)
    return box