import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.interpolate import interp1d
from Cross_Section_Kappa import M_Kappa_Cross_Section
from Querschnittsbreite import PolygonSection

class Druckgliedbemessung_KGV:
    def __init__(
        self,
        _LoadingType="csv_druckglied",
        Iter="Bruch",
        Reinforcement="csv",
        Querschnittsbemessung="Polygon",
    ):
        self.Bewehrung = Reinforcement
        self.LoadingType = _LoadingType

        self.Querschnittswerte(0.5)
        self.Bewehrungsangaben()
        self.ReadLoading()
        self.Calculate_M_Kappa_Interpolation()
        self.Calculate_Cross_Section_Capacity()
        self.Column_Parameters()
        self.Iteration_Second_Order()

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

        height = _height_test
        section_width = self.polygon.calculate_section_width_at_height(height / 2)

        self.h_c = height
        self.b_c = section_width

        self.A = self.polygon.A

        return section_width

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
        if self.LoadingType == "csv_druckglied":
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

        else:
            self.NEd_GZT = float(
                input("Geben Sie die Normalkraft NEd im GZT in [MN] ein: \n")
            )
            self.MEd_GZT1 = float(
                input("Geben Sie das Biegemoment an Stelle 1 im GZT in [MN] ein: \n")
            )

            self.MEd_GZT2 = float(
                input("Geben Sie das Biegemoment an Stelle 2 im GZT in [MN] ein: \n")
            )

    def Calculate_M_Kappa_Interpolation(self):
        self.M_Kappa = M_Kappa_Cross_Section("csv_druckglied")

    def Calculate_Cross_Section_Capacity(self):
        try:
            self.M_Rd = self.M_Kappa.M_D
            print("The maximum Moment for the cross section is: ", self.M_Rd)
        except:
            self.M_Rd = self.M_Kappa.M_C
            print("The maximum Moment for the cross section is: ", self.M_Rd)

    def Column_Parameters(self):
        df = pd.read_csv("Systemgeometrie/Druckglied.csv")
        self.l_col = df["lcol in [m]"].iloc[0]

    def Iteration_Second_Order(self):
        M_Ed1_0 = self.MEd1_GZT
        M_Ed1_1 = self.MEd1_GZT
        M_Ed2_0 = self.MEd2_GZT

        self.M_0_List = np.linspace(M_Ed1_0, M_Ed2_0, 100)
        self.M_1_List = np.linspace(self.l_col, 0, 100)

        kappa_1 = float(self.M_Kappa.Interpolation_Function(M_Ed1_1)[0])
        kappa_2 = float(self.M_Kappa.Interpolation_Function(M_Ed2_0)[0])

        print("KAPPA 1", kappa_1)

        x_list = np.linspace(0, float(self.l_col), 100)

        # kappa_list = [kappa_1 - (kappa_1 - kappa_2) / 99 * i for i in range(0, 100, 1)]
        kappa_list = [kappa_1 - (kappa_1 - kappa_2) / 99 * i for i in range(100)]


        d_0 = np.trapz(self.M_1_List * kappa_list, x_list)

        iter = 0
        while iter < 100:
            print(M_Ed1_1 - M_Ed1_0)
            M_Ed1_0 = self.MEd1_GZT

            d_1 = np.trapz(self.M_1_List * kappa_list, x_list)

            M_Ed1_1 = self.MEd1_GZT + d_1 * abs(self.NEd_GZT)

            print("M0", M_Ed1_0)
            print("M1", M_Ed1_1)

            self.M_0_List = np.linspace(M_Ed1_1, M_Ed2_0, 100)

            for i in range(0, 100, 1):
                kappa_i = float(self.M_Kappa.Interpolation_Function(
                    M_Ed1_1 - (M_Ed1_1 - M_Ed2_0) / 99 * i
                )[0])
                kappa_list[i] = kappa_i

            if abs(M_Ed1_1 - M_Ed1_0) < 1e-3:
                break

            iter += 1

        print("Iteration ", iter)
        print("Deflection ", d_1)

        print("Moment ", M_Ed1_1)

        plt.plot(kappa_list)
        plt.show()

        kappa_value, M_value, kappa,kappa_new,M_interpolated,M =self.M_Kappa.Interpolation_Function(M_Ed1_1)
        self.M_Kappa.Plot_Interpolation_M_Kappa(kappa_value, M_value, kappa,kappa_new,M_interpolated,M)



Bemess = Druckgliedbemessung_KGV()

print(Bemess.M_Kappa.Baustoff.Ecm)
print(Bemess.M_Kappa.Baustoff.fctm)