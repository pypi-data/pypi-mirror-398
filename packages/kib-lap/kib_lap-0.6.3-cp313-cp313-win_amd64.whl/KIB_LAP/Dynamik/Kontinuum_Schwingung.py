import numpy as np
import pandas as pd

from scipy.interpolate import interp1d

import sqlite3
import matplotlib.pyplot as plt
try:
    from Deformation_Method import DeformationMethod
    from Cross_Section_Properties import cross_section_polygon
except:
    from KIB_LAP.Dynamik.Deformation_Method import DeformationMethod
    from KIB_LAP.Dynamik.Cross_Section_Properties import cross_section_polygon  


class Balkenschwingungen:
    def __init__(
        self,
        _l=16.40,
        _A=1.00,
        _rho=5063,
        _xi=0.0257,
        _E=2.1e11,
        _I=0.0288,
        _t_ber = 5,
        _BC="Hinged-Hinged",
        _cross_section=None,
        _x0 = 16.4/2,
        _v_train = 300
    ):
        ## Calculation Parameters

        self.ndt = 20  # Anzahl der Unterteilungen der kleinsten

        self.x0 =  _x0  # Stelle der Ausgabe [m]

        self.n = 5  # Anzahl der berücksichtigten Eigenformen

        self.v_zug_kmh = _v_train # Zuggeschwindigkeit in [km/h]

        ## Parameters for the pedestrian force vectors

        self.v_pedestrian = 2.205  # Speed of the pedestrian walk in [m/s]

        # Calculation time for harmonic and pedestrian calculation

        self.t_ber = _t_ber  # Dauer der Berechnung
        self.dt = 1e-3  # Definition of the time step

        # Integrationsparameter
        self.alpha = 0.5
        self.beta = 0.25

        # Voreinstellung der Lagerbedingungen

        self.boundary_condition = _BC

        # System properties

        self.l = _l  # Trägerlänge [m]
        if _cross_section == None:
            self.A = _A
            self.I = _I  # Flächenträgheitsmoment [m^4]
        else:
            self.A = _cross_section.A
            self.I = _cross_section.I_yy
        self.rho = _rho
        self.mue = self.A * self.rho  # Masse pro Längeneinheit [kg/m]
        self.xi = _xi  # Dämpfungsmaß [-]

        self.E = _E  # Elastizitätsmodul [N/m^2]

        # Loading condition

        self.loading = "train"

        #   Harmonic-Loading

        self.OMEGA = 6.38 * 2 * np.pi
        self.PHI_0 = 0
        self.F_0_H = 1e5

        # Test function

        self.test = False
        # Functions

        if self.test == True:
            self.load_database()
            self.load_definition()
            self.system_properties()
            self.load_conditions()
            self.generalized_load_function()
            self.beta_newmark()

        else:
            self.load_database()
            self.load_definition()
            self.system_properties()
            self.load_conditions()
            self.generalized_load_function()
            self.beta_newmark()

    def load_database(self):
        db_name = "Database/eigenmodes.db"
        # Connect to the SQLite database
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

        # Initializing numpy arrays
        self.lambda_cantilever = np.zeros(20)
        self.lambda_clamped_hinged = np.zeros(20)
        self.lambda_hinged_hinged = np.zeros(20)
        self.lambda_clamped_clamped = np.zeros(20)

        self.lambda_hinged_hinged_twospan = np.zeros(20)

        self.a_lambda_cantilever = np.zeros(20)
        self.a_lambda_clamped_hinged = np.zeros(20)
        self.a_lambda_clamped_clamped = np.zeros(20)

        self.J1_cantilever = np.zeros(20)
        self.J1_clamped_hinged = np.zeros(20)
        self.J1_hinged_hinged = np.zeros(20)
        self.J1_clamped_clamped = np.zeros(20)

        self.J2_cantilever = np.zeros(20)
        self.J2_clamped_hinged = np.zeros(20)
        self.J2_hinged_hinged = np.zeros(20)
        self.J2_clamped_clamped = np.zeros(20)

        self.J3_cantilever = np.zeros(20)
        self.J3_clamped_hinged = np.zeros(20)
        self.J3_hinged_hinged = np.zeros(20)
        self.J3_clamped_clamped = np.zeros(20)

        # Saving the Data-Base into the numpy arrays

        self.cursor.execute(
            "SELECT lambda_cantilever, lambda_clamped_hinged, lambda_hinged_hinged, lambda_clamped_clamped FROM eigenvalues"
        )
        data = self.cursor.fetchall()
        for i, row in enumerate(data):
            (
                self.lambda_cantilever[i],
                self.lambda_clamped_hinged[i],
                self.lambda_hinged_hinged[i],
                self.lambda_clamped_clamped[i],
            ) = row

        self.cursor.execute(
            "SELECT a_lambda_cantilever, a_lambda_clamped_hinged, a_lambda_clamped_clamped FROM a_lambda"
        )
        data = self.cursor.fetchall()
        for i, row in enumerate(data):
            (
                self.a_lambda_cantilever[i],
                self.a_lambda_clamped_hinged[i],
                self.a_lambda_clamped_clamped[i],
            ) = row

        self.cursor.execute(
            "SELECT J1_cantilever, J1_clamped_hinged, J1_hinged_hinged, J1_clamped_clamped FROM J1"
        )
        data = self.cursor.fetchall()
        for i, row in enumerate(data):
            (
                self.J1_cantilever[i],
                self.J1_clamped_hinged[i],
                self.J1_hinged_hinged[i],
                self.J1_clamped_clamped[i],
            ) = row

        self.cursor.execute(
            "SELECT J2_cantilever, J2_clamped_hinged, J2_hinged_hinged, J2_clamped_clamped FROM J2"
        )
        data = self.cursor.fetchall()
        for i, row in enumerate(data):
            (
                self.J2_cantilever[i],
                self.J2_clamped_hinged[i],
                self.J2_hinged_hinged[i],
                self.J2_clamped_clamped[i],
            ) = row

        self.cursor.execute(
            "SELECT J3_cantilever, J3_clamped_hinged, J3_hinged_hinged, J3_clamped_clamped FROM J3"
        )
        data = self.cursor.fetchall()
        for i, row in enumerate(data):
            (
                self.J3_cantilever[i],
                self.J3_clamped_hinged[i],
                self.J3_hinged_hinged[i],
                self.J3_clamped_clamped[i],
            ) = row

        for i in range(1,len(data)+1):
            if (i%2==1):
                self.lambda_hinged_hinged_twospan[i-1] = self.lambda_hinged_hinged[(i-1)//2]
            else:
                self.lambda_hinged_hinged_twospan[i-1] = self.lambda_clamped_hinged[(i//2)-1]

        print("Lambda - Two Span")
        print(self.lambda_hinged_hinged_twospan)
        # Close the connection
        self.conn.close()

    def load_definition(self):
        if self.loading == "train":
            Kraftdefinition = pd.read_csv(
                "Trainpassing/Inputdatei_1.txt", delim_whitespace=True
            )
            # # # Coordinates related to the first pair of wheels in [m]
            self.x_k = Kraftdefinition.iloc[:, 0].to_list()
            # # # Axial loads in [kN]
            self.P_k = Kraftdefinition.iloc[:, 1].to_list()

            self.P_k_array = np.zeros(len(self.P_k))

            for i in range(0, len(self.P_k), 1):
                self.P_k_array[i] = self.P_k[i]

        elif self.loading == "harmonic_single":
            self.x_k = self.l / 2
            self.P_k = 1

    def numeric_eigenvalues(self):
        # Calculation for numeric eigenmodes
        if self.boundary_condition == "Hinged-Hinged-Numeric":
            self.Deformation_Num = DeformationMethod(
                30, self.E, self.I, self.A, self.rho, self.l, "SPG", [1, 1], 1000
            )
            self.Deformation_Num.single_span_girder()
            self.Deformation_Num.compute_eigenfrequencies()
            self.Deformation_Num.modal_matrices()
        elif self.boundary_condition == "Two-Span-Girder":
            self.Deformation_Num = DeformationMethod(
                30, self.E, self.I, self.A, self.rho, self.l, "SPG", [1, 1], 1000
            )
            self.Deformation_Num.single_span_girder()
            self.Deformation_Num.compute_eigenfrequencies()
            self.Deformation_Num.modal_matrices()

    def load_conditions(self):
        # Eigenformen am Ausgabepunkt
        self.phi_a = np.zeros(self.n)

        # Loop for defining the eigenmodes at the loading point
        for i in range(self.n):
            if self.boundary_condition == "Hinged-Hinged":
                self.phi_a[i] = self.hinged_hinged(self.x0, i)
            elif self.boundary_condition == "Hinged-Hinged-Numeric":
                self.phi_a[i] = self.hinged_hinged_numeric(self.x0, i)
            elif self.boundary_condition == "Clamped-Hinged":
                self.phi_a[i] = self.clamped_hinged(self.x0, i)
            elif self.boundary_condition == "Clamped-Clamped":
                self.phi_a[i] = self.clamped_clamped(self.x0, i)
            elif self.boundary_condition == "Cantilever":
                self.phi_a[i] = self.cantilever(self.x0, i)
            elif self.boundary_condition == "Hinged-Hinged-TwoSpan":
                self.phi_a[i] = self.hingedhinged_twospan(self.x0, i)

        if self.loading == "train":
            # Train-Passing
            self.v_zug = self.v_zug_kmh * 1000 / 3600  # Zuggeschwindigkeit in [m/s]
            self.dt = 1e-3
            self.l_zug = max(self.x_k)  # Zuglänge
            self.T_u = (self.l + self.l_zug) / (
                self.v_zug
            )  # Zeit zur Überquerung des Trägers

            self.nt = int(np.ceil(self.t_ber / self.dt) + 1)  # Anzahl der Zeitschritte

            # Erstellung des Zeitvektors
            self.t = np.arange(0, self.nt * self.dt, self.dt)

            # Kraftdefinition für die Berechnung

            # Matrix zur Berücksichtigung der sich auf der Brücke befindenden Lasten
            # in jedem Zeitschritt

            self.F_Mat = np.zeros(
                (len(self.x_k), self.nt)
            )  # rows -> Index of the train load, cols = number of time steps

            print(max(self.t))

            for i in range(self.nt):
                for j in range(len(self.x_k)):
                    if (-self.x_k[j] + self.v_zug * self.t[i] > 0) and (
                        -self.x_k[j] + self.v_zug * self.t[i] < self.l
                    ):  # Condition, that the train needs to be on the bridge
                        self.F_Mat[j][i] = self.P_k[j]
                    else:
                        self.F_Mat[j][i] = 0

        elif self.loading == "harmonic_single":
            self.nt = int(np.ceil(self.t_ber / self.dt) + 1)  # Anzahl der Zeitschritte
            self.t = np.arange(0, self.nt * self.dt, self.dt)

            self.F_Mat = np.zeros(
                self.nt
            )  # rows = number of time steps, because there is just one single load

            for i in range(self.nt):
                self.F_Mat[i] = self.F_0_H * np.sin(
                    self.OMEGA * self.dt * i - self.PHI_0
                )

        elif self.loading == "pedestrian":
            self.nt = int(np.ceil(self.t_ber / self.dt) + 1)  # Anzahl der Zeitschritte
            self.t = np.arange(0, self.nt * self.dt, self.dt)

            self.F_Mat = np.zeros(
                self.nt
            )  # rows = number of time steps, because there is just one single load

            g_pedestrian = 700  # 800 N for normal case
            coeff_1 = 0.50
            coeff_2 = 0.10
            coeff_3 = 0.10

            step = 0.90

            for i in range(self.nt):
                if (self.v_pedestrian * self.t[i] > 0) and (
                    self.v_pedestrian * self.t[i] < self.l
                ):
                    self.F_Mat[i] = (
                        1
                        + coeff_1 * np.sin(2 * np.pi * 2.45 * self.t[i])
                        + coeff_2 * np.sin(4 * np.pi * 2.45 * self.t[i] - np.pi / 2)
                        + coeff_3 * np.sin(6 * np.pi * 2.45 * self.t[i] - np.pi / 2)
                    ) * g_pedestrian
                else:
                    self.F_Mat[i] = 0

    def system_properties(self):
        # Berechnung weiterer System- und Berechnungsparameter
        self.Freq = np.zeros(self.n)  # Eigenfrequenzen
        self.Omega = np.zeros(self.n)  # Eigenkreisfrequenzen
        self.T = np.zeros(self.n)  # Eigenschwingzeiten

        if self.boundary_condition == "Hinged-Hinged":
            for i in range(0, self.n, 1):
                if i == 0:
                    self.Freq[i] = i  # Static movement due to the
                else:
                    self.Freq[i] = (
                        (self.lambda_hinged_hinged[i - 1]) ** 2
                        / (2 * np.pi * self.l**2)
                    ) * np.sqrt(self.E * self.I / self.mue)
                print(self.Freq[i])

                self.Omega[i] = 2 * np.pi * self.Freq[i]
                if i == 0:
                    self.T[i] = 1e9
                else:
                    self.T[i] = 1 / self.Freq[i]

            self.m = np.zeros(self.n)  # Vektor der modalen Massen
            self.k = np.zeros(self.n)  # Vektor der modalen Steifigkeiten
            self.d = np.zeros(self.n)  # Vektor der modalen Dämpferkonstanten

            for i in range(self.n):
                self.m[i] = self.J1_hinged_hinged[i] * self.mue * self.l
                self.k[i] = self.Omega[i] ** 2 * self.m[i]
                self.d[i] = 2 * self.xi * np.sqrt(self.k[i] * self.m[i])

                print(self.m)

        elif self.boundary_condition == "Hinged-Hinged-Numeric":
            print("System Properties")

            for i in range(0, self.n, 1):
                self.Freq[i] = self.Deformation_Num.eigenfrequencies[i] / (np.pi * 2)
                self.Omega[i] = self.Deformation_Num.eigenfrequencies[i]
                self.T[i] = 1 / self.Freq[i]

            print(self.Deformation_Num.M_trans)
            print(self.Deformation_Num.K_trans)

            self.m = np.zeros(self.n)  # Vektor der modalen Massen
            self.k = np.zeros(self.n)  # Vektor der modalen Steifigkeiten
            self.d = np.zeros(self.n)  # Vektor der modalen Dämpferkonstanten

            for i in range(self.n):
                self.m[i] = self.Deformation_Num.M_trans[i][i]
                self.k[i] = self.Deformation_Num.K_trans[i][i]
                self.d[i] = 2 * self.xi * np.sqrt(self.k[i] * self.m[i])

        elif self.boundary_condition == "Clamped-Hinged":
            for i in range(0, self.n, 1):
                if i == 0:
                    self.Freq[i] = i  # Static movement ? Check, if necessary
                else:
                    self.Freq[i] = (
                        (self.lambda_clamped_hinged[i - 1]) ** 2
                        / (2 * np.pi * self.l**2)
                    ) * np.sqrt(self.E * self.I / self.mue)
                print(self.Freq[i])

                self.Omega[i] = 2 * np.pi * self.Freq[i]
                if i == 0:
                    self.T[i] = 1e9
                else:
                    self.T[i] = 1 / self.Freq[i]

            self.m = np.zeros(self.n)  # Vektor der modalen Massen
            self.k = np.zeros(self.n)  # Vektor der modalen Steifigkeiten
            self.d = np.zeros(self.n)  # Vektor der modalen Dämpferkonstanten

            for i in range(self.n):
                self.m[i] = self.J1_clamped_hinged[i] * self.mue * self.l
                self.k[i] = self.Omega[i] ** 2 * self.m[i]
                self.d[i] = 2 * self.xi * np.sqrt(self.k[i] * self.m[i])

                print(self.m)

        elif self.boundary_condition == "Clamped-Clamped":
            for i in range(0, self.n, 1):
                if i == 0:
                    self.Freq[i] = i  # Static movement due to the
                else:
                    self.Freq[i] = (
                        (self.lambda_clamped_clamped[i - 1]) ** 2
                        / (2 * np.pi * self.l**2)
                    ) * np.sqrt(self.E * self.I / self.mue)
                print(self.Freq[i])

                self.Omega[i] = 2 * np.pi * self.Freq[i]
                if i == 0:
                    self.T[i] = 1e9
                else:
                    self.T[i] = 1 / self.Freq[i]

            self.m = np.zeros(self.n)  # Vektor der modalen Massen
            self.k = np.zeros(self.n)  # Vektor der modalen Steifigkeiten
            self.d = np.zeros(self.n)  # Vektor der modalen Dämpferkonstanten

            for i in range(self.n):
                self.m[i] = self.J1_clamped_clamped[i] * self.mue * self.l
                self.k[i] = self.Omega[i] ** 2 * self.m[i]
                self.d[i] = 2 * self.xi * np.sqrt(self.k[i] * self.m[i])

                print(self.m)

        elif self.boundary_condition == "Cantilever":
            for i in range(0, self.n, 1):
                if i == 0:
                    self.Freq[i] = i  # Static movement due to the
                else:
                    self.Freq[i] = (
                        (self.lambda_cantilever[i - 1]) ** 2 / (2 * np.pi * self.l**2)
                    ) * np.sqrt(self.E * self.I / self.mue)
                print(self.Freq[i])

                self.Omega[i] = 2 * np.pi * self.Freq[i]
                if i == 0:
                    self.T[i] = 1e9
                else:
                    self.T[i] = 1 / self.Freq[i]

            self.m = np.zeros(self.n)  # Vektor der modalen Massen
            self.k = np.zeros(self.n)  # Vektor der modalen Steifigkeiten
            self.d = np.zeros(self.n)  # Vektor der modalen Dämpferkonstanten

            for i in range(self.n):
                self.m[i] = self.J1_cantilever[i] * self.mue * self.l
                self.k[i] = self.Omega[i] ** 2 * self.m[i]
                self.d[i] = 2 * self.xi * np.sqrt(self.k[i] * self.m[i])

                print(self.m)

    def hinged_hinged(self, x_load, n_eigen):
        if n_eigen == 0:
            return np.sin(x_load * 0 / self.l)
        else:
            return np.sin(x_load * self.lambda_hinged_hinged[n_eigen - 1] / self.l)

    def hinged_hinged_numeric(self, x_load, n_eigen):
        interpolator = interp1d(
            self.Deformation_Num.len_plotting,
            self.Deformation_Num.eigenmodes_matrix[:, n_eigen],
            kind="linear",
            fill_value=0,
        )
        interpolated_value = interpolator(x_load)
        return interpolated_value

    def clamped_hinged(self, x_load, n_eigen):
        if n_eigen == 0:
            value = 0
        else:
            value = (
                np.sin(self.lambda_clamped_hinged[n_eigen - 1] * x_load / self.l)
                - np.sinh(self.lambda_clamped_hinged[n_eigen - 1] * x_load / self.l)
                + self.a_lambda_clamped_hinged[n_eigen - 1]
                * (
                    np.cosh(self.lambda_clamped_hinged[n_eigen - 1] * x_load / self.l)
                    - np.cos(self.lambda_clamped_hinged[n_eigen - 1] * x_load / self.l)
                )
            )
        return value

    def clamped_clamped(self, x_load, n_eigen):
        if n_eigen == 0:
            value = 0
        else:
            value = (
                np.sin(self.lambda_clamped_clamped[n_eigen - 1] * x_load / self.l)
                - np.sinh(self.lambda_clamped_clamped[n_eigen - 1] * x_load / self.l)
                + self.a_lambda_clamped_clamped[n_eigen - 1]
                * (
                    np.cosh(self.lambda_clamped_clamped[n_eigen - 1] * x_load / self.l)
                    - np.cos(self.lambda_clamped_clamped[n_eigen - 1] * x_load / self.l)
                )
            )
        return value

    def cantilever(self, x_load, n_eigen):
        if n_eigen == 0:
            value = 0
        else:
            value = (
                np.sin(self.lambda_cantilever[n_eigen - 1] * x_load / self.l)
                - np.sinh(self.lambda_cantilever[n_eigen - 1] * x_load / self.l)
                + self.a_lambda_cantilever[n_eigen - 1]
                * (
                    np.cosh(self.lambda_cantilever[n_eigen - 1] * x_load / self.l)
                    - np.cos(self.lambda_cantilever[n_eigen - 1] * x_load / self.l)
                )
            )
        return value

    def hingedhinged_twospan(self,x_load,n_eigen):
        if n_eigen == 0:
            return 0
        else:
            if (n_eigen %2 == 1):
                lambda_n = self.lambda_hinged_hinged[n_eigen-1]
                return np.sin(x_load * lambda_n / self.l)
            else:
                lambda_n = self.lambda_clamped_hinged[n_eigen-1]
                return np.sin(x_load *  lambda_n / self.l)

    def generalized_load_function(self):
        self.Gen_K = np.zeros(
            (self.n, self.nt)
        )  # rows -> Eigenmode 0,...,n , nt = number of the time steps
        if self.loading == "train":
            for u in range(self.n):  # Number of eigenmode
                for i in range(self.nt):    # Number of timesteps
                    for j in range(len(self.x_k)):
                        if self.boundary_condition == "Hinged-Hinged":
                            self.Gen_K[u][i] += self.F_Mat[j][i] * self.hinged_hinged(
                                -self.x_k[j] + self.v_zug * self.t[i], u
                            )
                        elif self.boundary_condition == "Hinged-Hinged-Numeric":
                            try:
                                self.Gen_K[u][i] += self.F_Mat[j][
                                    i
                                ] * self.hinged_hinged_numeric(
                                    -self.x_k[j] + self.v_zug * self.t[i], u
                                )
                            except:
                                self.Gen_K[u][i] += 0
                        elif self.boundary_condition == "Clamped-Hinged":
                            self.Gen_K[u][i] += self.F_Mat[j][i] * self.clamped_hinged(
                                -self.x_k[j] + self.v_zug * self.t[i], u
                            )
                        elif self.boundary_condition == "Clamped-Hinged-Numeric":
                            self.Gen_K[u][i] += self.F_Mat[j][i] * self.clamped_hinged(
                                -self.x_k[j] + self.v_zug * self.t[i], u
                            )
                        elif self.boundary_condition == "Clamped-Clamped":
                            self.Gen_K[u][i] += self.F_Mat[j][i] * self.clamped_clamped(
                                -self.x_k[j] + self.v_zug * self.t[i], u
                            )
                        elif self.boundary_condition == "Cantilever":
                            self.Gen_K[u][i] += self.F_Mat[j][i] * self.cantilever(
                                -self.x_k[j] + self.v_zug * self.t[i], u
                            )

        elif self.loading == "harmonic_single":
            for u in range(self.n):
                for i in range(self.nt):
                    if self.boundary_condition == "Hinged-Hinged":
                        self.Gen_K[u][i] = self.F_Mat[i] * self.hinged_hinged(
                            self.x0, u
                        )
                    elif self.boundary_condition == "Hinged-Hinged-Numeric":
                        self.Gen_K[u][i] = self.F_Mat[i] * self.hinged_hinged_numeric(
                            self.x0, u
                        )
                    elif self.boundary_condition == "Clamped-Hinged":
                        self.Gen_K[u][i] = self.F_Mat[i] * self.clamped_hinged(
                            self.x0, u
                        )
                    elif self.boundary_condition == "Clamped-Clamped":
                        self.Gen_K[u][i] = self.F_Mat[i] * self.clamped_clamped(
                            self.x0, u
                        )
                    elif self.boundary_condition == "Cantilever":
                        self.Gen_K[u][i] = self.F_Mat[i] * self.cantilever(self.x0, u)

        elif self.loading == "pedestrian":
            for u in range(self.n):
                for i in range(self.nt):
                    if self.boundary_condition == "Hinged-Hinged":
                        self.Gen_K[u][i] = self.F_Mat[i] * self.hinged_hinged(
                            self.v_pedestrian * self.t[i], u
                        )
                    elif self.boundary_condition == "Hinged-Hinged-Numeric":
                        try:
                            self.Gen_K[u][i] = self.F_Mat[
                                i
                            ] * self.hinged_hinged_numeric(
                                self.v_pedestrian * self.t[i], u
                            )
                        except:
                            self.Gen_K[u][i] = 0
                    elif self.boundary_condition == "Clamped-Hinged":
                        self.Gen_K[u][i] = self.F_Mat[i] * self.clamped_hinged(
                            self.v_pedestrian * self.t[i], u
                        )
                    elif self.boundary_condition == "Clamped-Clamped":
                        self.Gen_K[u][i] = self.F_Mat[i] * self.clamped_clamped(
                            self.v_pedestrian * self.t[i], u
                        )
                    elif self.boundary_condition == "Cantilever":
                        self.Gen_K[u][i] = self.F_Mat[i] * self.cantilever(
                            self.v_pedestrian * self.t[i], u
                        )

    def beta_newmark(self):
        # Berechnung der Schwingungsantwort mittels Newmark-Verfahren

        # Berechnungsvorschrift
        self.ita_y = np.zeros((self.n, len(self.t)))
        self.ita_v = np.zeros((self.n, len(self.t)))
        self.ita_a = np.zeros((self.n, len(self.t)))

        for j in range(self.n):
            for i in range(1, len(self.t)):
                self.a_h = (
                    ((1 / self.beta) * self.m[j])
                    + (self.alpha / self.beta) * self.d[j] * self.dt
                    + self.k[j] * self.dt**2
                )
                self.b_h = (
                    (
                        (1 / self.beta) * self.m[j]
                        + (self.alpha / self.beta) * self.d[j] * self.dt
                    )
                    * self.ita_y[j][i - 1]
                    + (
                        (1 / self.beta) * self.m[j]
                        + (self.alpha / self.beta - 1) * self.d[j] * self.dt
                    )
                    * self.dt
                    * self.ita_v[j][i - 1]
                    + (
                        (1 / (2 * self.beta) - 1) * self.m[j]
                        + (self.alpha / (2 * self.beta) - 1) * self.d[j] * self.dt
                    )
                    * self.dt**2
                    * self.ita_a[j][i - 1]
                    + self.Gen_K[j][i] * self.dt**2
                )
                self.ita_y[j][i] = self.a_h ** (-1) * self.b_h
                self.ita_v[j][i] = (
                    (self.alpha / (self.beta * self.dt))
                    * (self.ita_y[j][i] - self.ita_y[j][i - 1])
                    - ((self.alpha / self.beta) - 1) * self.ita_v[j][i - 1]
                    - (self.alpha / (2 * self.beta) - 1)
                    * self.dt
                    * self.ita_a[j][i - 1]
                )
                self.ita_a[j][i] = (
                    (1 / (self.beta * self.dt**2))
                    * (self.ita_y[j][i] - self.ita_y[j][i - 1])
                    - 1 / (self.beta * self.dt) * self.ita_v[j][i - 1]
                    - (1 / (2 * self.beta) - 1) * self.ita_a[j][i - 1]
                )

        # Überlagerung aller Eigenformen
        self.y = np.zeros(len(self.t))  # Vektor der Gesamtverschiebung
        self.v = np.zeros(len(self.t))  # Vektor der Gesamtgeschwindigkeit
        self.a = np.zeros(len(self.t))  # Vektor der Gesamtbeschleunigung

        for j in range(self.n):
            for i in range(len(self.t)):
                self.y_tot_h = self.phi_a[j] * self.ita_y[j][i]
                self.y[i] += self.y_tot_h
                self.v_tot_h = self.phi_a[j] * self.ita_v[j][i]
                self.v[i] += self.v_tot_h
                self.a_tot_h = self.phi_a[j] * self.ita_a[j][i]
                self.a[i] += self.a_tot_h

    def extrema(self):
        # Extremwerte
        self.ymax = max(self.y)
        self.ymin = min(self.y)
        self.vmax = max(self.v)
        self.vmin = min(self.v)
        self.amax = max(self.a)
        self.amin = min(self.a)

    def fourier_transformation(self):
        print("Fourier-Transform")

        self.delta_t = self.t[2] - self.t[1]  # Voraussetzung: Äquidistante Zeitschritte
        self.Tges = (
            len(self.t) * self.delta_t
        )  # Gesamtzeit: Letztes Element des Arrays - Erstes Element des Arrays

        self.srate = self.delta_t ** (-1)
        time = self.t
        npnts = len(time)

        # prepare the Fourier transform
        fourTime = np.array(range(npnts)) / npnts
        fCoefs = np.zeros((len(self.y)), dtype=complex)

        for fi in range(npnts):
            # create complex sine wave
            csw = np.exp(-1j * 2 * np.pi * fi * fourTime)
            # compute dot product between sine wave and signal
            # these are called the Fourier coefficients
            fCoefs[fi] = np.sum(np.multiply(self.y, csw)) / npnts

        # Fourier spectrum
        signalX = fCoefs

        self.hz = np.linspace(0, self.srate, npnts)

        print(len(self.hz))

        # amplitude
        self.ampl = np.abs(signalX[0 : len(self.hz)])

        for i in range(0, len(self.hz)):
            if i == 0:
                self.ampl[i] = self.ampl[i]
            else:
                self.ampl[i] = 2 * self.ampl[i]

        plt.stem(self.hz, self.ampl)
        plt.xlim(0, 30)
        plt.xlabel("Frequency (Hz)")
        plt.ylabel("Amplitude (a.u.)")
        plt.show()



