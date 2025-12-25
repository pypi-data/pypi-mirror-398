import numpy as np
from tabulate import tabulate
import matplotlib
from scipy.linalg import eig

# matplotlib.use('Agg')  # Setzt das Agg Backend, das keine Fenster öffnet
import matplotlib.pyplot as plt

import pandas as pd
from Querschnittswerte import CrossSectionThin
import sys

from Biegedrillknicken_Trigeometry import Biegedrillknicken


class StabRitz:
    def __init__(
        self,
        l_x,
        x0,
        x1,
        p,
        x0F,
        F,
        E,
        I,
        reihen=5,
        load_input="file",
        Ansatz="Polynom",
        Knoten="Querschnittseingabe/Knoten_2.csv",
        Elemente="Querschnittseingabe/Elemente_2.csv",
        _c_bett_z=0,
    ):
        """

        Args:
            l_x (_type_): Spannweite des Trägers \n
            x0 (_type_): Lasteinleitungsbegin Linienlast \n
            x1 (_type_): Lasteinleitungsende Linienlast \n
            p (_type_): Linienlast in [MN/m] \n
            x0F (_type_): Lasteinleitungsbegin Einzellast \n
            F (_type_): Einzellast in [MN] \n
            E (_type_): E-Modul in [MN/m**2] \n
            I (_type_): Flächenträgheitsmoment in [m**4] \n
            reihen (int, optional): Anzahl der zu berücksichtigenden Reihen. Entspricht der Größe der \n
            Matrix. Defaultwert ist 5.
        """
        self.l_x = l_x
        self.list_lx = np.linspace(1e-5, self.l_x, 1000)

        if Ansatz == "Fourier":
            self.reihen = reihen
        else:
            self.BC = pd.DataFrame(pd.read_csv("Federeingabe/Federeingabe.csv"))

            self.c_bett_z = _c_bett_z

            # Estimate the required precision
            self.precision = 1e-2
            for i in self.BC["xi[-]"]:
                i_prec = round(i * 1000, 0)
                i_mod = int(i_prec % 10)

                if i_mod == 0:
                    self.precision = 0.5e-1
                else:
                    self.precision = 0.5e-1

            self.reihen = int(1 / self.precision)

        self.K = np.zeros((self.reihen, self.reihen))
        self.P = np.zeros(self.reihen)

        self.x0 = x0
        self.x1 = x1
        self.p = p

        self.x0F = x0F
        self.F = F

        self.load_input = load_input
        # Einlesen der Querschnittswerte über Python-Klasse
        self.Querschnitt = CrossSectionThin(210000, 0.30, Knoten, Elemente)
        self.Querschnitt.read_node_input()
        self.Querschnitt.CalculateElementStiffness()
        self.Querschnitt.Calculate_GesMat()
        self.Querschnitt.SolverTorsion()
        self.Querschnitt.CalculateAyzw()
        self.Querschnitt.Update_SMP()
        self.Querschnitt.Calculate_IwIt()
        self.Querschnitt.Calculate_WoWu()
        self.Querschnitt.Calculate_ShearStress_Vz()
        self.Querschnitt.Calculate_imryrzrw()
        self.I = self.Querschnitt.I_yy
        self.EI = self.Querschnitt.E * self.I

        self.CrossSection = "Konstant"

        self.Ansatz = Ansatz

    def function_I(self, x):
        if self.CrossSection == "Linear":
            if x < self.l_x / 2:
                return self.I + x / (self.l_x) * 0.5 * 0.01
        else:
            return self.I

    def function(self, x, m):
        return np.sin(m * np.pi * x / self.l_x)

    def function_x(self, x, m):
        return np.cos(m * np.pi * x / self.l_x) * m * np.pi / self.l_x

    def function_xx(self, x, m):
        return np.sin(m * np.pi * x / self.l_x) * (m * np.pi / self.l_x) ** 2 * (-1)

    def function_xxx(self, x, m):
        return np.sin(m * np.pi * x / self.l_x) * (m * np.pi / self.l_x) ** 3 * (-1)

    def function_1_FE(self, x, le):
        return 1 - 3 * x**2 / le**2 + 2 * x**3 / le**3

    def function_1_FE_x(self, x, le):
        return -6 * x / le**2 + 6 * x**2 / le**3

    def function_1_FE_xx(self, x, le):
        return -6 / le**2 + 12 * x / le**3

    def function_1_FE_xxx(self, x, le):
        return 12 / le**3

    def function_2_FE(self, x, le):
        return x - 2 * x**2 / le + x**3 / le**2

    def function_2_FE_x(self, x, le):
        return 1 - 4 * x / le + 3 * x**2 / le**2

    def function_2_FE_xx(self, x, le):
        return -4 / le + 6 * x / le**2

    def function_2_FE_xxx(self, x, le):
        return 6 / le**2

    def function_3_FE(self, x, le):
        return 3 * x**2 / le**2 - 2 * x**3 / le**3

    def function_3_FE_x(self, x, le):
        return 6 * x / le**2 - 6 * x**2 / le**3

    def function_3_FE_xx(self, x, le):
        return 6 / le**2 - 12 * x / le**3

    def function_3_FE_xxx(self, x, le):
        return -12 / le**3

    def function_4_FE(self, x, le):
        return -(x**2) / le + x**3 / le**2

    def function_4_FE_x(self, x, le):
        return -2 * x / le + 3 * x**2 / le**2

    def function_4_FE_xx(self, x, le):
        return -2 / le + 6 * x / le**2

    def function_4_FE_xxx(self, x, le):
        return 6 / le**2

    def function_FE_load(self, x, le, q):
        return (
            q
            * le**4
            / (24 * self.EI)
            * ((x / le) ** 2 - 2 * (x / le) ** 3 + (x / le) ** 4)
        )

    def Calculate_All(self):
        self.SteMa()
        self.Lasteingabe()
        self.LoadMa()
        self.BoundaryConditions()
        self.Solver()
        self.CalculateElementSolutions()
        self.Verschiebungen(0.5)
        self.Schnittkraefte()

    def Calculate_All_II(self):
        self.SteMa()
        self.Lasteingabe()
        self.LoadMa()
        self.BoundaryConditions()
        self.Solver()
        self.CalculateElementSolutions()
        self.Verschiebungen(0.5)
        self.Schnittkraefte()
        self.Stabknicken_Element_Mat()
        self.CalculateDeflections_II_Order()

    def CalculatePrintALL(self):
        self.SteMa()
        self.Lasteingabe()
        self.LoadMa()
        self.BoundaryConditions()
        self.Solver()
        self.CalculateElementSolutions()
        self.Verschiebungen(0.5)
        self.Schnittkraefte()
        self.Verschiebungslinie()
        self.Momentenlinie()
        self.Querkraftlinie()

    def CalculatePrint_All_II(self):
        self.SteMa()
        self.Lasteingabe()
        self.LoadMa()
        self.BoundaryConditions()
        self.Solver()
        self.CalculateElementSolutions()
        self.Verschiebungen(0.5)
        self.Schnittkraefte()
        self.Stabknicken_Element_Mat()
        self.CalculateDeflections_II_Order()
        self.PlotDeflections_II_Order()

    def SteMa(self):
        if self.Ansatz == "Fourier":
            for m in range(1, self.reihen + 1, 1):
                for n in range(1, self.reihen + 1, 1):
                    self.K[m - 1][n - 1] = self.EI * np.trapz(
                        self.function_xx(self.list_lx, m)
                        * self.function_xx(self.list_lx, n),
                        self.list_lx,
                    )

            self.K = np.where(self.K < 1e-9, 0, self.K)

        elif self.Ansatz == "FE":
            ne = self.reihen
            le = self.l_x / ne

            self.list_lxle = np.linspace(0, le, 1000)

            self.K = np.zeros(((ne + 1) * 2, (ne + 1) * 2))
            self.K_el = np.zeros((4, 4))  # Elementsteifigkeitsmatrix
            self.K_el_bet = np.zeros((4, 4))  # Elementsteifigkeitsmatrix

            self.K_el_store = np.zeros((ne, 4, 4))

            # Start-Wert für die Index-Arrays
            start_werte = np.arange(
                0, 2 * ne, 2
            )  # Erstellt einen Array von Startwerten

            # Erstelle den Index-Vektor
            self.index_vector = np.array(
                [np.arange(start, start + 4) for start in start_werte]
            )

            for i in range(0, ne, 1):
                # Row = 0, Col = ...
                self.K_el[0][0] = self.EI * np.trapz(
                    self.function_1_FE_xx(self.list_lxle, le)
                    * self.function_1_FE_xx(self.list_lxle, le),
                    self.list_lxle,
                )

                self.K_el[0][1] = self.EI * np.trapz(
                    self.function_1_FE_xx(self.list_lxle, le)
                    * self.function_2_FE_xx(self.list_lxle, le),
                    self.list_lxle,
                )

                self.K_el[0][2] = self.EI * np.trapz(
                    self.function_1_FE_xx(self.list_lxle, le)
                    * self.function_3_FE_xx(self.list_lxle, le),
                    self.list_lxle,
                )

                self.K_el[0][3] = self.EI * np.trapz(
                    self.function_1_FE_xx(self.list_lxle, le)
                    * self.function_4_FE_xx(self.list_lxle, le),
                    self.list_lxle,
                )

                # Row = 1, Col = ...

                self.K_el[1][0] = self.EI * np.trapz(
                    self.function_2_FE_xx(self.list_lxle, le)
                    * self.function_1_FE_xx(self.list_lxle, le),
                    self.list_lxle,
                )

                self.K_el[1][1] = self.EI * np.trapz(
                    self.function_2_FE_xx(self.list_lxle, le)
                    * self.function_2_FE_xx(self.list_lxle, le),
                    self.list_lxle,
                )

                self.K_el[1][2] = self.EI * np.trapz(
                    self.function_2_FE_xx(self.list_lxle, le)
                    * self.function_3_FE_xx(self.list_lxle, le),
                    self.list_lxle,
                )

                self.K_el[1][3] = self.EI * np.trapz(
                    self.function_2_FE_xx(self.list_lxle, le)
                    * self.function_4_FE_xx(self.list_lxle, le),
                    self.list_lxle,
                )

                # Row = 2, Col = ...

                self.K_el[2][0] = self.EI * np.trapz(
                    self.function_3_FE_xx(self.list_lxle, le)
                    * self.function_1_FE_xx(self.list_lxle, le),
                    self.list_lxle,
                )

                self.K_el[2][1] = self.EI * np.trapz(
                    self.function_3_FE_xx(self.list_lxle, le)
                    * self.function_2_FE_xx(self.list_lxle, le),
                    self.list_lxle,
                )

                self.K_el[2][2] = self.EI * np.trapz(
                    self.function_3_FE_xx(self.list_lxle, le)
                    * self.function_3_FE_xx(self.list_lxle, le),
                    self.list_lxle,
                )

                self.K_el[2][3] = self.EI * np.trapz(
                    self.function_3_FE_xx(self.list_lxle, le)
                    * self.function_4_FE_xx(self.list_lxle, le),
                    self.list_lxle,
                )

                # Row = 3,  Col = ...

                self.K_el[3][0] = self.EI * np.trapz(
                    self.function_4_FE_xx(self.list_lxle, le)
                    * self.function_1_FE_xx(self.list_lxle, le),
                    self.list_lxle,
                )

                self.K_el[3][1] = self.EI * np.trapz(
                    self.function_4_FE_xx(self.list_lxle, le)
                    * self.function_2_FE_xx(self.list_lxle, le),
                    self.list_lxle,
                )

                self.K_el[3][2] = self.EI * np.trapz(
                    self.function_4_FE_xx(self.list_lxle, le)
                    * self.function_3_FE_xx(self.list_lxle, le),
                    self.list_lxle,
                )

                self.K_el[3][3] = self.EI * np.trapz(
                    self.function_4_FE_xx(self.list_lxle, le)
                    * self.function_4_FE_xx(self.list_lxle, le),
                    self.list_lxle,
                )
                # Bettung

                FE_funcs = [
                    self.function_1_FE,
                    self.function_2_FE,
                    self.function_3_FE,
                    self.function_4_FE,
                ]

                FE_funcs = [
                    self.function_1_FE,
                    self.function_2_FE,
                    self.function_3_FE,
                    self.function_4_FE,
                ]
                
                # 4) Integral über N_i * N_j
                for a, Na in enumerate(FE_funcs):
                    for b, Nb in enumerate(FE_funcs):
                        self.K_el_bet[a, b] = self.c_bett_z * np.trapz(
                            Na(self.list_lxle, le) * Nb(self.list_lxle, le),
                            self.list_lxle,
                        )

                # Steifigkeitsmatrix inklusive Bettung
                self.K_el_store[i, :, :] = (
                    self.K_el + self.K_el_bet
                )  # Speichert die 2D Arrays in das 3D Array ab

            for n in range(0, ne, 1):
                for row in range(0, 4, 1):
                    for col in range(0, 4, 1):
                        self.K[self.index_vector[n][row]][
                            self.index_vector[n][col]
                        ] += self.K_el_store[n][row][col]

    def Lasteingabe(self):
        self.Einzellasten = False
        self.Linienlasten = False
        if self.load_input == "console":
            # Implementieren Sie hier die Konsoleneingabe
            pass
        else:
            self.Einzellasten = pd.DataFrame(
                pd.read_csv("Lasteingabe_Text/Einzellasten.csv")
            )
            self.Linienlasten = pd.DataFrame(
                pd.read_csv("Lasteingabe_Text/Linienlasten.csv")
            )

    def LoadMa(self):
        if self.Ansatz == "Fourier":
            for m in range(1, self.reihen + 1, 1):
                if self.Ansatz == "Fourier":
                    self.P[m - 1] = (
                        np.trapz(self.function(self.list_lx, m), self.list_lx) * self.p
                    )

        elif self.Ansatz == "FE":
            ne = self.reihen
            self.P = np.zeros(2 * (ne + 1))
            le = self.l_x / ne

            # Element load-vector (Single Load from File)
            for i in self.Einzellasten["x0F in [m]"]:
                num_el = int(i / le + 1)
                x_el = (i / le - num_el + 1) * le

                load_index = self.index_vector[num_el - 1][0]

                self.F = self.Einzellasten["F in [MN]"][0]

                self.P[load_index + 0] += self.F * self.function_1_FE(x_el, le)
                self.P[load_index + 1] += self.F * self.function_2_FE(x_el, le)
                self.P[load_index + 2] += self.F * self.function_3_FE(x_el, le)
                self.P[load_index + 3] += self.F * self.function_4_FE(x_el, le)

            # Element load-vector (Constant line loads from File)
            for i in range(0, len(self.Linienlasten["x0"]), 1):
                num_el_0 = int(
                    self.Linienlasten["x0"][i] / le
                )  # Anfangselement der Linienlast
                x_el_0 = self.Linienlasten["x0"][
                    i
                ]  # Lokale Startposition im Anfangselement
                num_el_1 = int(np.ceil(self.Linienlasten["x1"][i] / le))

                x_el_1 = (
                    self.Linienlasten["x1"][i] - (num_el_1 - 1) * le
                )  # Lokale Endposition im Endelement

                # Check, if the load is smaller than the beam itself

                if self.Linienlasten["x1"][i] <= self.l_x:
                    print("HERE 1")
                else:
                    x_el_1 = le
                    num_el_1 = int(np.ceil(self.l_x / le))

                q = self.Linienlasten["q"][i]

                load_integration = np.zeros((num_el_1 - num_el_0, 10))
                for j in range(num_el_0, num_el_1):
                    local_start = (
                        x_el_0 if j == num_el_0 else 0
                    )  # Start bei x_el_0 für das erste betroffene Element, sonst bei le*j
                    local_end = (
                        x_el_1 if j == num_el_1 - 1 else le
                    )  # Ende bei x_el_1 für das letzte betroffene Element, sonst bei le
                    idx = j - num_el_0  # Korrigierter Index für load_integration
                    load_integration[idx][:] = np.linspace(local_start, local_end, 10)

                    load_index = self.index_vector[j][0]
                    local_le = local_end - local_start

                    self.P[load_index + 0] += q * np.trapz(
                        self.function_1_FE(load_integration[idx][:], local_le),
                        load_integration[idx][:],
                    )

                    self.P[load_index + 1] += q * np.trapz(
                        self.function_2_FE(load_integration[idx][:], local_le),
                        load_integration[idx][:],
                    )
                    self.P[load_index + 2] += q * np.trapz(
                        self.function_3_FE(load_integration[idx][:], local_le),
                        load_integration[idx][:],
                    )

                    self.P[load_index + 3] += q * np.trapz(
                        self.function_4_FE(load_integration[idx][:], local_le),
                        load_integration[idx][:],
                    )

    def BoundaryConditions(self):
        self.BC = pd.DataFrame(pd.read_csv("Federeingabe/Federeingabe.csv"))

        self.v = []
        self.v_cp = []
        self.phi = []
        self.phi_cp = []

        len_K = len(self.K)

        for j in self.BC["No"]:
            i = self.BC["xi[-]"][self.BC["No"] == j].iloc[0]
            BC_LOC = self.BC["DOF"][self.BC["No"] == j].iloc[0]
            cp = self.BC["cf in [MN/m]/[MNm/rad]"][self.BC["No"] == j].iloc[0]

            if BC_LOC == "v":
                self.v.append(
                    i * (len_K - 2)
                )  # Element which displacement is constrained
                self.v_cp.append(cp)
            elif BC_LOC == "phi":
                self.phi.append(i * (len_K - 2) + 1)
                self.phi_cp.append(cp)
        for i in self.v:
            node = int(i)
            self.K[node][node] += cp
        for j in self.phi:
            node = int(j)
            self.K[node][node] += cp

    def Solver(self):
        if self.Ansatz == "Fourier":
            self.x_reduced = np.linalg.solve(self.K, self.P)
            self.x_disp_red = self.x_reduced[::2]
        if self.Ansatz == "FE":
            self.x_reduced = np.linalg.solve(self.K, self.P)
            self.x_disp_red = self.x_reduced[::2]

    def CalculateElementSolutions(self):
        if self.Ansatz == "FE":
            ne = self.reihen
            self.x_disp_e = np.zeros((ne, 4))

            for i in range(0, ne, 1):
                for j in range(0, 4, 1):
                    self.x_disp_e[i][j] = self.x_reduced[j + i * 2]
        else:
            pass

    def Verschiebungen(self, x_cal):
        if self.Ansatz == "Fourier":
            self.x_disp = 0
            for m in range(1, self.reihen + 1, 1):
                self.x_disp += self.x_reduced[m - 1] * self.function(x_cal, m)
            return self.x_disp

        elif self.Ansatz == "FE":
            ne = self.reihen
            le = self.l_x / ne
            self.uz_el_store = np.zeros((ne, 2))
            self.phi_el_store = np.zeros((ne, 2))
            self.x_el_store = np.zeros((ne, 2))

            for i in range(0, ne, 1):
                self.uz_el_store[i] = self.x_disp_e[i][
                    ::2
                ]  # Elementweise Angabe der Knotenverschiebungen
                self.phi_el_store[i] = self.x_disp_e[i][
                    1::2
                ]  # Elementweise Angabe der Knotenverdrehungen

                self.x_el_store[i][0] = i * le
                self.x_el_store[i][1] = (i + 1) * le

    def Schnittkraefte(self, x_cal=0.5):
        """_summary_

        Args:
            x_cal (float, optional):    Auswertepunkt bei einem Fourieransatz. \n
                                        Defaultwert ist 0.5. Nicht notwendig, wenn die Berechnung \n
                                        mit FE-Ansatzfunktionen durchgeführt wird. \n

        Returns:
                _type_:     float-Value für Ansatz von Fourierreihen für die Annäherung an die Durchbiegung. \n
                            Kein Rückgabewert, wenn FE-Ansatz nach dem Ritzverfahren angewandt wird.
        """
        if self.Ansatz == "Fourier":
            self.m_y = 0
            for m in range(1, self.reihen, 1):
                self.m_y += (
                    self.x_reduced[m - 1] * self.function_xx(x_cal, m) * self.EI * (-1)
                )

            return self.m_y
        elif self.Ansatz == "FE":
            ne = self.reihen
            le = self.l_x / ne
            self.m_el_store = np.zeros((ne, 2))
            self.v_el_store = np.zeros((ne, 2))

            for i in range(0, ne, 1):
                self.inner_forces_el_store = np.matmul(
                    self.K_el_store[i], self.x_disp_e[i]
                )

                self.inner_forces_el_store[
                    0
                ] *= (
                    -1
                )  # Linkes Schnittufer der Querkraft , Umgedrehtes Vorzeichen aus FE-Konvention
                self.inner_forces_el_store[
                    3
                ] *= (
                    -1
                )  # Rechtes Schnittufer , Umgedrehtes Vorzeichen aus FE-Konvention
                self.m_el_store[i] = self.inner_forces_el_store[1::2]
                self.v_el_store[i] = self.inner_forces_el_store[::2]

    def Verschiebungslinie(self, interpolation=2):
        """
        Funktion zur Berechnung der Verschiebungen in den Elementen \n
        Aus der vorherigen Verschiebungsfunktion sind für die \n
        Polynomansätze die Verschiebungen an den Knoten bekannt. \n
        Über die Verschiebungen und die Kenntnis über die Linienbelastungen \n
        auf den Einzelelementen können die Elementschnittgrößen ermittelt werden \n
        Dies erfolgt über die Rückrechnung aus den Ansatzfunktionen \n

        """

        if self.Ansatz == "Fourier":
            self.v_list = np.zeros(len(self.list_lx))

            for i in range(0, len(self.list_lx), 1):
                self.v_list[i] = self.Verschiebungen(self.list_lx[i])
        else:
            ne = self.reihen
            n_inter = interpolation
            self.x_element_inter = np.zeros(
                (ne, n_inter)
            )  # Interpolierte Längenliste für die Elemente
            self.uz_element_inter = np.zeros((ne, n_inter))

            for i in range(0, ne, 1):
                xA = self.x_el_store[i][0]
                xB = self.x_el_store[i][1]
                le = self.l_x / ne
                dle = le / (n_inter - 1)

                wA = self.uz_el_store[i][0]
                PhiA = self.phi_el_store[i][0]
                wB = self.uz_el_store[i][1]
                PhiB = self.phi_el_store[i][1]

                for j in range(0, n_inter, 1):
                    x_loc = j * dle

                    f_1 = self.function_1_FE(x_loc, le)
                    f_2 = self.function_2_FE(x_loc, le)
                    f_3 = self.function_3_FE(x_loc, le)
                    f_4 = self.function_4_FE(x_loc, le)

                    f_load = self.function_FE_load(
                        x_loc, le, 0
                    )  # Load function not implemented
                    # Steps: Calculate q(x_loc) for each element necessary

                    self.x_element_inter[i][j] = x_loc
                    self.uz_element_inter[i][j] = (
                        f_1 * wA + f_2 * PhiA + f_3 * wB + f_4 * PhiB + f_load
                    )

                self.x_element_inter[i] += i * le

                plt.plot(self.x_element_inter[i], self.uz_element_inter[i])

            plt.show(block=False)
            plt.pause(0.1)
            plt.close()

    def Momentenlinie(self, interpolation=2):
        if self.Ansatz == "Fourier":
            self.m = np.zeros(len(self.list_lx))
            for i in range(0, len(self.list_lx), 1):
                self.m[i] = self.Schnittkraefte(self.list_lx[i])
        else:
            ne = self.reihen
            n_inter = interpolation
            self.x_element_inter = np.zeros(
                (ne, n_inter)
            )  # Interpolierte Längenliste für die Elemente
            self.m_element_inter = np.zeros((ne, n_inter))

            for i in range(0, ne, 1):
                xA = self.x_el_store[i][0]
                xB = self.x_el_store[i][1]
                le = self.l_x / ne
                dle = le / (n_inter - 1)

                wA = self.uz_el_store[i][0]
                PhiA = self.phi_el_store[i][0]
                wB = self.uz_el_store[i][1]
                PhiB = self.phi_el_store[i][1]

                for j in range(0, n_inter, 1):
                    x_loc = j * dle

                    f_1 = self.function_1_FE_xx(x_loc, le)
                    f_2 = self.function_2_FE_xx(x_loc, le)
                    f_3 = self.function_3_FE_xx(x_loc, le)
                    f_4 = self.function_4_FE_xx(x_loc, le)

                    self.x_element_inter[i][j] = x_loc
                    self.m_element_inter[i][j] = (
                        f_1 * wA + f_2 * PhiA + f_3 * wB + f_4 * PhiB
                    ) * (-self.EI)

                self.x_element_inter[i] += i * le

                plt.plot(self.x_element_inter[i], self.m_element_inter[i])

            # print("Max Bending Moment ", self.m_element_inter.max())
            # print("Min Bending Moment ", self.m_element_inter.min())
            plt.show(block=False)
            plt.pause(0.1)
            plt.close()

    def Querkraftlinie(self, interpolation=2):
        if self.Ansatz == "Fourier":
            self.m = np.zeros(len(self.list_lx))
            for i in range(0, len(self.list_lx), 1):
                self.m[i] = self.Schnittkraefte(self.list_lx[i])
        else:
            ne = self.reihen
            n_inter = interpolation
            self.x_element_inter = np.zeros(
                (ne, n_inter)
            )  # Interpolierte Längenliste für die Elemente
            self.vz_element_inter = np.zeros((ne, n_inter))

            for i in range(0, ne, 1):
                xA = self.x_el_store[i][0]
                xB = self.x_el_store[i][1]
                le = self.l_x / ne
                dle = le / (n_inter - 1)

                wA = self.uz_el_store[i][0]
                PhiA = self.phi_el_store[i][0]
                wB = self.uz_el_store[i][1]
                PhiB = self.phi_el_store[i][1]

                for j in range(0, n_inter, 1):
                    x_loc = j * dle

                    f_1 = self.function_1_FE_xxx(x_loc, le)
                    f_2 = self.function_2_FE_xxx(x_loc, le)
                    f_3 = self.function_3_FE_xxx(x_loc, le)
                    f_4 = self.function_4_FE_xxx(x_loc, le)

                    self.x_element_inter[i][j] = x_loc
                    self.vz_element_inter[i][j] = (
                        f_1 * wA + f_2 * PhiA + f_3 * wB + f_4 * PhiB
                    ) * (-self.EI)

                self.x_element_inter[i] += i * le

                plt.plot(self.x_element_inter[i], self.vz_element_inter[i])

            # print("Max Shear Force", self.vz_element_inter.max())
            plt.show(block=False)
            plt.pause(0.1)
            plt.close()

    def Stabknicken_Element_Mat(self):
        # Definieren Sie l und S entsprechend Ihren spezifischen Anforderungen
        self.S = -1  # Default value for the normal force to -1 MN (Compression)

        ne = self.reihen
        le = self.l_x / ne

        self.Kg_II = np.zeros(((ne + 1) * 2, (ne + 1) * 2))

        self.K_el_gII_store = np.zeros((ne, 4, 4))
        for i in range(0, ne, 1):

            # Definieren Sie die Matrix
            K_G_II = (
                self.S
                / (30 * le)
                * np.array(
                    [
                        [36, 3 * le, -36, 3 * le],
                        [3 * le, 4 * le**2, -3 * le, -(le**2)],
                        [-36, -3 * le, 36, -3 * le],
                        [3 * le, -(le**2), -3 * le, 4 * le**2],
                    ]
                )
            )

            self.K_el_gII_store[i, :, :] = (
                K_G_II  # Speichert die 2D Arrays in das 3D Array ab
            )

        # Index-vectors are the same as for the calculation with TH.I.Order
        for n in range(0, ne, 1):
            for row in range(0, 4, 1):
                for col in range(0, 4, 1):
                    self.Kg_II[self.index_vector[n][row]][
                        self.index_vector[n][col]
                    ] += self.K_el_gII_store[n][row][col]

    def Stabknicken_Eigenwerte(self):
        alpha_min = 0
        alpha_max = 25
        precision = 1e-3
        initial_delta_alpha = 0.1
        critical_alphas = []
        self.det_list = []

        for i in range(0, 2500, 1):
            a_cr = 0.01 * i
            det = np.linalg.det(self.K + a_cr * self.Kg_II)
            self.det_list.append(det)
            if (i > 0) and ((det < 0 and det_1 >= 0) or (det >= 0 and det_1 < 0)):
                print("Eigenvalue ", a_cr)
            det_1 = det

        self.alpha_crit, eigenmodes = eig(self.K, -self.Kg_II)

        # print(self.alpha_crit)

        min_index = np.argmin(self.alpha_crit)  # Index des kleinsten Eigenwertes

        min_eigenmode = eigenmodes[:, min_index]  # Zugehöriger Eigenvektor
        self.min_eigenmode_every_second = min_eigenmode[
            ::2
        ]  # Auswahl jedes zweiten Elements

        self.alpha_crit = min(self.alpha_crit)
        self.N_crit = self.alpha_crit * self.S

        return critical_alphas

    def PlotBucklingEigenmodes(self):
        print("Min acrit ", self.alpha_crit)

        plt.plot(self.min_eigenmode_every_second)
        plt.gca().invert_yaxis()  # 'gca' stands for 'get current axis'

        plt.show(block=False)
        plt.pause(3)
        plt.close()

        plt.plot(self.det_list)
        plt.show(block=False)
        plt.pause(3)
        plt.close()

    def CalculateDeflections_II_Order(self):
        self.x_II = np.linalg.solve((self.K + self.Kg_II), self.P)
        self.x_disp_II = self.x_II[::2]

    def PlotDeflections_II_Order(self):
        print("Max. Deflection First Order ", self.x_disp_red.max())
        print("Max. Deflection Second Order ", self.x_disp_II.max())
        print("Max. Moment First Order ", self.m_el_store.max())
        plt.plot(self.x_disp_II, color="Red")
        plt.plot(self.x_disp_red, color="Blue")
        plt.show(block=False)
        plt.pause(4)
        plt.close()

    def Biegedrillknicken_Aufruf(self):
        self.BDK = Biegedrillknicken(self)
        self.BDK.Calculate_All()
