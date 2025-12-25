def func(ff_param, all_info, gala_core):
    rcut = ff_param['rcut']
    n_grid_x = ff_param['n_grid_x']
    n_grid_y = ff_param['n_grid_y']
    n_grid_z = ff_param['n_grid_z']
    neighbor_list = gala_core.NeighborList(all_info, rcut, rcut * 0.2)
    neighbor_list.exclusion(["bond"])

    group = gala_core.ParticleSet(all_info, "charge")
    pm_force = gala_core.PMForce(all_info, neighbor_list, group)
    pm_force.setParams(int(2 ** n_grid_x), int(2 ** n_grid_y), int(2 ** n_grid_z), 3, rcut)
    kappa = pm_force.getKappa()

    ewald_force = gala_core.EwaldForce(all_info, neighbor_list, group, rcut)
    ewald_force.setParams(kappa)
    return [pm_force, ewald_force]
