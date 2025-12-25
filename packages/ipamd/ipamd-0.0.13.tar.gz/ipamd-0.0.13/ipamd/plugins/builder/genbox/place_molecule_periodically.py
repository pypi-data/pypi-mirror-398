configure = {
    "type": 'function',
    "schema": 'frame',
    "apply": []
}
def func(molecule, nx, ny, nz, frame):
    x = frame.box.x
    y = frame.box.y
    z = frame.box.z
    dx = x / nx
    dy = y / ny
    dz = z / nz
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                offset = [i * dx + 0.5 * dx, j * dy + 0.5 * dy, k * dz + 0.5 * dz]
                frame.add_molecule(molecule, offset=offset)
