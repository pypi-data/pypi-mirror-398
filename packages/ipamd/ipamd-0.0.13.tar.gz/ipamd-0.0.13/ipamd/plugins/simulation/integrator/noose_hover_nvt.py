def func(param, all_info, gala_core):
    group = gala_core.ParticleSet(all_info, 'non_rigid')
    comp_info = gala_core.ComputeInfo(all_info, group)
    t_reduced = param['temperature'] * 8.3143 / 1000.0
    rigid = param['rigid']
    nh = gala_core.NoseHooverNVT(all_info, group, comp_info, t_reduced, 0.05)
    if rigid:
        group_rigid = gala_core.ParticleSet(all_info, 'rigid')
        nh_rigid = gala_core.NVTRigid(all_info, group_rigid, t_reduced, 0.05)
    return nh, nh_rigid