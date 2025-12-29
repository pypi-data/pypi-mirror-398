# STABRAUM-Dependencies
try:
    from Steifigkeitsmatrix import *
    from InputData import Input
    from results import AnalysisResults
except:
    from KIB_LAP.STABRAUM.Steifigkeitsmatrix import *
    from KIB_LAP.STABRAUM.InputData import Input
    from KIB_LAP.STABRAUM.results import AnalysisResults


import sympy as sp

import matplotlib.pyplot as plt
import numpy as np

from mpl_toolkits.mplot3d import Axes3D  # nötig für 3D-Plots
import matplotlib.patches as mpatches
from matplotlib.widgets import Slider
from mpl_toolkits.mplot3d.art3d import Line3DCollection


def _set_axes_equal(ax, extra: float = 0.0):
    """
    Erzwingt identische numerische Achsenlimits.
    optional: 'extra' = zusätzlicher Rand als Prozentsatz (0-1).
    """
    import numpy as np

    # aktuelle Grenzen holen
    x_limits = np.array(ax.get_xlim3d())
    y_limits = np.array(ax.get_ylim3d())
    z_limits = np.array(ax.get_zlim3d())

    # Spannweiten & gemeinsames Maximum
    ranges = np.array([np.ptp(lim) for lim in (x_limits, y_limits, z_limits)])
    max_range = ranges.max()

    # sind alle Punkte (fast) in einer Ebene? -> Mindestspanne ansetzen
    if max_range == 0:
        max_range = 1.0  # beliebiger Würfel von 1 m

    # Mittelpunkt­koordinaten
    mids = np.array([lim.mean() for lim in (x_limits, y_limits, z_limits)])

    half = (1 + extra) * max_range / 2
    ax.set_xlim3d(mids[0] - half, mids[0] + half)
    ax.set_ylim3d(mids[1] - half, mids[1] + half)
    ax.set_zlim3d(mids[2] - half, mids[2] + half)

    # Darstellungswürfel in aktuellen MPL-Versionen
    try:
        ax.set_box_aspect((1, 1, 1))
    except AttributeError:
        pass


