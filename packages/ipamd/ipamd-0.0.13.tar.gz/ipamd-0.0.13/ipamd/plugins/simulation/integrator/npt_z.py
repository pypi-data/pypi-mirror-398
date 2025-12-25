def func(param, all_info, gala_core):
    group = gala_core.ParticleSet(all_info, 'all')
    group_nb = gala_core.ParticleSet(all_info, 'non_body')
    group_b = gala_core.ParticleSet(all_info, 'body')
    comp_info_nb = gala_core.ComputeInfo(all_info, group_nb)
    comp_info_b = gala_core.ComputeInfo(all_info, group_b)
    comp_info = gala_core.ComputeInfo(all_info, group)
    t_reduced = param['temperature'] * 8.3143 / 1000.0
    p = param['pressure']
    rigid = param['rigid']
    npt = gala_core.NPTMTK(all_info, group_nb, comp_info_nb, comp_info, t_reduced, p, 0.5, 1.0)
    npt.setSemiisotropic(0, p)
    npt.setCompressibility(0, 0, 7.47e-4)
    if rigid:
        npt_rigid = gala_core.NPTMTKRigid(all_info, group_b, comp_info_b, comp_info, t_reduced, p, 0.5, 1.0)
        npt_rigid.setSemiisotropic(0, p)
        npt_rigid.setCompressibility(0, 0, 7.47e-4)
    else:
        npt_rigid = None
    return npt,npt_rigid
