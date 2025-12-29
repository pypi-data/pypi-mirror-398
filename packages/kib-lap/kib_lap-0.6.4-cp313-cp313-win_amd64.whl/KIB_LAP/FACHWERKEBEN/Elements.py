# DEPENDENCIES
import copy  # Allows us to create copies of objects in memory
import math  # Math functionality
import numpy as np  # Numpy for working with arrays
import matplotlib.pyplot as plt  # Plotting functionality
import matplotlib.colors  # For colormap functionality
import ipywidgets as widgets
from glob import glob  # Allows check that file exists before import
from numpy import genfromtxt  # For importing structure data from csv
import pandas as pd


class Rope_Elements_III:
    def __init__(self, InputData):
        print("Rope elements")
        self.Inp = InputData

    def calculateTransMatrix(self, posI, posJ):
        """
        Takes in the position of node I and J and returns the transformation matrix for the member
        This will to be recalculated as the structure deflects with each iteration
        """
        T = np.zeros([2, 4])
        ix = posI[0]  # x-coord for node i
        iy = posI[1]  # y-coord for node i
        jx = posJ[0]  # x-coord for node j
        jy = posJ[1]  # y-coord for node j

        dx = jx - ix  # x-component of vector along member
        dy = jy - iy  # y-component of vector along member
        length = math.sqrt(dx**2 + dy**2)  # Magnitude of vector (length of member)

        lp = dx / length
        mp = dy / length
        lq = -mp
        mq = lp

        T = np.array([[-lp, -mp, lp, mp], [-lq, -mq, lq, mq]])

        return T

    def buildElementStiffnessMatrix(self, n, UG, TMs, lengths, P0, E, Areas):
        """
        Build element stiffness matrix based on current position and axial force
        n = member index
        UG = vector of global cumulative displacements
        """

        # Calculate 'new' positions of nodes using UG
        node_i = self.Inp.members[n][0]  # Node number for node i of this member
        node_j = self.Inp.members[n][1]  # Node number for node j of this member

        # Index of DoF for this member
        ia = 2 * node_i - 2  # horizontal DoF at node i of this member
        ib = 2 * node_i - 1  # vertical DoF at node i of this member
        ja = 2 * node_j - 2  # horizontal DoF at node j of this member
        jb = 2 * node_j - 1  # vertical DoF at node j of this member

        # Displacements
        d_ix = UG[ia, 0]
        d_iy = UG[ib, 0]
        d_jx = UG[ja, 0]
        d_jy = UG[jb, 0]

        # Extract current version of transformation matrix [T]
        TM = TMs[n, :, :]

        # Calculate local displacements [u, v, w] using global cumulative displacements UG
        localDisp = np.matmul(TM, np.array([[d_ix, d_iy, d_jx, d_jy]]).T)
        u = localDisp[0].item()
        v = localDisp[1].item()

        # Calculate extension, e
        Lo = lengths[n]
        e = math.sqrt((Lo + u) ** 2 + v**2) - Lo

        # Calculate matrix [AA]
        a1 = (Lo + u) / (Lo + e)
        a2 = v / (Lo + e)
        AA = np.array([[a1, a2]])

        # Calculate axial load, P

        P = P0[n] + (E[n] * Areas[n] / Lo) * e

        # Calculate matrix [d]
        d11 = P * v**2
        d12 = -P * v * (Lo + u)
        d21 = -P * v * (Lo + u)
        d22 = P * (Lo + u) ** 2
        denominator = (Lo + e) ** 3

        d = (1 / denominator) * np.array([[d11, d12], [d21, d22]])

        # Calculate element stiffness matrix

        NL = np.matrix((AA.T * (E[n] * Areas[n] / Lo) * AA) + d)
        k = TM.T * NL * TM

        # Return element stiffness matrix in quadrants
        K11 = k[0:2, 0:2]
        K12 = k[0:2, 2:4]
        K21 = k[2:4, 0:2]
        K22 = k[2:4, 2:4]

        return [K11, K12, K21, K22]


import numpy as np
import math


class BarElements_I:
    """
    2D Bar/Truss element (Theorie I. Ordnung, small displacement).
    2 DOF per node: ux, uy

    - Uses UNDEFORMED geometry for transformation and stiffness (linear).
    - Optional initial axial force P0 can be included in member force reporting,
      but is NOT used as geometric stiffness here (Theorie I. Ordnung).
    """

    def __init__(self, InputData):
        self.Inp = InputData

        # Precompute direction cosines + lengths from undeformed geometry (constant)
        self.L0 = np.zeros(len(self.Inp.members), dtype=float)
        self.c  = np.zeros(len(self.Inp.members), dtype=float)
        self.s  = np.zeros(len(self.Inp.members), dtype=float)

        for n, (ni, nj) in enumerate(self.Inp.members):
            ix, iy = self.Inp.nodes[ni - 1, 0], self.Inp.nodes[ni - 1, 1]
            jx, jy = self.Inp.nodes[nj - 1, 0], self.Inp.nodes[nj - 1, 1]
            dx, dy = (jx - ix), (jy - iy)
            L = math.sqrt(dx * dx + dy * dy)
            if L == 0.0:
                raise ValueError(f"Bar element has zero length at member index {n} (nodes {ni}-{nj})")

            self.L0[n] = L
            self.c[n]  = dx / L
            self.s[n]  = dy / L

    def buildElementStiffnessMatrix(self, n, UG, TMs_unused, lengths_unused, P0, E, Areas):
        """
        Returns [K11, K12, K21, K22] (each 2x2) in GLOBAL coordinates.
        """
        L  = self.L0[n]
        EA = E[n] * Areas[n]
        k0 = EA / L

        c = self.c[n]
        s = self.s[n]

        # 4x4 global stiffness for 2D truss
        k = k0 * np.array([
            [ c*c,  c*s, -c*c, -c*s],
            [ c*s,  s*s, -c*s, -s*s],
            [-c*c, -c*s,  c*c,  c*s],
            [-c*s, -s*s,  c*s,  s*s]
        ], dtype=float)

        K11 = k[0:2, 0:2]
        K12 = k[0:2, 2:4]
        K21 = k[2:4, 0:2]
        K22 = k[2:4, 2:4]
        return [K11, K12, K21, K22]

    def axial_force(self, n, UG, E, Areas, P0=None):
        """
        Member axial force (tension +) from SMALL displacement theory:
            N = (EA/L) * ( [-c -s c s] * u_e )
        Optionally + P0[n] if you want to report pretension as part of N.
        """
        ni, nj = self.Inp.members[n]
        ia, ib = 2 * ni - 2, 2 * ni - 1
        ja, jb = 2 * nj - 2, 2 * nj - 1

        ue = np.array([UG[ia, 0], UG[ib, 0], UG[ja, 0], UG[jb, 0]], dtype=float)

        c = self.c[n]
        s = self.s[n]
        L = self.L0[n]
        EA = E[n] * Areas[n]

        N = (EA / L) * (-c * ue[0] - s * ue[1] + c * ue[2] + s * ue[3])

        if P0 is not None:
            N = N + float(P0[n])
        return float(N)

    def internal_nodal_forces_global(self, n, UG, E, Areas, P0=None):
        """
        Equivalent internal nodal force vector (4x1) in global coords:
            f_int_e = N * [-c, -s, c, s]^T
        """
        c = self.c[n]
        s = self.s[n]
        N = self.axial_force(n, UG, E, Areas, P0=P0)

        f = N * np.array([[-c], [-s], [c], [s]], dtype=float)
        return f



class Rope_Elements_II:
    def __init__(self):
        print("Rope elements")


