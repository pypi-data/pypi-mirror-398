from Querschnittsbreite import PolygonSection
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.interpolate import interp1d


class Baustoffe:
    def __init__(self, liste_baustoffe, h_c=0.13, b_c=4, traeger="FT", t0=1, t=365):
        """
        Klasse zur Berechnung der Baustoffparameter: Eingabe in [MN/m², m , MN, etc.]


        """
        # Teilsicherheitsbeiwerte für Baustoffe
        self.gamma_c = 1.5
        self.gamma_s = 1.15
        # Stahlbeton
        self.fck = liste_baustoffe[0]
        self.fcd = self.fck / self.gamma_c * 0.85
        self.fctm = 0.30 * self.fck ** (2 / 3)  # Nach Eurocode 2 Tabelle 3.1
        self.fctk_005 = 0.7 * self.fctm
        self.fcm = self.fck + 8
        self.Ecm = 22000 * (0.1 * self.fcm) ** (0.3)

        self.alpha_T = 1.2e-5

        # Kriechen und Schwinden

        self.traeger = traeger
        self.Zement = "I42.5N"
        self.LF = 80

        self.t0 = t0  # Annahme: Belastungsbeginn der Fertigteile nach 28 d
        self.t = t

        # Querschnittswerte für Kriechen / Schwinden

        self.b_c = b_c
        self.h_c = h_c

        self.A = self.b_c * self.h_c
        if self.traeger == "FT":
            self.u = self.b_c
        elif self.traeger == "Normal":
            self.u = self.b_c * 2  # Zur Trocknung freigesetzter Umfang
        else:
            self.u = self.b_c * 2

        self.h_0 = 2 * self.A / self.u

        # Stahl
        self.fyk = liste_baustoffe[1]
        self.fyd = self.fyk / self.gamma_s
        self.Es = 2e5
        self.Materialgesetz_Beton()
        self.Kriechzahlen()
        self.Schwindzahlen()

    def Materialgesetz_Beton(self):
        self.eps_c1 = 0.7 * self.fcm**0.31
        self.eps_c1 = min(self.eps_c1, 2.8)  # Sicherstellen, dass eps_c1 <= 2.8

    def Kriechzahlen(self):
        self.Zement = "I42.5N"

        if self.Zement == "I42.5N" or self.Zement == "I32.5R":
            self.alpha = 0
        elif (
            self.Zement == "I42.5R"
            or self.Zement == "I52.5N"
            or self.Zement == "I52.5R"
        ):
            self.alpha = 1
        else:
            self.alpha = -1

        self.t_0 = self.t0

        self.t_0_eff = max(
            self.t_0 * (1 + 9 / (2 + self.t_0 ** (1.2))) ** self.alpha, 0.5
        )

        self.t_infty = (
            self.t
        )  # self.t_0+15       #70 * 365  Annahme: 15 Tage nach der Betonage

        self.RH = self.LF  # Außenliegendes Bauteil

        # Fallunterscheidung für Druckfestigkeit
        self.alpha_1 = min((35 / self.fcm) ** 0.7, 1)
        self.alpha_2 = min((35 / self.fcm) ** 0.2, 1)
        self.alpha_3 = min((35 / self.fcm) ** 0.5, 1)

        # Einfluss der Luftfeuchte und wirksamer Bauteildicke
        if self.fcm <= 35:
            self.phi_rh = 1 + (1 - self.RH / 100) / (
                0.1 * (self.h_0 * 1000) ** (0.3333333)
            )
        else:
            self.phi_rh = (
                1
                + (1 - self.RH / 100)
                / (0.1 * (self.h_0 * 1000) ** (0.3333333))
                * self.alpha_1
            ) * self.alpha_2

        # Einfluss der Betondruckfestigkeit
        self.beta_fcm = 16.8 / np.sqrt(self.fcm)
        # Einfluss des Belastungsbeginns
        self.beta_t0 = 1 / (0.1 + self.t_0_eff**0.2)

        # Einfluss der Luftfeuchte - Beta-Beiwert
        if self.fcm <= 35:
            self.beta_h = min(
                1.5 * (1 + (0.012 * self.RH) ** 18) * self.h_0 * 1000 + 250, 1500
            )
        else:
            self.beta_h = min(
                1.5 * (1 + (0.012 * self.RH) ** 18) * self.h_0 * 1000
                + 250 * self.alpha_3,
                1500 * self.alpha_3,
            )

        # Einfluss der Belastungsdauer und Belastungsbeginn

        self.beta_c_t_t0 = (
            (self.t_infty - self.t_0) / (self.beta_h + self.t_infty - self.t_0)
        ) ** 0.30

        self.phi_infty = (
            self.phi_rh * self.beta_fcm * self.beta_t0 * self.beta_c_t_t0
        )  # Kriechzahl zum Zeitpunkt t

        print("Kriechzahl phi ", self.phi_infty)

    def Schwindzahlen(self):
        self.beta_rh = 1.55 * (1 - (self.RH / 100) ** 3)

        if self.Zement == "I42.5N" or self.Zement == "I32.5R":
            self.alpha_as = 700
            self.alpha_ds1 = 4
            self.alpha_ds2 = 0.12
        elif (
            self.Zement == "I42.5R"
            or self.Zement == "I52.5N"
            or self.Zement == "I52.5R"
        ):
            self.alpha_as = 600
            self.alpha_ds1 = 6
            self.alpha_ds2 = 0.12
        else:
            self.alpha_as = 800
            self.alpha_ds1 = 3
            self.alpha_ds2 = 0.12

        self.epsilon_cd_0 = (
            0.85
            * ((220 + 110 * self.alpha_ds1) * np.exp(-self.alpha_ds2 * self.fcm / 10))
            * 1e-6
            * self.beta_rh
        )

        ts = 3  # Nachbehandlung des Betons
        self.t_s = ts

        t = self.t_infty
        self.t_infty_s = t

        self.beta_ds = (t - ts) / ((t - ts) + 0.04 * np.sqrt(self.h_0**3))

        if self.h_0 * 1000 <= 100:
            self.k_h = 1.00
        elif self.h_0 * 1000 > 100 and self.h_0 * 1000 <= 200:
            self.k_h = 1.00 - 0.15 / 100 * self.h_0 * 1000
        elif self.h_0 * 1000 > 200 and self.h_0 * 1000 <= 300:
            self.k_h = 0.85 - 0.10 / 100 * self.h_0 * 1000
        elif self.h_0 * 1000 > 300 and self.h_0 * 1000 <= 500:
            self.k_h = 0.75 - 0.05 / 100 * self.h_0 * 1000
        elif self.h_0 * 1000 > 500:
            self.k_h = 0.70

        self.epsilon_cd = self.beta_ds * self.epsilon_cd_0 * self.k_h

        # Autogenes Schwinden
        self.epsilon_ca_infty = 2.5 * (self.fck - 10) * 1e-6
        self.beta_as = 1 - np.exp(-0.2 * np.sqrt(t))

        self.epsilon_ca = self.beta_as * self.epsilon_ca_infty

        # Gesamtschwinden
        self.epsilon_cs = self.epsilon_cd + self.epsilon_ca

        print("Gesamtschwindmaß ", self.epsilon_cs)


