try:
    from Meshing import *
    from Element_Stiffness import *
    from Assemble_Stiffness import *
except:
    from KIB_LAP.SCHEIBE.Meshing import *
    from KIB_LAP.SCHEIBE.Element_Stiffness import *
    from KIB_LAP.SCHEIBE.Assemble_Stiffness import *

from matplotlib.collections import PatchCollection
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.widgets import Slider


import matplotlib.cm as cm
from tabulate import *
from scipy.interpolate import griddata

class ShellCalculation:
    def __init__(self,MeshingParams = "Meshing_R"):
        self.Meshing_Mode = MeshingParams
        self.Get_Meshing_Parameters()
        self.Get_Material_Parameters()
        self.Get_Element_Matrices()
        self.Assemble_Stiffness_Matrices()
        self.SolveAssembled_Matrix()
        self.StoreElementDisplacements()
        self.CalculateInnerElementForces_Gauss()


    def Get_Meshing_Parameters(self):
        
        
        try:
            self.Meshing_Params = pd.read_csv("Meshing_Parameters/Meshing_Params.csv")
        except:
            self.Meshing_Params = pd.read_csv(
                "../Meshing_Parameters/Meshing_Params.csv"
            )
        _d_1 = self.Meshing_Params.loc[
            self.Meshing_Params["Param"] == "d1", "Value"
        ].values[0]
        _d_2 = self.Meshing_Params.loc[
            self.Meshing_Params["Param"] == "d2", "Value"
        ].values[0]

        _num_x = self.Meshing_Params.loc[
            self.Meshing_Params["Param"] == "num_x", "Value"
        ].values[0]
        _num_y = self.Meshing_Params.loc[
            self.Meshing_Params["Param"] == "num_y", "Value"
        ].values[0]
        if (self.Meshing_Mode == "Meshing_R"):
            self.Meshing = MeshingClass(
                d1=_d_1, d2=_d_2, num_x=int(_num_x), num_y=int(_num_y), elem_type="rect"
            )

            self.Meshing.generating_rectangular_mesh()
        elif (self.Meshing_Mode == "Meshing_RQ"):
            self.Meshing = MeshingClass(d1=0, d2=0, num_x=int(_num_x), num_y=int(_num_y), elem_type="rect")
            self.Meshing.generating_quadrilateral_mesh_from_csv("Meshing_Parameters/Meshing_Params_q.csv")
   

        self.Meshing.plot_elements_rect()

    def Get_Material_Parameters(self):
        try:
            self.Material_Params = pd.read_csv("Material_Parameters/Material.csv")
        except:
            self.Material_Params = pd.read_csv("../Material_Parameters/Material.csv")
        self.E = self.Material_Params.loc[
            self.Material_Params["Parameter"] == "E", "Value"
        ].values[0]
        self.nu = self.Material_Params.loc[
            self.Material_Params["Parameter"] == "nu", "Value"
        ].values[0]
        self.t = self.Material_Params.loc[
            self.Material_Params["Parameter"] == "t", "Value"
        ].values[0]
        self.gamma = self.Material_Params.loc[
            self.Material_Params["Parameter"] == "gamma", "Value"
        ].values[0]

    def Get_Element_Matrices(self):
        self.EL_Matrices = np.zeros((len(self.Meshing.EL), 8, 8))
        self.EL_AreaLoads = np.zeros((8, len(self.Meshing.EL)))
        self.EL_AreaLoads_Nodes = np.zeros((len(self.Meshing.EL), 4))

        for i in range(0, len(self.Meshing.EL), 1):
            coords = np.zeros((4, 2))
            for j in range(0, len(self.Meshing.EL[0]), 1):
                index = int(self.Meshing.EL[i][j])
                _x = self.Meshing.NL[index - 1][0]
                _y = self.Meshing.NL[index - 1][1]
                coords[j][0] = _x
                coords[j][1] = _y

            self.stiffness_matrix = Stiffness_Matrix(
                coords, self.E, self.nu, self.t, self.gamma, self.Meshing
            )
            self.stiffness_matrix.stiffness()

            self.EL_Matrices[i] = self.stiffness_matrix.K

            self.stiffness_matrix.element_load_vector()
            self.EL_AreaLoads[:, i] = self.stiffness_matrix.element_loading_vec
            self.EL_AreaLoads_Nodes[i, :] = self.Meshing.EL[i]

    def Assemble_Stiffness_Matrices(self):
        self.AssembleMatrix = Assembled_Matrices(
            self.Meshing,
            self.Meshing.EL,
            self.Meshing.NL,
            self.EL_Matrices,
            self.stiffness_matrix.node_loading_vec,
            self.stiffness_matrix.node_store_vec,
            self.EL_AreaLoads,
            self.EL_AreaLoads_Nodes,
        )
        self.AssembleMatrix.assemble_K()
        self.AssembleMatrix.Load_BC()
        self.AssembleMatrix.LoadInput()
        self.AssembleMatrix.apply_BC()
        self.AssembleMatrix.GenerateLoadVector()

    def SolveAssembled_Matrix(self):
        self.AssembleMatrix.Solve()

    def StoreElementDisplacements(self):
        self.AssembleMatrix.StoreElementDisplacements()

    def Ns_Mat(self, xi, eta):
        self.Ns_Matrix = np.zeros(
            (self.stiffness_matrix._PD, self.stiffness_matrix._NPE)
        )
        self.Ns_Matrix_T = np.zeros(
            (self.stiffness_matrix._NPE, self.stiffness_matrix._PD)
        )

        if self.stiffness_matrix._NPE == 3:
            self.Ns_Matrix[0][0] = 1
            self.Ns_Matrix[0][1] = 0
            self.Ns_Matrix[0][2] = -1

            self.Ns_Matrix[1][0] = 0
            self.Ns_Matrix[1][1] = 1
            self.Ns_Matrix[1][2] = -1

        if self.stiffness_matrix._NPE == 4:
            self.Ns_Matrix[0][0] = -0.25 * (1 - eta)
            self.Ns_Matrix[0][1] = 0.25 * (1 - eta)
            self.Ns_Matrix[0][2] = 0.25 * (1 + eta)
            self.Ns_Matrix[0][3] = -0.25 * (1 + eta)

            self.Ns_Matrix[1][0] = -0.25 * (1 - xi)
            self.Ns_Matrix[1][1] = -0.25 * (1 + xi)
            self.Ns_Matrix[1][2] = 0.25 * (1 + xi)
            self.Ns_Matrix[1][3] = 0.25 * (1 - xi)

    def E_Mat(self):
        """
        Function to calculate the material matrix for each element \n
        """
        self.E_el = np.zeros((3, 3))

        self.E_el[0][0] = 1
        self.E_el[0][1] = self.nu
        self.E_el[0][2] = 0

        self.E_el[1][0] = self.nu
        self.E_el[1][1] = 1
        self.E_el[1][2] = 0

        self.E_el[2][0] = 0
        self.E_el[2][1] = 0
        self.E_el[2][2] = (1 - self.nu) / 2

        self.E_el *= self.E / (1 - self.nu**2)

    def _q4_dN_dxi_eta(xi, eta):
        # Q4, Knotenreihenfolge: 1(-1,-1), 2(+1,-1), 3(+1,+1), 4(-1,+1)
        dN_dxi = 0.25 * np.array([
            -(1 - eta),
            +(1 - eta),
            +(1 + eta),
            -(1 + eta)
        ], dtype=float)

        dN_deta = 0.25 * np.array([
            -(1 - xi),
            -(1 + xi),
            +(1 + xi),
            +(1 - xi)
        ], dtype=float)

        return dN_dxi, dN_deta


    def _D_plane_stress(E, nu):
        c = E / (1.0 - nu**2)
        return c * np.array([
            [1.0, nu, 0.0],
            [nu, 1.0, 0.0],
            [0.0, 0.0, (1.0 - nu)/2.0]
        ], dtype=float)


    def CalculateInnerElementForces_Gauss(self):
        """
        Rückrechnung an 2x2 Gauss-Punkten je Q4-Element (plane stress).
        Version A: nutzt direkt disp_element_matrix (interleaved: ux1,uy1,ux2,uy2,...)

        Speichert:
        self.gp_xy[e,gp,:]          -> phys. Koord. der Gauss-Punkte
        self.strain_gp[e,gp,:]      -> [eps_x, eps_y, gamma_xy]
        self.stress_gp[e,gp,:]      -> [sigma_x, sigma_y, tau_xy]
        self.stress_elem_avg[e,:]   -> Mittelwert aus 4 GP
        self.n_gp[e,gp,:]           -> [n_x, n_y, n_xy] = stress * t
        self.n_elem_avg[e,:]        -> Mittelwert
        Voraussetzungen:
        - self.Meshing.EL (Elem->4 NodeIDs, 1-basiert)
        - self.Meshing.NL (NodeID-1 -> [x,y])
        - self.AssembleMatrix.disp_element_matrix shape = (8, NoE)
        """

        import numpy as np

        # -------------------------
        # Gauss-Punkte 2x2
        # -------------------------
        gp = 1.0 / np.sqrt(3.0)
        gauss_pts = [(-gp, -gp), (+gp, -gp), (+gp, +gp), (-gp, +gp)]

        def dN_dxi_eta(xi, eta):
            # Q4: 1(-1,-1),2(+1,-1),3(+1,+1),4(-1,+1)
            dN_dxi = 0.25 * np.array([
                -(1 - eta),
                +(1 - eta),
                +(1 + eta),
                -(1 + eta)
            ], dtype=float)

            dN_deta = 0.25 * np.array([
                -(1 - xi),
                -(1 + xi),
                +(1 + xi),
                +(1 - xi)
            ], dtype=float)
            return dN_dxi, dN_deta

        def Nvals(xi, eta):
            return 0.25 * np.array([
                (1 - xi) * (1 - eta),
                (1 + xi) * (1 - eta),
                (1 + xi) * (1 + eta),
                (1 - xi) * (1 + eta)
            ], dtype=float)

        def D_plane_stress(E, nu):
            c = E / (1.0 - nu**2)
            return c * np.array([
                [1.0, nu, 0.0],
                [nu, 1.0, 0.0],
                [0.0, 0.0, (1.0 - nu)/2.0]
            ], dtype=float)

        # -------------------------
        # Elementanzahl + Speicher
        # -------------------------
        n_elem = len(self.Meshing.EL)

        self.gp_xy = np.zeros((n_elem, 4, 2), dtype=float)
        self.strain_gp = np.zeros((n_elem, 4, 3), dtype=float)
        self.stress_gp = np.zeros((n_elem, 4, 3), dtype=float)
        self.n_gp = np.zeros((n_elem, 4, 3), dtype=float)

        # -------------------------
        # Material / Dicke
        # (Passe hier an, falls du elementweise Material in deiner Struktur hast.)
        # -------------------------
        # Fallback: benutze self.E, self.nu, self.t falls vorhanden
        E0 = float(getattr(self, "E", 210e9))
        nu0 = float(getattr(self, "nu", 0.3))
        t0 = float(getattr(self, "t", 1.0))

        # Falls du elementweise Arrays hast (z.B. self.Ee[e]), hier einbauen:
        # E_e = self.Ee[e] else E0 etc.

        # -------------------------
        # Loop über Elemente
        # -------------------------
        for e in range(n_elem):
            el_nodes = self.Meshing.EL[e]  # [n1,n2,n3,n4]
            coords = np.array([self.Meshing.NL[nid - 1] for nid in el_nodes], dtype=float)  # (4,2)

            # ue: interleaved [ux1,uy1,ux2,uy2,ux3,uy3,ux4,uy4]
            ue = np.asarray(self.AssembleMatrix.disp_element_matrix[:, e], dtype=float).reshape(8)

            # Material (hier konstant)
            E = E0
            nu = nu0
            t = t0
            D = D_plane_stress(E, nu)

            for k, (xi, eta) in enumerate(gauss_pts):
                dN_dxi, dN_deta = dN_dxi_eta(xi, eta)

                # Jacobian J = [[dx/dxi, dx/deta],[dy/dxi, dy/deta]]
                J = np.zeros((2, 2), dtype=float)
                J[0, 0] = np.dot(dN_dxi,  coords[:, 0])
                J[0, 1] = np.dot(dN_deta, coords[:, 0])
                J[1, 0] = np.dot(dN_dxi,  coords[:, 1])
                J[1, 1] = np.dot(dN_deta, coords[:, 1])

                detJ = np.linalg.det(J)
                if detJ <= 0:
                    raise ValueError(f"detJ <= 0 in element {e+1}. Check node ordering / mesh.")

                invJ = np.linalg.inv(J)

                # Ableitungen nach x,y
                dN_dx = invJ[0, 0] * dN_dxi + invJ[0, 1] * dN_deta
                dN_dy = invJ[1, 0] * dN_dxi + invJ[1, 1] * dN_deta

                # B-Matrix für interleaved ue:
                # ue = [ux1,uy1,ux2,uy2,ux3,uy3,ux4,uy4]
                B = np.zeros((3, 8), dtype=float)
                for i in range(4):
                    B[0, 2*i + 0] = dN_dx[i]   # eps_x aus ux
                    B[1, 2*i + 1] = dN_dy[i]   # eps_y aus uy
                    B[2, 2*i + 0] = dN_dy[i]   # gamma_xy Anteil aus ux
                    B[2, 2*i + 1] = dN_dx[i]   # gamma_xy Anteil aus uy

                eps = B @ ue          # [eps_x, eps_y, gamma_xy]
                sig = D @ eps         # [sigma_x, sigma_y, tau_xy]

                # GP Position (optional)
                N = Nvals(xi, eta)
                x_gp = float(np.dot(N, coords[:, 0]))
                y_gp = float(np.dot(N, coords[:, 1]))

                self.gp_xy[e, k, :] = [x_gp, y_gp]
                self.strain_gp[e, k, :] = eps
                self.stress_gp[e, k, :] = sig
                self.n_gp[e, k, :] = sig * t  # Membrankräfte pro Länge

        self.stress_elem_avg = np.mean(self.stress_gp, axis=1)  # (n_elem,3)
        self.n_elem_avg = np.mean(self.n_gp, axis=1)            # (n_elem,3)

    def PlotStressAlongCut(self, cut_position, cut_direction="x", field="sigma_x"):
        import numpy as np
        import matplotlib.pyplot as plt
        from scipy.interpolate import griddata

        if not hasattr(self, "stress_elem_avg"):
            self.CalculateInnerElementForces_Gauss()

        field_idx = {"sigma_x": 0, "sigma_y": 1, "tau_xy": 2}
        j = field_idx[field]

        # Elementzentren
        centroids = []
        vals = []
        for e, el in enumerate(self.Meshing.EL):
            coords = np.array([self.Meshing.NL[nid - 1] for nid in el], dtype=float)
            centroids.append(coords.mean(axis=0))
            vals.append(float(self.stress_elem_avg[e, j]))
        centroids = np.array(centroids, dtype=float)  # (n_elem,2)
        vals = np.array(vals, dtype=float)            # (n_elem,)

        # Grid für Interpolation
        grid_x, grid_y = np.mgrid[
            centroids[:, 0].min():centroids[:, 0].max():200j,
            centroids[:, 1].min():centroids[:, 1].max():200j
        ]

        grid_z = griddata(centroids, vals, (grid_x, grid_y), method="linear")

        if cut_direction == "x":
            cut_index = int(np.argmin(np.abs(grid_x[:, 0] - cut_position)))
            cut_vals = grid_z[cut_index, :]
            cut_coords = grid_y[cut_index, :]
            xlabel = "y"
            title = f"{field} along x={cut_position}"
        else:
            cut_index = int(np.argmin(np.abs(grid_y[0, :] - cut_position)))
            cut_vals = grid_z[:, cut_index]
            cut_coords = grid_x[:, cut_index]
            xlabel = "x"
            title = f"{field} along y={cut_position}"

        plt.figure()
        plt.plot(cut_coords, cut_vals, label=title)
        plt.xlabel(xlabel)
        plt.ylabel(field)
        plt.grid(True)
        plt.legend()
        plt.title(title)
        plt.show()
