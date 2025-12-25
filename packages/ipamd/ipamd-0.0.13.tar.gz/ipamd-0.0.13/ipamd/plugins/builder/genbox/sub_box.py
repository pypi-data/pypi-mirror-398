configure = {
    "type": 'function',
    "schema": 'frame',
    "apply": []
}
def func(sub_box, x, y, z, frame):
    for molecule in sub_box.current_frame().molecules:
        offset = molecule['offset']
        mol = molecule['prototype']

        frame.add_molecule(mol,
                           offset=(
                               offset[0] + x,
                               offset[1] + y,
                               offset[2] + z
                           ))
