import numpy as np
import pandas as pd
from tabulate import *


class Linear_Algebra_Class:
    def matrix_transpose_symmetric(self, matrix, result=None):
        return np.transpose(matrix)

    def matrix_multiplication(self, mat1, mat2):
        return np.matmul(mat1, mat2)


class Gaucho_Method:
    def __init__(self, J):
        self.J = J
        self.det_J = None
        self.J_inv = None

    def ldl_decomposition(self):
        self.L = np.linalg.cholesky(self.J)
        self.D = np.diag(np.diag(self.L))
        self.L = self.L / np.sqrt(np.diag(self.L))[:, None]

    def calculate_inverse_gaucho(self):
        self.J_inv = np.linalg.inv(self.J)
        return self.J_inv

    def calculate_determinant_gaucho(self):
        self.det_J = np.linalg.det(self.J)
        return self.det_J


class Stiffness_Matrix:
    def __init__(self, coords, E, nu, t, gamma, _mesh=None):
        self._coords = np.array(coords)
        self._E = E
        self._nu = nu
        self._t = t
        self._gamma = gamma

        self._coords_T = np.transpose(self._coords)
        self.K = np.zeros((len(coords), len(coords)))
        self.K_ij = np.zeros((len(coords[0]), len(coords[0])))
        self.J = np.zeros((len(coords[0]), len(coords[0])))
        self.J_inv = np.zeros((len(coords[0]), len(coords[0])))

        self.grad = np.zeros((len(coords[0]), len(coords)))
        self.result_grad = np.zeros((len(coords[0]), len(coords)))
        self.result_grad_T = np.zeros((len(coords), len(coords[0])))

        self._NPE = len(coords)
        self._PD = len(coords[0])
        self._GPE = 4  # 4 GP for rectangular, 3 for triangular

        # Gaussian integration
        self.xi, self.eta, self.alpha = 0, 0, 0

        # Material parameters
        self.delta = 0
        self.C = 0
        self.det_J = 0

        # Friends
        self.lin_al = Linear_Algebra_Class()
        self.gaucho_ptr = None

        self.mesh_data = _mesh

    def gauss_points(self, gp):
        sqrt3_inv = 1 / np.sqrt(3)
        gauss_points = [
            (-sqrt3_inv, -sqrt3_inv, 1),
            (sqrt3_inv, -sqrt3_inv, 1),
            (sqrt3_inv, sqrt3_inv, 1),
            (-sqrt3_inv, sqrt3_inv, 1),
        ]
        if self._GPE == 4:
            self.xi, self.eta, self.alpha = gauss_points[gp - 1]

    def stiffness(self):
        self.K = np.zeros((self._NPE * self._PD, self._NPE * self._PD))
        self.det_J_store = np.zeros((2, 2))

        self._coords_T = self.lin_al.matrix_transpose_symmetric(self._coords)

        for i in range(self._NPE):
            for j in range(self._NPE):
                for gp in range(1, self._GPE + 1):
                    self.gauss_points(gp)
                    self.grad_N_nat()
                    self.J = self.lin_al.matrix_multiplication(
                        self._coords_T, self.result_grad_T
                    )
                    self.gaucho_ptr = Gaucho_Method(self.J)

                    self.gaucho_ptr.ldl_decomposition()
                    self.J_inv = self.gaucho_ptr.calculate_inverse_gaucho()
                    self.det_J = self.gaucho_ptr.calculate_determinant_gaucho()

                    self.grad = self.lin_al.matrix_multiplication(  # Transformed B-Matrix (Isoparametric)
                        self.J_inv, self.result_grad
                    )

                    for a in range(self._PD):
                        for b in range(self._PD):
                            for c in range(self._PD):
                                for d in range(self._PD):
                                    self.K[a * self._NPE + i, c * self._NPE + j] += (
                                        self.grad[b, i]
                                        * self.constitutive(a + 1, b + 1, c + 1, d + 1)
                                        * self.grad[d, j]
                                        * self.det_J
                                        * self.alpha
                                        * self._t
                                    )

    def grad_N_nat(self):
        self.result_grad = np.zeros((self._PD, self._NPE))
        self.result_grad_T = np.zeros((self._NPE, self._PD))

        if self._NPE == 3:
            self.result_grad[0][0] = 1
            self.result_grad[0][1] = 0
            self.result_grad[0][2] = -1

            self.result_grad[1][0] = 0
            self.result_grad[1][1] = 1
            self.result_grad[1][2] = -1

        if self._NPE == 4:
            self.result_grad[0][0] = -0.25 * (1 - self.eta)
            self.result_grad[0][1] = 0.25 * (1 - self.eta)
            self.result_grad[0][2] = 0.25 * (1 + self.eta)
            self.result_grad[0][3] = -0.25 * (1 + self.eta)

            self.result_grad[1][0] = -0.25 * (1 - self.xi)
            self.result_grad[1][1] = -0.25 * (1 + self.xi)
            self.result_grad[1][2] = 0.25 * (1 + self.xi)
            self.result_grad[1][3] = 0.25 * (1 - self.xi)

        self.result_grad_T = self.lin_al.matrix_transpose_symmetric(self.result_grad)

    def N_nat(self, xi, eta):
        self.result_N = np.zeros((2, 8))
        self.result_N_T = np.zeros((8, 2))

        if self._NPE == 4:
            self.result_N[0][0] = 0.25 * (1 - eta) * (1 - xi)
            self.result_N[0][2] = 0.25 * (1 - eta) * (1 + xi)
            self.result_N[0][4] = 0.25 * (1 + eta) * (1 + xi)
            self.result_N[0][6] = 0.25 * (1 + eta) * (1 - xi)

            self.result_N[1][1] = 0.25 * (1 - eta) * (1 - xi)
            self.result_N[1][3] = 0.25 * (1 - eta) * (1 + xi)
            self.result_N[1][5] = 0.25 * (1 + eta) * (1 + xi)
            self.result_N[1][7] = 0.25 * (1 + eta) * (1 - xi)

        self.result_N_T = self.lin_al.matrix_transpose_symmetric(self.result_N)

    def delta_func(self, i, j):
        return 1 if i == j else 0

    def constitutive(self, i, j, k, l):
        return (self._E / (2 * (1 + self._nu))) * (
            self.delta_func(i, l) * self.delta_func(j, k)
            + self.delta_func(i, k) * self.delta_func(j, l)
        ) + (self._E * self._nu) / (1 - self._nu**2) * self.delta_func(
            i, j
        ) * self.delta_func(
            k, l
        )

    def element_load_vector(self):
        try:
            self.loading_table = pd.DataFrame(pd.read_csv("Loading/Element_Loads.csv"))
        except:
            self.loading_table = pd.DataFrame(
                pd.read_csv("../Loading/Element_Loads.csv")
            )

        self.element_loading_vec = np.zeros(8)

        for i in self.loading_table["type"]:
            if i == "top":
                self.loading_nodes = self.mesh_data.get_top_border_nodes()
                self.node_loading_vec = np.zeros(
                    (2, int(len(self.loading_nodes) - 1) * 2)
                )
                self.node_store_vec = np.zeros(int((len(self.loading_nodes) - 1) * 2))

                for p in range(0, len(self.loading_nodes) - 1):
                    npa = self.loading_nodes[p]
                    npe = self.loading_nodes[p + 1]

                    self.node_store_vec[p * 2] = npa
                    self.node_store_vec[p * 2 + 1] = npe

                    x_npa = self.mesh_data.get_coordinate_x(npa)
                    z_npa = self.mesh_data.get_coordinate_z(npa)
                    x_npe = self.mesh_data.get_coordinate_x(npe)
                    z_npe = self.mesh_data.get_coordinate_z(npa)

                    l_x = abs(x_npe - x_npa)
                    l_z = abs(z_npe - z_npa)

                    px = self.loading_table[self.loading_table["type"] == "top"][
                        "px"
                    ].values
                    pz = self.loading_table[self.loading_table["type"] == "top"][
                        "pz"
                    ].values

                    # Numerical integration of the load vector at each node with an loadings

                    eta = 1  # At the top boundary, the eta value is 1 for all loops
                    WP = 1  # Numerical integration with 2 Gauss Points
                    for x in range(0, 2, 1):
                        xi = -1 / np.sqrt(3) + 1 / np.sqrt(3) * 2 * x
                        self.N_nat(xi, eta)

                        self.p_a_x = (
                            self.result_N[0][6] * px
                        )  # The beginning node is always form-function N4
                        self.p_a_z = self.result_N[1][7] * pz
                        self.p_e_x = self.result_N[0][4] * px
                        self.p_e_z = self.result_N[1][5] * pz

                        self.node_loading_vec[0][p * 2] += self.p_a_x * l_x / 2
                        self.node_loading_vec[1][p * 2] += self.p_a_z * l_x / 2

                        self.node_loading_vec[0][p * 2 + 1] += self.p_e_x * l_x / 2
                        self.node_loading_vec[1][p * 2 + 1] += self.p_e_z * l_x / 2
            elif i == "bottom":
                self.loading_nodes = self.mesh_data.get_bottom_border_nodes()
                self.node_loading_vec = np.zeros(
                    (2, int(len(self.loading_nodes) - 1) * 2)
                )
                self.node_store_vec = np.zeros(int((len(self.loading_nodes) - 1) * 2))

                for p in range(0, len(self.loading_nodes) - 1):
                    npa = self.loading_nodes[p]
                    npe = self.loading_nodes[p + 1]

                    self.node_store_vec[p * 2] = npa
                    self.node_store_vec[p * 2 + 1] = npe

                    x_npa = self.mesh_data.get_coordinate_x(npa)
                    z_npa = self.mesh_data.get_coordinate_z(npa)
                    x_npe = self.mesh_data.get_coordinate_x(npe)
                    z_npe = self.mesh_data.get_coordinate_z(npa)

                    l_x = abs(x_npe - x_npa)
                    l_z = abs(z_npe - z_npa)

                    px = self.loading_table[self.loading_table["type"] == "bottom"][
                        "px"
                    ].values
                    pz = self.loading_table[self.loading_table["type"] == "bottom"][
                        "pz"
                    ].values

                    # Numerical integration of the load vector at each node with an loadings

                    eta = 1  # At the top boundary, the eta value is 1 for all loops
                    WP = 1  # Numerical integration with 2 Gauss Points
                    for x in range(0, 2, 1):
                        xi = -1 / np.sqrt(3) + 1 / np.sqrt(3) * 2 * x
                        self.N_nat(xi, eta)

                        self.p_a_x = (
                            self.result_N[0][6] * px
                        )  # The beginning node is always form-function N4
                        self.p_a_z = self.result_N[1][7] * pz
                        self.p_e_x = self.result_N[0][4] * px
                        self.p_e_z = self.result_N[1][5] * pz

                        self.node_loading_vec[0][p * 2] += self.p_a_x * l_x / 2
                        self.node_loading_vec[1][p * 2] += self.p_a_z * l_x / 2

                        self.node_loading_vec[0][p * 2 + 1] += self.p_e_x * l_x / 2
                        self.node_loading_vec[1][p * 2 + 1] += self.p_e_z * l_x / 2

           

            if i == "selfweight":
                """_summary_

                Note on the Jacobian: The Determinant is needed before the element load vector \n
                from self weight can be calculated. Because it remains constant for all calculations, there is not need to calculate it \n
                in each iteration \n
                """
                self.q_self = np.zeros(8)
                self.q_self[1:9:2] = self._gamma * self._t

                WP_xi = 1  # Numerical integration with 2 Gauss Points
                WP_eta = 1  # Numerical integration with 2 Gauss Points

                for x in range(0, 2, 1):
                    xi = -1 / np.sqrt(3) + 1 / np.sqrt(3) * 2 * x
                    for y in range(0, 2, 1):
                        eta = -1 / np.sqrt(3) + 1 / np.sqrt(3) * 2 * y

                        self.N_nat(xi, eta)

                        self.element_loading_vec[1] += (
                            self.q_self[1]
                            * self.result_N[0][0]
                            * self.det_J
                            * WP_xi
                            * WP_eta
                        )
                        self.element_loading_vec[3] += (
                            self.q_self[3]
                            * self.result_N[0][2]
                            * self.det_J
                            * WP_xi
                            * WP_eta
                        )
                        self.element_loading_vec[5] += (
                            self.q_self[5]
                            * self.result_N[0][4]
                            * self.det_J
                            * WP_xi
                            * WP_eta
                        )
                        self.element_loading_vec[7] += (
                            self.q_self[7]
                            * self.result_N[0][6]
                            * self.det_J
                            * WP_xi
                            * WP_eta
                        )

    def __str__(self):
        output = "NODAL COORDINATES\n"
        output += "\n".join(
            "  ".join(str(self._coords_T[i][j]) for j in range(len(self._coords_T[0])))
            for i in range(len(self._coords_T))
        )

        output += "\ngrad\n"
        output += "\n".join(
            " ".join(str(self.grad[i][j]) for j in range(len(self.grad[0])))
            for i in range(len(self.grad))
        )

        output += "\nResult grad T\n"
        output += "\n".join(
            " ".join(
                str(self.result_grad_T[i][j]) for j in range(len(self.result_grad_T[0]))
            )
            for i in range(len(self.result_grad_T))
        )

        output += "\nStiffness matrix K\n"
        output += "\n".join(
            " ".join(str(self.K[i][j]) for j in range(len(self.K[0])))
            for i in range(len(self.K))
        )

        return output
