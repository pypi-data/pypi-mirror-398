import numpy as np
import matplotlib.pyplot as plt

class PolygonSection:
    def __init__(self, vertices=None):
        """
        Initialisiert das Polygon mit den gegebenen Eckpunkten.

        Parameter:
        vertices (Liste von Listen): Nx2-Array der Polygoneckpunkte [[y, z], [y, z], ...]
        """
        if vertices is None:
            vertices = []

        self.vertices = np.array(vertices)
        self.original_vertices = self.vertices.copy()

        # Extrahieren der y- und z-Koordinaten
        self.y_coords = self.vertices[:, 0]
        self.z_coords = self.vertices[:, 1]

        self.len = len(self.vertices)

        # Initialisierung der Querschnittsgrößen
        self.A = 0
        self.S_y = 0
        self.S_z = 0
        self.I_yy = 0
        self.I_zz = 0
        self.I_yz = 0
        self.ys = 0
        self.zs = 0

        if self.len > 0:
            self.calculate_area()
            self.calculate_first_moments()
            self.calculate_centroid()
            self.calculate_second_moments()
            self.calculate_deviation_moment_yz()

    # Berechnung der Querschnittsgrößen

    def calculate_area(self):
        self.A = 0
        n = self.len
        for i in range(n):
            j = (i + 1) % n
            self.A += 0.5 * (self.z_coords[j] * self.y_coords[i] - self.z_coords[i] * self.y_coords[j])

    def calculate_first_moments(self):
        self.S_y = 0
        self.S_z = 0
        n = self.len
        for i in range(n):
            j = (i + 1) % n
            common = self.y_coords[i] * self.z_coords[j] - self.y_coords[j] * self.z_coords[i]
            self.S_y += (self.z_coords[i] + self.z_coords[j]) * common
            self.S_z += (self.y_coords[i] + self.y_coords[j]) * common
        self.S_y /= 6
        self.S_z /= 6

    def calculate_centroid(self):
        # Berechnet den Schwerpunkt des Polygons
        self.ys = self.S_y / self.A
        self.zs = self.S_z / self.A
        self.centroid = np.array([self.ys, self.zs])

    def calculate_second_moments(self):
        self.I_yy = 0
        self.I_zz = 0
        n = self.len
        for i in range(n):
            j = (i + 1) % n
            common = self.y_coords[i] * self.z_coords[j] - self.y_coords[j] * self.z_coords[i]
            Iyy_term = (self.z_coords[i]**2 + self.z_coords[i]*self.z_coords[j] + self.z_coords[j]**2) * common
            Izz_term = (self.y_coords[i]**2 + self.y_coords[i]*self.y_coords[j] + self.y_coords[j]**2) * common
            self.I_yy += Iyy_term
            self.I_zz += Izz_term
        self.I_yy = self.I_yy / 12 - self.zs**2 * self.A  # Steiner-Anteil
        self.I_zz = self.I_zz / 12 - self.ys**2 * self.A  # Steiner-Anteil

    def calculate_deviation_moment_yz(self):
        self.I_yz = 0
        n = self.len
        for i in range(n):
            j = (i + 1) % n
            common = self.y_coords[i] * self.z_coords[j] - self.y_coords[j] * self.z_coords[i]
            term = (self.y_coords[i]*self.z_coords[j] + 2*self.y_coords[i]*self.z_coords[i] +
                    2*self.y_coords[j]*self.z_coords[j] + self.y_coords[j]*self.z_coords[i])
            self.I_yz += term * common
        self.I_yz = self.I_yz / 24 - self.ys * self.zs * self.A  # Steiner-Anteil

    # Funktionen zur Manipulation des Polygons

    def rotate(self, angle_degrees):
        """
        Rotiert das Polygon um seinen Schwerpunkt um den angegebenen Winkel.

        Parameter:
        angle_degrees (float): Rotationswinkel in Grad.
        """
        angle_radians = np.deg2rad(angle_degrees)
        # Translation zum Ursprung (Schwerpunkt am Ursprung)
        translated_polygon = self.original_vertices - self.centroid
        # Rotationsmatrix erstellen
        rotation_matrix = np.array([
            [np.cos(angle_radians), -np.sin(angle_radians)],
            [np.sin(angle_radians),  np.cos(angle_radians)]
        ])
        # Polygon rotieren
        rotated_polygon = np.dot(translated_polygon, rotation_matrix)
        # Zurück zum ursprünglichen Ort verschieben
        self.vertices = rotated_polygon + self.centroid
        # Aktualisieren der Koordinaten
        self.y_coords = self.vertices[:, 0]
        self.z_coords = self.vertices[:, 1]
        # Aktualisieren der ursprünglichen Vertices für weitere Rotationen
        self.original_vertices = self.vertices.copy()
        # Neu berechnen der Querschnittsgrößen
        self.calculate_area()
        self.calculate_first_moments()
        self.calculate_centroid()
        self.calculate_second_moments()
        self.calculate_deviation_moment_yz()

    def calculate_section_width_at_height(self, height):
        """
        Berechnet die Breite des Querschnitts auf einer bestimmten Höhe (y-Wert).

        Parameter:
        height (float): Der y-Wert, bei dem die Querschnittsbreite berechnet werden soll.

        Rückgabe:
        float: Breite des Querschnitts an der angegebenen Höhe.
        """
        # Kanten des Polygons erhalten
        edges = []
        for i in range(len(self.vertices)):
            p1 = self.vertices[i]
            p2 = self.vertices[(i + 1) % len(self.vertices)]
            edges.append((p1, p2))

        # Schnittpunkte mit der horizontalen Linie auf der angegebenen Höhe finden
        intersections = []
        for p1, p2 in edges:
            if (p1[1] <= height <= p2[1]) or (p2[1] <= height <= p1[1]):
                if p1[1] != p2[1]:  # Division durch Null vermeiden
                    x_intersect = p1[0] + (height - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])
                    intersections.append(x_intersect)

        # Breite berechnen
        if len(intersections) >= 2:
            intersections.sort()
            return intersections[-1] - intersections[0]
        return 0.0

    # Plot-Funktion
    def plot(self, height=None):
        """
        Zeichnet das ursprüngliche und das aktuelle Polygon und optional eine horizontale Linie auf der angegebenen Höhe.

        Parameter:
        height (float, optional): Der y-Wert, bei dem eine horizontale Linie gezeichnet werden soll.
        """
        plt.figure()
        plt.plot(*self.original_vertices.T, 'b-', label='Ursprüngliches Polygon')
        plt.plot(*self.vertices.T, 'r-', label='Aktuelles Polygon')
        plt.fill(*self.original_vertices.T, 'b', alpha=0.3)
        plt.fill(*self.vertices.T, 'r', alpha=0.3)
        if height is not None:
            plt.axhline(y=height, color='g', linestyle='--', label=f'Höhe = {height}')
        plt.legend()
        plt.xlabel('y')
        plt.ylabel('z')
        plt.title('Polygon und Querschnittsbreite auf spezifischer Höhe')
        plt.axis('equal')
        plt.show()


# vertices = [
#     [0, 0],
#     [0.40, 0],
#     [0.40, 0.40],
#     [0, 0.40]
# ]

# polygon = PolygonSection(vertices)

# print("Fläche A:", polygon.A)
# print("Flächenträgheitsmoment I_yy:", polygon.I_yy)
# print("Flächenträgheitsmoment I_zz:", polygon.I_zz)
# print("Produktträgheitsmoment I_yz:", polygon.I_yz)
# print("Schwerpunkt ys:", polygon.ys)
# print("Schwerpunkt zs:", polygon.zs)