def func(param, all_info, gala_core):
    rigid = param['rigid']
    group_nb = gala_core.ParticleSet(all_info, "non_body")
    group_b = gala_core.ParticleSet(all_info, "body")
    nve = gala_core.NVE(all_info, group_nb)
    if rigid:
        nve_rigid = gala_core.NVERigid(all_info, group_b)
    else:
        nve_rigid = None
    nve.setZeroVel(True, 1)
    nve.setLimit(0.001)
    return nve, nve_rigid
