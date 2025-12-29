from Shell_Calculation import *
from Output import Output_Class
from Plotting import ShellPlotter

Class = ShellCalculation("Meshing_MP")

Output = Output_Class()

Plotting = ShellPlotter(Class)

# Plotting.plot_mesh_with_node_ids()
# Plotting.plot_load_vector_interactive()
# Plotting.plot_deflected_interactive()
# # Displacements

# Output.report_nodal_extrema(Class)

# # Line forces n = stress * t  (n_gp shape: (n_elem,4,3))
# Output.report_extrema("n_x   [MN/m]",  Class.n_gp[:, :, 0], Class.gp_xy)
# Output.report_extrema("n_xy  [MN/m]",  Class.n_gp[:, :, 2], Class.gp_xy)

# # Stresses (stress_gp shape: (n_elem,4,3))
# Output.report_extrema("sigma_x [MN/m^2]", Class.stress_gp[:, :, 0], Class.gp_xy)
# Output.report_extrema("sigma_y [MN/m^2]", Class.stress_gp[:, :, 1], Class.gp_xy)
# Output.report_extrema("tau_xy  [MN/m^2]", Class.stress_gp[:, :, 2], Class.gp_xy)


# Plotting.plot_mesh()
# Plotting.plot_inner_element_forces()
# Plotting.plot_stress_along_cut(10.20, "x", "sigma_x", method="linear")

Plotting.plot_principal_membrane_forces("n1")
Plotting.plot_principal_membrane_forces("n2")