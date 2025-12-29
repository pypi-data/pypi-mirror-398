import numpy as np
from Stabberechnung_Klasse import StabRitz
from tabulate import tabulate
import matplotlib.pyplot as plt
import pandas as pd


class Biegedrillknicken:
    def __init__(self):
        print("Klasse")
        self.SG_TH_I = StabRitz(10, 0, 10, 1, 0, 0, 0, 0, 10, "-", "FE")
        self.SG_TH_I.Calculate_All()
        print("________Berechnung Biegedrillknicken_____________")
        # Cross Section Properties
        self.E = self.SG_TH_I.Querschnitt.E
        self.G = self.SG_TH_I.Querschnitt.G
        
        self.I_zz = self.SG_TH_I.Querschnitt.I_zz
        self.EIzz =  self.E * self.I_zz
        self.I_w = self.SG_TH_I.Querschnitt.I_w
        self.EIw =  self.E * self.I_w
        self.I_t = self.SG_TH_I.Querschnitt.I_T_GESAMT
        self.GIt = self.G * self.I_t
        self.z_M = self.SG_TH_I.Querschnitt.z_M  # Shear midpoint
        self.r = self.SG_TH_I.Querschnitt.ry

        self.z_j = 0#self.z_M - self.r / 2

        plt.show()

        print(self.EIw)
        print("IW", self.I_w)
        print(self.GIt)
        print("IT", self.I_t)
        print(self.EIzz)
        print("IZZ", self.I_zz)
        print("rz", self.r)

        # Inner Forces (TH.I.OG)
        self.My_x = self.SG_TH_I.m_element_inter  # Vektor mit Biegemoment
        self.l_x = self.SG_TH_I.l_x
        self.x = self.SG_TH_I.list_lx

        self.ne = self.SG_TH_I.reihen

        self.K_I_IW = np.zeros(
            (2 * (self.ne + 1), 2 * (self.ne + 1))
        )  # Steifigkeitsmatrizen mit konstanten Anteilen
        self.K_I_IT = np.zeros((2 * (self.ne + 1), 2 * (self.ne + 1)))
        self.K_I_q = np.zeros((2 * (self.ne + 1), 2 * (self.ne + 1)))
        self.K_I_P = np.zeros((2 * (self.ne + 1), 2 * (self.ne + 1)))

        self.K_I = np.zeros((2 * (self.ne + 1), 2 * (self.ne + 1)))

        self.K_II_Thet = np.zeros(
            (2 * (self.ne + 1), 2 * (self.ne + 1))
        )  # Steifigkeitsmatrix nach TH. II.OG für quadratischen Anteil
        self.K_II_Thet_s = np.zeros((2 * (self.ne + 1), 2 * (self.ne + 1)))

    def Calculate_All(self):
        self.Construct_IW_Mat()
        self.Construct_GIT_Mat()
        self.Construct_Mcr_Mat_1()
        self.Construct_Mcr_Mat_2()
        self.calculate_alpha_crit()

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

    def Construct_IW_Mat(self):
        le = self.l_x / self.ne
        self.list_lxle = np.linspace(0, le, 1000)

        self.K_el_IW = np.zeros((4, 4))  # Elementsteifigkeitsmatrix für IW

        self.K_el_IW_store = np.zeros((self.ne, 4, 4))  #

        # Start-Wert für die Index-Arrays
        start_werte = np.arange(
            0, 2 * self.ne, 2
        )  # Erstellt einen Array von Startwerten

        # Erstelle den Index-Vektor
        self.index_vector = np.array(
            [np.arange(start, start + 4) for start in start_werte]
        )

        for i in range(0, self.ne, 1):
            # Row = 0, Col = ...
            self.K_el_IW[0][0] = self.EIw * np.trapz(
                self.function_1_FE_xx(self.list_lxle, le)
                * self.function_1_FE_xx(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IW[0][1] = self.EIw * np.trapz(
                self.function_1_FE_xx(self.list_lxle, le)
                * self.function_2_FE_xx(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IW[0][2] = self.EIw * np.trapz(
                self.function_1_FE_xx(self.list_lxle, le)
                * self.function_3_FE_xx(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IW[0][3] = self.EIw * np.trapz(
                self.function_1_FE_xx(self.list_lxle, le)
                * self.function_4_FE_xx(self.list_lxle, le),
                self.list_lxle,
            )

            # Row = 1, Col = ...

            self.K_el_IW[1][0] = self.EIw * np.trapz(
                self.function_2_FE_xx(self.list_lxle, le)
                * self.function_1_FE_xx(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IW[1][1] = self.EIw * np.trapz(
                self.function_2_FE_xx(self.list_lxle, le)
                * self.function_2_FE_xx(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IW[1][2] = self.EIw * np.trapz(
                self.function_2_FE_xx(self.list_lxle, le)
                * self.function_3_FE_xx(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IW[1][3] = self.EIw * np.trapz(
                self.function_2_FE_xx(self.list_lxle, le)
                * self.function_4_FE_xx(self.list_lxle, le),
                self.list_lxle,
            )

            # Row = 2, Col = ...

            self.K_el_IW[2][0] = self.EIw * np.trapz(
                self.function_3_FE_xx(self.list_lxle, le)
                * self.function_1_FE_xx(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IW[2][1] = self.EIw * np.trapz(
                self.function_3_FE_xx(self.list_lxle, le)
                * self.function_2_FE_xx(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IW[2][2] = self.EIw * np.trapz(
                self.function_3_FE_xx(self.list_lxle, le)
                * self.function_3_FE_xx(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IW[2][3] = self.EIw * np.trapz(
                self.function_3_FE_xx(self.list_lxle, le)
                * self.function_4_FE_xx(self.list_lxle, le),
                self.list_lxle,
            )

            # Row = 3,  Col = ...

            self.K_el_IW[3][0] = self.EIw * np.trapz(
                self.function_4_FE_xx(self.list_lxle, le)
                * self.function_1_FE_xx(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IW[3][1] = self.EIw * np.trapz(
                self.function_4_FE_xx(self.list_lxle, le)
                * self.function_2_FE_xx(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IW[3][2] = self.EIw * np.trapz(
                self.function_4_FE_xx(self.list_lxle, le)
                * self.function_3_FE_xx(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IW[3][3] = self.EIw * np.trapz(
                self.function_4_FE_xx(self.list_lxle, le)
                * self.function_4_FE_xx(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IW_store[
                i, :, :
            ] = self.K_el_IW  # Speichert die 2D Arrays in das 3D Array ab

        for n in range(0, self.ne, 1):
            for row in range(0, 4, 1):
                for col in range(0, 4, 1):
                    self.K_I[self.index_vector[n][row]][
                        self.index_vector[n][col]
                    ] += self.K_el_IW_store[n][row][col]

    def Construct_GIT_Mat(self):
        le = self.l_x / self.ne
        self.list_lxle = np.linspace(0, le, 1000)

        self.K_el_IT = np.zeros((4, 4))  # Elementsteifigkeitsmatrix für IT
        self.K_el_IT_store = np.zeros((self.ne, 4, 4))  #

        # Start-Wert für die Index-Arrays
        start_werte = np.arange(
            0, 2 * self.ne, 2
        )  # Erstellt einen Array von Startwerten

        # Erstelle den Index-Vektor
        self.index_vector = np.array(
            [np.arange(start, start + 4) for start in start_werte]
        )

        for i in range(0, self.ne, 1):
            # Row = 0, Col = ...
            self.K_el_IT[0][0] = self.GIt * np.trapz(
                self.function_1_FE_x(self.list_lxle, le)
                * self.function_1_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IT[0][1] = self.GIt * np.trapz(
                self.function_1_FE_x(self.list_lxle, le)
                * self.function_2_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IT[0][2] = self.GIt * np.trapz(
                self.function_1_FE_x(self.list_lxle, le)
                * self.function_3_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IT[0][3] = self.GIt * np.trapz(
                self.function_1_FE_x(self.list_lxle, le)
                * self.function_4_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            # Row = 1, Col = ...

            self.K_el_IT[1][0] = self.GIt * np.trapz(
                self.function_2_FE_x(self.list_lxle, le)
                * self.function_1_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IT[1][1] = self.GIt * np.trapz(
                self.function_2_FE_x(self.list_lxle, le)
                * self.function_2_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IT[1][2] = self.GIt * np.trapz(
                self.function_2_FE_x(self.list_lxle, le)
                * self.function_3_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IT[1][3] = self.GIt * np.trapz(
                self.function_2_FE_x(self.list_lxle, le)
                * self.function_4_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            # Row = 2, Col = ...

            self.K_el_IT[2][0] = self.GIt * np.trapz(
                self.function_3_FE_x(self.list_lxle, le)
                * self.function_1_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IT[2][1] = self.GIt * np.trapz(
                self.function_3_FE_x(self.list_lxle, le)
                * self.function_2_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IT[2][2] = self.GIt * np.trapz(
                self.function_3_FE_x(self.list_lxle, le)
                * self.function_3_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IT[2][3] = self.GIt * np.trapz(
                self.function_3_FE_x(self.list_lxle, le)
                * self.function_4_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            # Row = 3,  Col = ...

            self.K_el_IT[3][0] = self.GIt * np.trapz(
                self.function_4_FE_x(self.list_lxle, le)
                * self.function_1_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IT[3][1] = self.GIt * np.trapz(
                self.function_4_FE_x(self.list_lxle, le)
                * self.function_2_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IT[3][2] = self.GIt * np.trapz(
                self.function_4_FE_x(self.list_lxle, le)
                * self.function_3_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IT[3][3] = self.GIt * np.trapz(
                self.function_4_FE_x(self.list_lxle, le)
                * self.function_4_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_IT_store[
                i, :, :
            ] = self.K_el_IT  # Speichert die 2D Arrays in das 3D Array ab

        for n in range(0, self.ne, 1):
            for row in range(0, 4, 1):
                for col in range(0, 4, 1):
                    self.K_I[self.index_vector[n][row]][
                        self.index_vector[n][col]
                    ] += self.K_el_IT_store[n][row][col]

    def Construct_Mcr_Mat_1(self):
        le = self.l_x / self.ne
        self.list_lxle = np.linspace(0, le, 5)      # Muss der Nummer der Interpolationsstellen entsprechen! Aus My-Berechnung

        self.K_el_EIZ = np.zeros(
            (4, 4)
        )  # Geometrische Steifigkeitsmatrix quadratischen Lastanteil

        self.K_el_EIZ_store = np.zeros((self.ne, 4, 4))  #

        # Start-Wert für die Index-Arrays
        start_werte = np.arange(
            0, 2 * self.ne, 2
        )  # Erstellt einen Array von Startwerten

        # Erstelle den Index-Vektor
        self.index_vector = np.array(
            [np.arange(start, start + 4) for start in start_werte]
        )

        for i in range(0, self.ne, 1):
            # Row = 0, Col = ...
            
            self.K_el_EIZ[0][0] = self.EIzz * np.trapz(
                self.My_x[i]**2 * 
                self.function_1_FE(self.list_lxle, le)
                * self.function_1_FE(self.list_lxle, le),
                self.list_lxle
            )

            self.K_el_EIZ[0][1] = self.EIzz* np.trapz(
                self.My_x[i]**2 * 
                self.function_1_FE(self.list_lxle, le)
                * self.function_2_FE(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_EIZ[0][2] = self.EIzz * np.trapz(
                self.My_x[i]**2 * 
                self.function_1_FE(self.list_lxle, le)
                * self.function_3_FE(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_EIZ[0][3] = self.EIzz * np.trapz(
                self.My_x[i]**2 * 
                self.function_1_FE(self.list_lxle, le)
                * self.function_4_FE(self.list_lxle, le),
                self.list_lxle,
            )

            # Row = 1, Col = ...

            self.K_el_EIZ[1][0] = self.EIzz * np.trapz(
                self.My_x[i]**2 * 
                self.function_2_FE(self.list_lxle, le)
                * self.function_1_FE(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_EIZ[1][1] = self.EIzz* np.trapz(
                self.My_x[i]**2 * 
                self.function_2_FE(self.list_lxle, le)
                * self.function_2_FE(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_EIZ[1][2] = self.EIzz * np.trapz(
                self.My_x[i]**2 * 
                self.function_2_FE(self.list_lxle, le)
                * self.function_3_FE(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_EIZ[1][3] = self.EIzz * np.trapz(
                self.My_x[i]**2 * 
                self.function_2_FE(self.list_lxle, le)
                * self.function_4_FE(self.list_lxle, le),
                self.list_lxle,
            )

            # Row = 2, Col = ...

            self.K_el_EIZ[2][0] = self.EIzz * np.trapz(
                self.My_x[i]**2 * 
                self.function_3_FE(self.list_lxle, le)
                * self.function_1_FE(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_EIZ[2][1] = self.EIzz* np.trapz(
                self.My_x[i]**2 * 
                self.function_3_FE(self.list_lxle, le)
                * self.function_2_FE(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_EIZ[2][2] = self.EIzz * np.trapz(
                self.My_x[i]**2 * 
                self.function_3_FE(self.list_lxle, le)
                * self.function_3_FE(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_EIZ[2][3] = self.EIzz * np.trapz(
                self.My_x[i]**2 * 
                self.function_3_FE(self.list_lxle, le)
                * self.function_4_FE(self.list_lxle, le),
                self.list_lxle,
            )

            # Row = 3,  Col = ...

            self.K_el_EIZ[3][0] = self.EIzz * np.trapz(
                self.My_x[i]**2 * 
                self.function_4_FE(self.list_lxle, le)
                * self.function_1_FE(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_EIZ[3][1] = self.EIzz * np.trapz(
                self.My_x[i]**2 * 
                self.function_4_FE(self.list_lxle, le)
                * self.function_2_FE(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_EIZ[3][2] = self.EIzz * np.trapz(
                self.My_x[i]**2 * 
                self.function_4_FE(self.list_lxle, le)
                * self.function_3_FE(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_EIZ[3][3] = self.EIzz * np.trapz(
                self.My_x[i]**2 * 
                self.function_4_FE(self.list_lxle, le)
                * self.function_4_FE(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_EIZ_store[
                i, :, :
            ] = self.K_el_EIZ  # Speichert die 2D Arrays in das 3D Array ab

        for n in range(0, self.ne, 1):
            for row in range(0, 4, 1):
                for col in range(0, 4, 1):
                    self.K_II_Thet[self.index_vector[n][row]][
                        self.index_vector[n][col]
                    ] += self.K_el_EIZ_store[n][row][col]

    def Construct_Mcr_Mat_2(self):
        le = self.l_x / self.ne
        self.list_lxle = np.linspace(0, le, 5)      # Muss der Nummer der Interpolationsstellen entsprechen! Aus My-Berechnung

        self.K_el_thet_II = np.zeros(
            (4, 4)
        )  # Geometrische Steifigkeitsmatrix quadratischen Lastanteil

        self.K_el_thet_II_store = np.zeros((self.ne, 4, 4))  #

        # Start-Wert für die Index-Arrays
        start_werte = np.arange(
            0, 2 * self.ne, 2
        )  # Erstellt einen Array von Startwerten

        # Erstelle den Index-Vektor
        self.index_vector = np.array(
            [np.arange(start, start + 4) for start in start_werte]
        )

        for i in range(0, self.ne, 1):
            # Row = 0, Col = ...
            
            self.K_el_thet_II[0][0] =  np.trapz(
                self.My_x[i]*  self.r * 
                self.function_1_FE_x(self.list_lxle, le)
                * self.function_1_FE_x(self.list_lxle, le),
                self.list_lxle
            )

            self.K_el_thet_II[0][1] =  np.trapz(
                self.My_x[i]* self.r *
                self.function_1_FE_x(self.list_lxle, le)
                * self.function_2_FE_x(self.list_lxle, le),
                self.list_lxle
            )

            self.K_el_thet_II[0][2] = np.trapz(
                self.My_x[i]* self.r  *
                self.function_1_FE_x(self.list_lxle, le)
                * self.function_3_FE_x(self.list_lxle, le),
                self.list_lxle
            )

            self.K_el_thet_II[0][3] =  np.trapz(
                self.My_x[i]* self.r *
                self.function_1_FE_x(self.list_lxle, le)
                * self.function_4_FE_x(self.list_lxle, le),
                self.list_lxle
            )

            # Row = 1, Col = ...

            self.K_el_thet_II[1][0] =  np.trapz(
                self.My_x[i]* self.r *
                self.function_2_FE_x(self.list_lxle, le)
                * self.function_1_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_thet_II[1][1] =  np.trapz(
                self.My_x[i] * self.r  *
                self.function_2_FE_x(self.list_lxle, le)
                * self.function_2_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_thet_II[1][2] =  np.trapz(
                self.My_x[i]* self.r  *
                self.function_2_FE_x(self.list_lxle, le)
                * self.function_3_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_thet_II[1][3] =  np.trapz(
                self.My_x[i]* self.r  *
                self.function_2_FE_x(self.list_lxle, le)
                * self.function_4_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            # Row = 2, Col = ...

            self.K_el_thet_II[2][0] =  np.trapz(
                self.My_x[i]* self.r  *
                self.function_3_FE_x(self.list_lxle, le)
                * self.function_1_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_thet_II[2][1] =  np.trapz(
                self.My_x[i]* self.r *
                self.function_3_FE_x(self.list_lxle, le)
                * self.function_2_FE_x(self.list_lxle, le),
                self.list_lxle
            )

            self.K_el_thet_II[2][2] =  np.trapz(
                self.My_x[i]* self.r *
                self.function_3_FE_x(self.list_lxle, le)
                * self.function_3_FE_x(self.list_lxle, le),
                self.list_lxle
            )

            self.K_el_thet_II[2][3] = np.trapz(
                self.My_x[i]* self.r  *
                self.function_3_FE_x(self.list_lxle, le)
                * self.function_4_FE_x(self.list_lxle, le),
                self.list_lxle
            )

            # Row = 3,  Col = ...

            self.K_el_thet_II[3][0] =  np.trapz(
                self.My_x[i]* self.r *
                self.function_4_FE_x(self.list_lxle, le)
                * self.function_1_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_thet_II[3][1] =  np.trapz(
                self.My_x[i]* self.r  *
                self.function_4_FE_x(self.list_lxle, le)
                * self.function_2_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_thet_II[3][2] =  np.trapz(
                self.My_x[i]* self.r *
                self.function_4_FE_x(self.list_lxle, le)
                * self.function_3_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_thet_II[3][3] =  np.trapz(
                self.My_x[i]* self.r *
                self.function_4_FE_x(self.list_lxle, le)
                * self.function_4_FE_x(self.list_lxle, le),
                self.list_lxle,
            )

            self.K_el_thet_II_store[
                i, :, :
            ] = self.K_el_thet_II  # Speichert die 2D Arrays in das 3D Array ab

        for n in range(0, self.ne, 1):
            for row in range(0, 4, 1):
                for col in range(0, 4, 1):
                    self.K_II_Thet_s[self.index_vector[n][row]][
                        self.index_vector[n][col]
                    ] += self.K_el_thet_II_store[n][row][col]



    def Export_ElementStiffness_IW(self, n_elem, name):
        Matrix = self.K_el_IW_store[n_elem].round(2)
        df = pd.DataFrame(Matrix, index=[1, 2, 3, 4])
        df.to_csv(
            f"Checks/Data/ElementStiffness_{name}_{n_elem}_IW.csv",
            header=False,
            index=[1, 2, 3, 4],
        )

        Matrix = self.K_el_IT_store[n_elem].round(2)
        df = pd.DataFrame(Matrix)
        df.to_csv(
            f"Checks/Data/ElementStiffness_{name}_{n_elem}_IT.csv",
            header=False,
            index=[1, 2, 3, 4],
        )

        Matrix = self.K_el_EIZ_store[n_elem].round(2)
        df = pd.DataFrame(Matrix)
        df.to_csv(
            f"Checks/Data/ElementStiffness_{name}_{n_elem}_KIITHET.csv",
            header=False,
            index=[1, 2, 3, 4],
        )

        Matrix = self.K_el_thet_II_store[n_elem].round(2)
        df = pd.DataFrame(Matrix)
        df.to_csv(
            f"Checks/Data/ElementStiffness_{name}_{n_elem}_KIITHET_s.csv",
            header=False,
            index=[1, 2, 3, 4],
        )


    def calculate_alpha_crit(self):
        alpha_min = 0
        alpha_max = 10
        precision = 1e-3
        initial_delta_alpha = 0.1
        critical_alphas = []
        self._recursive_search(alpha_min, alpha_max, initial_delta_alpha, precision, critical_alphas)
        return critical_alphas

    def _recursive_search(self, alpha_min, alpha_max, delta_alpha, precision, critical_alphas):
        alpha_0 = alpha_min
        det0 = np.linalg.det(self.K_I - alpha_0**2 * self.K_II_Thet + alpha_0 * self.K_II_Thet_s) # 
        for i in range(1, int((alpha_max - alpha_min) / delta_alpha) + 1):
            alpha_0 = alpha_min + i * delta_alpha
            det1 = np.linalg.det(self.K_I - alpha_0**2 * self.K_II_Thet + alpha_0 * self.K_II_Thet_s)# 
            try:
                val = det0 * det1 
            except:
                val = det0 * det1 / 1e50
            if val < 0:  # Vorzeichenwechsel erkannt
                if delta_alpha <= precision:
                    # Eigenwert gefunden, Mittelpunkt des Intervalls speichern
                    alpha_crit = (alpha_0 - delta_alpha / 2)
                    critical_alphas.append(alpha_crit)
                    print(f"Eigenwert gefunden: alpha_crit = {alpha_crit}, Mcrit = {alpha_crit * self.My_x.max()}")
                else:
                    # Weitere Suche in diesem Intervall mit feinerer Schrittweite
                    self._recursive_search(alpha_0 - delta_alpha, alpha_0, delta_alpha / 10, precision, critical_alphas)
            det0 = det1

BDK = Biegedrillknicken()
BDK.Calculate_All()
BDK.Export_ElementStiffness_IW(1, "Unittest")


print(tabulate(BDK.K_el_IW))
print(tabulate(BDK.K_el_IT))
print(BDK.r)
