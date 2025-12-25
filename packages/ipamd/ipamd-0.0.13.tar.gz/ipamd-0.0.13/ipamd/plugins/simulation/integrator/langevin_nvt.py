import random
def func(param, all_info, gala_core):
    group_nb = gala_core.ParticleSet(all_info, 'non_body')
    group_b = gala_core.ParticleSet(all_info, 'body')
    t_reduced = param['temperature'] * 8.3143 / 1000.0
    nvt = gala_core.LangevinNVT(all_info, group_nb, t_reduced, random.randint(1, 100))
    rigid = param['rigid']
    if rigid:
        nvt_rigid = gala_core.LangevinNVTRigid(all_info, group_b, t_reduced, random.randint(1, 100))
        nvt_rigid.setGamma(0.01)
    else:
        nvt_rigid = None
    nvt.setGamma(0.001)

    return nvt, nvt_rigid