class Laengsbemessung:
    def __init__(
        self,
        fck=30,
        fyk=500,
        _LoadingType="csv",
        Iter="Bruch",
        Reinforcement="csv",
        Querschnittsbemessung="Polygon",
        P_m_inf = 0, A_p = 0, d_p1 = 0
    ):
        # Calculation mode
        self.Iter = Iter
        # Material properties from input
        self.fck = fck
        self.fyk = fyk
        self.varepsilon_grenz = 2  # In Permille
        self.n_czone = 100
        # Init design values for loading
        self.LoadingType = _LoadingType

        self.NEd_GZT = 0
        self.MEd_GZT = 0
        self.MEds_GZT = 0
        self.Mrds_GZT = 0

        self.NEd_GZG = 0
        self.MEd_GZG = 0
        self.MEds_GZG = 0

        self.PM_inf = P_m_inf

        

        # Geometric parameters for the design
        self.Bewehrung = Reinforcement

        self.d_s1 = 0
        self.d_s2 = 0
        self.dp_1 = d_p1        # Abstand der Außenkante Biegezug bis elast. Zentrum des Spannglieds

        self.A_svorh = 0
        self.A_svorh2 = 0

        self.Ap = A_p
        try:
            self.epsilon_pm_inf = abs(self.PM_inf / self.Ap * 1/ self.Ep )    #Vordehnung
        except:
            self.epsilon_pm_inf = 0
        self.epsilon_yk = 1500/195000   # Für St 1550/1770

    def Calculate_All(self):
        self.Querschnittswerte()
        self.Bewehrungsangaben()
        self.Baustoffe()
        self.ReadLoading()
        self.Iter_Gebrauchslast()
        # if self.Iter == "Bruch":
        #     self.Iter_Compression()
        # else:
        #     self.Iter_Gebrauchslast()

    def Querschnittswerte(self, _height_test=0.5):
        # Example usage
        df = pd.read_csv("Polygon/Polygon.csv")
        self.vertices = df.values.tolist()

        self.polygon = PolygonSection(self.vertices)

        # Calculate the height of the polygon based on y-values

        y_values = [vertex[1] for vertex in self.vertices]
        self.height = abs(max(y_values) - min(y_values))
        self.z_su = self.height - self.polygon.centroid[0]
        self.z_so = self.height - self.z_su

        # Define the rotation angle
        self.angle_degrees = 0
        self.polygon.rotate(self.angle_degrees)

        height = _height_test
        section_width = self.polygon.calculate_section_width_at_height(height)

        return section_width

    def PlotCrossSection(self, _height_test=0.5):
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
                    self.A_svorh = df["As [cm**2]"][i]
                elif Lage == "Oben":
                    self.d_s2 = (
                        df["dsl [m]"][i] * 0.5 + df["cnom [m]"][i] + df["dsw [m]"][i]
                    )
                    self.A_svorh2 = df["As [cm**2]"][i]

            self.z_ds1 = self.z_su - self.d_s1
            self.z_ds2 = self.z_so - self.d_s2

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
                    self.MEd_GZT - self.NEd_GZT * self.z_ds1 + self.PM_inf * (self.dp_1 - self.d_s1)
                )  # Bezug auf die Biegezugbewehrung (Hier UNTEN)
                self.NEd_GZT -= self.PM_inf
                self.Zugseite_GZT = "UNTEN"
                self.d = self.height - self.d_s1
            elif self.MEd_GZT < 0:
                self.MEds_GZT = abs(
                    self.MEd_GZT + self.NEd_GZT * self.z_ds2 - self.PM_inf * (self.dp_1 - self.d_s1)
                )  # Bezug auf die Biegezugbewehrung (Hier OBEN)
                self.NEd_GZT -= self.PM_inf
                self.Zugseite_GZT = "OBEN"
                self.d = self.height - self.d_s2

            if self.MEd_GZG >= 0:
                self.MEds_GZG = self.MEd_GZG - self.NEd_GZG * self.z_ds1  + self.PM_inf * (self.dp_1 - self.d_s1)
                self.NEd_GZG -= self.PM_inf
                self.Zugseite_GZG = "UNTEN"
                self.d = self.height - self.d_s1
            elif self.MEd_GZG < 0:
                self.MEds_GZG = self.MEd_GZG + self.NEd_GZG * self.z_ds2  - self.PM_inf * (self.dp_1 - self.d_s1)
                self.NEd_GZG -= self.PM_inf
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

        df = pd.DataFrame(
            {
                "GZT": [
                    self.NEd_GZT,
                    self.MEd_GZT,
                    self.zsi_GZT,
                    self.MEds_GZT,
                    self.Zugseite_GZT,
                ],
                "GZG": [
                    self.NEd_GZG,
                    self.MEd_GZG,
                    self.zsi_GZG,
                    self.MEds_GZG,
                    self.Zugseite_GZG,
                ],
            },
            index=[
                "NEd [MN]",
                "MEd in [MNm]",
                "zsi in [m]",
                "|MEds| in [MNm]",
                "Zugseite",
            ],
        )

        df.to_csv("Output/Design_Forces.csv")

    def Baustoffe(self):
        self.fcd = self.fck / 1.5 * 0.85
        self.fctm = 0.30 * self.fck ** (2 / 3)  # Nach Eurocode 2 Tabelle 3.1
        self.fctk_005 = 0.7 * self.fctm
        self.fcm = self.fck + 8
        self.Ecm = 22000 * (self.fcm / 10) ** 0.3
        # Stahl
        self.fyd = self.fyk / 1.15
        self.Es = 200000
        # Spannstahl
        self.Ep = 195000 # Für Litzen

    def Sigma_ParabalRechteck(self, _varepsilon):
        if _varepsilon <= self.varepsilon_grenz:
            sigma = self.fcd * (1 - (1 - _varepsilon / self.varepsilon_grenz) ** 2)
            return sigma
        else:
            sigma = self.fcd
            return sigma

    def Sigma_Gebrauchslasten(self, _varepsilon):
        """
        This function returns the concrete stresses under
        servicability strains smaller than 0.5e-3.
        Args:
            _varepsilon (_type_): _description_

        Returns:
            _type_: _description_
        """
        return self.Ecm * _varepsilon * 1e-3

    def Iter_Compression(self):
        print("iteration")
        iter = 0
        self.epss = 25
        self.epsc = 0.00
        self.dimensionsless_moment = 0
        self.limit_dimensionless_moment = 0.296
        self.bcm_i = np.zeros(self.n_czone - 1)
        self.hcm_i = np.zeros(self.n_czone - 1)

        self.Fc_i = np.zeros(self.n_czone - 1)

        while self.Mrds <= self.Meds and iter <= 10000:
            self.xi = self.epsc / (self.epss + self.epsc)
            self.hu = self.height * (1 - self.xi)

            self.hc_i = np.linspace(self.hu, self.height, self.n_czone)
            self.Mrds = 0

            for i in range(0, self.n_czone - 1, 1):
                self.hcm_i[i] = 0.5 * (self.hc_i[i] + self.hc_i[i + 1])
                self.bcm_i[i] = 0.5 * (
                    self.Querschnittswerte(self.hc_i[i])
                    + self.Querschnittswerte(self.hc_i[i + 1])
                )

            for i in range(0, self.n_czone - 1, 1):
                epsilon_ci = abs(
                    self.epss
                    - (self.epsc + self.epss) / self.d * (self.hcm_i[i] - self.d_s1)
                )
                sigma_ci = self.Sigma_ParabalRechteck(epsilon_ci)

                self.Fc_i[i] = (
                    (self.hc_i[i + 1] - self.hc_i[i]) * self.bcm_i[i] * sigma_ci
                )

                self.Mrds += self.Fc_i[i] * (self.hcm_i[i] - self.d_s1)

            iter += 1

            if self.epsc >= 3.5:
                while self.Mrds <= self.Meds and iter <= 10000:
                    self.Mrds = 0

                    self.xi = self.epsc / (self.epss + self.epsc)
                    self.hu = self.height * (1 - self.xi)
                    self.hc_i = np.linspace(self.hu, self.height, self.n_czone)

                    for i in range(0, self.n_czone - 1, 1):
                        self.hcm_i[i] = 0.5 * (self.hc_i[i] + self.hc_i[i + 1])
                        self.bcm_i[i] = 0.5 * (
                            self.Querschnittswerte(self.hc_i[i])
                            + self.Querschnittswerte(self.hc_i[i + 1])
                        )
                        epsilon_ci = abs(
                            self.epss
                            - (self.epsc + self.epss)
                            / self.d
                            * (self.hcm_i[i] - self.d_s1)
                        )
                        sigma_ci = self.Sigma_ParabalRechteck(epsilon_ci)
                        self.Fc_i[i] = (
                            (self.hc_i[i + 1] - self.hc_i[i]) * self.bcm_i[i] * sigma_ci
                        )

                        self.Mrds += self.Fc_i[i] * (self.hcm_i[i] - self.d_s1)

                    iter += 1

                    if abs(self.Mrds - self.Meds) > 0.15:
                        self.epss -= 0.1
                    elif abs(self.Mrds - self.Meds) > 0.02:
                        self.epss -= 0.01
                    else:
                        self.epss -= 0.001

            if abs(self.Mrds - self.Meds) > 0.15:
                self.epsc += 0.1
            elif abs(self.Mrds - self.Meds) > 0.02:
                self.epsc += 0.01
            else:
                self.epsc += 0.0001

        self.F_sd = self.Fc_i.sum() + self.NEd
        self.A_serf = self.F_sd / self.fyd

        print(
            "The required reinforcement for bending is ",
            self.A_serf * 100**2,
            "cm**2",
        )
        
    def Iter_Gebrauchslast(self):
        iter = 0

        self.bcm_i = np.zeros(self.n_czone - 1)
        self.hcm_i = np.zeros(self.n_czone - 1)
        self.Fc_i = np.zeros(self.n_czone - 1)

        self.Fc_ges = 0
        self.F_c_list = []
        self.F_s1_ges = 0
        self.F_s1_list = []

        sum_h = []
        sum_F_s1 = []
        sum_F_s2 = []
        sum_F_c = []

        resu = []

        b = self.Querschnittswerte(self.height / 2)
        xi = 1e-4
        result = 1

        print("Iteration begins")
        p = 0
        while xi < 0.70:
            print(xi)
            x = xi * self.d

            epsilon_c2 = self.MEds_GZG / (
                (self.d - x / 3) * (0.5 * b * x * self.Ecm)
                + self.Es
                * (1 - self.d_s2 / x)
                * (self.d - self.d_s2)
                * self.A_svorh2
                * 0.01**2
            )

            sigma_c2 = epsilon_c2 * self.Ecm
            epsilon_s1 = epsilon_c2 * (self.d / x - 1)
            epsilon_s2 = epsilon_c2 * (1 - self.d_s2 / x)

            self.F_ci = 0.5 * b * x * sigma_c2 * (-1)
            if self.F_ci > 0:
                self.F_ci = 0

            self.F_s1 = (self.A_svorh * 0.01**2) * epsilon_s1 * self.Es
            self.F_s2 = epsilon_s2 * self.Es * self.A_svorh2 * 0.01**2 * (-1)

            result = - self.NEd_GZG + self.F_s1 + self.F_ci + self.F_s2

            sum_h.append(result)
            sum_F_s1.append(self.F_s1)
            sum_F_s2.append(self.F_s2)
            sum_F_c.append(self.F_ci)

            if abs(result) < 0.0001:
                print("The iterated compression zone height xi is ", xi ,"and x = ", xi*self.d)
                self.xi = xi
                break
            
            if abs(result) > 0.5:
                xi += 0.0001
            elif abs(result) > 0.01:
                xi += 0.00001
            else:
                xi += 0.000001
            
       
            p+=1

        print(xi)
        # plt.plot(sum_h)
        # plt.show()
    
    def Iter_Gebrauchslast_Spannbeton(self):
        iter = 0

        self.bcm_i = np.zeros(self.n_czone - 1)
        self.hcm_i = np.zeros(self.n_czone - 1)
        self.Fc_i = np.zeros(self.n_czone - 1)

        self.Fc_ges = 0
        self.F_c_list = []
        self.F_s1_ges = 0
        self.F_s1_list = []

        sum_h = []
        sum_F_s1 = []
        sum_F_s2 = []
        sum_F_c = []
        sum_F_p = []

        xi = 1e-5

        b = self.Querschnittswerte(self.height / 2)
        print("Iteration begins")

        while xi < 0.60:
            x = xi * self.d
            epsilon_c2 = self.MEds_GZG / (
                (self.d - x / 3) * (0.5 * b * x * self.Ecm)
                + self.Es
                * (1 - self.d_s2 / x)
                * (self.d - self.d_s2)
                * self.A_svorh2
                * 0.01**2
                
            )

            sigma_c2 = epsilon_c2 * self.Ecm
            epsilon_s1 = epsilon_c2 * (self.d / x - 1)
            epsilon_s2 = epsilon_c2 * (1 - self.d_s2 / x)

            epsilon_p = epsilon_c2 + (abs(epsilon_c2) + epsilon_s1)/self.d * (self.height - self.dp_1) # Additional strains in the prestressing cable

            self.F_ci = 0.5 * b * x * sigma_c2

            if self.F_ci < 0:
                self.F_ci = 0
            if (epsilon_s1 * self.Es <= self.fyk):
                self.F_s1 = (self.A_svorh * 0.01**2) * epsilon_s1 * self.Es
            else:
                self.F_s1 = (self.A_svorh * 0.01**2) * self.fyk
            if (epsilon_s2 * self.Es <= self.fyk):
                self.F_s2 = epsilon_s2 * self.Es * self.A_svorh2 * 0.01**2
            else:
                self.F_s2 = - self.fyk * self.A_svorh2 * 0.01**2

            if (abs(epsilon_p  +self.epsilon_pm_inf) <= self.epsilon_yk):
                self.F_p = abs((epsilon_p)) * self.Ep * self.Ap 
            else:
                self.F_p = 1500 * self.Ap 

            result = -self.NEd_GZG + self.F_s1 - self.F_ci + self.F_s2 + self.F_p

            sum_h.append(result)
            sum_F_s1.append(self.F_s1)
            sum_F_s2.append(self.F_s2)
            sum_F_c.append(self.F_ci)

            if abs(result) < 0.0001:
                print("The iterated compression zone height xi is ", xi)
                self.xi = xi
                break


            if abs(result) > 0.7:
                xi += 0.0001
            elif abs(result) > 0.10:
                xi += 0.00001
            else:
                xi += 0.000001

        print("Ned", self.NEd_GZG)
        print("xi",xi)
        print("Sum H", result)
        print("MEds - GZG", self.MEds_GZG)
        print("NEd - GZG", self.NEd_GZG)

        print("Fcd", self.F_ci)
        print("FP", self.F_p)
        print("Fs1" , self.F_s1)
        print("Fs2", self.F_s2)


Laengs = Laengsbemessung(P_m_inf=0,A_p=37.8*0.01**2,d_p1=0.19)

Laengs.Calculate_All()

print("Fcd" ,Laengs.F_ci)
print("Fs1",Laengs.F_s1)
print("Fs2",Laengs.F_s2)
print("NEd",Laengs.NEd_GZG)

print("Sigma_s1 [MPa]", Laengs.F_s1 / (Laengs.A_svorh*0.01**2))
print("Sigma_s2 [MPa]", Laengs.F_s2 / (Laengs.A_svorh2*0.01**2))

print(Laengs.MEds_GZG)

print(Laengs.z_su)
print(Laengs.d_s1)
print(Laengs.d_s2)

Laengs.PlotCrossSection()

# Laengs.Iter_Gebrauchslast_Spannbeton()

