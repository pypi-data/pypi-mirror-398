
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.interpolate import interp1d

try:
    from Materialkennwerte_Beton import Baustoffe
    from Querschnittsbreite import PolygonSection
except:
    from KIB_LAP.Betonbau.Materialkennwerte_Beton import Baustoffe
    from KIB_LAP.Betonbau.Querschnittsbreite import PolygonSection


class Laengsbemessung:
    def __init__(
        self,
        fck=30,
        fyk=500,
        varphi_cal  = 0,
        epsilon_cs = 0,
        _LoadingType="csv",
        Iter="Bruch",
        Reinforcement="csv",
        Querschnittsbemessung="Polygon",
        P_m_inf = 0, A_p = 0, d_p1 = 0
    ):
        """_summary_

        Args:
            fck (int, optional): Charateristic compression strength of concrete material. Defaults to 30.
            fyk (int, optional): _description_. Defaults to 500.
            varphi_cal (int, optional): _description_. Defaults to 0.
            epsilon_cs (int, optional): _description_. Defaults to 0.
            _LoadingType (str, optional): _description_. Defaults to "csv".
            Iter (str, optional): _description_. Defaults to "Bruch".
            Reinforcement (str, optional): _description_. Defaults to "csv".
            Querschnittsbemessung (str, optional): _description_. Defaults to "Polygon".
            P_m_inf (int, optional): _description_. Defaults to 0.
            A_p (int, optional): _description_. Defaults to 0.
            d_p1 (int, optional): _description_. Defaults to 0.
        """
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


    def Baustoffe(self):
        BS = Baustoffe([self.fck,self.fyk])
        self.Ecm = BS.Ecm
        self.Es = BS.Es

        try:
            df = pd.read_csv("Materialparameter/Spannstahl.csv")
            self.Ep = float(df["Ep"])
        except:
            pass

    def Calculate_All(self):
        self.Querschnittswerte()
        self.Bewehrungsangaben()
        self.Baustoffe()
        self.ReadLoading()

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
        self.zcm_i = np.zeros(self.n_czone - 1)
        self.eps_zwischen = np.zeros(self.n_czone - 1)
        self.Fc_i = np.zeros(self.n_czone - 1)

        self.Fc_ges = 0
        self.F_c_list = []
        self.F_s1_ges = 0
        self.F_s1_list = []

        sum_h = []
        sum_F_s1 = []
        sum_F_s2 = []
        sum_F_c = []

        xi = 1e-4
        result = 1

        print("Iteration begins")
        p = 0
        while xi < 0.70:
            x = xi * self.d
            self.hu = self.height * (1 - xi)
            self.hc_i = np.linspace(self.hu, self.height, self.n_czone)

            for i in range(0, self.n_czone - 1, 1):
                self.hcm_i[i] = 0.5 * (self.hc_i[i] + self.hc_i[i + 1])
                self.bcm_i[i] = 0.5 * (
                    self.Querschnittswerte(self.hc_i[i])
                    + self.Querschnittswerte(self.hc_i[i + 1])
                )
                self.zcm_i[i] = self.d -x + x/self.n_czone * (i+1)

                self.eps_zwischen[i] = (i+1)/(self.n_czone+1) * self.bcm_i[i] * (self.hc_i[1] - self.hc_i[0]) * self.Ecm * self.zcm_i[i]
                

            epsilon_c2 = self.MEds_GZG / (
                self.eps_zwischen.sum()
                + self.Es
                * (1 - self.d_s2 / x)
                * (self.d - self.d_s2)
                * self.A_svorh2
                * 0.01**2
            )

            

            epsilon_s1 = epsilon_c2 * (self.d / x - 1)
            epsilon_s2 = epsilon_c2 * (1 - self.d_s2 / x)

            self.F_ci = 0
            self.epc_i= np.zeros(self.n_czone - 1)
            for i in range(0, self.n_czone-1, 1):
                self.epc_i[i] = epsilon_c2 * (i+1)/self.n_czone
                self.F_ci -= epsilon_c2 * (i+1)/(self.n_czone+1) * self.bcm_i[i] * (self.hc_i[1] - self.hc_i[0]) * self.Ecm

            if self.F_ci > 0:
                self.F_ci = 0

            self.F_s1 = (self.A_svorh * 0.01**2) * epsilon_s1 * self.Es
            self.F_s2 = epsilon_s2 * self.Es * self.A_svorh2 * 0.01**2 * (-1)

            result = - self.NEd_GZG + self.F_s1 + self.F_ci + self.F_s2

            sum_h.append(result)
            sum_F_s1.append(self.F_s1)
            sum_F_s2.append(self.F_s2)
            sum_F_c.append(self.F_ci)

            if abs(result) < 0.001:
                print("The iterated compression zone height xi is ", xi ,"and x = ", xi*self.d)
                self.xi = xi
                break
            if abs(result) > 0.5:
                xi += 0.01
            elif abs(result) > 0.01:
                xi += 0.001
            else:
                xi += 0.0001
            
       
            p+=1

        self.epsilon_c2_end = epsilon_c2

    def Iter_Gebrauchslast_Rect(self):
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

        Flag_One = False
        Flag_Two = False
        Flag_Three = False

        b = self.Querschnittswerte(self.height / 2)
        xi = 1e-4
        result = 1

        print("Iteration begins")
        p = 0
        while xi < 0.70:
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
                xi += 0.01
            elif abs(result) > 0.01:
                xi += 0.001
            else:
                xi += 0.0001
            
       
            p+=1
        self.epsilon_c2_end = epsilon_c2

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

        self.F_s2 = 0
        self.F_p = 0
        self.F_s1 = 0

        xi = 1e-5

        b = self.Querschnittswerte(self.height / 2)
        print("Iteration begins")

        while xi < 0.60:
            x = xi * self.d
            epsilon_c2 = self.MEds_GZG / (
                (self.d - x / 3) * (0.5 * b * x * self.Ecm)
                + self.F_s2 * (self.d - self.d_s2)
                - self.F_p * (self.d - (self.height - self.dp_1))
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


# Laengs = Laengsbemessung(P_m_inf=0,A_p=81*0.01**2,d_p1=0.12)

# Laengs.Calculate_All()

# Laengs.Iter_Gebrauchslast()

# print("RESULTS ITERATION")
# print("Fcd" ,Laengs.F_ci)
# print("Fs1",Laengs.F_s1)
# print("Fs2",Laengs.F_s2)
# print("NEd",Laengs.NEd_GZG)

# print("eps2", Laengs.epsilon_c2_end)

# print("z_cm_i")
# plt.plot(Laengs.zcm_i)
# plt.show()

# print("Sigma_s1 [MPa]", Laengs.F_s1 / (Laengs.A_svorh*0.01**2))
# print("Sigma_s2 [MPa]", Laengs.F_s2 / (Laengs.A_svorh2*0.01**2))


# Laengs.Iter_Gebrauchslast_Rect()

# print("RESULTS - SEMI_ANALYTICAL")

# print("Fcd" ,Laengs.F_ci)
# print("Fs1",Laengs.F_s1)
# print("Fs2",Laengs.F_s2)
# print("NEd",Laengs.NEd_GZG)

# print("eps2", Laengs.epsilon_c2_end)

# print("Sigma_s1 [MPa]", Laengs.F_s1 / (Laengs.A_svorh*0.01**2))
# print("Sigma_s2 [MPa]", Laengs.F_s2 / (Laengs.A_svorh2*0.01**2))


# Laengs.Iter_Gebrauchslast_Spannbeton()

# print("Sigma_s1 [MPa]", Laengs.F_s1 / (Laengs.A_svorh*0.01**2))
# print("Sigma_s2 [MPa]", Laengs.F_s2 / (Laengs.A_svorh2*0.01**2))
