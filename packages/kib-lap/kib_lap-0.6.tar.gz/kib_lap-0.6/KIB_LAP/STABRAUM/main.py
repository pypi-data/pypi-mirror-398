from Programm import mainloop
from Plotting import StructurePlotter
from Output_Data import OutputData
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt


if __name__ == "__main__":
    calc = mainloop()
    res = calc.run()

    plotter = StructurePlotter(res)
    Output = OutputData()

    calc.check_global_equilibrium()

    # print(type(res), hasattr(res, "Inp"), hasattr(res, "GesMat"), hasattr(res, "u_ges"), hasattr(res, "FGes"))

    # res = calc.run()              

    out = OutputData()
    df = out.support_reactions_from_springs_table(res)
    print(df)

    calc.sum_reactions_fx()
    calc.sum_spring_reactions_fx()

    plotter.plot_support_reactions_2d_interactive()
    plt.show()

    plotter.plot_nodal_loads_2d_interactive()

    plt.show()

    fig, ax, s = plotter.plot_endforces_2d_interactive(kind="MY", scale_init=0.2, node_labels=True, elem_labels=True)

    plt.show()

    fig, ax, s = plotter.plot_endforces_2d_interactive(kind="N", scale_init=0.2, node_labels=True, elem_labels=True)

    plt.show()

    fig, ax, s = plotter.plot_endforces_2d_interactive(kind="VZ", scale_init=0.2, node_labels=True, elem_labels=True)

    plt.show()







