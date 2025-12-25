import numpy as np
import pandas as pd
from tabulate import tabulate


class CrossSectionThin:
    def __init__(
        self,
        E,
        nu,
        node_param_csv="Querschnittseingabe/Knoten.csv",
        element_param_csv="Querschnittseingabe/Elemente.csv",
        Speichername=None,
    ):
        self.x = 0
        self.y = 0
        self.node = 0

        self.Node_Cords = 0
        self.CrossSectionElements = 0
        # Read the element and node input parameters
        self.Node_Cords = pd.DataFrame(pd.read_csv(node_param_csv))
        self.CrossSectionElements = pd.DataFrame(pd.read_csv(element_param_csv))

        # Material parameters
        self.E = E
        self.nu = nu
        self.G = self.E / (2 * (1 + self.nu))
        # Initialize Elastic Cross Section Values

        self.Speichername = Speichername

    def read_node_input(self):
        self.CrossSectionElements["ya"] = 0
        self.CrossSectionElements["ye"] = 0
        self.CrossSectionElements["ymi"] = 0
        self.CrossSectionElements["za"] = 0
        self.CrossSectionElements["ze"] = 0
        self.CrossSectionElements["zmi"] = 0
        self.CrossSectionElements["l_i"] = 0  # Längenspalte
        self.CrossSectionElements["sin_bet_i"] = 0
        self.CrossSectionElements["cos_bet_i"] = 0
        self.CrossSectionElements["A_i"] = 0
        self.CrossSectionElements["A_z_i"] = 0
        self.CrossSectionElements["A_y_i"] = 0

        self.CrossSectionElements["I_yy_ET"] = 0
        self.CrossSectionElements["I_zz_ET"] = 0
        self.CrossSectionElements["I_yz_ET"] = 0

        self.CrossSectionElements["zM0"] = 0  # Schätzung für den Schubmittelpunkt
        self.CrossSectionElements["yM0"] = 0
        self.CrossSectionElements["rT0"] = 0

        for i in range(0, len(self.CrossSectionElements["nr"]), 1):
            nr_a = self.CrossSectionElements["npa"][i]
            nr_e = self.CrossSectionElements["npe"][i]
            # Nodal properties
            ya = float(self.Node_Cords["y"][self.Node_Cords["Nr."] == nr_a])
            ye = float(self.Node_Cords["y"][self.Node_Cords["Nr."] == nr_e])
            za = float(self.Node_Cords["z"][self.Node_Cords["Nr."] == nr_a])
            ze = float(self.Node_Cords["z"][self.Node_Cords["Nr."] == nr_e])
            t = float(self.CrossSectionElements["t [m]"][i])
            # Geometric properties
            l = np.sqrt((ye - ya) ** 2 + (ze - za) ** 2)
            sin_beta = (ze - za) / l
            cos_beta = (ye - ya) / l
            A = l * float(t)
            # Insert in Dataframe / Dictionary
            self.CrossSectionElements["A_i"][i] = A
            self.CrossSectionElements["sin_bet_i"][i] = sin_beta
            self.CrossSectionElements["cos_bet_i"][i] = cos_beta
            self.CrossSectionElements["l_i"][i] = l

            self.CrossSectionElements["ya"][i] = ya
            self.CrossSectionElements["ye"][i] = ye
            self.CrossSectionElements["ymi"][i] = 0.5 * (ya + ye)
            self.CrossSectionElements["za"][i] = za
            self.CrossSectionElements["ze"][i] = ze
            self.CrossSectionElements["zmi"][i] = 0.5 * (za + ze)

            self.CrossSectionElements["A_z_i"][i] = A * 0.5 * (za + ze)
            self.CrossSectionElements["A_y_i"][i] = A * 0.5 * (ya + ye)

            if sin_beta != 0:
                self.CrossSectionElements["I_yy_ET"][i] = A / 12 * (ze - za) ** 2
            else:
                self.CrossSectionElements["I_yy_ET"][i] = A * t**2 / 12

            if cos_beta != 0:
                self.CrossSectionElements["I_zz_ET"][i] = A / 12 * (ye - ya) ** 2
            else:
                self.CrossSectionElements["I_zz_ET"][i] = A * t**2 / 12

            self.CrossSectionElements["rT0"][i] = (
                self.CrossSectionElements["ymi"][i]
                - self.CrossSectionElements["yM0"][i]
            ) * sin_beta - (
                self.CrossSectionElements["zmi"][i]
                - self.CrossSectionElements["zM0"][i]
            ) * cos_beta

        self.A_ges = self.CrossSectionElements["A_i"].sum()
        A_z_i = self.CrossSectionElements["A_z_i"].sum()
        A_y_i = self.CrossSectionElements["A_y_i"].sum()

        self.ym = A_y_i / self.A_ges
        self.y_re = (
            max(self.CrossSectionElements["ye"].max(),self.CrossSectionElements["ya"].max())
            - self.ym
        )
        self.y_li = (
            min(self.CrossSectionElements["ye"].min(),self.CrossSectionElements["ya"].min())      
            - self.ym
        )

        self.zm = A_z_i / self.A_ges
        self.z_so = (
            min(self.CrossSectionElements["ze"].min(),self.CrossSectionElements["za"].min())
            - self.zm
        )


        self.z_su = (
            max(self.CrossSectionElements["ze"].max(),self.CrossSectionElements["za"].max())
            -self.zm
        )

        self.I_yy = 0
        self.I_zz = 0
        self.I_yz = 0

        for i in range(0, len(self.CrossSectionElements["nr"]), 1):
            # I_yy
            self.I_yy += self.CrossSectionElements["I_yy_ET"][i]
            self.I_yy += (
                self.zm - self.CrossSectionElements["zmi"][i]
            ) ** 2 * self.CrossSectionElements["A_i"][i]
            # I_zz
            self.I_zz += self.CrossSectionElements["I_zz_ET"][i]
            self.I_zz += (
                self.ym - self.CrossSectionElements["ymi"][i]
            ) ** 2 * self.CrossSectionElements["A_i"][i]
            # I_yz


    def CalculateElementStiffness(self):
        K_e = np.zeros((2, 2))
        f_th_e = np.zeros(2)
        # Storage matrix for ther element stifness matrices
        self.K_e_ges = np.zeros((len(self.CrossSectionElements["nr"]), 2, 2))
        self.f_th_ges = np.zeros((len(self.CrossSectionElements["nr"]), 2, 1))
        self.f_e_ges = np.zeros((len(self.CrossSectionElements["nr"]), 2, 1))

        for i in range(0, len(self.CrossSectionElements["nr"]), 1):
            t_el = self.CrossSectionElements["t [m]"][i]
            l_el = self.CrossSectionElements["l_i"][i]

            K_e[0][0] = 1 * self.G * t_el / l_el
            K_e[1][1] = K_e[0][0]
            K_e[1][0] = -1 * self.G * t_el / l_el
            K_e[0][1] = K_e[1][0]

            self.K_e_ges[i] = K_e

            # Lastvektor für die Wölbordinate
            r_t_el = self.CrossSectionElements["rT0"][i]
            self.f_th_ges[i][0] = self.G * t_el * r_t_el * (-1)
            self.f_th_ges[i][1] = self.G * t_el * r_t_el * (1)

    def Calculate_GesMat(self):
        no_nodes = len(self.Node_Cords["Nr."])

        self.Gesmat = np.zeros((no_nodes, no_nodes))
        self.GesLoadVec = np.zeros(no_nodes)

        for k in range(0, len(self.CrossSectionElements["nr"]), 1):
            i = int(self.CrossSectionElements["npa"][k] - 1)
            j = int(self.CrossSectionElements["npe"][k] - 1)

            # Stiffness matrix
            self.Gesmat[i][i] += self.K_e_ges[k][0][0]
            self.Gesmat[i][j] += self.K_e_ges[k][0][1]
            self.Gesmat[j][i] += self.K_e_ges[k][1][0]
            self.Gesmat[j][j] += self.K_e_ges[k][1][1]
            # Load vector f_th
            self.GesLoadVec[i] += self.f_th_ges[k][0]
            self.GesLoadVec[j] += self.f_th_ges[k][1]



    def SolverTorsion(self):
        self.Gesmat[0][0:] = 0
        self.Gesmat[1][0] = 0
        self.Gesmat[0][
            0
        ] = 1e30  # Einen FHG auf 1e9 setzen -> Analog zum Streichen der Zeile

        self.omega_start = np.linalg.solve(self.Gesmat, self.GesLoadVec)


    def CalculateAyzw(self):
        num_elem = len(self.CrossSectionElements["nr"])
        self.A_omega = 0
        self.A_zomega = 0
        self.A_yomega = 0

        for k in range(0, num_elem, 1):
            i = int(self.CrossSectionElements["npa"][k] - 1)
            j = int(self.CrossSectionElements["npe"][k] - 1)
            A_e = self.CrossSectionElements["A_i"][k]
            # Omega Values
            omega_a = self.omega_start[i]
            omega_b = self.omega_start[j]
            # y-Value Ayomega
            z_a = self.CrossSectionElements["za"][k]
            z_b = self.CrossSectionElements["ze"][k]
            # z-Values
            y_a = self.CrossSectionElements["ya"][k]
            y_b = self.CrossSectionElements["ye"][k]
            # Summation
            self.A_omega += 0.5 * (omega_a + omega_b) * A_e
            self.A_zomega += (
                1 / 6 * ((2 * z_a + z_b) * omega_a + (z_a + 2 * z_b) * omega_b) * A_e
            )
            self.A_yomega += (
                1 / 6 * ((2 * y_a + y_b) * omega_a + (y_a + 2 * y_b) * omega_b) * A_e
            )

        self.omega_k = self.A_omega / self.A_ges
        self.Delta_ZM = self.A_yomega / self.I_zz * (-1)  # Vorzeichen beachten!
        self.Delta_YM = self.A_zomega / self.I_yy

    def Update_SMP(self):
        self.CrossSectionElements["zM0"] += self.Delta_ZM
        self.CrossSectionElements["yM0"] += self.Delta_YM
        self.CrossSectionElements["rT"] = 0
        self.CrossSectionElements["omeg_a"] = 0
        self.CrossSectionElements["omeg_b"] = 0

        for i in range(0, len(self.CrossSectionElements["nr"]), 1):
            nr_a = self.CrossSectionElements["npa"][i]
            nr_e = self.CrossSectionElements["npe"][i]
            # Nodal properties
            ya = float(self.Node_Cords["y"][self.Node_Cords["Nr."] == nr_a])
            ye = float(self.Node_Cords["y"][self.Node_Cords["Nr."] == nr_e])
            za = float(self.Node_Cords["z"][self.Node_Cords["Nr."] == nr_a])
            ze = float(self.Node_Cords["z"][self.Node_Cords["Nr."] == nr_e])
            t = float(self.CrossSectionElements["t [m]"][i])
            # Geometric properties
            l = np.sqrt((ye - ya) ** 2 + (ze - za) ** 2)
            sin_beta = (ze - za) / l
            cos_beta = (ye - ya) / l
            A = l * float(t)
            self.CrossSectionElements["rT"][i] = (
                self.CrossSectionElements["ymi"][i]
                - self.CrossSectionElements["yM0"][i]
            ) * sin_beta - (
                self.CrossSectionElements["zmi"][i]
                - self.CrossSectionElements["zM0"][i]
            ) * cos_beta

    def Calculate_IwIt(self):
        ne = len(self.CrossSectionElements["nr"])
        self.I_w = 0
        self.I_T_OFFEN = 0
        self.I_T_GESCHLOSSEN = 0
        for k in range(0, ne, 1):
            i = int(self.CrossSectionElements["npa"][k] - 1)
            j = int(self.CrossSectionElements["npe"][k] - 1)
            t = self.CrossSectionElements["t [m]"][k]
            # Omega Values
            y_a = self.CrossSectionElements["ya"][k]
            y_e = self.CrossSectionElements["ye"][k]
            z_a = self.CrossSectionElements["za"][k]
            z_e = self.CrossSectionElements["ze"][k]
            omega_a = (
                self.omega_start[i]
                - self.omega_k
                + self.Delta_ZM * y_a
                - self.Delta_YM * z_a
            )
            omega_b = (
                self.omega_start[j]
                - self.omega_k
                + self.Delta_ZM * y_e
                - self.Delta_YM * z_e
            )
            self.CrossSectionElements["omeg_a"][k] = omega_a
            self.CrossSectionElements["omeg_b"][k] = omega_b
            # I_w-Values
            self.I_w += (
                self.CrossSectionElements["l_i"][k]
                * t
                / 3
                * (omega_a**2 + omega_a * omega_b + omega_b**2)
            )

            # Berechnung von IT_OFFEN
            l = self.CrossSectionElements["l_i"][k]
            t = self.CrossSectionElements["t [m]"][k]
            self.I_T_OFFEN += 1 / 3 * l * t**3
            # Berechnung IT_GESCHLOSSEN
            l_z = z_e - z_a
            l_y = y_e - y_a
            yM = self.CrossSectionElements["yM0"][k]
            zM = self.CrossSectionElements["zM0"][k]
            r_tj = (y_a - yM) * l_z / l - (z_a - zM) * l_y / l

            self.I_T_GESCHLOSSEN += r_tj * t * (r_tj * l + omega_a - omega_b)
            self.I_T_GESAMT = self.I_T_GESCHLOSSEN + self.I_T_OFFEN

    def Calculate_WoWu(self):
        self.W_o = self.I_yy / self.z_so
        self.W_u = self.I_yy / self.z_su
        self.W_li = self.I_zz / self.y_li
        self.W_re = self.I_zz / self.y_re

    def Calculate_ShearStress_Vz(self):
        # Load Vector for the Vz-Component
        f_e_vz = np.zeros(2)
        num_nodes = len(self.Node_Cords["Nr."])
        self.f_e_vz = np.zeros(num_nodes)

        num_elem = len(self.CrossSectionElements["nr"])
        self.CrossSectionElements["ua_vz"] = 0
        self.CrossSectionElements["ue_vz"] = 0
        self.CrossSectionElements["F_a_elem"] = 0
        self.CrossSectionElements["F_e_elem"] = 0

        self.CrossSectionElements["tau_a_vz"] = 0
        self.CrossSectionElements["tau_e_vz"] = 0

        for k in range(0, num_elem, 1):
            i = int(
                self.CrossSectionElements["npa"][k] - 1
            )  # Indices for the global load vector
            j = int(self.CrossSectionElements["npe"][k] - 1)

            l = self.CrossSectionElements["l_i"][k]
            t = self.CrossSectionElements["t [m]"][k]

            z_a = self.CrossSectionElements["za"][k] - self.zm
            z_b = self.CrossSectionElements["ze"][k] - self.zm

            self.f_e_vz[i] += (
                (1 / 3 * z_a / self.I_yy + 1 / 6 * z_b / self.I_yy) * t * l
            )
            self.f_e_vz[j] += (
                (1 / 6 * z_a / self.I_yy + 1 / 3 * z_b / self.I_yy) * t * l
            )

            self.CrossSectionElements.loc[k, "F_a_elem"] = z_a / self.I_yy
            self.CrossSectionElements.loc[k, "F_e_elem"] = z_b / self.I_yy

        # Solving for u_a / u_a for the vz-Component

        self.u_sol = np.linalg.solve(self.Gesmat, self.f_e_vz)

        # Entferne die erste Zeile und die erste Spalte der Matrix
        reduced_matrix = self.Gesmat[1:, 1:]

        # Entferne das erste Element des Vektors
        reduced_vector = self.f_e_vz[1:]

        # Löse das reduzierte Gleichungssystem
        self.u_sol_red = np.linalg.solve(reduced_matrix, reduced_vector)

        # Update of the nodal shear stress under a "1" load Vz
        for k in range(0, num_elem, 1):
            l = self.CrossSectionElements["l_i"][k]
            i = int(
                self.CrossSectionElements["npa"][k] - 1
            )  # Indices for the global node deformation vector
            j = int(self.CrossSectionElements["npe"][k] - 1)

            u_a = self.u_sol[i]
            u_b = self.u_sol[j]

            F_a = self.CrossSectionElements["F_a_elem"][k]
            F_b = self.CrossSectionElements["F_e_elem"][k]

            self.CrossSectionElements["tau_a_vz"][k] = self.G / l * (
                u_b - u_a
            ) + l / 6 * (F_a * 2 + F_b * 1)
            self.CrossSectionElements["tau_e_vz"][k] = self.G / l * (
                u_b - u_a
            ) - l / 6 * (F_a * 1 + F_b * 2)

    def Calculate_imryrzrw(self):
        """
        Function to calculate the geometric lengths for \n
        the calculation of geometric nonlinear problems (TH.II.Order) \n
        im =
        ry =
        rz =
        rw =
        For the values im,ry,rz the different lengths are calculated relative to the elastic centrum \n
        For the rw-values the length is taken from the previous calculation, which is based on the \n
        shear centre. \n
        """
        self.CrossSectionElements["im"] = 0
        self.CrossSectionElements["ry"] = 0
        self.CrossSectionElements["rz"] = 0
        self.CrossSectionElements["rw"] = 0
        self.CrossSectionElements["Ayyy"] = 0
        self.CrossSectionElements["Ayzz"] = 0
        self.CrossSectionElements["Azzz"] = 0
        self.CrossSectionElements["Azyy"] = 0

        for k in range(0, len(self.CrossSectionElements["nr"])):
            ym_t = (
                self.CrossSectionElements["ymi"][k] - self.ym
            )  # Transformierte Querschnittsordinaten
            zm_t = self.CrossSectionElements["zmi"][k] - self.zm
            dy = self.CrossSectionElements["ye"][k] - self.CrossSectionElements["ya"][k]
            dz = self.CrossSectionElements["ze"][k] - self.CrossSectionElements["za"][k]
            omega_m = (
                self.CrossSectionElements["omeg_a"][k]
                + self.CrossSectionElements["omeg_b"][k]
            ) * 0.5
            domega = (
                self.CrossSectionElements["omeg_b"][k]
                - self.CrossSectionElements["omeg_a"][k]
            )

            A = self.CrossSectionElements["A_i"][k]
            # A_XXX Params
            A_yyy = ym_t**3 * A + ym_t * dy**2 * A / 4
            A_yzz = (
                ym_t * zm_t**2 * A + (ym_t * dz**2 + 2 * zm_t * dy * dz) * A / 12
            )
            A_zzz = zm_t**3 * A + zm_t * dz**2 * A / 4
            A_zyy = (
                zm_t * ym_t**2 * A + (zm_t * dy**2 + 2 * ym_t * dz * dy) * A / 12
            )
            A_yyom = (
                ym_t**2 * omega_m * A
                + (omega_m * dy**2 + 2 * ym_t * dy * domega) * A / 12
            )
            A_zzom = (
                zm_t**2 * omega_m * A
                + (omega_m * dz**2 + 2 * zm_t * dz * domega) * A / 12
            )

            self.CrossSectionElements["Ayyy"][k] = A_yyy
            self.CrossSectionElements["Azzz"][k] = A_zzz
            self.CrossSectionElements["Ayzz"][k] = A_yzz
            self.CrossSectionElements["Azyy"][k] = A_zyy

            self.CrossSectionElements["ry"][k] = (A_yyy + A_yzz) * 1 / self.I_zz
            self.CrossSectionElements["rz"][k] = (A_zzz + A_zyy) * 1 / self.I_yy
            self.CrossSectionElements["rw"][k] = (A_yyom + A_zzom) * 1 / self.I_w

        YM = self.CrossSectionElements["yM0"][k] - self.ym
        ZM = self.CrossSectionElements["zM0"][k] - self.zm
        self.y_M = YM
        self.z_M = ZM

        self.rz = self.CrossSectionElements["rz"].sum() - 2 * ZM
        self.ry = self.CrossSectionElements["ry"].sum() - 2 * YM
        self.rw = self.CrossSectionElements["rw"].sum()


    def Export_Controll_Data(self):
        # nr,npa,npe,t [m],ya,ye,ymi,za,ze,zmi
        df_0 = pd.DataFrame(
            {
                "nr": self.CrossSectionElements["nr"],
                "npa": self.CrossSectionElements["npa"],
                "ya": self.CrossSectionElements["ya"],
                "ye": self.CrossSectionElements["ye"],
            }
        )

    def Export_Cross_Section_Data(self, _unit="cm"):
        unit = _unit
        if unit == "cm":
            df_Data_1 = pd.DataFrame(
                {
                    "A": [f"{self.A_ges * 100**2:.2f}"],
                    "Iyy": [f"{self.I_yy * 100**4:.2f}"],
                    "Izz": [f"{self.I_zz * 100**4:.2f}"],
                    "zM": [f"{self.z_M  * 100:.2f}"],
                    "yM": [f"{self.y_M  * 100:.2f}"],
                }
            )
            df_Data_1.to_csv(
                f"Checks/Data/CrossSectionProperties_1_{self.Speichername}.txt",
                index=False,
            )

            df_Data_2 = pd.DataFrame(
                {
                    "IT": [f"{self.I_T_GESAMT * 100**4:.2f}", 230.4],
                    "Iw": [f"{self.I_w * 100**6:.2f}", 960000],
                    "rz": [f"{self.rz*100:.2f}", 28.40],
                },
                index=["Berechnet", "Erwartet"],
            )

            df_Data_2.to_csv(
                f"Checks/Data/CrossSectionProperties_2_{self.Speichername}.txt",
                index=False,
            )


# Class = CrossSectionThin(
#     2.1e5,
#     0.3,
#     "Querschnittseingabe/Knoten_3.csv",
#     "Querschnittseingabe/Elemente_3.csv",
#     "Lit_Ex_1",
# )
# Class.read_node_input()
# Class.CalculateElementStiffness()
# Class.Calculate_GesMat()
# Class.SolverTorsion()
# Class.CalculateAyzw()
# Class.Update_SMP()
# Class.Calculate_IwIt()
# Class.Calculate_WoWu()
# Class.Calculate_ShearStress_Vz()
# Class.Calculate_imryrzrw()
# Class.Export_Controll_Data()
# Class.Export_Cross_Section_Data()

