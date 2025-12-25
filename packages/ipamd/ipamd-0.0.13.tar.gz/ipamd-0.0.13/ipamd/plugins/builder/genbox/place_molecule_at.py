configure = {
    "type": 'function',
    "schema": 'frame',
    "apply": []
}
def func(molecule, x, y, z, frame):
    frame.add_molecule(molecule, offset=[x, y, z])
