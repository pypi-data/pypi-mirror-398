import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import cg
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.widgets import Slider

try:
    from Element_Stiffness import Stiffness_Matrix
    from Meshing import MeshingClass
except:
    from KIB_LAP.Scheibe.Element_Stiffness import Stiffness_Matrix
    from KIB_LAP.Scheibe.Meshing import MeshingClass
    
import pandas as pd
from tabulate import *


class Assembled_Matrices:
    def __init__(
        self,
        _mesh,
        EL,
        NL,
        EL_Matrices,
        _ElementLoadVector,
        _ElementLoadVectorNodes,
        _ElementLoadVectorAreaLoads,
        _ElementLoadVectorAreaLoadsNodes,
        load_input="csv",
        bc_input="csv",
    ):
        # Meshing
        self.mesh = _mesh

        self.EL = EL
        self.NL = NL
        # Generate element stiffness matrices
        self.ElementLoadVector = _ElementLoadVector
        self.ElementLoadVectorNodes = _ElementLoadVectorNodes
        self.ElementLoadVectorAreaLoads = _ElementLoadVectorAreaLoads
        self.ElementLoadVectorAreaLoadsNodes = _ElementLoadVectorAreaLoadsNodes
        #  Assemble Stiffness matrices
        self._EL = np.array(EL)
        self._NoE = self._EL.shape[0]
        self._NPE = self._EL.shape[1]
        self.NoN = len(NL)
        self.PD = len(NL[0])
        self._EL_Matrices = np.array(EL_Matrices)
        self.load_input = load_input
        self.bc_input = bc_input

        self.K_Assemble = np.zeros((self.NoN * self.PD, self.NoN * self.PD))
        self.K_Assemble_BC = None
        self.Index_Vector_BC = []

    def assemble_K(self):
        for i in range(self._NoE):
            Index_Vector = np.zeros(self._NPE * 2, dtype=int)
            for j in range(self._NPE):
                Index_Vector[j] = int(self._EL[i, j] * 2 - 2)
                Index_Vector[j + self._NPE] = int(self._EL[i, j] * 2 - 1)

            for row in range(len(Index_Vector)):
                ind_row = Index_Vector[row]
                for col in range(len(Index_Vector)):
                    ind_col = Index_Vector[col]
                    self.K_Assemble[ind_row, ind_col] += self._EL_Matrices[i][row][col]

    def Load_BC(self):
        if self.bc_input == "console":
            # Implementieren Sie hier die Konsoleneingabe
            pass
        else:
            try:
                self.BC = pd.DataFrame(
                    pd.read_csv("Boundary_Conditions/Spring_Elements.csv")
                )
            except:
                """
                This exception is used, if the main file is started from a subfolder (e.g. the parametric studies or testing) \n
                folder \n
                """
                self.BC = pd.DataFrame(
                    pd.read_csv("../Boundary_Conditions/Spring_Elements.csv")
                )

    def apply_BC(self):
        self.K_Assemble_BC = np.copy(self.K_Assemble)
        self.Index_Vector_BC = np.zeros(0, dtype=int)
        self.stiffness_spring = []

        for i in range(len(self.BC["No"])):
            node = self.BC["No"][i]
            dof = self.BC["DOF"][i]
            stiffness = self.BC["cf in [MN/m]"][i]
            print("Stiffness ", stiffness)
            print(node)
            # Überprüfen, ob der Knoten ein numerischer Wert ist
            if str(node).isdigit():
                node = int(node)
                if dof == "x":
                    self.Index_Vector_BC = np.append(self.Index_Vector_BC, (node - 1) * 2)
                elif dof == "z":
                    self.Index_Vector_BC = np.append(self.Index_Vector_BC, (node - 1) * 2 + 1)
            elif node == "left":
                nodes = self.mesh.get_left_border_nodes()
                print("LEFT DOF")
                print(dof)
                for p in nodes:
                    if dof == "x":
                        self.Index_Vector_BC = np.append(self.Index_Vector_BC, (p - 1) * 2)
                    elif dof == "z":
                        self.Index_Vector_BC = np.append(self.Index_Vector_BC, (p - 1) * 2 + 1)
                    else:
                        print("Exception. No valid coordinate input for the left boundary.")
            elif node == "right":
                nodes = self.mesh.get_right_border_nodes()
                for p in nodes:
                    if dof == "x":
                        self.Index_Vector_BC = np.append(self.Index_Vector_BC, (p - 1) * 2)
                    elif dof == "z":
                        self.Index_Vector_BC = np.append(self.Index_Vector_BC, (p - 1) * 2 + 1)
                    else:
                        print("Exception. No valid coordinate input for the right boundary.")
            else:
                print("The input isn't usable! Please change the DOF of the boundary condition at Position "
                    + str(i + 1) + "\n")
            
            try:
                self.stiffness_spring.append(stiffness)
            except:
                print("Error with the spring stiffness")

        self.Index_Vector_BC = sorted(self.Index_Vector_BC)

        p = 0
        for index in sorted(self.Index_Vector_BC, reverse=True):
            self.K_Assemble_BC[index][index] += self.stiffness_spring[p]
            p+=1

        print(self.Index_Vector_BC)

    def LoadInput(self):
        self.Einzellasten = False
        self.Linienlasten = False
        if self.load_input == "console":
            # Implementieren Sie hier die Konsoleneingabe
            pass
        else:
            try:
                self.NodalForces = pd.DataFrame(pd.read_csv("Loading/Nodal_Loads.csv"))
                self.ElementLoads = pd.DataFrame(
                    pd.read_csv("Loading/Element_Loads.csv")
                )
            except:
                self.NodalForces = pd.DataFrame(
                    pd.read_csv("../Loading/Nodal_Loads.csv")
                )
                self.ElementLoads = pd.DataFrame(
                    pd.read_csv("../Loading/Element_Loads.csv")
                )

    def GenerateLoadVector(self):
        self.Load_Vector = np.zeros(len(self.K_Assemble_BC))

        for i in range(0, len(self.NodalForces["DOF"])):
            if self.NodalForces["DOF"][i] == "x":
                index_load = (self.NodalForces["No"][i] - 1) * 2  # x-Direction
                self.Load_Vector[index_load] = self.NodalForces["F in [MN]"][i]
            elif self.NodalForces["DOF"][i] == "z":
                index_load = (self.NodalForces["No"][i] - 1) * 2 + 1  # z-Direction
                self.Load_Vector[index_load] = self.NodalForces["F in [MN]"][i]

            else:
                print(
                    "The input isn't usable! Please change the DOF of the boundary condition at Position "
                    + i
                    + 1
                    + "\n"
                )

        for i in range(0, len(self.ElementLoadVectorNodes)):
            index_load_x = int((self.ElementLoadVectorNodes[i] - 1) * 2)
            index_load_z = int((self.ElementLoadVectorNodes[i] - 1) * 2 + 1)

            self.Load_Vector[index_load_x] += self.ElementLoadVector[0][i]
            self.Load_Vector[index_load_z] += self.ElementLoadVector[1][i]

        for i in range(0, len(self.ElementLoadVectorAreaLoadsNodes), 1):
            p = 0
            for j in range(0, len(self.ElementLoadVectorAreaLoadsNodes[i]), 1):
                index_load_x = int((self.ElementLoadVectorAreaLoadsNodes[i][j] - 1) * 2)
                index_load_z = int(
                    (self.ElementLoadVectorAreaLoadsNodes[i][j] - 1) * 2 + 1
                )

                self.Load_Vector[index_load_x] += self.ElementLoadVectorAreaLoads[
                    p * 2
                ][i]
                self.Load_Vector[index_load_z] += self.ElementLoadVectorAreaLoads[
                    p * 2 + 1
                ][i]

                p += 1

    def get_assembled(self):
        return self.K_Assemble

    def get_assembled_BC(self):
        return self.K_Assemble_BC

    def Solve(self):
        if len(self.K_Assemble) < 20:
            self.x_reduced = np.linalg.solve(self.K_Assemble_BC, self.Load_Vector)
        else:
            self.x_reduced, sparse_info = cg(self.K_Assemble_BC, self.Load_Vector)
            print("Information about sparse solver ")
            sparse_info

        self.x_disp = self.x_reduced[::2]
        self.z_disp = self.x_reduced[1::2]

    def StoreElementDisplacements(self):
        self.disp_element_matrix = np.zeros((8, self._NoE))
        for row in range(0, len(self.EL), 1):
            p = 0
            for col in range(0, len(self.EL[0]), 1):
                index_x = int((self.EL[row][col] - 1) * 2)
                index_z = int((self.EL[row][col] - 1) * 2 + 1)

                disp_x = self.x_reduced[index_x]
                disp_z = self.x_reduced[index_z]

                self.disp_element_matrix[p * 2][row] = disp_x
                self.disp_element_matrix[p * 2 + 1][row] = disp_z

                p += 1


    def __str__(self):
        output = "Assembled stiffness matrix\n"
        output += tabulate(self.K_Assemble) + "\n"
        output += "Assembled stiffness matrix with boundary conditions\n"
        output += tabulate(self.K_Assemble_BC)
        return output
