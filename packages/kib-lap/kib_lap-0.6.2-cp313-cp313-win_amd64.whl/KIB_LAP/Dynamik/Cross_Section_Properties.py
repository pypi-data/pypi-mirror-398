class cross_section_polygon:
    def __init__(self, y, z):
        """_summary_
        Calculation of cross section properties for polygons. The coordinates need to be inserted clockwise  \n
        for positive areas, and anti-clockwise for wholes. \n
        Args:
            y (_type_): _description_
            z (_type_): _description_
        """
        self.y_restart = [float(y_f) for y_f in y]
        self.z_restart = [float(z_f) for z_f in z]
        self.len_y = len(self.y_restart)
        A_Test = 0
        for row in range(0, self.len_y - 1, 1):
            A_Test += 0.5 * (
                self.z_restart[row + 1] * self.y_restart[row]
                - self.z_restart[row] * self.y_restart[row + 1]
            )

        if A_Test >= 0:
            self.y = [float(y_f) for y_f in y]
            self.y.append(
                self.y[0]
            )  # Last element is necessary for loop over polygon (left rotation direction)
            self.z = [float(z_f) for z_f in z]
            self.z.append(self.z[0])
        elif A_Test < 0:
            self.y = [float(y_f) for y_f in y]
            self.y.append(self.y[0])
            self.y = self.y[::-1]
            self.z = [float(z_f) for z_f in z]
            self.z.append(self.z[0])
            self.z = self.z[::-1]

        print(self.y)
        print(self.z)

        print(self.len_y)
        self.A = 0
        self.S_y = 0
        self.S_z = 0
        self.I_yy = 0
        self.I_zz = 0
        self.I_yz = 0
        self.ys = 0
        self.zs = 0

        self.list_names = []
        self.list_unit = []
        self.list_value = []

        self.section_props()

    def section_props(self):
        print("Section_Props is accessed")
        self.list_names = []
        self.list_unit = []
        self.list_value = []
        for row in range(0, self.len_y - 1, 1):
            self.A += 0.5 * (
                self.z[row + 1] * self.y[row] - self.z[row] * self.y[row + 1]
            )
            print(self.A)
            self.S_y += (
                1
                / 6
                * (
                    (self.z[row] + self.z[row + 1])
                    * (self.z[row + 1] * self.y[row] - self.z[row] * self.y[row + 1])
                )
            )
            self.S_z += (
                1
                / 6
                * (
                    (self.y[row] + self.y[row + 1])
                    * (self.z[row + 1] * self.y[row] - self.z[row] * self.y[row + 1])
                )
            )
            self.I_yy += (
                1
                / 12
                * (
                    (
                        self.z[row + 1] ** 2
                        + (self.z[row] + self.z[row + 1]) * self.z[row]
                    )
                    * (self.z[row + 1] * self.y[row] - self.z[row] * self.y[row + 1])
                )
            )
            self.I_zz += (
                1
                / 12
                * (
                    (
                        self.y[row + 1] ** 2
                        + (self.y[row] + self.y[row + 1]) * self.y[row]
                    )
                    * (self.z[row + 1] * self.y[row] - self.z[row] * self.y[row + 1])
                )
            )
            self.I_yz += (
                1
                / 12
                * (
                    1 / 2 * self.y[row + 1] ** 2 * self.z[row] ** 2
                    - 1 / 2 * self.y[row] ** 2 * self.z[row + 1] ** 2
                    - (self.z[row + 1] * self.y[row] - self.z[row] * self.y[row + 1])
                    * (self.y[row] * self.z[row] + self.y[row + 1] * self.z[row + 1])
                )
            )

        self.ys = self.S_z / self.A
        self.zs = self.S_y / self.A

        self.I_yy = self.I_yy - self.zs**2 * self.A
        self.I_zz = self.I_zz - self.ys**2 * self.A
        self.I_yz = self.I_yz + self.ys * self.zs * self.A

        

        print("Area", self.A)

        print("First moment of area in y-direction", self.S_y)

        print("Second moment of area in y-direction", self.I_yy)

        self.list_names.append("Area")
        self.list_names.append("First moment of area in y-direction Sy")
        self.list_names.append("First moment of area in z-direction Sz")
        self.list_names.append("Second moment of area about y-Axis Iyy")
        self.list_names.append("Second moment of area about z-Axis Izz")

        self.list_unit.append("m**2")
        self.list_unit.append("m**3")
        self.list_unit.append("m**3")
        self.list_unit.append("m**4")
        self.list_unit.append("m**4")

        self.list_value.append(self.A)
        self.list_value.append(self.S_y)
        self.list_value.append(self.S_z)
        self.list_value.append(self.I_yy)
        self.list_value.append(self.I_zz)

        return self.list_names, self.list_value, self.list_unit
    



# _y = [0,0,2,2]
# _z = [0,1,1,0]


# Test = cross_section_polygon(_y,_z)