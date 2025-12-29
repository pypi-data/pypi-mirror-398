import numpy as np
from math import sin, cos
from matplotlib import pyplot as plt


class TwoMassesSpringRopeRK4:
    def __init__(
        self,
        r_inp=5,
        E_inp=30000e6,
        I_inp=833.33,
        l_inp=30,
        m1_inp=5.625e6,
        m2_inp=981250,
        dtinp = 1e-3, timeinp = 10,
        _phi_0 = 30 , _x1_0 = 0,
        _dphi_0 = 0 , _dx1_0 = 0
    ):
        self.r = r_inp
        E = E_inp
        I = I_inp
        l = l_inp


        self.k_1 = 3 * E * I / l**3  

        # Mass parameters
        self.m_1 = m1_inp
        self.m_2 = m2_inp

        # Damping parameters

        # Gravity

        self.g = 9.81  # Gravity constant

        # Initial conditions
        self.x1_0 = _x1_0
        self.phi_0 =  _phi_0  / 180 * np.pi
        self.xd1_0 =  _dphi_0
        self.phid_0 = _x1_0

        # Time steps
        self.dt = dtinp
        self.T_ges = timeinp
        self.N_steps = int(self.T_ges / self.dt)

    def construct_mass_matrix(self, phi):
        m_11 = self.m_1 + self.m_2
        m_12 = self.m_2 * self.r * cos(phi)
        m_21 = self.m_2 * self.r * cos(phi)
        m_22 = self.m_2 * self.r**2

        M = np.array([[m_11, m_12], [m_21, m_22]])
        return M

    def construct_force_vector(self, phi, phid):
        f_10 = -self.k_1 * self.x1_0 + self.m_2 * self.r * phid**2 * sin(phi)
        f_20 = -self.m_2 * self.g * self.r * sin(phi)

        F = np.array([f_10, f_20])
        return F

    def equations_of_motion(self, state):
        x1, phi, xd1, phid = state
        M = self.construct_mass_matrix(phi)
        F = self.construct_force_vector(phi, phid)
        acc = np.linalg.solve(M, F)
        return np.array([xd1, phid, acc[0], acc[1]])

    def RK4_step(self, state):
        k1 = self.equations_of_motion(state)
        k2 = self.equations_of_motion(state + 0.5 * k1 * self.dt)
        k3 = self.equations_of_motion(state + 0.5 * k2 * self.dt)
        k4 = self.equations_of_motion(state + k3 * self.dt)
        return state + self.dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6

    def solve(self):
        state = np.array(
            [self.x1_0, self.phi_0, self.xd1_0, self.phid_0]
        )  # Initial state [x1, phi, xd1, phid]
        list_x1 = []
        list_phi = []
        time = []

        for i in range(self.N_steps):
            state = self.RK4_step(state)
            list_x1.append(state[0])
            list_phi.append(state[1])
            time.append(self.dt * i)

        return time, list_x1, list_phi


