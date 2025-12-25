def func(ff_param, all_info, gala_core):
    rcut_max = float(ff_param['rcut'])
    neighbor_list = gala_core.NeighborList(all_info, rcut_max * 1.5, rcut_max * 0.2)
    neighbor_list.exclusion(["bond"])
    wf_force = gala_core.WFForce(all_info, neighbor_list, rcut_max)
    atom_type = all_info.getBasicInfo().getParticleTypes()
    for i in range(len(atom_type)):
        for j in range(i, len(atom_type)):
            atom1 = atom_type[i]
            atom2 = atom_type[j]
            type_name_guess_1 = f'{atom1}-{atom2}'
            if type_name_guess_1 in ff_param.keys():
                type_name = type_name_guess_1
            else:
                type_name = f'{atom2}-{atom1}'
            param = ff_param[type_name]
            epsilon = param['epsilon']
            sigma = param['sigma']
            nu = 1
            mu = param['mu']
            rcut = 3 * sigma
            wf_force.setParams(atom1, atom2, epsilon, sigma, nu, mu, rcut)
    return wf_force