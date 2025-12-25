def func(param, all_info, gala_core):
    all_group = gala_core.ParticleSet(all_info, 'all')
    nb_group = gala_core.ParticleSet(all_info, 'non_body')
    b_group = gala_core.ParticleSet(all_info, 'body')
    t_reduced = param['temperature'] * 8.3143 / 1000.0
    p = param['pressure']
    rigid = param['rigid']
    comp_info_all = gala_core.ComputeInfo(all_info, all_group)
    comp_info_non_body = gala_core.ComputeInfo(all_info, nb_group)
    comp_info_body = gala_core.ComputeInfo(all_info, b_group)

    npt = gala_core.NPT(all_info, nb_group, comp_info_non_body, comp_info_all, t_reduced, p, 0.5, 0.1)
    if rigid:
        npt_rigid = gala_core.NPTRigid(all_info, b_group, comp_info_body, comp_info_all, t_reduced, p, 0.5, 0.1)
    else:
        npt_rigid = None
    return npt, npt_rigid