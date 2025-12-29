import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd


class MeshingClass:
    def __init__(self, d1, d2, num_x, num_y, elem_type):
        self._d1 = d1
        self._d2 = d2
        self._num_x = num_x
        self._num_y = num_y
        self._elem_type = elem_type
        self.PD = 2  # Problem-Dimension
        self.NoN = 0  # Number of Nodes NoN
        self.NoE = 0  # Number of Elements NoE
        self.NPE = 4 if elem_type == "rect" else 3  # Nodes per elements
        self.q = np.zeros((4, 2))
        self.NL = np.zeros((1, self.PD))
        self.EL = np.zeros((1, self.NPE))
        self.a = 0
        self.b = 0
        self.element_edges = {}  # Dictionary to store edges by element

    def get_NL(self):
        return self.NL

    def get_EL(self):
        return self.EL

    def get_NPE(self):
        return self.NPE

    def general_mesh_input(self):
        self.q = np.array([[0, 0], [self._d1, 0], [0, self._d2], [self._d1, self._d2]])
        self.NoN = (self._num_x + 1) * (self._num_y + 1)
        self.NoE = self._num_x * self._num_y
        self.NL = np.zeros((self.NoN, self.PD))
        self.EL = np.zeros((self.NoE, self.NPE), dtype=int)
        self.a = (self.q[1, 0] - self.q[0, 0]) / self._num_x
        self.b = (self.q[2, 1] - self.q[0, 1]) / self._num_y

    def generating_rectangular_mesh(self):
        self.general_mesh_input()
        n = 0
        for i in range(1, self._num_y + 2):
            for j in range(1, self._num_x + 2):
                self.NL[n, 0] = self.q[0, 0] + (j - 1) * self.a
                self.NL[n, 1] = self.q[0, 1] + (i - 1) * self.b
                n += 1

        for i in range(1, self._num_y + 1):
            for j in range(1, self._num_x + 1):
                if j == 1:
                    self.EL[(i - 1) * self._num_x + j - 1, 0] = (i - 1) * (
                        self._num_x + 1
                    ) + j
                    self.EL[(i - 1) * self._num_x + j - 1, 1] = (
                        self.EL[(i - 1) * self._num_x + j - 1, 0] + 1
                    )
                    self.EL[(i - 1) * self._num_x + j - 1, 3] = (
                        self.EL[(i - 1) * self._num_x + j - 1, 0] + self._num_x + 1
                    )
                    self.EL[(i - 1) * self._num_x + j - 1, 2] = (
                        self.EL[(i - 1) * self._num_x + j - 1, 3] + 1
                    )
                else:
                    self.EL[(i - 1) * self._num_x + j - 1, 0] = self.EL[
                        (i - 1) * self._num_x + j - 2, 1
                    ]
                    self.EL[(i - 1) * self._num_x + j - 1, 3] = self.EL[
                        (i - 1) * self._num_x + j - 2, 2
                    ]
                    self.EL[(i - 1) * self._num_x + j - 1, 1] = (
                        self.EL[(i - 1) * self._num_x + j - 1, 0] + 1
                    )
                    self.EL[(i - 1) * self._num_x + j - 1, 2] = (
                        self.EL[(i - 1) * self._num_x + j - 1, 3] + 1
                    )

        self.generate_edges()

    def generating_quadrilateral_mesh(self, q):
        """
        Structured Q4 mesh on a general convex quadrilateral using bilinear mapping.

        q: array-like shape (4,2) with corner points in boundary order.
        Recommended order: [q1,q2,q3,q4] counter-clockwise (CCW).
        Example: q1 bottom-left, q2 bottom-right, q3 top-right, q4 top-left.
        """
        q = np.asarray(q, dtype=float)
        if q.shape != (4, 2):
            raise ValueError("q must have shape (4,2)")

        # Store corners
        self.q = q.copy()

        # Setup sizes
        self.NoN = (self._num_x + 1) * (self._num_y + 1)
        self.NoE = self._num_x * self._num_y
        self.NL = np.zeros((self.NoN, self.PD))
        self.EL = np.zeros((self.NoE, self.NPE), dtype=int)

        # For plotting margins: use average edge lengths / divisions
        Lx = 0.5 * (np.linalg.norm(q[1] - q[0]) + np.linalg.norm(q[2] - q[3]))
        Ly = 0.5 * (np.linalg.norm(q[3] - q[0]) + np.linalg.norm(q[2] - q[1]))
        self.a = Lx / self._num_x
        self.b = Ly / self._num_y

        # Bilinear map from (s,t) in [0,1]^2
        q1, q2, q3, q4 = q[0], q[1], q[2], q[3]

        def map_st(s, t):
            return (1 - s) * (1 - t) * q1 + s * (1 - t) * q2 + s * t * q3 + (1 - s) * t * q4

        # Create nodes (same numbering scheme as your rectangular mesh)
        n = 0
        for i in range(0, self._num_y + 1):
            t = i / self._num_y if self._num_y > 0 else 0.0
            for j in range(0, self._num_x + 1):
                s = j / self._num_x if self._num_x > 0 else 0.0
                xy = map_st(s, t)
                self.NL[n, 0] = xy[0]
                self.NL[n, 1] = xy[1]
                n += 1

        # Create elements connectivity (identical pattern as rectangular case)
        # Node numbering: row-major
        for i in range(1, self._num_y + 1):
            for j in range(1, self._num_x + 1):
                # bottom-left node id in this cell
                n1 = (i - 1) * (self._num_x + 1) + j
                n2 = n1 + 1
                n4 = n1 + (self._num_x + 1)
                n3 = n4 + 1

                e = (i - 1) * self._num_x + (j - 1)
                self.EL[e, :] = [n1, n2, n3, n4]

        self.generate_edges()

    def read_q_from_csv(self, filepath="Meshing_Params_q.csv"):
        """
        Liest 4 Eckpunkte q aus CSV mit Spalten 'x[m]' und 'y[m]'.
        Rückgabe: np.array shape (4,2)
        """
        df = pd.read_csv(filepath)

        # toleranter Umgang mit Spaltennamen (falls mal ohne [m])
        cols = [c.strip() for c in df.columns]
        df.columns = cols

        xcol = "x[m]" if "x[m]" in df.columns else ("x" if "x" in df.columns else None)
        ycol = "y[m]" if "y[m]" in df.columns else ("y" if "y" in df.columns else None)
        if xcol is None or ycol is None:
            raise ValueError(f"CSV muss Spalten 'x[m]'/'y[m]' oder 'x'/'y' enthalten. Gefunden: {list(df.columns)}")

        if len(df) != 4:
            raise ValueError(f"CSV muss genau 4 Punkte enthalten, gefunden: {len(df)}")

        q = df[[xcol, ycol]].to_numpy(dtype=float)
        return q

    def generating_quadrilateral_mesh_from_csv(self, filepath="Meshing_Params_q.csv"):
        """
        Convenience: liest q aus CSV und erzeugt direkt das Mesh.
        """
        q = self.read_q_from_csv(filepath)
        self.generating_quadrilateral_mesh(q)

    def generate_edges(self):
        for el_index, el in enumerate(self.EL):
            edges = {
                "left": (el[0], el[3]),
                "bottom": (el[0], el[1]),
                "right": (el[1], el[2]),
                "top": (el[2], el[3]),
            }
            for orientation in edges:
                edges[orientation] = tuple(sorted(edges[orientation]))
            self.element_edges[el_index] = edges

    def _tol(self):
        # typische Elementgröße als Toleranzmaß
        a = float(getattr(self, "a", 0.0))
        b = float(getattr(self, "b", 0.0))
        h = max(a, b, 1e-12)
        return 1e-6 * h  # z.B. 1e-6 der Elementgröße

    def get_left_border_nodes(self, tol=None):
        NL = np.asarray(self.NL, dtype=float)
        if tol is None:
            tol = self._tol()
        x_min = float(NL[:, 0].min())
        return [i + 1 for i, x in enumerate(NL[:, 0]) if abs(x - x_min) <= tol]

    def get_right_border_nodes(self, tol=None):
        NL = np.asarray(self.NL, dtype=float)
        if tol is None:
            tol = self._tol()
        x_max = float(NL[:, 0].max())
        return [i + 1 for i, x in enumerate(NL[:, 0]) if abs(x - x_max) <= tol]

    def get_bottom_border_nodes(self, tol=None):
        NL = np.asarray(self.NL, dtype=float)
        if tol is None:
            tol = self._tol()
        y_min = float(NL[:, 1].min())
        return [i + 1 for i, y in enumerate(NL[:, 1]) if abs(y - y_min) <= tol]

    def get_top_border_nodes(self, tol=None):
        NL = np.asarray(self.NL, dtype=float)
        if tol is None:
            tol = self._tol()
        y_max = float(NL[:, 1].max())
        return [i + 1 for i, y in enumerate(NL[:, 1]) if abs(y - y_max) <= tol]

    def get_element_edges(self):
        return self.element_edges

    def get_coordinate_x(self, node_nr):
        for i in range(0, len(self.EL), 1):
            for j in range(0, len(self.EL[0]), 1):
                index = int(self.EL[i][j])

                if index == node_nr:
                    return self.NL[index - 1][0]

    def get_coordinate_z(self, node_nr):
        for i in range(0, len(self.EL), 1):
            for j in range(0, len(self.EL[0]), 1):
                index = int(self.EL[i][j])

                if index == node_nr:
                    return self.NL[index - 1][1]


    # ============================================================
    # MERGE / STITCH SUPPORT
    # ============================================================

    def merge_with_mesh(self, other, tol=None):
        """
        Vereint self-Mesh und other-Mesh, indem Knoten mit gleichen Koordinaten
        (bis tol) zusammengeführt werden. EL bleibt 1-based.
        """
        if tol is None:
            tol = max(self._tol(), other._tol())

        NL_A = np.asarray(self.NL, float)
        EL_A = np.asarray(self.EL, int)
        NL_B = np.asarray(other.NL, float)
        EL_B = np.asarray(other.EL, int)

        # spatial hash on A
        def key(pt):
            return (round(pt[0] / tol), round(pt[1] / tol))

        hashA = {}
        for i, pt in enumerate(NL_A, start=1):  # 1-based ids
            hashA[key(pt)] = i

        NL = NL_A.tolist()
        mapB = {}  # old B node id -> merged node id

        for j, pt in enumerate(NL_B, start=1):
            k = key(pt)
            if k in hashA:
                mapB[j] = hashA[k]
            else:
                NL.append([pt[0], pt[1]])
                mapB[j] = len(NL)

        # remap B elements
        EL_B_new = np.zeros_like(EL_B)
        for e in range(EL_B.shape[0]):
            for a in range(EL_B.shape[1]):
                EL_B_new[e, a] = mapB[int(EL_B[e, a])]

        # combine
        self.NL = np.asarray(NL, float)
        self.EL = np.vstack([EL_A, EL_B_new]).astype(int)

        self.NoN = len(self.NL)
        self.NoE = len(self.EL)

        # edges aktualisieren
        self.element_edges = {}
        self.generate_edges()

        # optional: mapping speichern
        self.merge_map_other_nodes = mapB


    # in MeshingClass ergänzen
    def translate(self, dx=0.0, dy=0.0):
        self.NL[:, 0] += float(dx)
        self.NL[:, 1] += float(dy)


    def plot_mesh(self,
                show_node_numbers=True,
                show_element_numbers=False,
                node_fontsize=7,
                elem_fontsize=8,
                ax=None):
        """
        Plottet das aktuelle Mesh (NL, EL) inkl. optionaler
        Knoten- und Elementnummern.
        """

        NL = np.asarray(self.NL, float)
        EL = np.asarray(self.EL, int)

        if ax is None:
            fig, ax = plt.subplots(figsize=(7, 6))

        # -------------------------
        # Elemente zeichnen
        # -------------------------
        for e, el in enumerate(EL):
            node_ids = el - 1  # 0-based
            coords = NL[node_ids, :]

            poly = np.vstack([coords, coords[0]])
            ax.plot(poly[:, 0], poly[:, 1], color="black", linewidth=0.8)

            if show_element_numbers:
                xc = coords[:, 0].mean()
                yc = coords[:, 1].mean()
                ax.text(
                    xc, yc, f"E{e+1}",
                    color="red",
                    fontsize=elem_fontsize,
                    ha="center", va="center",
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.6)
                )

        # -------------------------
        # Knoten plotten
        # -------------------------
        ax.scatter(NL[:, 0], NL[:, 1], s=10, color="black", zorder=3)

        if show_node_numbers:
            for i, (x, y) in enumerate(NL):
                ax.text(
                    x, y, f"N{i+1}",
                    color="blue",
                    fontsize=node_fontsize,
                    ha="right", va="bottom",
                    zorder=4,
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.6)
                )

        # -------------------------
        # Plot-Layout
        # -------------------------
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.set_title("Finite-Element-Netz")

        plt.tight_layout()
        plt.show()
