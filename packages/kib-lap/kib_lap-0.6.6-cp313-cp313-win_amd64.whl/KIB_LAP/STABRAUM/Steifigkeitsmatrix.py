import sympy as sp
import numpy as np
import math

class ElemStema:
    def __init__(self):

        # Initialisierung der Steifigkeitsmatrix
        self.Ke = np.zeros((14, 14))

    def TransformationMatrix(self, posI, posJ):
        Pi = np.asarray(posI, dtype=float).reshape(3,)
        Pj = np.asarray(posJ, dtype=float).reshape(3,)

        v = Pj - Pi
        L = np.linalg.norm(v)

        T = np.zeros((14, 14), dtype=float)

        # identische Knoten
        if L < 1e-12:
            np.fill_diagonal(T, 1.0)
            return T

        # lokale x-Achse
        ex = v / L

        # robuste Referenzachse wählen (nicht parallel zu ex)
        g = np.array([0.0, 1.0, 0.0], dtype=float)  # bevorzugt global y
        if abs(np.dot(ex, g)) > 0.95:
            g = np.array([0.0, 0.0, 1.0], dtype=float)  # sonst global z
            if abs(np.dot(ex, g)) > 0.95:
                g = np.array([1.0, 0.0, 0.0], dtype=float)  # zur Not global x

        # --- Stabiler Aufbau: erst ey als Projektion von g orthogonal zu ex ---
        ey = g - np.dot(g, ex) * ex
        ney = np.linalg.norm(ey)
        if ney < 1e-12:
            raise ValueError("Degeneriertes lokales Achsensystem (ey ~ 0).")
        ey = ey / ney

        # --- Rechtshändiges System erzwingen ---
        ez = np.cross(ex, ey)
        nez = np.linalg.norm(ez)
        if nez < 1e-12:
            raise ValueError("Degeneriertes lokales Achsensystem (ez ~ 0).")
        ez = ez / nez

        # Optional: Flip-Schutz (ey soll möglichst in Richtung g zeigen)
        # verhindert, dass bei ähnlichen Elementen ey/ez um 180° springen
        if np.dot(ey, g) < 0.0:
            ey *= -1.0
            ez *= -1.0

        # R: local -> global (Spalten sind ex, ey, ez)
        R = np.column_stack((ex, ey, ez))

        # ---- 6x6 Transformationsblock passend zu deiner DOF-Reihenfolge ----
        Ti = np.zeros((6, 6), dtype=float)

        # translations: [ux, uy, uz] sitzen auf [0,1,3]
        trans = [0, 1, 3]
        # rotations: [rx, ry, rz] sitzen auf [5,4,2]
        rot = [5, 4, 2]

        Ti[np.ix_(trans, trans)] = R
        Ti[np.ix_(rot,  rot )]  = R

        # In 14x14 einbauen (Knoten a: 0..6, Knoten b: 7..13)
        T[0:6, 0:6]   = Ti
        T[7:13, 7:13] = Ti

        # Warping
        T[6, 6] = 1.0
        T[13, 13] = 1.0

        # Debug-Sanity
        if not np.isfinite(T).all():
            print("TM NaN/Inf:", posI, posJ)
            print(T)
            raise ValueError("TM enthält NaN/Inf")

        return T

    
    
    def insert_elements(self, S, E, G, A, I_y, I_z, I_omega, I_T, cv, z1, cw, z2, c_thet, l):
        """
        Element-Stiffness-Matrix:
        Na
        Vya
        Mza
        Vza
        Mya
        Mxa
        Mwa
        Nb
        Vyb
        Mzb
        Vzb
        Myb
        Mxb
        Mwb
        """
        self.Ke[:, :] = 0.0
        self.S = S  # Stiffness of shear field

        self.E = E  # Material stiffness of the beam
        self.G = G

        self.A = A
        self.I_y = I_y
        self.I_z = I_z

        self.I_omega = I_omega
        self.I_T = I_T

        self.cv = cv
        self.z1 = z1
        self.cw = cw
        self.z2 = z2

        self.c_thet = c_thet

        self.l = l
        # Matrixeinträge gemäß Tabelle definieren
        self.Ke[0, 0] = self.Ke[7, 7] = self.E * self.A / self.l
        self.Ke[0, 7] = self.Ke[7, 0] = -self.E * self.A / self.l

        self.Ke[1, 1] = self.Ke[8, 8] = (
            12 * self.E * self.I_z / self.l**3 + 13 / 35 * self.cv * self.l + 1.2 * self.S / self.l
        )
        self.Ke[1, 2] = 6 * self.E * self.I_z / self.l**2   + 11 / 210 * self.cv * self.l**2 + 0.1 * self.S

        self.Ke[1, 5] = 13 / 35 * self.cv * self.l * self.z1 - 1.2 * self.S / self.l * self.z2
        self.Ke[1, 6] = -11 / 210 * self.cv * self.l**2 * self.z1 + 0.1 * self.S * self.z2

        self.Ke[1, 8] = -12 * self.E * self.I_z / self.l**3 + 9 / 70 * self.cv * self.l - 1.2 * self.S / self.l
        self.Ke[1, 9] = 6 * self.E * self.I_z / self.l**2 - 13 / 420 * self.cv * self.l**2 + 0.1 * self.S

        self.Ke[1, 12] = 9 / 70 * self.cv * self.l * self.z1 + 1.2 * self.S / self.l * self.z2
        self.Ke[1, 13] = 13 / 420 * self.cv * self.l**2 * z1 + 0.1 * self.S * self.z2

        self.Ke[2, 2] = 4 * self.E * self.I_z / self.l + 1 / 105 * self.cv * self.l**3 + 2 / 15 * self.S * self.l
        self.Ke[9, 9] = self.Ke[2, 2]

        self.Ke[2, 5] = 11 / 210 * self.cv * l**2 * self.z1 - 0.1 * self.S * self.z2
        self.Ke[2, 6] = -1 / 105 * self.cv * self.l**3 * self.z1 + 2 / 15 * self.S * self.l * self.z2
        self.Ke[2, 8] = -6 * self.E * self.I_z / self.l**2 + 13 / 420 * self.cv * l**2 - 0.1 * self.S

        self.Ke[2, 9] = 2 * self.E * self.I_z / self.l - 1 / 140 * self.cv * self.l**3 - 1 / 30 * self.S * self.l
        self.Ke[2, 12] = 13 / 420 * self.cv * self.l**2 * self.z1 + 0.1 * self.S * self.z2
        self.Ke[2, 13] = 1 / 140 * self.cv * self.l**3 * self.z1 - 1 / 30 * self.S * self.l * self.z2

        self.Ke[3, 3] = 12 * self.E * self.I_y / self.l**3 + 13 / 35 * self.cw * self.l
        self.Ke[10, 10] = self.Ke[3, 3]

        self.Ke[3, 4] = -6 * self.E * self.I_y / self.l**2 - 11 / 210 * self.cw * self.l**2
        self.Ke[3, 10] = -12 * self.E * self.I_y / self.l**3 + 9 / 70 * self.cw * self.l
        self.Ke[3, 11] = -6 * self.E * self.I_y / self.l**2 + 13 / 420 * self.cw * self.l**2

        self.Ke[4, 4] = 4 * self.E * self.I_y / self.l + 1 / 105 * self.cw * self.l**3
        self.Ke[11, 11] = self.Ke[4, 4]

        self.Ke[4, 10] = 6 * self.E * self.I_y / self.l**2 - 13 / 420 * self.cw * self.l**2
        self.Ke[4, 11] = 2 * self.E * self.I_y / self.l - 1 / 140 * self.cw * self.l**3

        self.Ke[5, 5] = self.Ke[12, 12] = (
            12 * self.E * self.I_omega / self.l**3
            + 1.2 * self.G * self.I_T / self.l
            + 13 / 35 * self.c_thet * self.l
            + 13 / 35 * self.cv * self.l * self.z1**2
            + 1.2 * self.S / self.l * self.z2**2
        )
        self.Ke[5, 6] = (
            -6 * self.E * self.I_omega / self.l**2
            - 0.1 * self.G * self.I_T
            - 11 / 210 * self.c_thet * self.l**2
            - 11 / 210 * self.cv * self.l**2 * self.z1**2
            - 0.1 * self.S * self.z2**2
        )
        self.Ke[5, 8] = 9 / 70 * self.cv * l * self.z1 + 1.2 * self.S / self.l * self.z2
        self.Ke[5, 9] = -13 / 420 * self.cv * self.l * self.z1 - 0.1 * self.S * self.z2
        self.Ke[5, 12] = (
            -12 * self.E * self.I_omega / self.l**3
            - 1.2 * self.G * self.I_T / self.l
            + 9 / 70 * self.c_thet * self.l
            + 9 / 70 * self.cv * self.l * self.z1**2
            - 1.2 * self.S / self.l * self.z2**2
        )
        self.Ke[5, 13] = (
            -6 * self.E * self.I_omega / self.l**2
            - 0.1 * self.G * self.I_T
            + 13 / 420 * self.c_thet * self.l**2
            + 13 / 420 * self.cv * self.l**2 * self.z1**2
            - 0.1 * self.S * self.z2**2
        )
        self.Ke[6, 6] = self.Ke[13, 13] = (
            4 * self.E * self.I_omega / self.l
            + 2 / 15 * self.G * self.I_T * self.l
            + 1 / 105 * self.c_thet * self.l**3
            + 1 / 105 * self.cv * self.l**3 * self.z1
            + 2 / 15 * self.S * self.l * self.z2**2
        )

        self.Ke[6, 8] = -13 / 420 * self.cv * self.l**2 * self.z1 - 0.1 * self.S * self.z2
        self.Ke[6, 9] = 1 / 140 * self.cv * self.l**3 * self.z1 - 1 / 30 * self.S * self.l * self.z2
        self.Ke[6, 12] = (
            6 * self.E * self.I_omega / self.l**2
            + 0.1 * self.G * self.I_T
            - 13 / 420 * self.c_thet * self.l**2
            - 13 / 420 * self.cv * self.l**2 * self.z1**2
            + 0.1 * self.S * self.z2**2
        )
        self.Ke[6, 13] = (
            2 * self.E * self.I_omega / self.l
            - 1 / 30 * self.G * self.I_T * self.l
            - 1 / 140 * self.c_thet * self.l**3
            - 1 / 140 * self.cv * l**3 * self.z1**2
            - 1 / 30 * self.S * self.l * self.z2**2
        )
        self.Ke[8, 9] = -6 * self.E * self.I_z / self.l**2 - 11 / 210 * self.cv * self.l**2 - 0.1 * self.S
        self.Ke[8, 12] = 13 / 35 * self.cv * self.l * self.z1 - 1.2 * self.S / self.l * self.z2
        self.Ke[8, 13] = 11 / 210 * self.cv * self.l**2 * self.z1 - 0.1 * self.S * self.z2
        self.Ke[9, 12] = -11 / 210 * self.cv * self.l**2 * self.z1 + 0.1 * self.S * self.z2
        self.Ke[9, 13] = -1 / 105 * self.cv * self.l**3 * z1 + 2 / 15 * self.S * self.l * self.z2
        self.Ke[10, 11] = 6 * E * I_y / l**2 + 11 / 210 * cw * l**2
        self.Ke[12, 13] = (
            6 * E * I_omega / l**2
            + 0.1 * G * I_T
            + 11 / 210 * c_thet * l**2
            + 11 / 210 * cv * l**2 * z1**2
            + 0.1 * S * z2**2
        )

        # Elem Matrix is symmetrical

        for i in range(14):
            for j in range(i):
                self.Ke[i, j] = self.Ke[j, i]

        return self.Ke

    def print_elem_matrix(self):
        sp.pprint(self.Ke)
