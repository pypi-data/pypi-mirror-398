import numpy as np
from scipy.linalg import eigh


class DeformationMethod:
    def __init__(
        self,
        num_input,
        E_inp=1,
        I_inp=1,
        A_inp=1,
        rho_inp=1,
        l_inp=1,
        static_inp="SPG",
        l_inp_multi=[1, 1],
        _num_integral = 1000
    ):
        """_summary_

        Args:
            num_input (_type_): _description_
            E_inp (int, optional): _description_. Defaults to 1.
            I_inp (int, optional): _description_. Defaults to 1.
            A_inp (int, optional): _description_. Defaults to 1.
            rho_inp (int, optional): _description_. Defaults to 1.
            l_inp (int, optional): _description_. Defaults to 1.
            static_inp (str, optional): _description_. Defaults to "SPG".
            l_inp_multi (list, optional): _description_. Defaults to [1,1]. First Value: Multispan in [m] and Second value:
        """
        self.statical_system = static_inp
        self.input_discret = num_input
        self.E = E_inp
        self.I = I_inp
        self.A = A_inp
        self.l = l_inp
        self.rho = rho_inp

        self.l_2 = l_inp_multi[0]

        self.absorber_node = []
        self.absorber_mass = []
        self.absorber_stiffness = []

        self.num_integral = _num_integral  # Check for the required accuracy:
        self.f_s = 1 / 10000

        # Length vector for numerical integration

        self.length = [
            self.l / self.num_integral * i for i in range(self.num_integral + 1)
        ]

        self.length_2 = [
            self.l_2 / self.num_integral * i for i in range(self.num_integral + 1)
        ]

    def calculation_params_spg(self):
        self.xi = [
            (i + 1) / (self.input_discret + 1) for i in range(self.input_discret)
        ]
        self.m_moment = np.zeros((self.num_integral, self.input_discret))

        for col in range(self.input_discret):
            for row in range(self.num_integral):
                A_Bearing = 1 - self.xi[col]
                B_Bearing = self.xi[col]
                if row <= self.xi[col] * (self.num_integral):
                    self.m_moment[row][col] = (
                        A_Bearing * row / self.num_integral * self.l
                    )

                else:
                    self.m_moment[row][col] = (
                        A_Bearing * row / self.num_integral * self.l
                        - (row / self.num_integral - self.xi[col]) * self.l
                    )

    def calculation_params_ctb(self):
        self.xi = [(i + 1) / self.input_discret for i in range(self.input_discret)]
        self.m_moment = np.zeros((self.num_integral, self.input_discret))

        for col in range(self.input_discret):
            for row in range(self.num_integral):
                A_Bearing = 1
                M_Bearing = self.xi[col] * self.l * A_Bearing
                if row <= int(self.xi[col] * self.num_integral):
                    self.m_moment[row][col] = (
                        M_Bearing - A_Bearing * row / self.num_integral * self.l
                    )
                else:
                    self.m_moment[row][col] = 0
        self.length = [
            self.l / self.num_integral * i for i in range(self.num_integral + 1)
        ]

    def calculation_params_two_span_girder(self):
        ## Calculating the M0-Moment-Curve for discrete single loads at each point
        self.xi = [
            (i + 1) / (self.input_discret + 1) for i in range(self.input_discret)
        ]
        self.m_moment_0 = np.zeros((self.num_integral + 1, self.input_discret))
        self.m_moment_1 = np.zeros(
            self.num_integral + 1
        )  # valid, if the bearing of the two-span girder is in the middle of the bridge (Usually fullfilled)
        self.m_moment = np.zeros((self.num_integral + 1, self.input_discret))

        for col in range(self.input_discret):
            for row in range(self.num_integral + 1):
                A_Bearing = 1 - self.xi[col]
                B_Bearing = self.xi[col]
                if row <= self.xi[col] * self.num_integral:
                    self.m_moment_0[row][col] = (
                        A_Bearing * row / self.num_integral * self.l
                    )
                else:
                    self.m_moment_0[row][col] = (
                        A_Bearing * row / self.num_integral * self.l
                        - (row / self.num_integral - self.xi[col]) * self.l
                    )
                if col == 0:
                    if row <= (self.num_integral + 1) / 2:
                        self.m_moment_1[row] = -row / self.num_integral * self.l * 0.5
                    else:
                        self.m_moment_1[row] = (
                            -self.l / 4
                            + (row - (self.num_integral) / 2)
                            / self.num_integral
                            * self.l
                            * 0.5
                        )

        self.m_moment_1[-1] = 0
        self.length_0 = [
            self.l / self.num_integral * i for i in range(self.num_integral)
        ]

        ## Calculation of the delta-coefficients
        integral_11 = [
            self.m_moment_1[i] * self.m_moment_1[i]
            for i in range(0, len(self.m_moment_1), 1)
        ]

        delta_11 = np.trapz(integral_11, self.length) * 1 / (self.E * self.I)

        x1 = np.zeros(self.input_discret)  # Statically indetermined
        self.delta_10_mat = np.zeros(self.input_discret)  # For testing purposes

        for col in range(self.input_discret):
            m_moment_inte = np.zeros(self.num_integral + 1)
            for i in range(self.num_integral + 1):
                m_moment_inte[i] = self.m_moment_0[i][col]

            integrant_10 = m_moment_inte * self.m_moment_1
            delta_10 = np.trapz(integrant_10, self.length) * 1 / (self.E * self.I)

            self.delta_10_mat[col] = delta_10
            x1[col] = -delta_10 / delta_11

            for i in range(self.num_integral + 1):
                self.m_moment[i][col] = (
                    self.m_moment_0[i][col] + x1[col] * self.m_moment_1[i]
                )

    def calculation_params_two_span_girder_SPG(self):
        ## Calculating the M0-Moment-Curve for discrete single loads at each point
        self.xi = [
            (i + 1) / (self.input_discret + 1) for i in range(self.input_discret)
        ]
        self.m_moment_0_1 = np.zeros(
            (self.num_integral + 1, self.input_discret)
        )  # First statically determined part system
        self.m_moment_0_2 = np.zeros(
            (self.num_integral + 1, self.input_discret)
        )  # Second statically determined part system

        self.m_moment_1_1 = np.zeros(self.num_integral + 1)
        self.m_moment_1_2 = np.zeros(self.num_integral + 1)

        self.m_moment = np.zeros(((self.num_integral + 1) * 2, self.input_discret * 2))

        # Calulating the moment-curves for the first span

        for col in range(self.input_discret):
            for row in range(self.num_integral + 1):
                A_Bearing = 1 - self.xi[col]
                B_Bearing = self.xi[col]
                if row <= self.xi[col] * self.num_integral:
                    self.m_moment_0_1[row][col] = (
                        A_Bearing * row / self.num_integral * self.l
                    )
                else:
                    self.m_moment_0_1[row][col] = (
                        A_Bearing * row / self.num_integral * self.l
                        - (row / self.num_integral - self.xi[col]) * self.l
                    )

                if col == 0:
                    self.m_moment_1_1[row] = -row / self.num_integral * self.l * 1 / self.l


                # Calculating the moment curves for the second span

        # Calculating the moment-curves for the second span
        for col in range(self.input_discret):
            for row in range(self.num_integral + 1):
                A_Bearing = 1 - self.xi[col]
                B_Bearing = self.xi[col]
                if row <= self.xi[col] * self.num_integral:
                    self.m_moment_0_2[row][col] = (
                        A_Bearing * row / self.num_integral * self.l_2
                    )
                else:
                    self.m_moment_0_2[row][col] = (
                        A_Bearing * row / self.num_integral * self.l_2
                        - (row / self.num_integral - self.xi[col]) * self.l_2
                    )

                if col == 0:
                    self.m_moment_1_2[row] = (
                            -1 + row / self.num_integral * self.l_2 * 1 / self.l_2
                        )

                        
        # Calculating the influence number for delta_11

        integral_11_1 = [
            self.m_moment_1_1[i] * self.m_moment_1_1[i]
            for i in range(0, len(self.m_moment_1_1), 1)
        ]

        delta_11_1 = np.trapz(integral_11_1, self.length) * 1 / (self.E * self.I)

        integral_11_2 = [
            self.m_moment_1_2[i] * self.m_moment_1_2[i]
            for i in range(0, len(self.m_moment_1_2), 1)
        ]

        delta_11_2 = np.trapz(integral_11_2, self.length_2) * 1 / (self.E * self.I)


        # Calulating the influence number for delta_10 for the first span

        x1 = np.zeros(self.input_discret)  # Statically indetermined moment an the middle bearing

        for col in range(self.input_discret):
            m_moment_inte_1 = np.zeros(self.num_integral + 1)
            m_moment_inte_2 = np.zeros(self.num_integral + 1)
            for i in range(self.num_integral + 1):
                m_moment_inte_1[i] = self.m_moment_0_1[i][col]
                m_moment_inte_2[i] = self.m_moment_0_2[i][col]

            integrant_10_1 = m_moment_inte_1 * self.m_moment_1_1
            delta_10_1 = np.trapz(integrant_10_1, self.length) * 1 / (self.E * self.I)

            # print("Statically determined moment")
            # print(self.m_moment_0_1)
            # print("Virtual Moment - 1")
            # print(self.m_moment_1_1)
            # print("Virtual Moment - 2")
            # print(self.m_moment_1_2)

            # print("delta 10 ")

            # print(delta_10_1)

            # print("delta 11")

            # print(delta_11_1 + delta_11_2)

            x1[col] = -(delta_10_1 / (delta_11_1 + delta_11_2))

            # print(x1)

            # Integration result for the first span

            for i in range(self.num_integral + 1):
                self.m_moment[i][col] = (
                    self.m_moment_0_1[i][col] + x1[col] * self.m_moment_1_1[i]
                )

            # Integration result for the second span

            for i in range(self.num_integral + 1, (self.num_integral + 1) * 2):
                self.m_moment[i][col] = (
                    0 + x1[col] * self.m_moment_1_2[int(i-(self.num_integral + 1))]
                )

        # Calculating the influence number for delta_10 for the second span
        x1 = np.zeros(self.input_discret)  # Statically indetermined moment an the middle bearing

        for col in range(self.input_discret,self.input_discret*2):
            m_moment_inte_1 = np.zeros(self.num_integral + 1)
            m_moment_inte_2 = np.zeros(self.num_integral + 1)
            for i in range(self.num_integral + 1):
                m_moment_inte_2[i] = self.m_moment_0_2[i][int(col-self.input_discret)]

            integrant_10_2 = m_moment_inte_2 * self.m_moment_1_2
            delta_10_2 = np.trapz(integrant_10_2, self.length_2) * 1 / (self.E * self.I)

            # print("Statically determined moment")
            # print(self.m_moment_0_2)
            # print("Virtual Moment - 1")
            # print(self.m_moment_1_1)
            # print("Virtual Moment - 2")
            # print(self.m_moment_1_2)

            # print("delta 10 ")

            # print(delta_10_2)

            # print("delta 11")

            # print(delta_11_1 + delta_11_2)

            x1[int(col-self.input_discret)] = -(delta_10_2 / (delta_11_1 + delta_11_2))

            # print(x1)

            # Integration result for the first span

            for i in range(self.num_integral + 1):
                self.m_moment[i][col] = (
                    x1[int(col-self.input_discret)] * self.m_moment_1_1[i]
                )

            # Integration result for the second span

            for i in range(self.num_integral + 1, (self.num_integral+1) * 2):
                self.m_moment[i][col] = (  
                    self.m_moment_0_2[i-(self.num_integral + 1)][int(col-self.input_discret)] + x1[int(col-self.input_discret)] * self.m_moment_1_2[int(i-(self.num_integral + 1))]
                )

    def mass_matrix(self):
        if (self.statical_system == "TSG_H"):
            self.M_matrix = np.zeros(
                (
                    self.input_discret*2 + len(self.absorber_node),
                    self.input_discret*2 + len(self.absorber_node),
                )
            )

            m_i_1 = self.rho * self.l * self.A / (self.input_discret + 1)
            m_i_2 = self.rho * self.l_2 * self.A / (self.input_discret + 1)
            
            for row in range(self.input_discret):
                self.M_matrix[row][row] = m_i_1
                self.M_matrix[row+self.input_discret][row+self.input_discret] = m_i_2

            for row in range(len(self.absorber_node)):
                self.M_matrix[row + self.input_discret*2][
                    row + self.input_discret * 2
                ] = self.absorber_mass[row]

        else:
            self.M_matrix = np.zeros(
                (
                    self.input_discret + len(self.absorber_node),
                    self.input_discret + len(self.absorber_node),
                )
            )
            m_i = self.rho * self.l * self.A / (self.input_discret + 1)

            for row in range(self.input_discret):
                self.M_matrix[row][row] = m_i

            for row in range(len(self.absorber_node)):
                self.M_matrix[row + self.input_discret][
                    row + self.input_discret
                ] = self.absorber_mass[row]

    def single_span_girder(self):
        self.mass_matrix()
        EI = self.E * self.I
        self.calculation_params_spg()
        integral = np.zeros(self.num_integral+1)
        self.delta_i = np.zeros((self.input_discret, self.input_discret))

        for row in range(self.input_discret):
            for col in range(self.input_discret):
                for i in range(self.m_moment.shape[0]):
                    integral[i] = self.m_moment[i][row] * self.m_moment[i][col]
                self.delta_i[row][col] = (1 / EI) * np.trapz(integral, self.length)

        self.K_matrix = np.linalg.inv(self.delta_i)

    def cantilever_beam(self):
        self.mass_matrix()
        EI = self.E * self.I
        self.calculation_params_ctb()
        integral = np.zeros(self.num_integral+1)
        self.delta_i = np.zeros((self.input_discret, self.input_discret))

        for row in range(self.input_discret):
            for col in range(self.input_discret):
                for i in range(self.m_moment.shape[0]):
                    integral[i] = self.m_moment[i][row] * self.m_moment[i][col]
                self.delta_i[row][col] = (1 / EI) * np.trapz(integral, self.length)

        self.K_matrix = np.linalg.inv(self.delta_i)

    def two_span_girder(self):
        self.mass_matrix()
        EI = self.E * self.I
        self.calculation_params_two_span_girder()

        integral = np.zeros(self.num_integral + 1)
        self.delta_i = np.zeros((self.input_discret, self.input_discret))

        for row in range(self.input_discret):
            for col in range(self.input_discret):
                for i in range(self.m_moment.shape[0]):
                    integral[i] = (
                        self.m_moment[i][row] * self.m_moment_0[i][col]
                    )  # m_moment_0 ->
                    # Virtual moment at the statically determined system
                    # Virtual moment is equal to the moment_0
                self.delta_i[row][col] = (1 / EI) * np.trapz(integral, self.length)

        # Define your threshold for deflection values below which rows and columns are removed

        threshold = 1e-15

        # Calculate the absolute values of the matrices
        abs_GSM = np.abs(self.delta_i)
        abs_GMM = np.abs(self.M_matrix)

        # Create masks to identify rows and columns with values above the threshold
        rows_to_keep_GSM = np.any(abs_GSM >= threshold, axis=1)
        cols_to_keep_GSM = np.any(abs_GSM >= threshold, axis=0)

        # Perform row reduction based on the threshold for the global stiffness matrix
        rrgsm = self.delta_i[rows_to_keep_GSM]
        crgsm = rrgsm[:, cols_to_keep_GSM]
        self.delta_i = crgsm

        # Perform row reduction based on the threshold for the global mass matrix
        rgmm = self.M_matrix[rows_to_keep_GSM]
        crgmm = rgmm[:, cols_to_keep_GSM]
        self.M_matrix = crgmm

        self.K_matrix = np.linalg.inv(self.delta_i)
   

    def two_span_girder_hinged(self):
        print("Two span girder with a hinge")
        self.mass_matrix()
        EI = self.E * self.I
        self.calculation_params_two_span_girder_SPG()

        integral_1 = np.zeros(self.num_integral + 1)
        integral_2 = np.zeros(self.num_integral + 1)

        self.delta_i = np.zeros((self.input_discret * 2, self.input_discret * 2))

        for row in range(self.input_discret*2):             # Corresponds to the loading node (Single load 1)
            for col in range(self.input_discret*2):         # Corresponds to the reaction node (Node, where the deflection is calculated (Virtual Moment!))
                for i in range(int(self.m_moment.shape[0]/2)):
                    if (col < self.input_discret):
                        # Case 1: The deformations are calculated for the first n = self.input_discrete masses in the span 1
                        # Therefore the integral in the second span is zero, because the moment curves are decoupled due to the hinge 
                        # in the midspan
                        integral_1[i] = (
                            self.m_moment[i][row] * self.m_moment_0_1[i][col-self.input_discret]
                        )  
                        integral_2[i] = (
                            self.m_moment[i+int(self.m_moment.shape[0]/2)][row] * 0
                        )
                    else:
                        # Case 2: The deformations are calculated for the second n = self.input_discrete masses in the span 2
                        # Therefore the integral in the first span is zero, because the moment curves are decoupled due to the hinge 
                        # in the midspan. 
                        integral_1[i] = (
                            self.m_moment[i][row] * 0
                        )  
                        integral_2[i] = (
                            self.m_moment[i+int(self.m_moment.shape[0]/2)][row] *self.m_moment_0_2[i][col-self.input_discret]
                        )

                #     print(self.m_moment[i+int(self.m_moment.shape[0]/2)][row])

                self.delta_i[row][col] = (1 / EI) * (np.trapz(integral_1, self.length) + np.trapz(integral_2, self.length_2) ) 



        self.K_matrix = np.linalg.inv(self.delta_i)

    def compute_eigenfrequencies(self):
        try:
            eigenvalues, eigenvectors = eigh(self.K_matrix, self.M_matrix, subset_by_index=(0, 20 - 1))
        except:
            eigenvalues, eigenvectors = eigh(self.K_matrix, self.M_matrix)      # Eigenvalues with Number of DOFS below 20

        num_eigenval = len(eigenvalues)

        self.eigenfrequencies = np.sqrt(np.abs(eigenvalues))

        normalized_modes = eigenvectors / np.abs(eigenvectors).max(axis=0)

        self.eigenmodes_matrix_storage = normalized_modes

        self.eigenmodes_matrix = normalized_modes


        num_rows, num_columns = self.eigenmodes_matrix.shape

        # Define the number of zeros to add at the beginning and end of each column
        num_zeros = 1  # You want to add one zero at each end

        # Create a new matrix with the desired structure
        new_num_rows = num_rows + 2 * num_zeros  # Calculate the new number of rows
        new_matrix = np.zeros((new_num_rows, num_columns))  # Initialize a new matrix with zeros

        # Copy the original matrix into the center of the new matrix
        new_matrix[num_zeros:num_zeros + num_rows, :] = self.eigenmodes_matrix

        self.eigenmodes_matrix = new_matrix

        if self.statical_system == "TSG_H":     # Adding a zero deflection point, because of the vertical bearing

            new_num_rows = self.eigenmodes_matrix.shape[0] + 1  # Calculate the new number of rows
            new_matrix = np.zeros((new_num_rows, num_columns))  # Initialize a new matrix with zeros

            # Copy the first half of the original matrix between the first row and the middle row
            for row in range(0, 1 + self.input_discret):
                for col in range(num_eigenval):
                    new_matrix[row][col] = self.eigenmodes_matrix[row][col]
            try:
                for row in range(1 + self.input_discret, self.input_discret*2+3):
                    print(row)
                    for col in range(num_eigenval):
                        new_matrix[row+1][col] =  self.eigenmodes_matrix[row][col]
            except:
                pass

            for row in range(1 + self.input_discret, self.input_discret*2+2):
                print(row)
                for col in range(num_eigenval):
                    new_matrix[row+1][col] =  self.eigenmodes_matrix[row][col]


            self.eigenmodes_matrix = new_matrix

            # Length-Vector for the whole structure

            self.len_plotting = np.zeros(2*self.input_discret+3)

            for i in range(0,self.input_discret+1,1):
                self.len_plotting[i] = self.l / (self.input_discret+1) * i

            self.len_plotting[self.input_discret+1] = self.l

            for i in range(0,self.input_discret+1,1):
                self.len_plotting[i+self.input_discret+2] = self.l + self.l_2 / (self.input_discret+1) * (i+1)


        else:
            # Length-Vector for the whole structure
            self.len_plotting = np.zeros(self.input_discret+2)

            for i in range(0, self.input_discret+1, 1):
                self.len_plotting[i] = self.l / (self.input_discret+1) * i

            self.len_plotting[self.input_discret+1] = self.l


        return self.eigenfrequencies, self.eigenmodes_matrix


    def modal_matrices(self):
        self.M_trans = np.dot(np.transpose(self.eigenmodes_matrix_storage),np.dot(self.M_matrix,self.eigenmodes_matrix_storage))
        self.K_trans = np.dot(np.transpose(self.eigenmodes_matrix_storage),np.dot(self.K_matrix,self.eigenmodes_matrix_storage))


    def print_modes_matrix(self):
        print("Circular eigenfrequencies")
        print(self.eigenfrequencies)

        print("Eigenfrequencies")

        print(self.eigenfrequencies / (2 * np.pi))

        print("Normalized eigenmodes")

        for row in self.eigenmodes_matrix:
            formatted_row = ["{:.4f}".format(item) for item in row]
            print(" | ".join(formatted_row))
            print("-" * (len(formatted_row) * 8))  # Print dashes for clarity
