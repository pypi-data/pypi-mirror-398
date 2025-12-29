import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.interpolate import interp1d
from Iterative_Design import Baustoffe
from Querschnittsbreite import PolygonSection

class M_Kappa_Cross_Section:
    def __init__(
        self,
        _LoadingType="csv",
        Iter="Bruch",
        Reinforcement="csv",
        Querschnittsbemessung="Polygon",
    ):
        # Init design values for loading
        self.LoadingType = _LoadingType
        # Geometric parameters for the design
        self.Bewehrung = Reinforcement

        self.readBaustoffe()
        self.Querschnittswerte()
        self.Bewehrungsangaben()
        self.ReadLoading()

        print("height", self.h_c)
        print("width", self.b_c)

        # Latex-Ausgabe

        self.results_A = []
        self.results_B = []
        self.results_B_Iterate = []
        self.results_C = []
        self.results_C_Iterate = []
        self.results_D = []
        self.results_D_Iterate = []

        # Bemessungswerte der Baustoffwerte

        self.Point_A()
        self.Point_B()
        self.Point_B_Iterate()
        self.Point_C()
        self.Point_C_Iterative()
        # self.Point_D()

    def readBaustoffe(self):
        csv_read_beton = pd.read_csv("Materialparameter/Beton.csv")
        csv_read_stahl = pd.read_csv("Materialparameter/Betonstahl.csv")

        print(csv_read_beton["traeger"])
        self.Baustoff = Baustoffe(
            [csv_read_beton["fck"].iloc[0], csv_read_stahl["fyk[MPa]"].iloc[0]],
            csv_read_beton["h_c"].iloc[0],
            csv_read_beton["b_c"].iloc[0],
            csv_read_beton["traeger"].iloc[0],
            csv_read_beton["t0"].iloc[0],
            csv_read_beton["t"].iloc[0],
        )

    def Querschnittswerte(self, _height_test=0.5):
        # Example usage
        df = pd.read_csv("Polygon/Polygon.csv")
        self.vertices = df.values.tolist()

        self.polygon = PolygonSection(self.vertices)

        # Calculate the height of the polygon based on y-values

        y_values = [vertex[1] for vertex in self.vertices]
        self.height = abs(max(y_values) - min(y_values))
        self.z_cu = self.height - self.polygon.centroid[1]
        self.z_co = self.height - self.z_cu

        # Define the rotation angle
        self.angle_degrees = 0
        self.polygon.rotate(self.angle_degrees)

        height = self.height


        self.num_stripes = 1000
        self.section_width_list = [
            self.polygon.calculate_section_width_at_height(
                height / (self.num_stripes) * (i + 0.5)
            )
            for i in range(0, self.num_stripes, 1)
        ]
        self.section_height_list = [
            height / (self.num_stripes) * (i + 0.5)
            for i in range(0, self.num_stripes, 1)
        ]
        self.delta_height = height / self.num_stripes

        self.h_c = self.height
        self.b_c = self.polygon.calculate_section_width_at_height(_height_test)

        self.A = self.polygon.A

    
    def PlotCrossSection(self, _height_test=0.25):
        # Define the height at which to calculate the section width
        height = _height_test
        section_width = self.polygon.calculate_section_width_at_height(height)
        print(
            f"Section width at height {height} after rotating by {self.angle_degrees} degrees: {section_width}"
        )

        # Plot the polygon and the horizontal line
        self.polygon.plot(height)

    def Bewehrungsangaben(self):
        if self.Bewehrung == "csv":
            df = pd.read_csv("Bewehrung/Linienbewehrung.csv")
            print(df)
            for i in range(0, len(df["Lage"]), 1):
                Lage = df["Lage"][i]
                if Lage == "Unten":
                    self.d_s1 = (
                        df["dsl [m]"][i] * 0.5 + df["cnom [m]"][i] + df["dsw [m]"][i]
                    )
                    self.A_s1 = df["As [cm**2]"][i] * 0.01**2
                elif Lage == "Oben":
                    self.d_s2 = (
                        df["dsl [m]"][i] * 0.5 + df["cnom [m]"][i] + df["dsw [m]"][i]
                    )
                    self.A_s2 = df["As [cm**2]"][i] * 0.01**2

            self.z_ds1 = self.z_cu - self.d_s1
            self.z_ds2 = self.z_co - self.d_s2

    def ReadLoading(self):
        if self.LoadingType == "csv":
            df = pd.read_csv("Lasteingabe/Lasten.csv")
            print(df)
            self.Zugseite = None
            for i in range(0, len(df["Grenzzustand"]), 1):
                if df["Grenzzustand"][i] == "GZT":
                    self.NEd_GZT = df["NEd in [MN]"][i]
                    self.MEd_GZT = df["MEd in [MNm]"][i]
                elif df["Grenzzustand"][i] == "GZG":
                    self.NEd_GZG = df["NEd in [MN]"][i]
                    self.MEd_GZG = df["MEd in [MNm]"][i]

            if self.MEd_GZT >= 0:
                self.MEds_GZT = abs(
                    self.MEd_GZT - self.NEd_GZT * self.z_ds1
                )  # Bezug auf die Biegezugbewehrung (Hier UNTEN)
                self.Zugseite_GZT = "UNTEN"
                self.d = self.height - self.d_s1
            elif self.MEd_GZT < 0:
                self.MEds_GZT = abs(
                    self.MEd_GZT + self.NEd_GZT * self.z_ds2
                )  # Bezug auf die Biegezugbewehrung (Hier OBEN)
                self.Zugseite_GZT = "OBEN"
                self.d = self.height - self.d_s2

            if self.MEd_GZG >= 0:
                self.MEds_GZG = self.MEd_GZG - self.NEd_GZG * self.z_ds1
                self.Zugseite_GZG = "UNTEN"
                self.d = self.height - self.d_s1
            elif self.MEd_GZG < 0:
                self.MEds_GZG = self.MEd_GZG + self.NEd_GZG * self.z_ds2
                self.Zugseite_GZG = "OBEN"
                self.d = self.height - self.d_s2

        elif self.LoadingType == "csv_druckglied":
            df = pd.read_csv("Lasteingabe/Lasten_Druckglied.csv")
            print(df)
            self.Zugseite = None
            for i in range(0, len(df["Grenzzustand"]), 1):
                if df["Grenzzustand"][i] == "GZT":
                    self.NEd_GZT = df["NEd in [MN]"][i]
                    self.MEd1_GZT = df["MEd1 in [MNm]"][i]
                    self.MEd2_GZT = df["MEd2 in [MNm]"][i]
                elif df["Grenzzustand"][i] == "GZG":
                    self.NEd_GZG = df["NEd in [MN]"][i]
                    self.MEd1_GZG = df["MEd1 in [MNm]"][i]
                    self.MEd2_GZG = df["MEd2 in [MNm]"][i]

            if self.MEd1_GZT >= 0:
                self.Zugseite_GZT = "UNTEN"
                self.d = self.height - self.d_s1
            elif self.MEd1_GZT < 0:
                self.Zugseite_GZT = "OBEN"
                self.d = self.height - self.d_s2

            if self.MEd1_GZG >= 0:
                self.Zugseite_GZG = "UNTEN"
                self.d = self.height - self.d_s1
            elif self.MEd1_GZG < 0:
                self.Zugseite_GZG = "OBEN"
                self.d = self.height - self.d_s2

        else:
            self.NEd_GZT = float(
                input("Geben Sie die Normalkraft NEd im GZT in [MN] ein: \n")
            )
            self.MEd_GZT = float(
                input("Geben Sie das Biegemoment im GZT in [MN] ein: \n")
            )
            if self.MEd_GZT >= 0:
                self.MEds_GZT = self.MEd_GZT - self.NEd_GZT * self.z_ds1
            elif self.MEd_GZT < 0:
                self.MEds_GZT = self.MEd_GZT + self.NEd_GZT * self.z_ds1

            if self.MEd_GZG >= 0:
                self.MEds_GZG = self.MEd_GZG - self.NEd_GZG * self.z_ds1
            elif self.MEd_GZG < 0:
                self.MEds_GZG = self.MEd_GZG + self.NEd_GZG * self.z_ds1

        # Export loading parameters to the output folder
        self.zsi_GZT = None
        self.zsi_GZG = None

        if self.Zugseite_GZT == "UNTEN":
            self.zsi_GZT = self.z_ds1
        else:
            self.zsi_GZT = self.z_ds2

        if self.Zugseite_GZG == "UNTEN":
            self.zsi_GZG = self.z_ds1
        else:
            self.zsi_GZG = self.z_ds2

    def Nonlinear_Material_Law(self, eps_c):
        # Berechnung von eta und k
        eta = abs(eps_c / (self.Baustoff.eps_c1 * 1e-3))
        k = (
            1.05
            * self.Baustoff.Ecm
            / 1.5
            * abs(self.Baustoff.eps_c1 * 1e-3)
            / self.Baustoff.fcd
        )

        # Berechnung von sigma_c

        sigma_c = self.Baustoff.fcd * (k * eta - eta**2) / (1 + (k - 2) * eta)

        return eta, k, sigma_c

    def Point_A(self):
        """
        Calculates the strain for the case, that the cross section is cracking at one edge
        """

        self.Wco = self.polygon.I_yy / self.z_co
        self.Wcu = self.polygon.I_yy / self.z_cu
        self.A = self.polygon.A

        self.M_cr_o = self.Wco * (self.Baustoff.fctm - self.NEd_GZT / self.A)
        self.M_cr_u = self.Wcu * (self.Baustoff.fctm - self.NEd_GZT / self.A)

        print("Area", self.polygon.A)
        print("Trägheitsmoment ", self.polygon.I_yy)
        print("Widerstandsmoment ", self.Wco)
        print("Zugfestigkeit ", self.Baustoff.fctm)

        self.M_A = min(self.M_cr_o, self.M_cr_u)
        self.kappa_A = self.M_A / (self.Baustoff.Ecm * self.polygon.I_yy)

        # Save results
        self.results_A.append(("I_y", self.polygon.I_yy))
        self.results_A.append(("Wco", self.Wco))
        self.results_A.append(("Wcu", self.Wcu))
        self.results_A.append(("A", self.A))
        self.results_A.append(("M_cr_o", self.M_cr_o))
        self.results_A.append(("M_cr_u", self.M_cr_u))
        self.results_A.append(("M_A", self.M_A))
        self.results_A.append(("Kappa_A", self.kappa_A))

        self.latex_table_A = self.results_to_latex_table(
            self.results_A, ["Parameter", "Wert"], "Results of Point A"
        )

    def Point_B(self):
        """
        Point B is the case, where the compression reinforcement reaches its \n
        yielding stress. \n
        The iterations starts at the yielding strains of -2.174e-3 in both compression and \n
        tension reinforcement.
        """
        N_Rd_B = self.NEd_GZT - 10
        iter = 0

        epsilon_s2 = -2.174e-3
        epsilon_s1 = -2.174e-3
        epsilon_c2 = epsilon_s2 + (
            (epsilon_s2 - epsilon_s1) / (self.h_c - self.d_s1 - self.d_s2) * (self.d_s2)
        )

        print(epsilon_c2)

        N_Rd_B_list = []

        x = self.h_c

        while (N_Rd_B < self.NEd_GZT) and (iter < 1000) and (epsilon_c2 >= -0.0035):
            eta = self.Nonlinear_Material_Law(epsilon_c2)[0]
            k = self.Nonlinear_Material_Law(epsilon_c2)[1]
            sigma_c = self.Nonlinear_Material_Law(epsilon_c2)[2]

            epsilon_c_list = np.linspace(0, epsilon_c2, 100)

            sigma_c_list = self.Nonlinear_Material_Law(epsilon_c_list)[2]

            x_list = np.linspace(0, x, 100)

            if abs(N_Rd_B - self.NEd_GZT) > 1e-1:
                epsilon_s1 += 1e-4
            else:
                epsilon_s1 += 1e-5

            epsilon_c2 = epsilon_s2 + (
                (epsilon_s2 - epsilon_s1)
                / (self.h_c - self.d_s1 - self.d_s2)
                * (self.d_s2)
            )

            N_cRd_B = np.trapz(sigma_c_list, x_list) * self.b_c * (-1)

            if abs(epsilon_s2) <= 2.174e-3:
                N_s2_Rd_B = epsilon_s2 * self.A_s2 * self.Baustoff.Es
            else:
                N_s2_Rd_B = -self.A_s2 * self.Baustoff.fyd
            if abs(epsilon_s1) <= 2.174e-3:
                N_s1_Rd_B = epsilon_s1 * self.A_s1 * self.Baustoff.Es
            else:
                N_s1_Rd_B = self.Baustoff.fyd * self.A_s1

            # Berechnung des Abstands der Druckresultierenden von DNL

            N_Rd_B_list.append(N_cRd_B)

            dx = x_list[1] - x_list[0]

            # Berechnung der Fläche unter der Kurve (Flächenmoment 0. Grades)
            A = np.sum(sigma_c_list * dx)

            # Berechnung des 1. Flächenmoments um den Ursprung
            S = np.sum(sigma_c_list * x_list * dx)

            # Berechnung des Schwerpunkts
            a = S / A

            N_Rd_B = N_cRd_B + N_s2_Rd_B + N_s1_Rd_B

            iter += 1

        print("eps s1", epsilon_s1)
        print("eps s2", epsilon_s2)
        print("eps c2", epsilon_c2)

        print("NRd_B", N_Rd_B)
        print("NRd_s1", N_s1_Rd_B)
        print("NRd_s2", N_s2_Rd_B)

        self.M_B = (
            abs(N_cRd_B) * (self.z_cu - a)
            + abs(N_s2_Rd_B) * (self.z_cu - self.d_s2)
            + abs(N_s1_Rd_B) * (self.z_co - self.d_s1)
        )

        self.kappa_B = (epsilon_s1 - epsilon_c2) / self.d

        if epsilon_c2 < -0.0035:
            self.M_B = None
            self.kappa_B = None

        self.results_B.append(("M_B", self.M_B))
        self.results_B.append(("Kappa_B", self.kappa_B))

    def Point_B_Iterate(self):
        """
        Point B is the case, where the compression reinforcement reaches its \n
        yielding stress. \n
        The iterations starts at the yielding strains of -2.174e-3 in both compression and \n
        tension reinforcement. \n
        This function is the iterative representative for general cross sections.
        """
        N_Rd_B = self.NEd_GZT - 10
        iter = 0

        epsilon_s2 = -2.174e-3
        epsilon_s1 = -2.174e-3
        epsilon_c2 = epsilon_s2 + (
            (epsilon_s2 - epsilon_s1) / (self.h_c - self.d_s1 - self.d_s2) * (self.d_s2)
        )

        N_Rd_B_list = []
        x = self.h_c

        while (N_Rd_B < self.NEd_GZT) and (iter < 1000) and (epsilon_c2 >= -0.0035):

            eps_0 = epsilon_s2 - (epsilon_s2 - epsilon_s1) / (
                self.h_c - self.d_s1 - self.d_s2
            ) * (self.h_c - self.d_s2)

            delta_eps_h = epsilon_c2 - eps_0

            print(delta_eps_h)

            N_cRd_B = 0
            F_cd_list = np.zeros(1000)

            for i in range(0, len(self.section_height_list), 1):
                epsilon_i = eps_0 + delta_eps_h / (self.num_stripes) * (i)
                if epsilon_i < 0:
                    sigma_c = self.Nonlinear_Material_Law(epsilon_i)[2]
                else:
                    sigma_c = 0

                F_cd_i = sigma_c * self.delta_height * self.section_width_list[i]
                F_cd_list[i] = F_cd_i

            N_cRd_B = sum(F_cd_list) * (-1)

            if abs(N_Rd_B - self.NEd_GZT) > 1e-1:
                epsilon_s1 += 1e-4
            else:
                epsilon_s1 += 1e-5

            epsilon_c2 = epsilon_s2 + (
                (epsilon_s2 - epsilon_s1)
                / (self.h_c - self.d_s1 - self.d_s2)
                * (self.d_s2)
            )

            if abs(epsilon_s2) <= 2.174e-3:
                N_s2_Rd_B = epsilon_s2 * self.A_s2 * self.Baustoff.Es
            else:
                N_s2_Rd_B = -self.A_s2 * self.Baustoff.fyd
            if abs(epsilon_s1) <= 2.174e-3:
                N_s1_Rd_B = epsilon_s1 * self.A_s1 * self.Baustoff.Es
            else:
                N_s1_Rd_B = self.Baustoff.fyd * self.A_s1

            N_Rd_B = N_cRd_B + N_s2_Rd_B + N_s1_Rd_B

            # print("N_c_RdB", N_cRd_B)
            # print("N_s1", N_s1_Rd_B)
            # print("N_s2", N_s2_Rd_B)
            # print("Ned",self.NEd_GZT)

            iter += 1
        print("H-GGW", abs(N_Rd_B - self.NEd_GZT))
        print("eps s1 - ITER", epsilon_s1)
        print("eps s2 - ITER", epsilon_s2)
        print("eps c2 - ITER", epsilon_c2)

        print("NRd_B - ITER", N_Rd_B)
        print("NRd_s1 - ITER", N_s1_Rd_B)
        print("NRd_s2 - ITER", N_s2_Rd_B)

        # self.M_B_Iterate = (
        #     abs(N_cRd_B) * (self.z_cu - a)
        #     + abs(N_s2_Rd_B) * (self.z_cu - self.d_s2)
        #     + abs(N_s1_Rd_B) * (self.z_co - self.d_s1)
        # )

        # self.kappa_B_Iterate = (epsilon_s1 - epsilon_c2) / self.d

        # if epsilon_c2 < -0.0035:
        #     self.M_B = None
        #     self.kappa_B = None

        # self.results_B_Iterate.append(("M_B", self.M_B_Iterate))
        # self.results_B_Iterate.append(("Kappa_B", self.kappa_B_Iterate))

        # plt.plot(F_cd_list)
        # plt.show()

    def Point_C(self):
        """
        Point C represents the point in the M-Kappa-Law, where \n
        the tensional reinforcement reaches the yielding stresses. \n
        Therefore the iteration starts at 2.174e-3 \n
        The iteration is performed over the strain of the compressional reinforcement \n

        """
        print("Point C")
        N_Rd_C = self.NEd_GZT + 1
        iter = 0

        epsilon_s1 = +2.174e-3
        epsilon_s2 = 0

        epsilon_c2 = epsilon_s1 + (
            (epsilon_s2 - epsilon_s1)
            / (self.h_c - self.d_s1 - self.d_s2)
            * (self.h_c - self.d_s1)
        )

        x = epsilon_c2 / (epsilon_c2 - epsilon_s1) * self.d

        print()

        while (N_Rd_C > self.NEd_GZT) and (iter < 1000) and (abs(epsilon_c2) <= 3.5e-3):
            
            eta = self.Nonlinear_Material_Law(epsilon_c2)[0]
            k = self.Nonlinear_Material_Law(epsilon_c2)[1]
            sigma_c = self.Nonlinear_Material_Law(epsilon_c2)[2]

            epsilon_c_list = np.linspace(0, epsilon_c2, 100)

            sigma_c_list = self.Nonlinear_Material_Law(epsilon_c_list)[2]

            x_list = np.linspace(0, x, 100)

            if abs(N_Rd_C - self.NEd_GZT) > 1e-1:
                epsilon_s2 -= 1e-4
            else:
                epsilon_s2 -= 1e-5

            epsilon_c2 = epsilon_s1 + (
                (epsilon_s2 - epsilon_s1)
                / (self.h_c - self.d_s1 - self.d_s2)
                * (self.h_c - self.d_s1)
            )

            x = epsilon_c2 / (epsilon_c2 - epsilon_s1) * self.d

            N_cRd_C = np.trapz(sigma_c_list, x_list) * self.b_c * (-1)

            if abs(epsilon_s2) <= 2.174e-3:
                N_s2_Rd_C = epsilon_s2 * self.A_s2 * self.Baustoff.Es
            else:
                N_s2_Rd_C = -self.A_s2 * self.Baustoff.fyd
            if abs(epsilon_s1) <= 2.174e-3:
                N_s1_Rd_C = epsilon_s1 * self.A_s1 * self.Baustoff.Es
            else:
                N_s1_Rd_C = self.Baustoff.fyd * self.A_s1

            N_Rd_C = N_cRd_C + N_s2_Rd_C + N_s1_Rd_C

            # Berechnung des Abstands der Druckresultierenden von DNL

            dx = x_list[1] - x_list[0]

            # Berechnung der Fläche unter der Kurve (Flächenmoment 0. Grades)
            A = np.sum(sigma_c_list * dx)

            # Berechnung des 1. Flächenmoments um den Ursprung
            S = np.sum(sigma_c_list * x_list * dx)

            # Berechnung des Schwerpunkts
            a = S / A

            iter += 1

        print("H-GGW", abs(N_Rd_C - self.NEd_GZT))
        print("eps s1 ", epsilon_s1)
        print("eps s2 ", epsilon_s2)
        print("eps c2 ", epsilon_c2)

        print("NRd_C ", N_Rd_C)
        print("NRd_s1 ", N_s1_Rd_C)
        print("NRd_s2 ", N_s2_Rd_C)

        plt.plot([epsilon_s1,epsilon_s2,epsilon_c2],[0,self.d,self.height])
        plt.show()

        self.M_C = (
            abs(N_cRd_C) * (self.z_cu - x + a)
            + abs(N_s2_Rd_C) * (self.z_cu - self.d_s2)
            + abs(N_s1_Rd_C) * (self.z_co - self.d_s1)
        )

        self.kappa_C = (epsilon_s1 - epsilon_c2) / self.d

        self.results_C.append(("M_C", self.M_C))
        self.results_C.append(("Kappa_C", self.kappa_C))

    def Point_C_Iterative(self):
        N_Rd_C = self.NEd_GZT + 1
        iter = 0

        epsilon_s1 = +2.174e-3
        epsilon_s2 = 0

        epsilon_c2 = epsilon_s1 + (
            (epsilon_s2 - epsilon_s1)
            / (self.h_c - self.d_s1 - self.d_s2)
            * (self.h_c - self.d_s1)
        )

        x = epsilon_c2 / (epsilon_c2 - epsilon_s1) * self.d


        while (N_Rd_C > self.NEd_GZT) and (iter < 1000) and (abs(epsilon_c2) <= 3.5e-3):
            

            eps_0 = epsilon_s2 + (abs(epsilon_s2 - epsilon_s1)) / (
                self.h_c - self.d_s1 - self.d_s2
            ) * (self.h_c - self.d_s2)

            delta_eps_h = epsilon_c2 - eps_0

            x = epsilon_c2 / (epsilon_c2 - epsilon_s1) * self.d

            N_cRd_C = 0
            F_cd_list = np.zeros(1000)

            eps_list = []

            for i in range(0, len(self.section_height_list), 1):
                
                epsilon_i = eps_0 + delta_eps_h / (self.num_stripes) * (i+1.5)

                if epsilon_i <= 0:
                    sigma_c = self.Nonlinear_Material_Law(epsilon_i)[2]
                else:
                    sigma_c = 0

                F_cd_i = sigma_c * self.delta_height * self.section_width_list[i]

                F_cd_list[i] = F_cd_i

            N_cRd_C = F_cd_list.sum() * (-1)

            if abs(epsilon_s2) <= 2.174e-3:
                N_s2_Rd_C = epsilon_s2 * self.A_s2 * self.Baustoff.Es
            else:
                N_s2_Rd_C = -self.A_s2 * self.Baustoff.fyd

            if abs(epsilon_s1) <= 2.174e-3:
                N_s1_Rd_C = epsilon_s1 * self.A_s1 * self.Baustoff.Es
            else:
                N_s1_Rd_C = self.Baustoff.fyd * self.A_s1

            N_Rd_C = N_cRd_C + N_s2_Rd_C + N_s1_Rd_C

            if abs(N_Rd_C - self.NEd_GZT) > 1e-1:
                epsilon_s2 -= 1e-4
            else:
                epsilon_s2 -= 1e-5

            epsilon_c2 = epsilon_s1 + (
                (epsilon_s2 - epsilon_s1)
                / (self.h_c - self.d_s1 - self.d_s2)
                * (self.h_c - self.d_s1)
            )

            iter += 1




        print("H-GGW", abs(N_Rd_C - self.NEd_GZT))
        print("eps s1 - ITER", epsilon_s1)
        print("eps s2 - ITER", epsilon_s2)
        print("eps c2 - ITER", epsilon_c2)

        print("NRd_C - ITER", N_Rd_C)
        print("NRd_s1 - ITER", N_s1_Rd_C)
        print("NRd_s2 - ITER", N_s2_Rd_C)
        

        # self.M_C_Iter = (
        #     abs(N_cRd_C) * (self.z_cu - x + a)
        #     + abs(N_s2_Rd_C) * (self.z_cu - self.d_s2)
        #     + abs(N_s1_Rd_C) * (self.z_co - self.d_s1)
        # )

        # self.kappa_C_Iter = (epsilon_s1 - epsilon_c2) / self.d

        # self.results_C_Iterate.append(("M_C", self.M_C_Iter))
        # self.results_C_Iterate.append(("Kappa_C", self.kappa_Iter))

    def Point_D(self):
        """
        Point D represents the point in the M-Kappa-Law, where \n
        the concrete reaches its breaking strain. \n
        Therefore the iteration starts at -3.50e-3 for the concrete strain epsilon_c2 \n
        The iteration is performed over the strain of the tensional reinforcement \n

        """
        N_Rd_D = self.NEd_GZT - 1
        iter = 0

        epsilon_s1 = 0

        epsilon_c2 = -3.5e-3
        epsilon_s2 = epsilon_c2 + (epsilon_c2 - epsilon_s1) / (self.d) * (self.d_s2)

        x = epsilon_c2 / (epsilon_c2 - epsilon_s1) * self.d

        while (N_Rd_D < self.NEd_GZT) and (iter < 10000):
            eta = self.Nonlinear_Material_Law(epsilon_c2)[0]
            k = self.Nonlinear_Material_Law(epsilon_c2)[1]
            sigma_c = self.Nonlinear_Material_Law(epsilon_c2)[2]

            epsilon_c_list = np.linspace(0, epsilon_c2, 100)

            sigma_c_list = self.Nonlinear_Material_Law(epsilon_c_list)[2]

            x_list = np.linspace(0, x, 100)

            if abs(N_Rd_D - self.NEd_GZT) > 1e-1:
                epsilon_s1 += 1e-4
            else:
                epsilon_s1 += 1e-5

            print("epsilon s2", epsilon_s2)

            epsilon_s2 = epsilon_c2 + (epsilon_c2 - epsilon_s1) / (self.d) * (self.d_s2)

            x = epsilon_c2 / (epsilon_c2 - epsilon_s1) * self.d

            N_cRd_D = np.trapz(sigma_c_list, x_list) * self.b_c * (-1)
            if abs(epsilon_s2) <= 2.174e-3:
                N_s2_Rd_D = epsilon_s2 * self.A_s2 * self.Baustoff.Es
            else:
                N_s2_Rd_D = -self.A_s2 * self.Baustoff.fyd
            if abs(epsilon_s1) <= 2.174e-3:
                N_s1_Rd_D = epsilon_s1 * self.A_s1 * self.Baustoff.Es
            else:
                N_s1_Rd_D = self.Baustoff.fyd * self.A_s1

            N_Rd_D = N_cRd_D + N_s2_Rd_D + N_s1_Rd_D

            print("N_D", N_cRd_D)
            print("NDs2", N_s2_Rd_D)
            print("NDs1", N_s1_Rd_D)

            print("NDRd", N_Rd_D)

            print("NEd", self.NEd_GZT)

            print(N_Rd_D > self.NEd_GZT)

            print(epsilon_c2)

            # Berechnung des Abstands der Druckresultierenden von DNL

            dx = x_list[1] - x_list[0]

            # Berechnung der Fläche unter der Kurve (Flächenmoment 0. Grades)
            A = np.sum(sigma_c_list * dx)

            # Berechnung des 1. Flächenmoments um den Ursprung
            S = np.sum(sigma_c_list * x_list * dx)

            # Berechnung des Schwerpunkts
            a = S / A

            iter += 1

        print("a", a)
        print("x", x)

        self.M_D = (
            abs(N_cRd_D) * (self.z_cu - x + a)
            + abs(N_s2_Rd_D) * (self.z_cu - self.d_s2)
            + abs(N_s1_Rd_D) * (self.z_co - self.d_s1)
        )

        print(self.M_D)

        self.kappa_D = (epsilon_s1 - epsilon_c2) / self.d

        self.results_D.append(("M_D", self.M_D))
        self.results_D.append(("Kappa_D", self.kappa_D))

    def Point_D_Iterative(self):
        print("Point D Iterative")

    def Interpolation_Function(self, _M_Value):
        if self.kappa_B == None or round(self.A_s2, 0) == 0:
            try:
                kappa = [0, self.kappa_A, self.kappa_C, self.kappa_D]
                M = [0, self.M_A, self.M_C, self.M_D]
            except:
                kappa = [0, self.kappa_A, self.kappa_C]
                M = [0, self.M_A, self.M_C]
        else:
            try:
                kappa = [0, self.kappa_A, self.kappa_B, self.kappa_C]
                M = [0, self.M_A, self.M_B, self.M_C]
            except:
                kappa = [0, self.kappa_A, self.kappa_B, self.kappa_C]
                M = [0, self.M_A, self.M_B, self.M_C]

        moment_to_kappa_function = interp1d(M, kappa, kind="linear")

        # Gegebenen Momentenwert, für den du den kappa-Wert finden möchtest
        M_value = _M_Value  # Beispielwert für das Moment

        # Berechne den zugehörigen kappa-Wert
        kappa_value = moment_to_kappa_function(M_value)

        # Einzelwert ausgeben
        # print(f"Der zugehörige kappa-Wert für M = {M_value} ist kappa = {kappa_value}")

        # Plot der Original-Stützpunkte und der interpolierten Werte
        kappa_new = np.linspace(min(kappa), max(kappa), 100)
        M_interpolated = interp1d(kappa, M, kind="linear")(
            kappa_new
        )  # Interpolierte Momentenwerte


        return kappa_value, M_value, kappa,kappa_new,M_interpolated,M
    

    
    def Plot_Interpolation_M_Kappa(self, kappa_value, M_value, kappa,kappa_new,M_interpolated,M):
        plt.plot(kappa, M, "o", label="Stützpunkte")  # Original-Stützpunkte
        plt.plot(
            kappa_new, M_interpolated, "-", label="Interpolierte Werte"
        )  # Interpolierte Werte

        # Einzelnen interpolierten Punkt für den Momentenwert markieren
        plt.plot(kappa_value, M_value, "ro", label=f"kappa-Wert bei M={M_value:.2f}")
        plt.text(
            kappa_value,
            M_value,
            f"kappa = {kappa_value:.2e}, M = {M_value:.2f} ",
            color="red",
            verticalalignment="bottom",
        )

        # Legende und Plot anzeigen

        plt.legend()
        plt.show(block=False)  # block=False sorgt dafür, dass das Skript nicht anhält

        # 3 Sekunden warten
        plt.pause(5)

        # Fenster schließen
        plt.close()

    def results_to_latex_table(self, results, headers, caption):
        # Initialisiere LaTeX-Code mit Table- und Tabular-Umgebung
        latex_code = (
            "\\begin{table}[htbp]\n\\centering\n\\begin{tabular}{|"
            + "|".join(["c"] * len(headers))
            + "|}\n\\hline\n"
        )

        # Füge die Kopfzeile hinzu
        latex_code += " & ".join(headers) + " \\\\ \\hline\n"

        # Füge die Datenzeilen hinzu
        for result in results:
            # Überprüfen, ob alle Werte in der Zeile numerisch sind, bevor sie formatiert werden
            formatted_result = []
            for val in result:
                if isinstance(val, float):
                    formatted_result.append(f"{val:.4f}")
                else:
                    formatted_result.append(str(val))

            latex_code += " & ".join(formatted_result) + " \\\\ \\hline\n"

        # Schließe die Tabular- und Table-Umgebung
        latex_code += "\\end{tabular}\n\\caption{" + caption + "}\n\\end{table}\n"

        return latex_code

    def generate_latex_plot(
        self,
        data_x,
        data_y,
        xlabel="x",
        ylabel="y",
        plot_title="Plot Title",
        plot_style="thick,blue",
        caption="Plot caption",
        connect_points=True,
    ):
        # Start des LaTeX-Codes
        latex_code = "\\begin{figure}[htbp]\n\\centering\n"

        # pgfplots Umgebung
        latex_code += "\\begin{tikzpicture}\n\\begin{axis}[\n"
        latex_code += f"title={{{plot_title}}},\n"
        latex_code += f"xlabel={{{xlabel}}},\n"
        latex_code += f"ylabel={{{ylabel}}},\n"
        latex_code += "grid=major,\n]\n"

        # Plotdaten
        plot_option = plot_style
        if connect_points:
            plot_option += ",sharp plot"

        latex_code += f"\\addplot[{plot_option}] coordinates {{\n"
        for x, y in zip(data_x, data_y):
            latex_code += f"({x},{y})\n"
        latex_code += "};\n"

        # Ende der pgfplots Umgebung
        latex_code += "\\end{axis}\n\\end{tikzpicture}\n"

        # Caption und Ende der Figure-Umgebung
        latex_code += f"\\caption{{{caption}}}\n"
        latex_code += "\\end{figure}\n"

        return latex_code


# Baumgart = M_Kappa_Cross_Section()

# print(Baumgart.section_width_list)

# Baumgart.PlotCrossSection()

# Baumgart.Interpolation_Function(0.20)


# # Erzeuge das LaTeX-Diagramm mit den korrekten Daten
# latex_code = Baumgart.generate_latex_plot(data_x=kappa, data_y=M)

# Image = Baumgart.generate_latex_plot(kappa, M)

# plt.plot(kappa,M)


# # Speicher den LaTeX-Code in einer .tex-Datei
# with open("Output/Baumgart.tex", "w") as tex_file:
#     tex_file.write(Image )


