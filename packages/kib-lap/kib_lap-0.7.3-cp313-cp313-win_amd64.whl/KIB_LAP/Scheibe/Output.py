import numpy as np


class Output_Class:
    def __init__(self):
        init = None
    def report_nodal_extrema(self,fieldname):
        print("Max. x- Displacement: ", max(fieldname.AssembleMatrix.x_disp), "[m]")
        print("Min. x- Displacement: ", min(fieldname.AssembleMatrix.x_disp), "[m]")
        print("Max. z- Displacement: ", max(fieldname.AssembleMatrix.z_disp), "[m]")
        print("Min. z- Displacement: ", min(fieldname.AssembleMatrix.z_disp), "[m]")

    def report_extrema(self,field_name, arr_2d, gp_xy):
        """
        arr_2d: shape (n_elem, 4)  -> Werte je Element und Gauss-Punkt
        gp_xy : shape (n_elem, 4, 2) -> phys. Koordinaten der Gauss-Punkte
        """
        n_elem, n_gp = arr_2d.shape

        # MAX
        imax = np.argmax(arr_2d)
        emax, gmax = np.unravel_index(imax, arr_2d.shape)
        vmax = float(arr_2d[emax, gmax])
        x_max, y_max = gp_xy[emax, gmax, :]

        # MIN
        imin = np.argmin(arr_2d)
        emin, gmin = np.unravel_index(imin, arr_2d.shape)
        vmin = float(arr_2d[emin, gmin])
        x_min, y_min = gp_xy[emin, gmin, :]

        print(f"\n--- {field_name} ---")
        print(f"MAX: {vmax:.6g}  in Element {emax+1}, GP {gmax+1}  at (x,y)=({x_max:.6g},{y_max:.6g})")
        print(f"MIN: {vmin:.6g}  in Element {emin+1}, GP {gmin+1}  at (x,y)=({x_min:.6g},{y_min:.6g})")