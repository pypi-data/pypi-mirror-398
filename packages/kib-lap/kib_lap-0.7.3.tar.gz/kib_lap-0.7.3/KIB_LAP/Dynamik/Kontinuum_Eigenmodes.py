import numpy as np
from scipy.optimize import newton
import sqlite3
from scipy import integrate
from scipy.misc import derivative


class eigenmodes:
    def __init__(self):
        self.num_x = 10000

        self.lambda_cantilever = np.zeros(20)
        self.a_lambda_cantilever = np.zeros(20)
        self.j1_cantilever = np.zeros(20)
        self.y_cantilever = np.zeros((20, self.num_x))
        self.y_xx_cantilever = np.zeros((20, self.num_x))

        self.lambda_clamped_hinged = np.zeros(20)
        self.a_lambda_clamped_hinged = np.zeros(20)
        self.j1_clamped_hinged = np.zeros(20)
        self.y_clamped_hinged = np.zeros((20, self.num_x))
        self.y_xx_clamped_hinged = np.zeros((20, self.num_x))

        self.lambda_hinged_hinged = np.zeros(20)
        self.j1_hinged_hinged = np.zeros(20)
        self.y_hinged_hinged = np.zeros((20, self.num_x))
        self.y_xx_hinged_hinged = np.zeros((20, self.num_x))

        self.lambda_clamped_clamped = np.zeros(20)
        self.a_lambda_clamped_clamped = np.zeros(20)
        self.j1_clamped_clamped = np.zeros(20)
        self.y_clamped_clamped = np.zeros((20, self.num_x))
        self.y_xx_clamped_clamped = np.zeros((20, self.num_x))

        self.J_2_hinged_hinged = np.zeros(20)
        self.J_2_clamped_hinged = np.zeros(20)
        self.J_2_clamped_clamped = np.zeros(20)
        self.J_2_cantilever = np.zeros(20)

        self.J_3_hinged_hinged = np.zeros(20)
        self.J_3_clamped_hinged = np.zeros(20)
        self.J_3_clamped_clamped = np.zeros(20)
        self.J_3_cantilever = np.zeros(20)

    # Functions for the lambda-values

    def equation_cantilever_cal(self, lambda_val):
        return np.cosh(lambda_val) * np.cos(lambda_val) + 1

    def equation_clamped_hinged_cal(self, lambda_val):
        return np.tanh(lambda_val) - np.tan(lambda_val)

    def equation_hinged_hinged_cal(self, lambda_val):
        return np.sin(lambda_val)

    def equation_clamped_clamped_cal(self, lambda_val):
        return np.cosh(lambda_val) * np.cos(lambda_val) - 1

    # Functions for a lambda

    def a_lambda_cantilever_cal(self, lambda_values):
        return (np.sinh(lambda_values) + np.sin(lambda_values)) * (
            np.cosh(lambda_values) + np.cos(lambda_values)
        ) ** (-1)

    def a_lambda_clamped_hinged_cal(self, lambda_values):
        return (np.sinh(lambda_values) - np.sin(lambda_values)) * (
            np.cosh(lambda_values) - np.cos(lambda_values)
        ) ** (-1)

    def a_lambda_hinged_hinged_cal(self, lambda_values):
        return (lambda_values) * 0

    def a_lambda_clamped_clamped_cal(self, lambda_values):
        return (np.sinh(lambda_values) - np.sin(lambda_values)) * (
            np.cosh(lambda_values) - np.cos(lambda_values)
        ) ** (-1)

    def solving_eigenvalues(self):
        guess_cantilever = 0
        guess_clamped_hinged = 0
        guess_hinged_hinged = 0
        guess_clamped_clamped = 0

        for i in range(0, 20, 1):
            if i == 0:
                guess_cantilever = 1.874
                guess_clamped_hinged = 3.92
                guess_clamped_clamped = 4.73

            elif i == 1:
                guess_cantilever = 4.68
                guess_clamped_hinged = 7.06
                guess_clamped_clamped = 7.85
            elif i == 2:
                guess_cantilever = 7.84
                guess_clamped_hinged = 10.21
                guess_clamped_clamped = 10.99
            else:
                guess_cantilever = (
                    2 * (i + 1) - 1
                ) * np.pi / 2 - 0.02  # Important: i+1, because of the formulation for the eigenfrequencies
                guess_clamped_hinged = (
                    i + 1 + 0.25
                ) * np.pi  # Otherwise the convergance for the eigenfrequencies won't work, because a lower frequency value
                guess_clamped_clamped = (i + 1 + 0.5) * np.pi  # is calculated

            guess_hinged_hinged = (
                i + 1
            ) * np.pi  # The hinged-hinged always equals to i * np.pi

            print(guess_hinged_hinged)

            self.lambda_cantilever[i] = newton(
                self.equation_cantilever_cal, guess_cantilever
            )
            self.lambda_clamped_hinged[i] = newton(
                self.equation_clamped_hinged_cal, guess_clamped_hinged
            )
            self.lambda_hinged_hinged[i] = newton(
                self.equation_hinged_hinged_cal, guess_hinged_hinged
            )
            self.lambda_clamped_clamped[i] = newton(
                self.equation_clamped_clamped_cal, guess_clamped_clamped
            )

    def calculation_a_lambda(self):
        for i in range(0, 20, 1):
            self.a_lambda_cantilever[i] = self.a_lambda_cantilever_cal(
                self.lambda_cantilever[i]
            )
            self.a_lambda_clamped_hinged[i] = self.a_lambda_clamped_hinged_cal(
                self.lambda_clamped_hinged[i]
            )
            self.a_lambda_clamped_clamped[i] = self.a_lambda_clamped_clamped_cal(
                self.lambda_clamped_clamped[i]
            )

    def calculating_j1(self):
        self.x_values = np.linspace(0, 1, num=self.num_x)
        for i in range(0, 20, 1):
            for j in range(0, len(self.x_values), 1):
                self.y_hinged_hinged[i][j] = np.sin(
                    self.lambda_hinged_hinged[i] * self.x_values[j]
                )

                self.y_clamped_clamped[i][j] = (
                    np.sin(self.lambda_clamped_clamped[i] * self.x_values[j])
                    - np.sinh(self.lambda_clamped_clamped[i] * self.x_values[j])
                    + self.a_lambda_clamped_clamped[i]
                    * (
                        np.cosh(self.lambda_clamped_clamped[i] * self.x_values[j])
                        - np.cos(self.lambda_clamped_clamped[i] * self.x_values[j])
                    )
                )
                self.y_clamped_hinged[i][j] = (
                    np.sin(self.lambda_clamped_hinged[i] * self.x_values[j])
                    - np.sinh(self.lambda_clamped_hinged[i] * self.x_values[j])
                    + self.a_lambda_clamped_hinged[i]
                    * (
                        np.cosh(self.lambda_clamped_hinged[i] * self.x_values[j])
                        - np.cos(self.lambda_clamped_hinged[i] * self.x_values[j])
                    )
                )

                self.y_cantilever[i][j] = (
                    np.sin(self.lambda_cantilever[i] * self.x_values[j])
                    - np.sinh(self.lambda_cantilever[i] * self.x_values[j])
                    + self.a_lambda_cantilever[i]
                    * (
                        np.cosh(self.lambda_cantilever[i] * self.x_values[j])
                        - np.cos(self.lambda_cantilever[i] * self.x_values[j])
                    )
                )

                self.j1_hinged_hinged[i] = integrate.simps(
                    self.y_hinged_hinged[i][:] ** 2, x=self.x_values
                )
                self.j1_clamped_hinged[i] = integrate.simps(
                    self.y_clamped_hinged[i][:] ** 2, x=self.x_values
                )
                self.j1_clamped_clamped[i] = integrate.simps(
                    self.y_clamped_clamped[i][:] ** 2, x=self.x_values
                )
                self.j1_cantilever[i] = integrate.simps(
                    self.y_cantilever[i][:] ** 2, x=self.x_values
                )

    def numerical_derivative(self, data, delta_x):
        """
        Compute the numerical derivative of the given data using central difference quotient.
        :param data: List of function values.
        :param delta_x: Spacing between the x-values.
        :return: List of derivative values.
        """
        derivative = []
        for i in range(1, len(data) - 1):
            df = (data[i + 1] - data[i - 1]) / (2 * delta_x)
            derivative.append(df)
        return derivative

    def second_derivative(self, data, delta_x):
        # Compute the first derivative
        first_derivative = self.numerical_derivative(data, delta_x)

        # Compute the second derivative from the first derivative
        return self.numerical_derivative(first_derivative, delta_x)

    def calculating_j2(self):
        for i in range(0, 20, 1):
            y_xx_temp_cantilever = self.second_derivative(
                self.y_cantilever[i][:], 1 / self.num_x
            )
            self.y_xx_cantilever[i][2:-2] = y_xx_temp_cantilever

            y_xx_temp_hinged_hinged = self.second_derivative(
                self.y_hinged_hinged[i][:], 1 / self.num_x
            )
            self.y_xx_hinged_hinged[i][2:-2] = y_xx_temp_hinged_hinged

            y_xx_temp_clamped_hinged = self.second_derivative(
                self.y_clamped_hinged[i][:], 1 / self.num_x
            )
            self.y_xx_clamped_hinged[i][2:-2] = y_xx_temp_clamped_hinged

            y_xx_temp_clamped_clamped = self.second_derivative(
                self.y_clamped_clamped[i][:], 1 / self.num_x
            )
            self.y_xx_clamped_clamped[i][2:-2] = y_xx_temp_clamped_clamped

            self.J_2_cantilever[i] = integrate.simps(
                self.y_xx_cantilever[i][:] ** 2, x=self.x_values
            )
            self.J_2_hinged_hinged[i] = integrate.simps(
                self.y_xx_hinged_hinged[i][:] ** 2, x=self.x_values
            )
            self.J_2_clamped_hinged[i] = integrate.simps(
                self.y_xx_clamped_hinged[i][:] ** 2, x=self.x_values
            )

            self.J_2_clamped_clamped[i] = integrate.simps(
                self.y_xx_clamped_clamped[i][:] ** 2, x=self.x_values
            )

    def calculating_j3(self):
        for i in range(0, 20, 1):
            self.J_3_cantilever[i] = integrate.simps(
                    self.y_cantilever[i][:], x=self.x_values
                )
            self.J_3_clamped_clamped[i] = integrate.simps(
                    self.y_clamped_clamped[i][:], x=self.x_values
                )
            self.J_3_clamped_hinged[i] = integrate.simps(
                    self.y_clamped_hinged[i][:], x=self.x_values
                )
            self.J_3_hinged_hinged[i] =integrate.simps(
                    self.y_hinged_hinged[i][:], x=self.x_values
                )

    def save_to_database(self, db_name="Database/eigenmodes.db"):
        # Connect to the SQLite database
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Create tables
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS eigenvalues (
                id INTEGER PRIMARY KEY,
                lambda_cantilever REAL,
                lambda_clamped_hinged REAL,
                lambda_hinged_hinged REAL,
                lambda_clamped_clamped REAL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS a_lambda (
                id INTEGER PRIMARY KEY,
                a_lambda_cantilever REAL,
                a_lambda_clamped_hinged REAL,
                a_lambda_clamped_clamped REAL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS J1 (
                id INTEGER PRIMARY KEY,
                J1_cantilever REAL,
                J1_clamped_hinged REAL,
                J1_hinged_hinged REAL,
                J1_clamped_clamped REAL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS J2 (
                id INTEGER PRIMARY KEY,
                J2_cantilever REAL,
                J2_clamped_hinged REAL,
                J2_hinged_hinged REAL,
                J2_clamped_clamped REAL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS J3 (
                id INTEGER PRIMARY KEY,
                J3_cantilever REAL,
                J3_clamped_hinged REAL,
                J3_hinged_hinged REAL,
                J3_clamped_clamped REAL
            )
            """
        )

        # Delete existing data to avoid duplicate entries
        cursor.execute("DELETE FROM eigenvalues")
        cursor.execute("DELETE FROM a_lambda")
        cursor.execute("DELETE FROM J1")
        cursor.execute("DELETE FROM J2")
        cursor.execute("DELETE FROM J3")

        # Insert data
        for i in range(20):
            cursor.execute(
                """
                INSERT INTO eigenvalues (lambda_cantilever, lambda_clamped_hinged, lambda_hinged_hinged, lambda_clamped_clamped)
                VALUES (?, ?, ?, ?)
                """,
                (
                    self.lambda_cantilever[i],
                    self.lambda_clamped_hinged[i],
                    self.lambda_hinged_hinged[i],
                    self.lambda_clamped_clamped[i],
                ),
            )

            cursor.execute(
                """
                INSERT INTO a_lambda (a_lambda_cantilever, a_lambda_clamped_hinged, a_lambda_clamped_clamped)
                VALUES (?, ?,?)
                """,
                (self.a_lambda_cantilever[i], self.a_lambda_clamped_hinged[i],self.a_lambda_clamped_clamped[i])
            )

            cursor.execute(
                """
                INSERT INTO J1 (J1_cantilever, J1_clamped_hinged, J1_hinged_hinged, J1_clamped_clamped)
                VALUES (?, ?, ?, ?)
                """,
                (
                    self.j1_cantilever[i],
                    self.j1_clamped_hinged[i],
                    self.j1_hinged_hinged[i],
                    self.j1_clamped_clamped[i],
                ),
            )

            cursor.execute(
                """
                INSERT INTO J2 (J2_cantilever, J2_clamped_hinged, J2_hinged_hinged, J2_clamped_clamped)
                VALUES (?, ?, ?, ?)
                """,
                (
                    self.J_2_cantilever[i],
                    self.J_2_clamped_hinged[i],
                    self.J_2_hinged_hinged[i],
                    self.J_2_clamped_clamped[i],
                ),
            )

            cursor.execute(
                """
                INSERT INTO J3 (J3_cantilever, J3_clamped_hinged, J3_hinged_hinged, J3_clamped_clamped)
                VALUES (?, ?, ?, ?)
                """,
                (
                    self.J_3_cantilever[i],
                    self.J_3_clamped_hinged[i],
                    self.J_3_hinged_hinged[i],
                    self.J_3_clamped_clamped[i],
                ),
            )

        # Commit changes and close connection
        conn.commit()
        conn.close()


test_class = eigenmodes()

test_class.solving_eigenvalues()

print("Testing for the cantilever")
print(test_class.lambda_cantilever)
print("Testing for the clamped hinged beam")
print(test_class.lambda_clamped_hinged)

print("Testing for the hinged hinged beam")
print(test_class.lambda_hinged_hinged)
print("Testing for the clamped clamped beam")
print(test_class.lambda_clamped_clamped)

test_class.calculation_a_lambda()
test_class.calculating_j1()
test_class.calculating_j2()
test_class.calculating_j3()

test_class.save_to_database()
