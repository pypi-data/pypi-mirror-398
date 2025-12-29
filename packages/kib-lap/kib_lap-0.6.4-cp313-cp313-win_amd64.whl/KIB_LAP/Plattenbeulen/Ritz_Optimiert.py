import numpy as np
from scipy.linalg import eig
try:
    import plate_buckling_cpp  # Import des kompilierten C++-Moduls
except:
    from KIB_LAP.Plattenbeulen import plate_buckling_cpp

class PlateBucklingRitz:
    def __init__(
        self,
        a,
        b,
        t,
        E,
        nu,
        Nx_params,
        Ny_params,
        Nxy,
        m_terms,
        n_terms,
        x_s_positions,
        I_s_values,
        A_s_values,
        y_s_positions,
        I_t_values,
        A_t_values
    ):
        # Initialisierung der Parameter
        self.a = a
        self.b = b
        self.t = t
        self.E = E
        self.nu = nu
        self.Nx0, self.Nx1 = Nx_params
        self.Ny0, self.Ny1 = Ny_params
        self.Nxy = Nxy
        self.m_terms = m_terms
        self.n_terms = n_terms
        self.x_s_positions = x_s_positions
        self.I_s_values = I_s_values
        self.A_s_values = A_s_values
        self.y_s_positions = y_s_positions
        self.I_t_values = I_t_values
        self.A_t_values = A_t_values

        self.num_terms = len(self.m_terms) * len(self.n_terms)

    def assemble_matrices(self):
        num_terms = self.num_terms
        index_map = {}
        idx = 0
        m_list = []
        n_list = []
        for m_i in self.m_terms:
            for n_i in self.n_terms:
                index_map[(m_i, n_i)] = idx
                m_list.append(m_i)
                n_list.append(n_i)
                idx += 1

        self.index_map = index_map  # Speichern für spätere Verwendung
        self.m_list = m_list
        self.n_list = n_list

        # Nach der Erstellung von m_list und n_list in assemble_matrices()
        self.stiffener_indices_m1 = []
        for idx, (m_i, n_i) in enumerate(zip(self.m_list, self.n_list)):
            if m_i == 1:
                # Überprüfen, ob dieser Term einen Beitrag von den Längssteifen hat
                # Angenommen, die Längssteifen beeinflussen alle DOFs, dies muss ggf. angepasst werden
                self.stiffener_indices_m1.append(idx)


        m_array = np.array(m_list, dtype=np.int32)
        n_array = np.array(n_list, dtype=np.int32)

        K_flat = np.zeros(num_terms * num_terms)
        G_flat = np.zeros(num_terms * num_terms)

        x_s_array = np.array(self.x_s_positions, dtype=np.float64)
        I_s_array = np.array(self.I_s_values, dtype=np.float64)
        A_s_array = np.array(self.A_s_values, dtype=np.float64)

        y_s_array = np.array(self.y_s_positions, dtype=np.float64)
        I_t_array = np.array(self.I_t_values, dtype=np.float64)
        A_t_array = np.array(self.A_t_values, dtype=np.float64)

        # Aufruf der angepassten C++-Funktion zur Assemblierung
        plate_buckling_cpp.assemble_matrices_with_stiffeners_cpp(
            m_array,
            n_array,
            self.a,
            self.b,
            self.Nx0,
            self.Nx1,
            self.Ny0,
            self.Ny1,
            self.Nxy,
            self.E,
            self.t,
            self.nu,
            x_s_array,
            I_s_array,
            A_s_array,
            y_s_array,
            I_t_array,
            A_t_array,
            K_flat,
            G_flat,
        )

        K = K_flat.reshape((num_terms, num_terms))
        G = G_flat.reshape((num_terms, num_terms))

        self.K = K
        self.G = G

    def solve_eigenvalue_problem(self):
        """
        Löse das Eigenwertproblem und bestimme die kritischen Beullasten.
        """
        self.assemble_matrices()
        eigenvalues, eigenvectors = eig(self.K, self.G)

        # Filtern der positiven Eigenwerte
        positive_idx = np.where(eigenvalues > 1e-8)[0]
        eigenvalues_positive = np.real(eigenvalues[positive_idx])
        eigenvectors_positive = np.real(eigenvectors[:, positive_idx])

        if len(eigenvalues_positive) == 0:
            raise ValueError(
                "Keine positiven Eigenwerte gefunden. Überprüfen Sie die Eingangsparameter."
            )

        # Sortieren der Eigenwerte und zugehörigen Eigenvektoren
        sorted_idx = eigenvalues_positive.argsort()
        eigenvalues_positive = eigenvalues_positive[sorted_idx]
        eigenvectors_positive = eigenvectors_positive[:, sorted_idx]

        self.eigenvalues = eigenvalues_positive
        self.eigenvectors = eigenvectors_positive


        # Analyse der Eigenvektoren, um die Modi mit m=1 zu identifizieren
        m_array = np.array(self.m_list)
        m_equals_one = (m_array == 1)
        fraction_m1_list = []
        for k in range(len(self.eigenvalues)):
            eigenvector = self.eigenvectors[:, k]
            total_contribution = np.sum(eigenvector**2)
            contribution_m1 = np.sum(eigenvector[m_equals_one]**2)
            fraction_m1 = contribution_m1 / total_contribution
            fraction_m1_list.append(fraction_m1)

        self.fraction_m1_array = np.array(fraction_m1_list)

        return self.eigenvalues, self.eigenvectors

    def get_mode_along_transverse_stiffener(self, y_s, eigenvector=None, num_points=100):
        """
        Berechnet den Verlauf der Beulform entlang einer Quersteife bei Position y_s.

        Parameters:
            y_s (float): Position der Quersteife in y-Richtung
            eigenvector (ndarray): Eigenvektor, der die Beulform definiert (Standard: erster Eigenvektor)
            num_points (int): Anzahl der Punkte in x-Richtung für die Darstellung

        Returns:
            x (ndarray): Array der x-Koordinaten
            W (ndarray): Verformungen W(x, y_s) entlang der Quersteife
        """
        if eigenvector is None:
            eigenvector = self.eigenvectors[:, 0]  # Standardmäßig erste Beulform

        x = np.linspace(0, self.a, num_points)
        W = np.zeros_like(x)

        idx = 0
        for m_i in self.m_terms:
            sin_m = np.sin(m_i * np.pi * x / self.a)
            for n_i in self.n_terms:
                sin_n = np.sin(n_i * np.pi * y_s / self.b)
                W += eigenvector[idx] * sin_m * sin_n
                idx += 1

        return x, W

    def plot_modes_along_transverse_stiffeners(self, modes=None, num_modes=1, num_points=100):
        """
        Plottet den Verlauf der Beulform entlang aller Quersteifen für die angegebenen Moden.

        Parameters:
            modes (list of int): Liste der zu plottenden Modenindizes. Wenn None, werden die ersten `num_modes` Moden geplottet.
            num_modes (int): Anzahl der zu plottenden Moden, wenn `modes` None ist.
            num_points (int): Anzahl der Punkte in x-Richtung für die Darstellung.
        """
        import matplotlib.pyplot as plt

        if not hasattr(self, 'eigenvalues'):
            self.solve_eigenvalue_problem()

        if modes is None:
            modes = list(range(num_modes))

        num_plots = len(modes)
        # Bestimmen der Anzahl der Zeilen und Spalten für die Subplots
        num_cols = 2  # Sie können dies nach Bedarf anpassen
        num_rows = (num_plots + num_cols - 1) // num_cols

        fig, axs = plt.subplots(num_rows, num_cols, figsize=(8 * num_cols, 6 * num_rows))
        axs = axs.flatten()

        for i, mode_idx in enumerate(modes):
            eigenvector = self.eigenvectors[:, mode_idx]
            ax = axs[i]
            for y_s in self.y_s_positions:
                x, W = self.get_mode_along_transverse_stiffener(y_s, eigenvector, num_points)
                ax.plot(x, W, label=f'y = {y_s:.2f} m')
            ax.set_xlabel('x (m)')
            ax.set_ylabel('Verformung $W(x, y_s)$')
            ax.set_title(f'Modus {mode_idx}: Verlauf entlang Quersteifen')
            ax.legend()
            ax.grid(True)

        # Verstecken von nicht genutzten Subplots
        for j in range(i + 1, len(axs)):
            fig.delaxes(axs[j])

        plt.tight_layout()
        plt.show()

    def get_critical_load_m1_mode(self, threshold=0.9):
        """
        Gibt die kleinste kritische Beullast für Modi mit m=1 zurück.

        Parameters:
        - threshold (float): Schwellenwert für den Anteil der m=1 Komponenten

        Returns:
        - lambda_cr_m1 (float): Kritischer Lastfaktor für m=1 Modus
        - eigenvector_m1 (ndarray): Eigenvektor des m=1 Modus
        """
        if not hasattr(self, 'eigenvalues'):
            self.solve_eigenvalue_problem()

        indices_m1_modes = np.where(self.fraction_m1_array >= threshold)[0]

        if len(indices_m1_modes) > 0:
            idx = indices_m1_modes[0]
            lambda_cr_m1 = self.eigenvalues[idx]
            eigenvector_m1 = self.eigenvectors[:, idx]
            self.plot_modes_along_transverse_stiffeners(None,10,100)
            return lambda_cr_m1, eigenvector_m1
        else:
            print("Auswahl des dominanten Modes:")
            self.plot_modes_along_transverse_stiffeners(None,10,100)    
            print("Auf der sicheren Seite liegend, kann der Wert 1 für die erste Eigenform angesetzt werden. ")
            mode = int(input(f"Vorgabe des anzusetzenden Eigenmodes: \n"))

            return self.eigenvalues[mode-1], self.eigenvectors[:, mode-1]   # -1, Da Matrix / Vektor-Zählweise

    def get_buckling_mode(self, eigenvector=None, num_points=50, normalize=True):
        """
        Berechnet die Beulform für einen gegebenen Eigenvektor.

        Parameters:
        - eigenvector (ndarray): Eigenvektor, der die Beulform definiert
        - num_points (int): Anzahl der Punkte in x- und y-Richtung für die Darstellung
        - normalize (bool): Ob die Beulform auf maximale Amplitude 1 normiert werden soll

        Returns:
        - X, Y (ndarray): Meshgrid der x- und y-Koordinaten
        - W (ndarray): Beulformwerte an den Gitterpunkten
        """
        m_terms = self.m_terms
        n_terms = self.n_terms
        a = self.a
        b = self.b
        x = np.linspace(0, a, num_points)
        y = np.linspace(0, b, num_points)
        X, Y = np.meshgrid(x, y)
        W = np.zeros_like(X)

        if eigenvector is None:
            eigenvector = self.eigenvectors[:, 0]  # Standardmäßig erste Beulform

        idx = 0
        for m in m_terms:
            for n in n_terms:
                phi = np.sin(m * np.pi * X / a) * np.sin(n * np.pi * Y / b)
                W += eigenvector[idx] * phi
                idx += 1

        if normalize:
            max_W = np.max(np.abs(W))
            if max_W != 0:
                W = W / max_W

        return X, Y, W

    def get_critical_load(self):
        """
        Gibt die kleinste kritische Beullast zurück.

        Returns:
        - lambda_cr (float): Kritischer Lastfaktor
        - eigenvector (ndarray): Eigenvektor zur kleinsten kritischen Last
        """
        if not hasattr(self, 'eigenvalues'):
            self.solve_eigenvalue_problem()

        lambda_cr = self.eigenvalues[0]
        eigenvector = self.eigenvectors[:, 0]
        return lambda_cr, eigenvector

    def write_latex_output(
        self, filename, include_k_matrix=False, include_g_matrix=False, matrix_size=10
    ):
        """
        Schreibt die Dokumentation der Berechnung in eine LaTeX-Datei.

        Parameters:
        - filename (str): Pfad zur Ausgabedatei (.tex)
        - include_k_matrix (bool): Ob die Steifigkeitsmatrix K ausgegeben werden soll
        - include_g_matrix (bool): Ob die Massenmatrix G ausgegeben werden soll
        - matrix_size (int): Größe der auszuschreibenden Matrix (z.B. 10 für eine 10x10 Matrix)
        """
        # Stellen Sie sicher, dass die Matrizen und Eigenwerte berechnet sind
        if not hasattr(self, "K") or not hasattr(self, "G"):
            self.assemble_matrices()
        if not hasattr(self, "eigenvalues") or not hasattr(self, "eigenvectors"):
            self.solve_eigenvalue_problem()

        with open(filename, "w", encoding="utf-8") as f:
            # Präambel
            f.write(r"\documentclass{article}" + "\n")
            f.write(r"\usepackage{amsmath, amssymb, booktabs, geometry}" + "\n")
            f.write(r"\usepackage{graphicx}" + "\n")
            f.write(r"\usepackage[utf8]{inputenc}" + "\n")  # UTF-8 Eingabe
            f.write(r"\usepackage[T1]{fontenc}" + "\n")  # Schriftkodierung
            f.write(r"\usepackage{lmodern}" + "\n")  # Latin Modern Schriftart
            f.write(r"\usepackage{psfrag,epsfig}" + "\n")
            f.write(r"\usepackage{siunitx}")
            f.write(
                r"\allowdisplaybreaks % Erlaubt Seitenumbrüche in Gleichungsumgebungen"
                + "\n"
            )
            f.write(r"\geometry{a4paper, margin=1in}" + "\n")
            f.write(r"\begin{document}" + "\n\n")

            # Titel
            f.write(r"\title{Dokumentation der Plattenbeulanalyse}" + "\n")
            f.write(r"\author{Erstellt mit PlateBucklingRitz}" + "\n")
            f.write(r"\date{\today}" + "\n")
            f.write(r"\maketitle" + "\n\n")

            # Einleitung
            f.write(r"\section{Einleitung}" + "\n")
            f.write(
                "Diese Dokumentation enthält die Ergebnisse der Plattenbeulanalyse unter Verwendung der Ritz-Methode. "
                "Die Berechnung umfasst die Bestimmung der kritischen Beullasten sowie der zugehörigen Beulformen.\n\n"
            )

            # Parameterübersicht in einer Tabelle
            f.write(r"\section{Eingangsparameter}" + "\n")
            f.write(
                "Die folgenden Tabellen fassen die Eingangsparameter der Berechnung zusammen.\n\n"
            )

            f.write(r"\begin{table}[h!]" + "\n")
            f.write(r"\centering" + "\n")
            f.write(r"\begin{tabular}{ll}" + "\n")
            f.write(r"\toprule" + "\n")
            f.write(r"\textbf{Parameter} & \textbf{Wert} \\" + "\n")
            f.write(r"\midrule" + "\n")
            # Tabelle mit den Eingangsparametern
            f.write(f"Länge der Platte in x-Richtung, $a$ (m) & {self.a} \\\\" + "\n")
            f.write(f"Breite der Platte in y-Richtung, $b$ (m) & {self.b} \\\\" + "\n")
            f.write(f"Dicke der Platte, $t$ (m) & {self.t} \\\\" + "\n")
            f.write(f"Elastizitätsmodul, $E$ (MPa) & {self.E} \\\\" + "\n")
            f.write(f"Poissonzahl, $\\nu$ & {self.nu} \\\\" + "\n")
            f.write(
                f"Normalkraft in x-Richtung, $N_x(y)$ (MN/m) & $N_{{x0}}$ = {self.Nx0}, $N_{{x1}}$ = {self.Nx1} \\\\"
                + "\n"
            )
            f.write(
                f"Normalkraft in y-Richtung, $N_y(x)$ (MN/m) & $N_{{y0}}$ = {self.Ny0}, $N_{{y1}}$ = {self.Ny1} \\\\"
                + "\n"
            )
            f.write(
                f"Schubkraft pro Längeneinheit, $N_{{xy}}$ (MN/m) & {self.Nxy} \\\\"
                + "\n"
            )
            f.write(f"Ansatzfunktionen: m & {self.m_terms} \\\\" + "\n")
            f.write(f"Ansatzfunktionen: n & {self.n_terms} \\\\" + "\n")
            f.write(
                f"Positionen der Quersteifen (x-Richtung) (m) & {self.x_s_positions} \\\\"
                + "\n"
            )
            f.write(
                f"Flächenmomente der Quersteifen (m$^4$) & {self.I_s_values} \\\\"
                + "\n"
            )
            f.write(
                f"Positionen der Längssteifen (y-Richtung) (m) & {self.y_s_positions} \\\\"
                + "\n"
            )
            f.write(
                f"Flächenmomente der Längssteifen (m$^4$) & {self.I_t_values} \\\\"
                + "\n"
            )
            f.write(r"\bottomrule" + "\n")
            f.write(r"\end{tabular}" + "\n")
            f.write(r"\caption{Übersicht der Eingangsparameter}" + "\n")
            f.write(r"\label{tab:input_parameters}" + "\n")
            f.write(r"\end{table}" + "\n\n")

            # Eigenwerte
            f.write(r"\section{Eigenwerte und Kritische Lasten}" + "\n")
            f.write(
                "Die folgenden Eigenwerte repräsentieren die kritischen Beullasten der Platte. "
                "Nur die positiven Eigenwerte werden berücksichtigt.\n\n"
            )

            # Tabelle der Eigenwerte
            f.write(r"\begin{table}[htbp!]" + "\n")
            f.write(r"\centering" + "\n")
            f.write(r"\begin{tabular}{|c|c|}" + "\n")
            f.write(r"\hline" + "\n")
            f.write(r"Index & Kritische Last ($\lambda_{\text{cr}}$) \\" + "\n")
            f.write(r"\hline" + "\n")
            for idx, eigenvalue in enumerate(self.eigenvalues[0:10]):
                f.write(f"{idx+1} & {eigenvalue:.4f} \\\\" + "\n")
                f.write(r"\hline" + "\n")
            f.write(r"\end{tabular}" + "\n")
            f.write(r"\caption{Liste der positiven Eigenwerte}" + "\n")
            f.write(r"\label{tab:eigenvalues}" + "\n")
            f.write(r"\end{table}" + "\n\n")

            f.write(r"\clearpage" + "\n")

            # Kritische Beulspannung
            f.write(r"\subsection{Kritische Beulspannung}" + "\n")
            f.write(
                "Die kleinste kritische Beullast ist der erste Eigenwert und entspricht der "
                "kritischen Beulspannung der Platte.\n\n"
            )
            f.write(r"\begin{flalign*}" + "\n")
            f.write(r"& \lambda_{\text{cr}} = " + f"{self.eigenvalues[0]:.4f} & " + "\n")
            f.write(r"\end{flalign*}" + "\n\n")


            f.write(
                "Für den Beulwert für das maßgebende Gesamtfeldbeulen gilt: \n\n"
            )
            f.write(r"\begin{flalign*}" + "\n")
            f.write(r"& \lambda_{\text{cr}} = " + f"{self.get_critical_load_m1_mode()[0]:.4f} & " + "\n")
            f.write(r"\end{flalign*}" + "\n\n")

            # Weitere Berechnungen (z.B. sigma_e, k_sigma, k_tau)
            sigma_e = (
                np.pi**2 * self.E / (12 * (1 - self.nu**2)) * (self.t / self.b) ** 2
            )
            k_sigma = self.eigenvalues[0] * self.Nx0 / self.t / sigma_e
            k_tau = self.eigenvalues[0] * self.Nxy / self.t / sigma_e

            f.write(r"\subsection{Zusätzliche Berechnungen}" + "\n")
            f.write(
                "Basierend auf der kleinsten kritischen Last werden weitere Spannungen berechnet:\n\n"
            )
            f.write(r"\begin{align}" + "\n")
            f.write(
                f"k_\\sigma &= \\frac{{\\lambda_{{\\text{{cr}}}} \\cdot N_x0}}{{t \\cdot \\sigma_e}} = {k_sigma:.4f} \\\\"
                + "\n"
            )
            f.write(
                f"k_\\tau &= \\frac{{\\lambda_{{\\text{{cr}}}} \\cdot N_{{xy}}}}{{t \\cdot \\sigma_e}} = {k_tau:.4f}"
                + "\n"
            )
            f.write(r"\end{align}" + "\n\n")

            f.write(r"Hierbei ist $\sigma_e$ gegeben durch: \\" + "\n")
            f.write(r"\begin{equation}" + "\n")
            f.write(
                r"\sigma_e = \frac{\pi^2 E}{12(1-\nu^2)} \left(\frac{t}{b}\right)^2 = "
                + f"{sigma_e:.4f} , "
                + r"\si{MN/m^2}"
                + "\n"
            )
            f.write(r"\end{equation} " + "\n")

            # Optionale Ausgabe der Steifigkeitsmatrix K
            if include_k_matrix:
                f.write(r"\section{Steifigkeitsmatrix $K$}" + "\n")
                f.write(
                    f"Die Steifigkeitsmatrix $K$ wird bis zur Größe {matrix_size}x{matrix_size} angezeigt.\n\n"
                )
                f.write(r"\begin{table}[htbp!]" + "\n")
                f.write(r"\centering" + "\n")
                f.write(r"\begin{tabular}{|" + "c|" * (matrix_size + 1) + "}" + "\n")
                f.write(r"\hline" + "\n")
                # Korrigierte Header-Zeile ohne 'i'
                header = (
                    "Index & "
                    + " & ".join([f"$K_{{{j+1}}}$" for j in range(matrix_size)])
                    + r" \\"
                    + "\n"
                )
                f.write(header)
                f.write(r"\hline" + "\n")
                for i in range(matrix_size):
                    row = (
                        f"{i+1} & "
                        + " & ".join([f"{self.K[i,j]:.4e}" for j in range(matrix_size)])
                        + r" \\"
                        + "\n"
                    )
                    f.write(row)
                    f.write(r"\hline" + "\n")
                f.write(r"\end{tabular}" + "\n")
                f.write(r"\caption{Steifigkeitsmatrix $K$ (Teilansicht)}" + "\n")
                f.write(r"\label{tab:K_matrix}" + "\n")
                f.write(r"\end{table}" + "\n\n")

            # Optionale Ausgabe der Massenmatrix G
            if include_g_matrix:
                f.write(r"\section{Geometrische Steifigkeitsmatrix $G$}" + "\n")
                f.write(
                    f"Die geometrische Steifigkeitsmatrix $G$ wird bis zur Größe {matrix_size}x{matrix_size} angezeigt.\n\n"
                )
                f.write(r"\begin{table}[htbp!]" + "\n")
                f.write(r"\centering" + "\n")
                f.write(r"\begin{tabular}{|" + "c|" * (matrix_size + 1) + "}" + "\n")
                f.write(r"\hline" + "\n")
                # Korrigierte Header-Zeile ohne 'i'
                header = (
                    "Index & "
                    + " & ".join([f"$G_{{{j+1}}}$" for j in range(matrix_size)])
                    + r" \\"
                    + "\n"
                )
                f.write(header)
                f.write(r"\hline" + "\n")
                for i in range(matrix_size):
                    row = (
                        f"{i+1} & "
                        + " & ".join([f"{self.G[i,j]:.4e}" for j in range(matrix_size)])
                        + r" \\"
                        + "\n"
                    )
                    f.write(row)
                    f.write(r"\hline" + "\n")
                f.write(r"\end{tabular}" + "\n")
                f.write(r"\caption{Massenmatrix $G$ (Teilansicht)}" + "\n")
                f.write(r"\label{tab:G_matrix}" + "\n")
                f.write(r"\end{table}" + "\n\n")

            # Eigenvektoren (Beulformen)
            f.write(r"\section{Eigenvektoren (Beulformen)}" + "\n")
            f.write(
                "Die Eigenvektoren entsprechen den Beulformen der Platte für die jeweiligen kritischen Lasten.\n\n"
            )

            # Beispiel für die erste Beulform
            f.write(r"\subsection{Beulform für die kleinste kritische Last}" + "\n")
            f.write(
                "Die folgende Abbildung zeigt die Beulform der Platte für die kleinste kritische Last.\n\n"
            )

            # Berechnung und Einfügen der Beulform
            X, Y, W = self.get_buckling_mode()
            # Speichern der Beulform als Bild
            plot_filename = "buckling_mode"
            # Plotten beider Eigenformen nebeneinander
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D

            fig = plt.figure(figsize=(16, 6))

            # Plot für die erste Eigenform
            ax1 = fig.add_subplot(1, 2, 1, projection="3d")
            ax1.plot_surface(X_first, Y_first, W_first, cmap="viridis", alpha=0.5)
            ax1.set_xlabel("x (m)")
            ax1.set_ylabel("y (m)")
            ax1.set_zlabel("w (m)")
            ax1.set_title("Erste Eigenform (kleinste kritische Last)")

            # Plotten der Längssteifen (x-Richtung)
            for x_s, I_s in zip(plate.x_s_positions, plate.I_s_values):
                if I_s > 1e-8:
                    x_idx = (np.abs(X_first[0, :] - x_s)).argmin()
                    x_val = X_first[0, x_idx]
                    y_vals = Y_first[:, x_idx]
                    w_vals = W_first[:, x_idx]
                    ax1.plot([x_val] * len(y_vals), y_vals, w_vals, color="black", linewidth=10)

            # Plotten der Quersteifen (y-Richtung)
            for y_s, I_t in zip(plate.y_s_positions, plate.I_t_values):
                if I_t > 1e-8:
                    y_idx = (np.abs(Y_first[:, 0] - y_s)).argmin()
                    y_val = Y_first[y_idx, 0]
                    x_vals = X_first[y_idx, :]
                    w_vals = W_first[y_idx, :]
                    ax1.plot(x_vals, [y_val] * len(x_vals), w_vals, color="black", linewidth=10)

            # Plot für den dominanten m=1 Modus
            ax2 = fig.add_subplot(1, 2, 2, projection="3d")
            if X_m1 is not None:
                ax2.plot_surface(X_m1, Y_m1, W_m1, cmap="viridis", alpha=0.5)
                ax2.set_xlabel("x (m)")
                ax2.set_ylabel("y (m)")
                ax2.set_zlabel("w (m)")
                ax2.set_title("Dominanter Eigenmodus mit m=1")

                # Plotten der Längssteifen (x-Richtung)
                for x_s, I_s in zip(plate.x_s_positions, plate.I_s_values):
                    if I_s > 1e-8:
                        x_idx = (np.abs(X_m1[0, :] - x_s)).argmin()
                        x_val = X_m1[0, x_idx]
                        y_vals = Y_m1[:, x_idx]
                        w_vals = W_m1[:, x_idx]
                        ax2.plot([x_val] * len(y_vals), y_vals, w_vals, color="black", linewidth=10)

                # Plotten der Quersteifen (y-Richtung)
                for y_s, I_t in zip(plate.y_s_positions, plate.I_t_values):
                    if I_t > 1e-8:
                        y_idx = (np.abs(Y_m1[:, 0] - y_s)).argmin()
                        y_val = Y_m1[y_idx, 0]
                        x_vals = X_m1[y_idx, :]
                        w_vals = W_m1[y_idx, :]
                        ax2.plot(x_vals, [y_val] * len(x_vals), w_vals, color="black", linewidth=10)
            else:
                ax2.text(0.5, 0.5, 0.5, "Kein dominanter m=1 Modus gefunden.", ha='center')
                ax2.axis('off')
            plt.savefig(r"Dokumentation/Abbildungen/" + plot_filename + ".png")
            plt.savefig(r"Dokumentation/Abbildungen/" + plot_filename + ".eps", format="eps")
            plt.close(fig)

            # Einfügen des Bildes in LaTeX
            f.write(r"\begin{figure}[h!]" + "\n")
            f.write(r"\centering" + "\n")
            f.write(
                r"\includegraphics[width=0.8\textwidth]{Abbildungen/"
                + f"{plot_filename}.eps"
                + "}"
                + "\n"
            )
            f.write(
                r"\caption{Beulform der Platte für die kleinste kritische Last}" + "\n"
            )
            f.write(r"\label{fig:buckling_mode}" + "\n")
            f.write(r"\end{figure}" + "\n\n")

            # Abschluss des Dokuments
            f.write(r"\end{document}" + "\n")

        print(f"LaTeX-Dokument erfolgreich erstellt: {filename}")