class mainloop:
    def __init__(self):
        ##________ Subclasses __________##
        self.Inp = Input()
        self.ElemStem = ElemStema()
        ##_____ Class variables ___________##
        self.K_el_i_store = np.zeros((len(self.Inp.members), 14, 14))

        self.MY_el_i_store = np.zeros((len(self.Inp.members), 2, 1))
        self.VZ_el_i_store = np.zeros((len(self.Inp.members), 2, 1))

        self.MZ_el_i_store = np.zeros((len(self.Inp.members), 2, 1))
        self.VY_el_i_store = np.zeros((len(self.Inp.members), 2, 1))
        self.MX_el_i_store = np.zeros((len(self.Inp.members), 2, 1))

        self.MTP_el_i_store = np.zeros((len(self.Inp.members), 2, 1))
        self.MTS_el_i_store = np.zeros((len(self.Inp.members), 2, 1))
        self.N_el_i_store = np.zeros((len(self.Inp.members), 2, 1))

    # ------------------------------------------------------------
    # DEBUG / SINGULARITÄTSTEST
    # ------------------------------------------------------------
    def check_singularity(self, K=None, tol_row=1e-10, tol_rank=1e-8, verbose=True):
        """
        Prüft typische Ursachen für Singularität:
        - Rank-Defizit
        - Nullzeilen/Nullspalten (DOFs ohne Steifigkeit)
        - isolierte Knoten (nicht in members)
        - 0-Längen-Elemente
        Gibt ein Dict mit Diagnosen zurück.
        """
        if K is None:
            K = self.GesMat

        info = {}

        # -------- Rank --------
        try:
            r = np.linalg.matrix_rank(K, tol=tol_rank)
        except TypeError:
            # falls numpy Version keine tol als kw hat
            r = np.linalg.matrix_rank(K)
        n = K.shape[0]
        info["rank"] = int(r)
        info["n"] = int(n)
        info["deficit"] = int(n - r)

        # -------- Nullzeilen/Nullspalten --------
        row_norm = np.linalg.norm(K, axis=1)
        col_norm = np.linalg.norm(K, axis=0)
        zero_rows = np.where(row_norm < tol_row)[0]
        zero_cols = np.where(col_norm < tol_row)[0]

        info["zero_rows"] = zero_rows.tolist()
        info["zero_cols"] = zero_cols.tolist()

        # -------- DOF Mapping (nur wenn 7 dof/node) --------
        def gdof_to_node_ldof(gdof):
            return int(gdof // 7 + 1), int(gdof % 7)

        info["zero_rows_nodes"] = [gdof_to_node_ldof(i) for i in zero_rows]
        info["zero_cols_nodes"] = [gdof_to_node_ldof(i) for i in zero_cols]

        # -------- isolierte Knoten --------
        try:
            na = list(self.Inp.members["na"])
            ne = list(self.Inp.members["ne"])
            used = set(na) | set(ne)
            all_nodes = set(range(1, len(self.Inp.nodes["x[m]"]) + 1))
            isolated = sorted(all_nodes - used)
        except Exception:
            isolated = []
        info["isolated_nodes"] = isolated

        # -------- 0-Längen-Elemente --------
        zero_len_elems = []
        try:
            for eidx, (a, e) in enumerate(zip(self.Inp.members["na"], self.Inp.members["ne"]), start=1):
                xa = self.Inp.nodes["x[m]"][a-1]; ya = self.Inp.nodes["y[m]"][a-1]; za = self.Inp.nodes["z[m]"][a-1]
                xb = self.Inp.nodes["x[m]"][e-1]; yb = self.Inp.nodes["y[m]"][e-1]; zb = self.Inp.nodes["z[m]"][e-1]
                L = float(np.sqrt((xa-xb)**2 + (ya-yb)**2 + (za-zb)**2))
                if L < 1e-12:
                    zero_len_elems.append((eidx, int(a), int(e)))
        except Exception:
            pass
        info["zero_length_elements"] = zero_len_elems

        # -------- Ausgabe --------
        if verbose:
            print("\n=== Singularity check ===")
            print(f"size n = {n}, rank = {r}, deficit = {n-r}")
            print(f"zero rows: {len(zero_rows)}, zero cols: {len(zero_cols)}")
            if len(zero_rows) > 0:
                print("first zero rows (gdof -> node,ldof):")
                for gdof in zero_rows[:30]:
                    node, ldof = gdof_to_node_ldof(gdof)
                    print(f"  gdof {gdof:4d} -> node {node}, ldof {ldof}")
            if len(isolated) > 0:
                print("isolated nodes:", isolated)
            if len(zero_len_elems) > 0:
                print("zero-length elements (eid, na, ne):", zero_len_elems)

        return info



    def CalculateTransMat(self):
        print("Calculate Transmatrices")

        TransformationMatrices = np.zeros((len(self.Inp.members), 14, 14))
        na_memb = self.Inp.members["na"]
        ne_memb = self.Inp.members["ne"]
        for i in range(len(self.Inp.members["na"])):

            node_i = na_memb[i]  # Node number for node i of this member
            node_j = ne_memb[i]  # Node number for node j of this member

            # Index of DoF for this member
            ia = 2 * node_i - 2  # horizontal DoF at node i of this member
            ib = 2 * node_i - 1  # vertical DoF at node i of this member
            ja = 2 * node_j - 2  # horizontal DoF at node j of this member
            jb = 2 * node_j - 1  # vertical DoF at node j of this member

            # New positions = initial pos + cum deflection
            ix = self.Inp.nodes["x[m]"][node_i - 1]
            iy = self.Inp.nodes["y[m]"][node_i - 1]
            iz = self.Inp.nodes["z[m]"][node_i - 1]

            jx = self.Inp.nodes["x[m]"][node_j - 1]
            jy = self.Inp.nodes["y[m]"][node_j - 1]
            jz = self.Inp.nodes["z[m]"][node_j - 1]

            TM = self.ElemStem.TransformationMatrix([ix, iy, iz], [jx, jy, jz])

            TransformationMatrices[i, :, :] = TM
        print("Transmat")
        print(TransformationMatrices[0])
        return TransformationMatrices

    def BuildStructureStiffnessMatrix(self):
        """
        Standard construction of Primary and Structure stiffness matrix
        Construction of non-linear element stiffness matrix handled in a child function
        """
        Kp = np.zeros(
            [self.Inp.nDoF, self.Inp.nDoF]
        )  # Initialise the primary stiffness matrix
        self.member_length = []

        na_memb = self.Inp.members["na"]
        ne_memb = self.Inp.members["ne"]
        crosssec_members = self.Inp.members["cs"]

        for i in range(0, len(self.Inp.members["na"]), 1):
            node_i = na_memb[i]  # Node number for node i of this member
            node_j = ne_memb[i]  # Node number for node j of this member

            # New positions = initial pos + cum deflection
            ix = self.Inp.nodes["x[m]"][node_i - 1]
            iy = self.Inp.nodes["y[m]"][node_i - 1]
            iz = self.Inp.nodes["z[m]"][node_i - 1]

            jx = self.Inp.nodes["x[m]"][node_j - 1]
            jy = self.Inp.nodes["y[m]"][node_j - 1]
            jz = self.Inp.nodes["z[m]"][node_j - 1]

            dx = abs(ix - jx)
            dy = abs(iy - jy)
            dz = abs(iz - jz)

            length = np.sqrt(dx**2 + dy**2 + dz**2)
            self.member_length.append(length)

            num_cs = crosssec_members[i]
            mat_num_i = self.Inp.CrossSection.loc[
                self.Inp.CrossSection["No"] == num_cs, "material"
            ].iloc[0]

            I_y_i = self.Inp.CrossSection.loc[
                self.Inp.CrossSection["No"] == num_cs, "Iy"
            ].iloc[0]
            I_z_i = self.Inp.CrossSection.loc[
                self.Inp.CrossSection["No"] == num_cs, "Iz"
            ].iloc[0]
            A_i = self.Inp.CrossSection.loc[
                self.Inp.CrossSection["No"] == num_cs, "A"
            ].iloc[0]
            I_w_i = self.Inp.CrossSection.loc[
                self.Inp.CrossSection["No"] == num_cs, "Iw"
            ].iloc[0]
            I_T_i = self.Inp.CrossSection.loc[
                self.Inp.CrossSection["No"] == num_cs, "It"
            ].iloc[0]

            print("Material NUmber")
            print(mat_num_i)

            E_i = self.Inp.Material.loc[self.Inp.Material["No"] == mat_num_i, "E"].iloc[
                0
            ]
            G_i = self.Inp.Material.loc[self.Inp.Material["No"] == mat_num_i, "G"].iloc[
                0
            ]
            print("Material E_i")
            print(E_i)

            K_el_i = self.ElemStem.insert_elements(
                S=0,
                E=E_i,
                G=G_i,
                A=A_i,
                I_y=I_y_i,
                I_z=I_z_i,
                I_omega=I_w_i,
                I_T=I_T_i,
                cv=0,
                z1=0,
                cw=0,
                z2=0,
                c_thet=0,
                l=length,
            )

            K_el_i = np.matmul(
                self.TransMats[i], np.matmul(K_el_i, self.TransMats[i].T)
            )

            self.K_el_i_store[i] = K_el_i

            K_11 = K_el_i[0:7, 0:7]
            K_12 = K_el_i[0:7, 7:14]
            K_21 = K_el_i[7:14, 0:7]
            K_22 = K_el_i[7:14, 7:14]

            Kp[
                7 * (node_i - 1) : 7 * (node_i - 1) + 7,
                7 * (node_i - 1) : 7 * (node_i - 1) + 7,
            ] += K_11

            Kp[
                7 * (node_i - 1) : 7 * (node_i - 1) + 7,
                7 * (node_j - 1) : 7 * (node_j - 1) + 7,
            ] += K_12

            Kp[
                7 * (node_j - 1) : 7 * (node_j - 1) + 7,
                7 * (node_i - 1) : 7 * (node_i - 1) + 7,
            ] += K_21

            Kp[
                7 * (node_j - 1) : 7 * (node_j - 1) + 7,
                7 * (node_j - 1) : 7 * (node_j - 1) + 7,
            ] += K_22

        return Kp

    def RestraintData(self):
        """
        This functions implements the restraint data, which is loaded from the \n
        input file. \n
        There are 7 DOF's per node. \n
        Therefore the restrained DOF in the global stiffness matrix can be expressed by: \n
        GDOF = 7 * (node-1) + DOF \n
        """
        res_nodes = self.Inp.RestraintData["Node"]
        res_dof = self.Inp.RestraintData["Dof"]
        res_stif = self.Inp.RestraintData["Cp[MN/m]/[MNm/m]"]

        for i in range(len(res_dof)):
            glob_dof = 7 * (res_nodes[i] - 1) + res_dof[i]
            print("restrain ", glob_dof)
            self.GesMat[glob_dof, glob_dof] += res_stif[i]

    def LocalLoadVectorLine(self):
        """
        Lokale Festendkräfte aus Linienlasten (lokales System!).
        Speichert in self.S_loc_elem_line und gibt dieses Array zurück.
        """
        n_elem = len(self.Inp.members["na"])
        self.S_loc_elem_line = np.zeros((14, n_elem), dtype=float)

        res_mbr    = self.Inp.ElementLoads["Member"]
        res_line_a = self.Inp.ElementLoads["qza"]
        res_line_b = self.Inp.ElementLoads["qze"]  # aktuell nicht benutzt

        for k in range(len(res_mbr)):
            e = int(res_mbr[k] - 1)

            L = float(self.member_length[e])
            q = float(res_line_a[k])  # TODO: falls qza != qze -> konsistente Formeln

            # Lokale Festendkräfte (deine Konvention beibehalten)
            # Vz
            self.S_loc_elem_line[3,  e]  += +q * L / 2.0
            self.S_loc_elem_line[10, e]  += +q * L / 2.0

            # My
            self.S_loc_elem_line[4,  e]  += -q * L**2 / 12.0
            self.S_loc_elem_line[11, e]  += +q * L**2 / 12.0

        return self.S_loc_elem_line
    
    def LocalLoadVectorTemp(self):
        """
        Lokale Festendkräfte aus Temperatur (lokales System!).
        Speichert in self.S_loc_elem_temp und gibt dieses Array zurück.
        """
        n_elem = len(self.Inp.members["na"])
        self.S_loc_elem_temp = np.zeros((14, n_elem), dtype=float)

        res_mbr     = self.Inp.TemperatureForces["Member"]
        res_tem_dT  = self.Inp.TemperatureForces["dT[K]"]
        res_tem_dTz = self.Inp.TemperatureForces["dTz[K]"]
        res_tem_dTy = self.Inp.TemperatureForces["dTy[K]"]

        for k in range(len(res_mbr)):
            e = int(res_mbr[k] - 1)

            EA = self.ElemStem.E * self.ElemStem.A
            EIz = self.ElemStem.E * self.ElemStem.I_z
            EIy = self.ElemStem.E * self.ElemStem.I_y

            dT  = float(res_tem_dT[k])
            dTz = float(res_tem_dTz[k])
            dTy = float(res_tem_dTy[k])

            # N
            self.S_loc_elem_temp[0, e]  += -EA  * 1e-5 * dT
            self.S_loc_elem_temp[7, e]  += +EA  * 1e-5 * dT

            # Mz
            self.S_loc_elem_temp[2, e]  += -EIz * 1e-5 * dTy
            self.S_loc_elem_temp[9, e]  += +EIz * 1e-5 * dTy

            # My
            self.S_loc_elem_temp[4, e]  += -EIy * 1e-5 * dTz
            self.S_loc_elem_temp[11,e]  += +EIy * 1e-5 * dTz

        return self.S_loc_elem_temp

    def GlobalLoadVector(self):
        """
        Globaler Lastvektor:
        - Element-Festendkräfte (Temp + Linienlast) lokal -> global via T
        - Knotenlasten (global) addieren
        """
        # erzeugt/updated self.S_loc_elem_temp / self.S_loc_elem_line
        self.LocalLoadVectorTemp()
        self.LocalLoadVectorLine()

        n_elem = len(self.Inp.members["na"])
        F_glob = np.zeros(self.Inp.nDoF, dtype=float)

        na_memb = self.Inp.members["na"]
        ne_memb = self.Inp.members["ne"]

        for e in range(n_elem):
            node_i = int(na_memb[e])
            node_j = int(ne_memb[e])

            base_i = 7 * (node_i - 1)
            base_j = 7 * (node_j - 1)

            F_e_loc = (self.S_loc_elem_temp[:, e] + self.S_loc_elem_line[:, e]).reshape(14, 1)

            T = self.TransMats[e]              # local -> global
            F_e_glob = (T @ F_e_loc).ravel()   # (14,)

            F_glob[base_i:base_i+7] += F_e_glob[0:7]
            F_glob[base_j:base_j+7] += F_e_glob[7:14]

        # Knotenlasten (global)
        res_nodes = self.Inp.NodalForces["Node"]
        res_dof   = self.Inp.NodalForces["Dof"]
        res_forc  = self.Inp.NodalForces["Value[MN/MNm]"]

        for k in range(len(res_nodes)):
            node = int(res_nodes[k])
            base = 7 * (node - 1)
            dof  = str(res_dof[k]).strip().lower()

            if dof == "fx":
                idx = base + 0
            elif dof == "fy":
                idx = base + 1
            elif dof == "fz":
                idx = base + 3
            else:
                continue

            F_glob[idx] += float(res_forc[k])

        return F_glob

    def SolveDisplacement(self):
        u_glob = np.linalg.solve(self.GesMat, self.FGes)
        return u_glob

    def StoreLocalDisplacements(self):
        u_el = np.zeros(
            [14, len(self.Inp.members["na"])]
        )  # Initialise the primary stiffness matrix

        na_memb = self.Inp.members["na"]
        ne_memb = self.Inp.members["ne"]

        for i in range(0, len(self.Inp.members["na"]), 1):
            numa = 7 * (na_memb[i] - 1)
            nume = 7 * (ne_memb[i] - 1)

            u_el[0:7, i] = self.u_ges[numa : numa + 7]
            u_el[7:14, i] = self.u_ges[nume : nume + 7]

            # u_el[:,i] = np.matmul(self.TransMats[i],u_el[:,i])

        return u_el

    def CalculateLocalInnerForces(self):
        """
        Berechnet lokale Schnittgrößen an linkem und rechtem Schnittufer:

        - f_glob = K_el_global @ u_el_global  (wie bei dir gespeichert)
        - f_loc  = T.T @ f_glob               (global -> local, da T local->global)
        - f_eff  = f_loc - (f0_temp_loc + f0_line_loc)

        Konvention:
        - Linkes Schnittufer:   s_L = - f_I,loc
        - Rechtes Schnittufer:  s_R = + f_J,loc
        - Zug positiv

        Ergebnis in self.*_el_i_store[i] jeweils als (2,1): [links; rechts]
        """

        n_elem = len(self.Inp.members["na"])
        s_el = np.zeros((14, n_elem), dtype=float)

        # Hole (lokale) Festendkräfte. Falls du die Arrays noch nicht als Attribute speicherst,
        # werden sie hier neu erzeugt.
        F_loc_temp = self.LocalLoadVectorTemp()
        F_loc_line = self.LocalLoadVectorLine()

        for e in range(n_elem):

            # 1) Element-Endkräfte aus K*u (im Koordinatensystem von K_el_i_store & u_el)
            f_glob = (self.K_el_i_store[e] @ self.u_el[:, e]).reshape(14, 1)
            s_el[:, e] = f_glob.ravel()

            # 2) global -> local
            T = self.TransMats[e]          # local -> global
            f_loc = T.T @ f_glob           # global -> local

            # 3) lokale Festendkräfte (Temp + Linienlast)
            f0_loc = (F_loc_temp[:, e] + F_loc_line[:, e]).reshape(14, 1)

            # 4) wirksame lokale Endkräfte
            f_eff = f_loc - f0_loc

            # 5) Schnittufer-Abbildung: links = -f_I, rechts = +f_J
            # Indizes laut Layout:
            # [0] Na  [1] Vya [2] Mza [3] Vza [4] Mya [5] Mxa [6] Mwa
            # [7] Nb  [8] Vyb [9] Mzb [10]Vzb [11]Myb [12]Mxb [13]Mwb

            N_L,  N_R  = -f_eff[0, 0],   f_eff[7, 0]
            Vy_L, Vy_R = -f_eff[1, 0],   f_eff[8, 0]
            Mz_L, Mz_R = -f_eff[2, 0],   f_eff[9, 0]
            Vz_L, Vz_R = -f_eff[3, 0],   f_eff[10,0]
            My_L, My_R = -f_eff[4, 0],   f_eff[11,0]
            Mx_L, Mx_R = -f_eff[5, 0],   f_eff[12,0]

            self.N_el_i_store[e]  = np.array([N_L,  N_R ]).reshape(2, 1)
            self.VY_el_i_store[e] = np.array([Vy_L, Vy_R]).reshape(2, 1)
            self.VZ_el_i_store[e] = np.array([Vz_L, Vz_R]).reshape(2, 1)

            self.MZ_el_i_store[e] = np.array([Mz_L, Mz_R]).reshape(2, 1)
            self.MY_el_i_store[e] = np.array([My_L, My_R]).reshape(2, 1)
            self.MX_el_i_store[e] = np.array([Mx_L, Mx_R]).reshape(2, 1)

        return s_el

    def MainConvergence(self):

        self.TransMats = self.CalculateTransMat()
        self.GesMat = self.BuildStructureStiffnessMatrix()

        self.RestraintData()

        # <<< HIER: Singularitäts-Check >>>
        self.check_singularity(self.GesMat, verbose=True)

        self.FGes = self.GlobalLoadVector()

        self.u_ges = self.SolveDisplacement()

        self.u_el = self.StoreLocalDisplacements()

        self.s_el = self.CalculateLocalInnerForces()

    def run(self) -> AnalysisResults:
        """
        Führt die komplette Berechnung aus und gibt ein Results-Objekt zurück.
        """
        self.MainConvergence()

        return AnalysisResults(
            Inp=self.Inp,
            u_ges=self.u_ges,
            GesMat=self.GesMat,
            FGes=self.FGes,
            TransMats=self.TransMats,
            K_el_i_store=self.K_el_i_store,
            u_el=self.u_el,
            s_el=self.s_el,
            N_el_i_store=self.N_el_i_store,
            VY_el_i_store=self.VY_el_i_store,
            VZ_el_i_store=self.VZ_el_i_store,
            MX_el_i_store=self.MX_el_i_store,
            MY_el_i_store=self.MY_el_i_store,
            MZ_el_i_store=self.MZ_el_i_store,
            member_length=np.array(self.member_length, dtype=float),
        )

    def check_global_equilibrium(self):
        r = (self.GesMat @ self.u_ges - self.FGes).ravel()  # Reaktionsvektor auf allen DOFs

        # welche DOFs sind "gelagert"? (klassisch: Cp groß oder Fix)
        # Bei dir: RestraintData addiert Cp auf Diagonale.
        # -> als Näherung: DOF ist gelagert, wenn Cp > 0 in Input.
        restrained = np.zeros_like(r, dtype=bool)
        for _, row in self.Inp.RestraintData.iterrows():
            gdof = 7*(int(row["Node"])-1) + int(row["Dof"])
            restrained[gdof] = True

        free = ~restrained

        print("max residual on FREE dofs:", np.max(np.abs(r[free])))
        print("sum residual on FREE dofs:", np.sum(r[free]))

    def debug_single_fx(self, node=2, Fx=1.0):
        # setze alle Lasten leer
        self.Inp.ElementLoads = self.Inp.ElementLoads.iloc[0:0].copy()
        self.Inp.TemperatureForces = self.Inp.TemperatureForces.iloc[0:0].copy()
        self.Inp.NodalForces = self.Inp.NodalForces.iloc[0:0].copy()

        # eine Last
        import pandas as pd
        self.Inp.NodalForces = pd.DataFrame([{"Node":node, "Dof":"Fx", "Value[MN/MNm]":Fx}])

        self.MainConvergence()

        ux = self.u_ges[7*(node-1) + 0]
        uy = self.u_ges[7*(node-1) + 1]
        uz = self.u_ges[7*(node-1) + 3]
        print("ux, uy, uz =", ux, uy, uz)

    def sum_reactions_fx(self):
        r = (self.GesMat @ self.u_ges - self.FGes).ravel()

        Rx = 0.0
        for _, row in self.Inp.RestraintData.iterrows():
            node = int(row["Node"])
            dof  = int(row["Dof"])
            if dof == 0:  # ux-DOF
                Rx += r[7*(node-1) + 0]

        Fx = 0.0
        for _, row in self.Inp.NodalForces.iterrows():
            if str(row["Dof"]).strip().lower() == "fx":
                Fx += float(row["Value[MN/MNm]"])

        print("Sum Fx (applied) =", Fx)
        print("Sum Rx (support) =", Rx)
        print("Fx + Rx          =", Fx + Rx)

    def sum_spring_reactions_fx(self):
        u = self.u_ges.ravel()

        Rx = 0.0
        Fx = 0.0

        # aufgebrachte nodale Fx
        for _, row in self.Inp.NodalForces.iterrows():
            if str(row["Dof"]).strip().lower() == "fx":
                Fx += float(row["Value[MN/MNm]"])

        # Federkräfte aus RestraintData: k * u an genau diesen DOFs
        for _, row in self.Inp.RestraintData.iterrows():
            node = int(row["Node"])
            dof  = int(row["Dof"])
            k    = float(row["Cp[MN/m]/[MNm/m]"])
            gdof = 7*(node-1) + dof

            if dof == 0:  # ux
                Rx += k * u[gdof]

        print("Sum Fx (applied) =", Fx)
        print("Sum spring Rx    =", Rx)
        print("Fx - Rx          =", Fx - Rx)



