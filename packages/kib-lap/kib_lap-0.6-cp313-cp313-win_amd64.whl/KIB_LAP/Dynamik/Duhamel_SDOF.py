import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from Kontinuum_Schwingung import *

class DuhamelSolver:
    def __init__(self, k, m, zeta, dt, duration, loading = "Pedestrian", parameters = [2,1.3,800,60], m2_imp = 0):
        """
        loading = Pedestrian, Harmonic, Impulse
        parameters = [Frequency in Hz, 
        Speed in [m/s],
        First harmonic Loading in [N],  
        Length of the Bridge in [m]]
        """
        self.k = k
        self.m = m + m2_imp      # mass of the system, including the impact mass
        self.m2 = m2_imp        # impact mass, if impact response is calculated
        self.zeta = zeta
        self.dt = dt
        self.duration = duration

        self.loading = loading
        self.parameters = parameters
        self.L = self.parameters[-1]

        # Train passing 
        try:
            Kraftdefinition=pd.read_csv('TrainPassing/Inputdatei_1.txt',delim_whitespace=True)

            # # # % Koordinaten der Radsätze mit Bezug auf den ersten Radsatz [m]
            self.x_k=Kraftdefinition.iloc[:, 0].to_list()
            # # # % Achslasten in [N]
            self.P_k=Kraftdefinition.iloc[:, 1].to_list()
        except:
            pass

    def load_function(self, time_step):

        if (self.loading == "Pedestrian"):

            phi = 0
            if (time_step < self.L / self.parameters[1]):
                xp = self.parameters[1] * time_step
                phi = np.sin(np.pi * xp / self.L)
            else:
                phi = 0

            coeff_1 = 0.50
            coeff_2 = 0.10
            coeff_3 = 0.10

            Fn = (1+ coeff_1  * np.sin(2  *np.pi * self.parameters[0]* time_step)
                                    + coeff_2  * np.sin(4  *np.pi * self.parameters[0]* time_step -np.pi/2	)
                                     +coeff_3 * np.sin(6  *np.pi * self.parameters[0]* time_step -np.pi/2	)
            )  * self.parameters[2] * phi


            return Fn


        elif ( self.loading == "Harmonic"):
            return np.sin(np.sqrt(self.k/self.m)* time_step) * 1000


        elif (self.loading == "impact"):
            return self.m2 * 9.81
        
        elif (self.loading == "trainpassing"):
            self.v_train = self.parameters[1]
            time = np.arange(0, self.duration + self.dt, self.dt)
            nt = len(time)


            P_k_array = np.array(self.P_k)

            F_Mat = np.zeros((len(self.x_k)))        # rows -> Index of the train load, cols = number of time steps
                                                

            for j in range(len(self.x_k)):
                if ((-self.x_k[j] + self.v_train * time_step > 0) and (-self.x_k[j] + self.v_train * time_step < self.L)): 
                    xp =    -self.x_k[j] + self.v_train * time_step     # Condition, that the train needs to be on the bridge
                    phi = np.sin(np.pi * xp / self.L)
                    F_Mat[j] = self.P_k[j] * phi
                else:
                    F_Mat[j] = 0

            return F_Mat.sum(axis=0) 

        else:
            if time_step < 3e-3:
                return 1000
            else:
                return 0

    def solve(self):
        omega_0 = np.sqrt(self.k / self.m)
        omega_d = omega_0 * np.sqrt(1 - self.zeta**2)

        time = np.arange(0, self.duration + self.dt, self.dt)
        self.time_output = time
        u = np.zeros(len(time))

        ACum_i = 0
        BCum_i = 0

        for i, t in enumerate(time):
            if i > 0:
                y_i = np.exp(self.zeta * omega_0 * time[i]) * self.load_function(time[i]) * np.cos(omega_d * time[i])
                y_i_1 = np.exp(self.zeta * omega_0 * time[i-1]) * self.load_function(time[i-1]) * np.cos(omega_d * time[i-1])
                area_i = 0.5 * self.dt * (y_i + y_i_1)
                ACum_i += area_i

                y_i = np.exp(self.zeta * omega_0 * time[i]) * self.load_function(time[i]) * np.sin(omega_d * time[i])
                y_i_1 = np.exp(self.zeta * omega_0 * time[i-1]) * self.load_function(time[i-1]) * np.sin(omega_d * time[i-1])
                area_i = 0.5 * self.dt * (y_i + y_i_1)
                BCum_i += area_i

                u[i] = (1 / (self.m * omega_d)) * (ACum_i) * np.exp(-self.zeta * omega_0 * time[i]) * np.sin(omega_d * time[i]) - (1 / (self.m * omega_d)) * (BCum_i) * np.exp(-self.zeta * omega_0 * time[i]) * np.cos(omega_d * time[i])

        return time, u

    def calculate_velocity_and_acceleration(self):
        time, u = self.solve()
        velocity = (np.roll(u, -1) - np.roll(u, 1)) / (2 * self.dt)
        acceleration = (np.roll(u, -1) - 2 * u + np.roll(u, 1)) / (self.dt**2)
        # Remove the erroneous first and last elements
        velocity = velocity[1:-1]
        acceleration = acceleration[1:-1]
        time = time[1:-1]
        return time, velocity, acceleration

    def plot_solution(self):
        time, self.u = self.solve()
        self._time = time
        self.time_v_a , self.vel, self.acc = self.calculate_velocity_and_acceleration()


        fig,axes = plt.subplots(nrows = 3, ncols=1)

        axes[0].plot(self._time,self.u, label = "Deflection")
        axes[0].set_ylabel("Deflection in [m]")
        axes[1].plot(self.time_v_a, self.vel, label = "Velocity")
        axes[1].set_ylabel("Velocity in [m/s]")
        axes[2].plot(self.time_v_a, self.acc, label = "Acceleration")
        axes[2].set_ylabel("Acceleration in [m/s²]")
        fig.suptitle("Vibrations with the Duhamel integral")

        plt.xlabel('Time in [s]')
        plt.tight_layout()
        plt.grid(True)
        plt.show(block = False)
        plt.pause(10)
        plt.close()

    def plot_load_function(self):
        self.time_modal_load = np.arange(0, self.duration + self.dt, self.dt)
        self.load_values = np.array([self.load_function(t) for t in self.time_modal_load])

        plt.figure()
        plt.plot(self.time_modal_load ,self.load_values, label='Load Function')
        plt.xlabel('Time in [s]')
        plt.ylabel('Load in [N]')
        plt.title('Load Function over Time')
        plt.grid(True)
        plt.legend()
        plt.show()



