import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import pandas as pd
import time
import os
from scipy import optimize
from scipy.integrate import simpson
import math

try:
    import plate_bending_cpp
except:
    from KIB_LAP.Plattentragwerke import plate_bending_cpp


class PlateBendingKirchhoffClass:
    def __init__(
        self,
        E,
        t,
        a,
        b,
        p0,
        x0,
        u,
        y0,
        v,
        nu=0.0,
        kappa_s=5 / 6,
        K=0,
        n_inte=50,
        loading="Regular",
        support="hhhh",
        reihen=8,
        x_s_positions=[],
        I_s_values=[],
        y_s_positions=[],
        I_t_values=[],
    ):
        """
        Initialisierung der Klasse PlateBendingKirchhoff.

        Args:
            E (float): Elastizitätsmodul.
            t (float): Dicke der Platte.
            a (float): Länge der Platte in x-Richtung.
            b (float): Länge der Platte in y-Richtung.
            p0 (float): Maximale Last.
            x0 (float): Startpunkt der Last in x-Richtung.
            u (float): Breite der Last in x-Richtung.
            y0 (float): Startpunkt der Last in y-Richtung.
            v (float): Breite der Last in y-Richtung.
            nu (float, optional): Querdehnzahl. Standardmäßig 0.0.
            kappa_s (float, optional): Schubkorrekturfaktor. Standardmäßig 5/6.
            K (int, optional): Torsionssteifigkeit. Standardmäßig 0.
            n_inte (int, optional): Anzahl der Integrationspunkte. Standardmäßig 50.
            loading (str, optional): Art der Belastung. Standardmäßig "Regular". Andere Eingabewerte Liste
            support (str, optional): Lagerungsbedingungen. Standardmäßig "hhhh".
            reihen (int, optional): Anzahl der Reihen für die Reihenentwicklung. Standardmäßig 8.
        """
        # Materialien
        self.E = E
        self.nu = nu
        self.kappa_s = kappa_s
        self.K = K
        # Plattenabmessungen in [m]
        self.t = t
        self.a = a
        self.b = b

        self.n_inte = n_inte

        self.list_a = np.linspace(0, self.a, self.n_inte)
        self.list_b = np.linspace(0, self.b, self.n_inte)

        # Belastung
        self.p0 = p0
        self.x0 = x0
        self.u = u
        self.y0 = y0
        self.v = v

        self.loading = loading

        # Steifigkeitsmatrix-Komponenten
        self.D_11 = E * t**3 / (12 * (1 - nu**2))
        self.D_22 = self.D_11
        self.D_12 = self.D_11 * nu
        self.D_66 = (1 - nu) / 2 * self.D_11

        self.support = support

        self.reihen = reihen

        self.mat = np.zeros((self.reihen**2, self.reihen**2))

        self.load = np.zeros((self.reihen**2))

        self.x_s_array = np.array(x_s_positions, dtype=np.float64)
        self.I_s_array = np.array(I_s_values, dtype=np.float64)

        self.y_s_array = np.array(y_s_positions, dtype=np.float64)
        self.I_t_array = np.array(I_t_values, dtype=np.float64)

    def CalculateAll(self):
        """
        Führt alle Berechnungsschritte aus.
        """
        self.AssembleStiffnessMatrix()
        self.Construct_Loadvector()
        self.ReduceMatrix()
        self.SolveSystem()
        self.TransformSolutionMatrix()

    def AssembleStiffnessMatrix(self):
        """
        Berechnung der Steifigkeitsmatrix für die Plattenstruktur mit dem C++-Modul via pybind11.
        """
        # Sicherstellen, dass das C++-Modul importiert werden kann
        try:
            pass
        except ImportError as e:
            print("Fehler beim Import des C++-Moduls:", e)
            raise
        print(self.support)
        # Aufruf der assemble_stiffness_matrix-Funktion aus dem C++-Modul
        self.mat = plate_bending_cpp.assemble_stiffness_matrix(
            self.D_11,
            self.D_22,
            self.D_12,
            self.D_66,
            self.reihen,
            self.n_inte,
            self.a,
            self.b,
            self.support,
            self.E,
            self.x_s_array,
            self.I_s_array,
            self.y_s_array,
            self.I_t_array,
        )

        self.mat = np.array(self.mat)  # Konvertierung in ein NumPy-Array

    def Construct_Loadvector(self):
        """
        Konstruktion des Lastvektors basierend auf der aufgebrachten Belastung.
        """
        if self.loading == "Regular":
            rectangular_loads = [
                # [x0, x1, y0, y1, p0]
                [self.x0, self.x0 + self.u, self.y0, self.y0 + self.v, self.p0]
            ]

            for load in rectangular_loads:
                x0, x1, y0, y1, p0 = load

                # Sicherstellen, dass die Last innerhalb der Plattenabmessungen liegt
                x0 = max(0, min(self.a, x0))
                x1 = max(0, min(self.a, x1))
                y0 = max(0, min(self.b, y0))
                y1 = max(0, min(self.b, y1))

                list_load_inte_x = np.linspace(x0, x1, 100)
                list_load_inte_y = np.linspace(y0, y1, 100)
                for m in range(1, self.reihen + 1):
                    for n in range(1, self.reihen + 1):
                        # Integration über die Lastfläche

                        y_values_1 = self.function_1(list_load_inte_x, m)
                        omega_1m = simpson(y_values_1, x=list_load_inte_x)

                        y_values_2 = self.function_2(list_load_inte_y, n)
                        omega_1n = simpson(y_values_2, x=list_load_inte_y)

                        self.load[n - 1 + self.reihen * (m - 1)] += (
                            p0 * omega_1m * omega_1n
                        )
        else:
            self.RectangularLoad = pd.DataFrame(
                pd.read_csv("Loading/Constant_Loading.csv")
            )
            for i in range(0, len(self.RectangularLoad["x0[m]"]), 1):
                x0 = float(self.RectangularLoad["x0[m]"][i])
                if (x0 < 0) or (x0 > self.a):
                    x0 = 0
                x1 = float(self.RectangularLoad["x1[m]"][i])
                if x1 > self.a or x1 < 0:
                    x1 = self.a
                y0 = float(self.RectangularLoad["y0[m]"][i])
                if y0 < 0 or y0 > self.b:
                    y0 = 0
                y1 = float(self.RectangularLoad["y1[m]"][i])
                if y1 < 0 or y1 > self.b:
                    y1 = self.b

                p0 = float(self.RectangularLoad["p0[MN/m**2]"][i])

                list_load_inte_x = np.linspace(x0, x1, 100)
                list_load_inte_y = np.linspace(y0, y1, 100)
                for m in range(1, self.reihen + 1, 1):
                    for n in range(1, self.reihen + 1, 1):

                        y_values_1 = self.function_1(list_load_inte_x, m)
                        omega_1m = simpson(y_values_1, x=list_load_inte_x)

                        y_values_2 = self.function_2(list_load_inte_y, n)
                        omega_1n = simpson(y_values_2, x=list_load_inte_y)

                        self.load[n - 1 + self.reihen * (m - 1)] += (
                            p0 * omega_1m * omega_1n
                        )

    def ReduceMatrix(self):
        """
        Reduziert die Matrix und den Lastvektor, um Nullzeilen und -spalten zu entfernen.
        """
        # Prüfen, welche Zeilen und Spalten nur Nullen enthalten
        non_zero_rows = ~np.all(self.mat == 0, axis=1)
        non_zero_cols = ~np.all(self.mat == 0, axis=0)

        # Reduziere die Matrix und den Vektor, um nur Nicht-Null Zeilen und Spalten zu behalten
        self.reduced_mat = self.mat[non_zero_rows, :][:, non_zero_cols]
        self.reduced_load = self.load[non_zero_rows]

    def SolveSystem(self):
        """
        Löst das reduzierte Gleichungssystem.
        """
        if self.reduced_mat.size > 0:
            self.x_reduced = np.linalg.solve(self.reduced_mat, self.reduced_load)
        else:
            print("Keine Lösung möglich, da das Gleichungssystem nur Nullen enthält.")

    def TransformSolutionMatrix(self):
        """
        Transformiert die Lösungsvektoren in eine Matrixform.
        """
        # Berechnen der Dimension der quadratischen Matrix
        n = int(np.sqrt(len(self.x_reduced)))

        if n**2 != len(self.x_reduced):
            raise ValueError(
                "Die Länge von x_reduced ist nicht das Quadrat einer ganzen Zahl"
            )

        # Umstrukturieren des Vektors x_reduced in eine quadratische n x n Matrix
        self.matrix = self.x_reduced.reshape(n, n)

    def SolutionPointDisp(self, a_sol, b_sol):
        """
        Berechnet die Durchbiegung an einem bestimmten Punkt (a_sol, b_sol).
        """
        x_disp = 0.0

        for m in range(1, self.reihen + 1):
            for n in range(1, self.reihen + 1):
                x_disp += (
                    self.matrix[m - 1][n - 1]
                    * self.function_1(a_sol, m)
                    * self.function_2(b_sol, n)
                )

        return x_disp

    def SolutionPointMomentx(self, a_sol, b_sol):
        """
        Berechnet den Biegemoment mxx an einem bestimmten Punkt (a_sol, b_sol).
        """
        mxx = 0.0

        for m in range(1, self.reihen + 1):
            for n in range(1, self.reihen + 1):
                mxx += self.matrix[m - 1][n - 1] * (
                    -self.D_11 * self.function_1xx(a_sol, m) * self.function_2(b_sol, n)
                    - self.D_12
                    * self.function_2yy(b_sol, n)
                    * self.function_1(a_sol, m)
                )

        return mxx

    def SolutionPointMomenty(self, a_sol, b_sol):
        """
        Berechnet den Biegemoment myy an einem bestimmten Punkt (a_sol, b_sol).
        """
        myy = 0.0

        for m in range(1, self.reihen + 1):
            for n in range(1, self.reihen + 1):
                myy += self.matrix[m - 1][n - 1] * (
                    -self.D_12 * self.function_1xx(a_sol, m) * self.function_2(b_sol, n)
                    - self.D_22
                    * self.function_2yy(b_sol, n)
                    * self.function_1(a_sol, m)
                )

        return myy

    def SolutionPointMomentxy(self, a_sol, b_sol):
        """
        Berechnet das Drillmoment Mxy an einem bestimmten Punkt (a_sol, b_sol).
        """
        mxy = 0.0

        for m in range(1, self.reihen + 1):
            for n in range(1, self.reihen + 1):
                mxy += (
                    -self.D_66
                    * self.matrix[m - 1][n - 1]
                    * (self.function_1x(a_sol, m) * self.function_2y(b_sol, n))
                )

        return mxy

    def SolutionPointShearForceX(self, a_sol, b_sol):
        """
        Berechnet die Querkraft Qx an einem bestimmten Punkt (a_sol, b_sol).
        """
        Qx = 0.0

        for m in range(1, self.reihen + 1):
            for n in range(1, self.reihen + 1):
                term1 = (
                    self.D_11 * self.function_1xxx(a_sol, m) * self.function_2(b_sol, n)
                )
                term2 = (
                    (self.D_12 + self.D_66)
                    * self.function_1x(a_sol, m)
                    * self.function_2yy(b_sol, n)
                )
                Qx += self.matrix[m - 1][n - 1] * (term1 + term2)

        return Qx

    def SolutionPointShearForceY(self, a_sol, b_sol):
        """
        Berechnet die Querkraft Qy an einem bestimmten Punkt (a_sol, b_sol).
        """
        Qy = 0.0

        for m in range(1, self.reihen + 1):
            for n in range(1, self.reihen + 1):
                term1 = (
                    self.D_22 * self.function_1(a_sol, m) * self.function_2yyy(b_sol, n)
                )
                term2 = (
                    (self.D_12 + self.D_66)
                    * self.function_1xx(a_sol, m)
                    * self.function_2y(b_sol, n)
                )
                Qy += self.matrix[m - 1][n - 1] * (term1 + term2)

        return Qy

    def function_1(self, x, m):
        if self.support == "hhhh":
            return np.sin(x * np.pi / self.a * m)
        elif self.support == "cccc":
            return 1 - np.cos(2 * m * np.pi * x / self.a)
        elif self.support == "hhff":

            lambda_m = (0.50 + m - 1) * np.pi
            if m == 2:
                lambda_m = 4.730041
            elif m == 3:
                lambda_m = 7.853205
            elif m == 4:
                lambda_m = 10.99561

            alpha = lambda_m / self.a

            a_j = (np.sinh(lambda_m) - np.sin(lambda_m)) / (
                np.cosh(lambda_m) - np.cos(lambda_m)
            )
            if m > 1:
                return (np.sin(alpha * x) + np.sinh(alpha * x)) / (
                    np.sin(lambda_m) - np.sinh(lambda_m)
                ) - a_j * (np.cosh(alpha * x) + np.cos(alpha * x)) / (
                    np.cos(lambda_m) - np.cosh(lambda_m)
                )
            else:
                return np.ones_like(x)
        elif self.support == "hhhf":
            lambda_m = (0.25 + m - 1) * np.pi
            if m == 2:
                lambda_m = 3.926602
            elif m == 3:
                lambda_m = 7.068582
            elif m == 4:
                lambda_m = 10.21018

            alpha = lambda_m / self.a
            if m > 1:
                return np.sin(alpha * x) + np.sinh(alpha * x) * np.sin(
                    lambda_m
                ) / np.sinh(lambda_m)
            else:
                return x / self.a
        else:
            return np.zeros_like(x)

    def function_2(self, y, n):
        if self.support == "hhhh":
            return np.sin(y * np.pi / self.b * n)
        elif self.support == "cccc":
            return 1 - np.cos(2 * n * np.pi * y / self.b)
        elif self.support == "hhff":
            return np.sin(y * np.pi / self.b * n)
        elif self.support == "hhhf":
            return np.sin(y * np.pi / self.b * n)
        else:
            return np.zeros_like(y)

    def function_1x(self, x, m):
        if self.support == "hhhh":
            return np.cos(x * np.pi / self.a * m) * np.pi / self.a * m
        elif self.support == "cccc":
            return 2 * np.pi * m * np.sin(2 * np.pi * m * x / self.a) / self.a
        elif self.support == "hhff":
            lambda_m = (0.50 + m) * np.pi
            if m == 2:
                lambda_m = 4.730041
            elif m == 3:
                lambda_m = 7.853205
            elif m == 4:
                lambda_m = 10.99561

            alpha = lambda_m / self.a
            a_j = (np.sinh(lambda_m) - np.sin(lambda_m)) / (
                np.cosh(lambda_m) - np.cos(lambda_m)
            )
            if m > 1:
                return alpha * (
                    (np.cos(alpha * x) + np.cosh(alpha * x))
                    / (np.sin(lambda_m) - np.sinh(lambda_m))
                    - a_j
                    * (np.sinh(alpha * x) - np.sin(alpha * x))
                    / (np.cos(lambda_m) - np.cosh(lambda_m))
                )
            else:
                return np.zeros_like(x)

        elif self.support == "hhhf":
            lambda_m = (0.25 + m - 1) * np.pi
            if m == 2:
                lambda_m = 3.926602
            elif m == 3:
                lambda_m = 7.068582
            elif m == 4:
                lambda_m = 10.21018

            alpha = lambda_m / self.a
            if m > 1:
                return alpha * (
                    np.cos(alpha * x)
                    + np.cosh(alpha * x) * np.sin(lambda_m) / np.sinh(lambda_m)
                )
            else:
                return 1 / self.a
        else:
            return np.zeros_like(x)

    def function_1xx(self, x, m):
        if self.support == "hhhh":
            return -np.sin(x * np.pi / self.a * m) * (np.pi / self.a * m) ** 2
        elif self.support == "cccc":
            return 4 * np.pi**2 * m**2 * np.cos(2 * np.pi * m * x / self.a) / self.a**2
        elif self.support == "hhff":
            lambda_m = (0.50 + m - 1) * np.pi
            if m == 2:
                lambda_m = 4.730041
            elif m == 3:
                lambda_m = 7.853205
            elif m == 4:
                lambda_m = 10.99561

            alpha = lambda_m / self.a
            a_j = (np.sinh(lambda_m) - np.sin(lambda_m)) / (
                np.cosh(lambda_m) - np.cos(lambda_m)
            )
            if m > 1:
                return (alpha**2) * (
                    (-np.sin(alpha * x) + np.sinh(alpha * x))
                    / (np.sin(lambda_m) - np.sinh(lambda_m))
                    - a_j
                    * (np.cosh(alpha * x) - np.cos(alpha * x))
                    / ((np.cos(lambda_m) - np.cosh(lambda_m)))
                )
            else:
                return np.zeros_like(x)

        elif self.support == "hhhf":
            lambda_m = (0.25 + m - 1) * np.pi
            if m == 2:
                lambda_m = 3.926602
            elif m == 3:
                lambda_m = 7.068582
            elif m == 4:
                lambda_m = 10.21018

            alpha = lambda_m / self.a
            if m > 1:
                return alpha**2 * (
                    -np.sin(alpha * x)
                    + np.sinh(alpha * x) * np.sin(lambda_m) / np.sinh(lambda_m)
                )
            else:
                return 0

        else:
            return np.zeros_like(x)

    def function_1xxx(self, x, m):
        if self.support == "hhhh":
            return np.cos(x * np.pi / self.a * m) * (np.pi / self.a * m) ** 3 * (-1)

        elif self.support == "cccc":
            return -8 * np.pi**3 * m**3 * np.sin(2 * np.pi * m * x / self.a) / self.a**3

        elif self.support == "hhff":
            lambda_m = (0.50 + m - 1) * np.pi
            if m == 2:
                lambda_m = 4.730041
            elif m == 3:
                lambda_m = 7.853205
            elif m == 4:
                lambda_m = 10.99561

            alpha = lambda_m / self.a
            a_j = (np.sinh(lambda_m) - np.sin(lambda_m)) / (
                np.cosh(lambda_m) - np.cos(lambda_m)
            )
            if m > 1:
                return (alpha**3) * (
                    (-np.cos(alpha * x) + np.cosh(alpha * x))
                    / (np.sin(lambda_m) - np.sinh(lambda_m))
                    - a_j
                    * (np.sinh(alpha * x) + np.sin(alpha * x))
                    / (np.cos(lambda_m) - np.cosh(lambda_m))
                )
            else:
                return np.zeros_like(x)  # Starrkörperverschiebung

        elif self.support == "hhhf":
            lambda_m = (0.25 + m - 1) * np.pi
            if m == 2:
                lambda_m = 3.926602
            elif m == 3:
                lambda_m = 7.068582
            elif m == 4:
                lambda_m = 10.21018

            alpha = lambda_m / self.a
            if m > 1:
                return alpha**3 * (
                    -np.cos(alpha * x)
                    + np.cosh(alpha * x) * np.sin(lambda_m) / np.sinh(lambda_m)
                )
            else:
                return 0
        else:
            return np.zeros_like(x)

    def function_2y(self, y, n):
        if self.support == "hhhh":
            return np.cos(y * np.pi / self.b * n) * np.pi / self.b * n
        elif self.support == "cccc":
            return 2 * np.pi * n * np.sin(2 * np.pi * n * y / self.b) / self.b
        elif self.support == "hhff":
            return 2 * np.pi * n * np.sin(2 * np.pi * n * y / self.b) / self.b
        elif self.support == "hhhf":
            return 2 * np.pi * n * np.sin(2 * np.pi * n * y / self.b) / self.b
        else:
            return np.zeros_like(x)

    def function_2yy(self, y, n):
        if self.support == "hhhh":
            return -np.sin(y * np.pi / self.b * n) * (np.pi / self.b * n) ** 2
        elif self.support == "cccc":
            return 4 * np.pi**2 * n**2 * np.cos(2 * np.pi * n * y / self.b) / self.b**2
        elif self.support == "hhff":
            return -np.sin(y * np.pi / self.b * n) * (np.pi / self.b * n) ** 2
        elif self.support == "hhhf":
            return -np.sin(y * np.pi / self.b * n) * (np.pi / self.b * n) ** 2
        else:
            return np.zeros_like(y)

    def function_2yyy(self, y, n):
        if self.support == "hhhh":
            return np.cos(y * np.pi / self.b * n) * (np.pi / self.b * n) ** 3 * (-1)
        elif self.support == "cccc":
            return -8 * np.pi**3 * n**3 * np.sin(2 * np.pi * n * y / self.b) / self.b**3
        elif self.support == "hhff":
            return np.cos(y * np.pi / self.b * n) * (np.pi / self.b * n) ** 3 * (-1)
        elif self.support == "hhhf":
            return np.cos(y * np.pi / self.b * n) * (np.pi / self.b * n) ** 3 * (-1)
        else:
            return np.zeros_like(y)

    def PlotLoad(self):
        """
        Plottet die aufgebrachte Belastung auf der Platte.
        """
        x_values = [0, self.a, self.a, 0, 0]
        y_values = [0, 0, self.b, self.b, 0]

        if self.loading == "Regular":
            rectangular_loads = [
                # [x0, x1, y0, y1]
                [self.x0, self.x0 + self.u, self.y0, self.y0 + self.v]
            ]

            for load in rectangular_loads:
                x0, x1, y0, y1 = load
                x = [x0, x1, x1, x0, x0]
                y = [y0, y0, y1, y1, y0]
                plt.plot(x, y)
        else:
            print("Else")
            for i in range(0, len(self.RectangularLoad["x0[m]"]), 1):
                x = [
                    self.RectangularLoad["x0[m]"][i],
                    self.RectangularLoad["x1[m]"][i],
                    self.RectangularLoad["x1[m]"][i],
                    self.RectangularLoad["x0[m]"][i],
                    self.RectangularLoad["x0[m]"][i],
                ]
                y = [
                    self.RectangularLoad["y0[m]"][i],
                    self.RectangularLoad["y0[m]"][i],
                    self.RectangularLoad["y1[m]"][i],
                    self.RectangularLoad["y1[m]"][i],
                    self.RectangularLoad["y0[m]"][i],
                ]

                plt.plot(x, y)

        plt.plot(x_values, y_values)
        plt.gca().set_aspect("equal", adjustable="box")
        plt.show(block=False)
        plt.pause(2)
        plt.close()

    def PlotDeflectionGrid(self, grid_size=20):
        """
        Berechnet und plottet ein Raster der Momentenverläufe.

        Args:
            grid_size (int): Anzahl der Unterteilungen in x- und y-Richtung. Standardmäßig 20.
        """
        x_values = np.linspace(0, self.a, grid_size)
        y_values = np.linspace(0, self.b, grid_size)
        self.w_values = np.zeros((grid_size, grid_size))

        for i, x in enumerate(x_values):
            for j, y in enumerate(y_values):
                self.w_values[i][j] = self.SolutionPointDisp(x, y)

        print("Max. Deflection", self.w_values.max())

        X, Y = np.meshgrid(x_values, y_values)
        fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
        surf = ax.plot_surface(
            X, Y, self.w_values, cmap=cm.coolwarm, linewidth=0, antialiased=False
        )
        ax.set_title("Deflections w in [mm]")
        plt.show(block=False)
        plt.pause(6)
        plt.close()

    def PlotMomentGrid(self, grid_size=20):
        """
        Berechnet und plottet ein Raster der Momentenverläufe.

        Args:
            grid_size (int): Anzahl der Unterteilungen in x- und y-Richtung. Standardmäßig 20.
        """
        x_values = np.linspace(0, self.a, grid_size)
        y_values = np.linspace(0, self.b, grid_size)
        self.mx_values = np.zeros((grid_size, grid_size))
        self.my_values = np.zeros((grid_size, grid_size))

        for i, x in enumerate(x_values):
            for j, y in enumerate(y_values):
                self.mx_values[i][j] = self.SolutionPointMomentx(x, y)
                self.my_values[i][j] = self.SolutionPointMomenty(x, y)

        print("Max-Moment x in [kNm]", self.mx_values.max() * 1000)
        print("Min-Moment x in [kNm]", self.mx_values.min() * 1000)
        print("Max-Moment y in [kNm]", self.my_values.max() * 1000)
        print("Min-Moment y in [kNm]", self.my_values.min() * 1000)

        X, Y = np.meshgrid(x_values, y_values)
        fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
        surf = ax.plot_surface(
            X, Y, self.mx_values, cmap=cm.coolwarm, linewidth=0, antialiased=False
        )
        ax.set_title("Moment Mx")
        plt.show(block=False)
        plt.pause(6)
        plt.close()

        fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
        surf = ax.plot_surface(
            X, Y, self.my_values, cmap=cm.coolwarm, linewidth=0, antialiased=False
        )
        ax.set_title("Moment My")
        plt.show(block=False)
        plt.pause(6)
        plt.close()

    def PlotShearForceGrid(self, grid_size=20):
        """
        Berechnet und plottet ein Raster der Querkräfte.
        """
        x_values = np.linspace(0, self.a, grid_size)
        y_values = np.linspace(0, self.b, grid_size)
        self.qx_values = np.zeros((grid_size, grid_size))
        self.qy_values = np.zeros((grid_size, grid_size))

        for i, x in enumerate(x_values):
            for j, y in enumerate(y_values):
                self.qx_values[i][j] = self.SolutionPointShearForceX(x, y)
                self.qy_values[i][j] = self.SolutionPointShearForceY(x, y)

        print("Max Qx in [kN/m]", self.qx_values.max() * 1000)
        print("Min Qx in [kN/m]", self.qx_values.min() * 1000)
        print("Max Qy in [kN/m]", self.qy_values.max() * 1000)
        print("Min Qy in [kN/m]", self.qy_values.min() * 1000)

        X, Y = np.meshgrid(x_values, y_values)
        fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
        surf = ax.plot_surface(
            X, Y, self.qx_values, cmap=cm.coolwarm, linewidth=0, antialiased=False
        )
        ax.set_title("Querkraft Qx")
        plt.show(block=False)
        plt.pause(6)
        plt.close()

        fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
        surf = ax.plot_surface(
            X, Y, self.qy_values, cmap=cm.coolwarm, linewidth=0, antialiased=False
        )
        ax.set_title("Querkraft Qy")
        plt.show(block=False)
        plt.pause(6)
        plt.close()

    def PlotTorsionalMomentGrid(self, grid_size=20):
        """
        Berechnet und plottet ein Raster der Drillmomente.
        """
        x_values = np.linspace(0, self.a, grid_size)
        y_values = np.linspace(0, self.b, grid_size)
        self.mxy_values = np.zeros((grid_size, grid_size))

        for i, x in enumerate(x_values):
            for j, y in enumerate(y_values):
                self.mxy_values[i][j] = self.SolutionPointMomentxy(x, y)

        print("Max Mxy in [kNm/m]", self.mxy_values.max() * 1000)
        print("Min Mxy in [kNm/m]", self.mxy_values.min() * 1000)

        X, Y = np.meshgrid(x_values, y_values)
        fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
        surf = ax.plot_surface(
            X, Y, self.mxy_values, cmap=cm.coolwarm, linewidth=0, antialiased=False
        )
        ax.set_title("Drillmoment Mxy")
        plt.show(block=False)
        plt.pause(6)
        plt.close()


