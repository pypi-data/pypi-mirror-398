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


class Rope_Elements_II:
    def __init__(self):
        print("Rope elements")


class BarElements:
    def __init__(self):
        print("Bar elements")