# Impact = DuhamelSolver(1e6, 1000, 0.01, 0.001, 10, loading = "impact", parameters = [2,1.3,800,60], m2_imp = 100)
# Impact.plot_solution()


# u_stat = 100/1e6*9.81

# print("udyn", max(Impact.u))
# print("ustat", u_stat)
# print("faktor",  max(Impact.u)/u_stat )

v_train = 300/3.6
l_up = 25
f_train = v_train / l_up 
E = 2.1e11
I = 0.5
EI = E*I
l = 60
f = l**3/(48 * EI)
m = 0.5 * l * 5160

t_cal = 10


TrainPassing = DuhamelSolver(1/f, m , 0.0257,  0.001, t_cal, loading = "trainpassing", parameters = [f_train,v_train,0,l], m2_imp = 100)
TrainPassing.plot_solution()

# print("time for passing in [s]", (60+393.7) / v_train)


Schwingung = Balkenschwingungen(l, 1, 5063, 0.0257, E, I, t_cal,"Hinged-Hinged",None,l/2,300)



fig,axes = plt.subplots(nrows = 3, ncols=1)

axes[0].plot(TrainPassing._time,TrainPassing.u, label = "Deflection SDOF")
axes[0].plot(Schwingung.t,Schwingung.y, label = "Deflection continuum")
axes[0].set_ylabel("Deflection in [m]")
axes[1].plot(TrainPassing.time_v_a, TrainPassing.vel, label = "Velocity SDOF")
axes[1].plot(Schwingung.t,Schwingung.v, label = "Velocity continuum")
axes[1].set_ylabel("Velocity in [m/s]")
axes[2].plot(TrainPassing.time_v_a, TrainPassing.acc, label = "Acceleration SDOF")
axes[2].plot(Schwingung.t,Schwingung.a, label = "Acceleration continuum")
axes[2].set_ylabel("Acceleration in [m/s²]")
fig.suptitle("Vibrations with the Duhamel integral and continuum")

plt.xlabel('Time in [s]')
plt.tight_layout()
plt.grid(True)
plt.show(block = False)
plt.pause(10)
plt.close()