a = 15
b = 6

Plate = PlateBendingKirchhoffClass(
    35000,
    0.30,
    a,
    b,
    1,
    0.5,
    0.5,
    0.5,
    0.5,
    0.0,
    0,
    0,
    n_inte=50,
    loading="Liste",
    support="hhhh",
    reihen=8,
)


btire = 0.37
p_tire = 120 / (4 * btire**2) / 1000

print("tire pressure [MN/m²]: ", p_tire)

# Daten als Liste von Listen
new_data = [
    ["No.", "x0[m]", "x1[m]", "y0[m]", "y1[m]", "p0[MN/m**2]"],
    [1, 3 + 2 - btire, 3 + 2 + btire, 0.5, 0.5 + 2 * btire, p_tire * 1.5],
    [2, 3 + 3.2 - btire, 3 + 3.2 + btire, 0.5, 0.5 + 2 * btire, p_tire * 1.5],
    [3, 3 + 3.2 - btire, 3 + 3.2 + btire, 2.5, 2.5 + 2 * btire, p_tire * 1.5],
    [4, 3 + 2 - btire, 3 + 2 + btire, 2.5, 2.5 + 2 * btire, p_tire * 1.5],
    [5, 0, 15, 0, 3, 6.5 / 1000 * 1.5],
    [6, 0, 15, 0, 6, 2.5 / 1000 * 1.5],
    [7, 0, 15, 0, 6, 0.35 * 25 / 1000 * 1.35],
    # [6,2-0.2,2+0.2,3.5,3.9,100/0.4**2/1000],
    # [7,3.2-0.2,3.2+0.2,3.5,3.9,100/0.4**2/1000],
    # [8,3.2-0.2,3.2+0.2,5.5,5.9,100/0.4**2/1000],
    # [9,2-0.2,2+0.2,5.5,5.9,100/0.4**2/1000],
    # [10,2-0.2,2+0.2,6.5,6.9,100/0.4**2/1000],
    # [11,3.2-0.2,3.2+0.2,6.5,6.9,100/0.4**2/1000],
    # [12,3.2-0.2,3.2+0.2,8.5,8.9,100/0.4**2/1000],
    # [13,2-0.2,2+0.2,8.5,8.9,100/0.4**2/1000]
]

# Konvertiere die Daten in ein DataFrame
df = pd.DataFrame(new_data[1:], columns=new_data[0])

# Dateipfad zur CSV-Datei
file_path = "Loading/Constant_Loading.csv"

# Schreibe das DataFrame in eine CSV-Datei
df.to_csv(file_path, index=False)


Plate.CalculateAll()

Plate.SolutionPointDisp(0.5, 0.5)
Plate.SolutionPointMomentx(0.5, 0.5)
Plate.SolutionPointMomenty(0.5, 0.5)


Plate.PlotLoad()
print("BENDING MOMENTS")
Plate.PlotMomentGrid()
print("SHEAR FORCES")
Plate.PlotShearForceGrid()
print("DRILL MOMENTS")
Plate.PlotTorsionalMomentGrid()
