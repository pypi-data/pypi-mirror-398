import numpy as np
# from Stabberechnung_Klasse import StabRitz
from tabulate import tabulate
import matplotlib.pyplot as plt
import pandas as pd
from scipy.linalg import eig

class Biegedrillknicken:
    def __init__(self,StabRitzObjekt):
        print("Klasse")
        self.SG_TH_I = StabRitzObjekt #StabRitz(20, 0, 10, 1, 0, 0, 0, 0, 10, "-", "FE")
        #self.SG_TH_I.Calculate_All()
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
        self.rz = self.SG_TH_I.Querschnitt.rz

        self.ho = self.SG_TH_I.Querschnitt.z_so
        self.hu = self.SG_TH_I.Querschnitt.z_su

        self.z_j = 0
        
        print("Iy", self.SG_TH_I.Querschnitt.I_yy)
        print("EIw",self.EIw)
        print("IW", self.I_w)
        print("GIT",self.GIt)
        print("IT", self.I_t)
        print("EIZZ",self.EIzz)
        print("IZZ", self.I_zz)
        print("rz", self.rz)
        print("zM", self.z_M)

        print("ho", self.ho)
        print("hu", self.hu)

        # Inner Forces (TH.I.OG)
        self.My_x = self.SG_TH_I.m_element_inter  # Vektor mit Biegemoment
        self.l_x = self.SG_TH_I.l_x
        self.x = self.SG_TH_I.list_lx

        self.ne = self.SG_TH_I.reihen

        self.K_I_IW = np.zeros(
            (self.ne, self.ne)
        ) 
        self.K_I_IT = np.zeros((self.ne, self.ne))
        self.K_I_EIZ = np.zeros((self.ne, self.ne))

        self.K_I_GES = np.zeros((2*self.ne,2*self.ne))

        self.K_II_Coupling = np.zeros((self.ne,self.ne))
        self.K_II_Theta_s = np.zeros((self.ne,self.ne))
        self.K_II_Theta = np.zeros((self.ne,self.ne))

        self.K_II_GES = np.zeros((2*self.ne,2*self.ne))



    def Calculate_All(self):
        self.Construct_IW_Mat()
        self.Construct_GIT_Mat()
        self.Construct_EIZ_Mat()
        self.Construct_K_II_Coupling_Part()
        self.Construct_K_II_Theta_s()
        self.Construc_K_II_Theta()

        self.Construct_K_I_Ges()
        self.Construct_K_II_ges()
        self.Calculate_Alpha_Crit()


    def function_theta(self, x, m):
        return np.sin(m * np.pi * x / self.l_x)

    def function_theta_x(self, x, m):
        return np.cos(m * np.pi * x / self.l_x) * m * np.pi / self.l_x

    def function_theta_xx(self, x, m):
        return np.sin(m * np.pi * x / self.l_x) * (m * np.pi / self.l_x) ** 2 * (-1)

    def function_theta_xxx(self, x, m):
        return np.sin(m * np.pi * x / self.l_x) * (m * np.pi / self.l_x) ** 3 * (-1)
    

    def function_u(self, x, m):
        return np.sin(m * np.pi * x / self.l_x)

    def function_u_x(self, x, m):
        return np.cos(m * np.pi * x / self.l_x) * m * np.pi / self.l_x

    def function_u_xx(self, x, m):
        return np.sin(m * np.pi * x / self.l_x) * (m * np.pi / self.l_x) ** 2 * (-1)

    def function_u_xxx(self, x, m):
        return np.sin(m * np.pi * x / self.l_x) * (m * np.pi / self.l_x) ** 3 * (-1)
    

    def M_x(self,x,q):
        """
        Test-Function to calculate the moment curve for a simple supported beam under uniform \n
        line load \n

        Args:
            x (_type_): x-value: Input via scalar variable or vector, depending on the desired \n
                                 result
            q (_type_): Scalar variable for the line load: In MN/m or equivalent \n
        """

        return q * (self.l_x-x)*x * 0.5

    def Construct_IW_Mat(self):
        le = self.l_x 
        self.list_lxle = np.linspace(0, le, 1000)

        for m in range(1, self.ne + 1, 1):
            for n in range(1, self.ne + 1, 1):
                if (m==n):
                    self.K_I_IW[m - 1][n - 1] = self.EIw * np.trapz(
                        self.function_theta_xx(self.list_lxle , m)
                        * self.function_theta_xx(self.list_lxle , n),
                        self.list_lxle
                    )
                else:
                    self.K_I_IW[m - 1][n - 1] = 0.5 * self.EIw * np.trapz(
                        self.function_theta_xx(self.list_lxle , m)
                        * self.function_theta_xx(self.list_lxle , n),
                        self.list_lxle
                    )

        self.K_I_IW = np.where(self.K_I_IW  < 1e-9, 0, self.K_I_IW )

        # print(self.K_I_IW )

    def Construct_GIT_Mat(self):
        le = self.l_x 
        self.list_lxle = np.linspace(0, le, 1000)
        for m in range(1, self.ne + 1, 1):
            for n in range(1, self.ne + 1, 1):
                if (m==n):
                    self.K_I_IT[m - 1][n - 1] = self.GIt * np.trapz(
                        self.function_theta_x(self.list_lxle , m)
                        * self.function_theta_x(self.list_lxle , n),
                        self.list_lxle
                    )
                else:
                    self.K_I_IT[m - 1][n - 1] = 0.5 * self.GIt * np.trapz(
                        self.function_theta_x(self.list_lxle , m)
                        * self.function_theta_x(self.list_lxle , n),
                        self.list_lxle
                    )

        self.K_I_IT = np.where(self.K_I_IT  < 1e-9, 0, self.K_I_IT )

        # print(self.K_I_IT )

    def Construct_EIZ_Mat(self):
        le = self.l_x 
        self.list_lxle = np.linspace(0, le, 1000)
        for m in range(1, self.ne + 1, 1):
            for n in range(1, self.ne + 1, 1):
                if (m == n):
                    self.K_I_EIZ[m - 1][n - 1] = self.EIzz * np.trapz(
                        self.function_u_xx(self.list_lxle , m)
                        * self.function_u_xx(self.list_lxle , n),
                        self.list_lxle
                    )
                else:
                    self.K_I_EIZ[m - 1][n - 1] = 0.5 * self.EIzz * np.trapz(
                        self.function_u_xx(self.list_lxle , m)
                        * self.function_u_xx(self.list_lxle , n),
                        self.list_lxle
                    )

        self.K_I_EIZ = np.where(self.K_I_EIZ  < 1e-9, 0, self.K_I_EIZ )

        # print(self.K_I_EIZ)

    def Construct_K_II_Coupling_Part(self):
        """
        Note: The stiffness matrix comes from the derivative of 1/2 * PI \n
        Therefore 1/2 * 2 = 1 for the calculation of the stiffness matrices, \n
        in accordance to the stiffness matrices for the theory of first order \n
        """
        le = self.l_x / self.ne
        # print(le)
        
        for i in range(0,self.ne,1):
            for m in range(1, self.ne + 1, 1):
                self.list_lxle = np.linspace(le*(i), le*(i+1), 2)
                for n in range(1, self.ne + 1, 1):
                    self.K_II_Coupling[m - 1][n - 1] +=   np.trapz(
                        self.My_x[i] * 
                        self.function_u_xx(self.list_lxle , m)
                        * self.function_theta(self.list_lxle , n),
                        self.list_lxle
                    )

        self.M_max = self.My_x.max()
        self.K_II_Coupling = np.where(abs(self.K_II_Coupling)  < 1e-9, 0, self.K_II_Coupling)

    def Construct_K_II_Theta_s(self):
        """
        Function to construct the stiffness component for the 
        """
        le = self.l_x  / self.ne

        for i in range(0,self.ne,1):
            for m in range(1, self.ne + 1, 1):
                self.list_lxle = np.linspace(le*(i), le*(i+1), 2)
                for n in range(1, self.ne + 1, 1):
                    if (m == n):
                        self.K_II_Theta_s[m-1][n-1] +=   self.rz *np.trapz(
                            self.My_x[i]   
                            *self.function_theta_x(self.list_lxle , m)
                            * self.function_theta_x(self.list_lxle , n),
                            self.list_lxle
                        )
                    else:
                        self.K_II_Theta_s[m-1][n-1] +=  0.5* self.rz *np.trapz(
                            self.My_x[i]   
                            *self.function_theta_x(self.list_lxle , m)
                            * self.function_theta_x(self.list_lxle , n),
                            self.list_lxle
                        )

        self.K_II_Theta_s = np.where(abs(self.K_II_Theta_s)  < 1e-9, 0, self.K_II_Theta_s)

        # print(self.K_II_Theta_s)

    def Construc_K_II_Theta(self):
        """
        Function to construct the stiffness component for the influence of the \n
        load parts, which is stationed in a distance to the non torsional cross section center \n
        """
        le = self.l_x 
        self.list_lxle = np.linspace(0, le, 1000)
        for m in range(1, self.ne + 1, 1):
            for n in range(1, self.ne + 1, 1):
                self.K_II_Theta[m-1][n-1] = 0 * np.trapz(
                    0.1 * self.z_j * 
                    self.function_theta(self.list_lxle , m)
                    * self.function_theta(self.list_lxle , n),
                    self.list_lxle
                )

        self.K_II_Theta = np.where(abs(self.K_II_Theta)  < 1e-9, 0, self.K_II_Theta)

        # print(self.K_II_Theta)


    def Construct_K_I_Ges(self):
        self.K_I_GES[0:self.ne,0:self.ne] = self.K_I_EIZ
        self.K_I_GES[self.ne:2*self.ne,self.ne:2*self.ne] =  self.K_I_IW + self.K_I_IT

        # print(tabulate(self.K_I_GES))

    def Construct_K_II_ges(self):
        self.K_II_GES[self.ne:2*self.ne, 0:self.ne] = self.K_II_Coupling
        self.K_II_GES[0:self.ne, self.ne:2*self.ne] = self.K_II_Coupling
        self.K_II_GES[self.ne:2*self.ne,self.ne:2*self.ne] =  (self.K_II_Theta_s + self.K_II_Theta)*(-1)

        # print(tabulate(self.K_II_GES))

    def Export_ElementStiffness_Complete(self, n_elem, name):
        Matrix = self.K_I_IW[n_elem].round(2)
        df = pd.DataFrame(Matrix, index=[1, 2, 3, 4])
        df.to_csv(
            f"Checks/Data/ElementStiffness_{name}_{n_elem}_IW.csv",
            header=False,
            index=[1, 2, 3, 4],
        )

        Matrix = self.K_I_IT[n_elem].round(2)
        df = pd.DataFrame(Matrix)
        df.to_csv(
            f"Checks/Data/ElementStiffness_{name}_{n_elem}_IT.csv",
            header=False,
            index=[1, 2, 3, 4],
        )

        Matrix = self.K_I_EIZ[n_elem].round(2)
        df = pd.DataFrame(Matrix)
        df.to_csv(
            f"Checks/Data/ElementStiffness_{name}_{n_elem}_KIITHET.csv",
            header=False,
            index=[1, 2, 3, 4],
        )


    def Calculate_Alpha_Crit(self):
        alpha_crit, eigenmodes = eig(self.K_I_GES,self.K_II_GES)

        # Extraktion der positiven Werte
        positive_alpha_crit = np.sort(alpha_crit[alpha_crit > 0])
        # Extraktion der negativen Werte
        negative_alpha_crit = np.sort(alpha_crit[alpha_crit < 0])[::-1]  # Sortiere absteigend

        # print("Sortierte positive Werte:", positive_alpha_crit)
        # print("Sortierte negative Werte:", negative_alpha_crit)
        print("alpha_crit",positive_alpha_crit.min())
        print("Maximales Moment ", self.M_max)
        print("Mcr", positive_alpha_crit.min() *self.M_max  )

        self.alpha_crit_res = positive_alpha_crit.min()
        self.M_cr_res = positive_alpha_crit.min() *self.M_max


    def Export_Results(self,path = "Checks/Data/Testing_Examples/Example_1.csv"):
        df = pd.DataFrame({
                "acrit": [round(self.alpha_crit_res.real,2)], 
                "Mcr": [round(self.M_cr_res.real,2)]
            }, index = None)
        df.to_csv(path, header = [r"$a_{crit}$", r"$M_{cr}$ in [MNm]"])
        print(df)

# BDK = Biegedrillknicken()
# BDK.Calculate_All()

# BDK.Export_Results("Checks/Data/Testing_Examples/Example_2.csv")
