import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.cm as cm
import matplotlib.colors as colors
from matplotlib.widgets import Slider

from scipy.interpolate import griddata

class ShellPlotter:
    def __init__(self, model):
        """
        model: ShellCalculation Instanz (hat Meshing, AssembleMatrix, stress_elem_avg, ...)
        """
        self.m = model
        self.A = self.m.AssembleMatrix     # Assembled_Matrices

    # ---------- helpers ----------
    def _mesh_bounds(self, pad_rel=0.05, pad_abs=0.0):
        """
        Robuste Auto-Achsen: aus NL min/max + Rand.
        pad_rel: relativer Rand (5% der Größe)
        pad_abs: absoluter Rand (z.B. 0.1 m)
        """
        NL = np.asarray(self.m.Meshing.NL, dtype=float)
        xmin, ymin = NL.min(axis=0)
        xmax, ymax = NL.max(axis=0)
        dx = max(xmax - xmin, 1e-12)
        dy = max(ymax - ymin, 1e-12)
        pad = max(pad_abs, pad_rel * max(dx, dy))
        return xmin - pad, xmax + pad, ymin - pad, ymax + pad

    def _element_coords(self, el):
        return np.array([self.m.Meshing.NL[nid - 1] for nid in el], dtype=float)

    # ---------- plots ----------
    def plot_mesh(self, show_node_ids=False, show_elem_ids=False):
        fig, ax = plt.subplots()
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True)

        # elements
        for e, el in enumerate(self.m.Meshing.EL):
            coords = self._element_coords(el)
            ax.add_patch(patches.Polygon(coords, closed=True, fill=False, edgecolor="r", linewidth=1.0))

            if show_elem_ids:
                c = coords.mean(axis=0)
                ax.text(c[0], c[1], str(e+1), fontsize=9, ha="center", va="center")

        # nodes
        if show_node_ids:
            for i, node in enumerate(self.m.Meshing.NL):
                ax.scatter(node[0], node[1])
                ax.text(node[0], node[1], str(i+1), fontsize=9, ha="right")

        xmin, xmax, ymin, ymax = self._mesh_bounds()
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        plt.show()

    def plot_deflected_interactive(self, factor0=1000.0, factor_max=5000.0, show_undeformed=True):
        mesh = self.m.Meshing
        EL = mesh.EL
        NL = mesh.NL



        fig, ax = plt.subplots()
        plt.subplots_adjust(bottom=0.18)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True)

        xmin, xmax, ymin, ymax = self._mesh_bounds(pad_rel=0.08)
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)

        # undeformed
        if show_undeformed:
            for el in EL:
                coords = [NL[nid - 1] for nid in el]
                coords.append(coords[0])
                ax.add_patch(patches.Polygon(coords, closed=True, fill=False, edgecolor="0.7", linewidth=1.0))

        # deflected artists
        poly_def = []
        for _ in EL:
            p = patches.Polygon([[0, 0]], closed=True, fill=False, edgecolor="r", linewidth=1.5)
            ax.add_patch(p)
            poly_def.append(p)

        ax_slider = plt.axes([0.15, 0.06, 0.70, 0.03])
        s_factor = Slider(ax_slider, "Scale", 0.0, factor_max, valinit=factor0)

        # prefetch displacements (interleaved per element column)
        Ue = self.m.AssembleMatrix.disp_element_matrix  # shape (8, NoE)

        def _update(factor):
            for e, el in enumerate(EL):
                coords_def = []
                ue = Ue[:, e]
                for local_i, nid in enumerate(el):
                    x0, y0 = NL[nid - 1]
                    ux = ue[2*local_i + 0]
                    uy = ue[2*local_i + 1]
                    coords_def.append([x0 + ux * factor, y0 + uy * factor])
                coords_def.append(coords_def[0])
                poly_def[e].set_xy(coords_def)
            fig.canvas.draw_idle()

        s_factor.on_changed(_update)
        _update(factor0)
        self._add_springs_to_ax(ax, spring_scale=1.0)
        plt.show()

    def plot_inner_element_forces(self, field="sigma_x", show_principal=False):
        if not hasattr(self.m, "stress_elem_avg"):
            self.m.CalculateInnerElementForces_Gauss()

        field_idx = {"sigma_x": 0, "sigma_y": 1, "tau_xy": 2,
                     "n_x": 0, "n_y": 1, "n_xy": 2}

        use_n = field.startswith("n_")
        j = field_idx[field]

        vals = (self.m.n_elem_avg[:, j] if use_n else self.m.stress_elem_avg[:, j])
        vals = np.asarray(vals, dtype=float)

        vmin, vmax = float(vals.min()), float(vals.max())
        if np.isclose(vmin, vmax):
            vmin -= 1.0
            vmax += 1.0

        norm = colors.Normalize(vmin=vmin, vmax=vmax)
        cmap = cm.viridis

        fig, ax = plt.subplots()
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True)

        for e, el in enumerate(self.m.Meshing.EL):
            coords = self._element_coords(el)

            polygon = patches.Polygon(coords, closed=True, edgecolor="k", facecolor=cmap(norm(vals[e])))
            ax.add_patch(polygon)

            if show_principal and (not use_n):
                sx, sy, txy = self.m.stress_elem_avg[e, :]
                s_avg = 0.5 * (sx + sy)
                R = np.sqrt((0.5*(sx - sy))**2 + txy**2)
                s1 = s_avg + R
                s2 = s_avg - R
                theta = 0.5 * np.arctan2(2.0*txy, (sx - sy))

                c = coords.mean(axis=0)
                L = 0.15 * max((coords[:,0].max()-coords[:,0].min()),
                               (coords[:,1].max()-coords[:,1].min()), 1e-9)
                c1 = "b" if s1 > 0 else "r"
                c2 = "b" if s2 > 0 else "r"
                ax.arrow(c[0], c[1], L*np.cos(theta), L*np.sin(theta),
                         head_width=0.03*L, head_length=0.03*L, fc=c1, ec=c1)
                ax.arrow(c[0], c[1], L*np.cos(theta+np.pi/2), L*np.sin(theta+np.pi/2),
                         head_width=0.03*L, head_length=0.03*L, fc=c2, ec=c2)

        xmin, xmax, ymin, ymax = self._mesh_bounds(pad_rel=0.05)
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_title(field)

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        fig.colorbar(sm, ax=ax, orientation="vertical", label=field)
        self._add_springs_to_ax(ax, spring_scale=1.0)
        plt.show()

    def plot_stress_along_cut(self, cut_position, cut_direction="x", field="sigma_x",
                            ngrid=250, method="linear"):
        """
        Plot of a stress component along a straight cut line (x=const or y=const),
        using interpolation of element-center values.

        cut_direction: "x" -> vertical line x=cut_position (plot vs y)
                    "y" -> horizontal line y=cut_position (plot vs x)
        field: "sigma_x" | "sigma_y" | "tau_xy" | "n_x" | "n_y" | "n_xy"
        """



        # Ensure stresses exist
        if not hasattr(self.m, "stress_elem_avg"):
            self.m.CalculateInnerElementForces_Gauss()

        field_idx = {"sigma_x": 0, "sigma_y": 1, "tau_xy": 2,
                    "n_x": 0, "n_y": 1, "n_xy": 2}

        if field not in field_idx:
            raise ValueError(f"Unknown field '{field}'. Choose from {list(field_idx.keys())}")

        use_n = field.startswith("n_")
        j = field_idx[field]

        # Element centers + values
        centroids = np.zeros((len(self.m.Meshing.EL), 2), dtype=float)
        vals = np.zeros((len(self.m.Meshing.EL),), dtype=float)

        for e, el in enumerate(self.m.Meshing.EL):
            coords = np.array([self.m.Meshing.NL[nid - 1] for nid in el], dtype=float)
            centroids[e, :] = coords.mean(axis=0)
            vals[e] = float(self.m.n_elem_avg[e, j] if use_n else self.m.stress_elem_avg[e, j])

        # --- IMPORTANT: grid bounds like the OLD function (centroid bounds) ---
        xmin, ymin = centroids.min(axis=0)
        xmax, ymax = centroids.max(axis=0)

        # --- clamp cut_position to valid interpolation range (old behavior) ---
        if cut_direction.lower() == "x":
            cut_position = float(np.clip(cut_position, xmin, xmax))
        elif cut_direction.lower() == "y":
            cut_position = float(np.clip(cut_position, ymin, ymax))
        else:
            raise ValueError("cut_direction must be 'x' or 'y'")

        # Interpolation grid
        grid_x, grid_y = np.mgrid[
            xmin:xmax:complex(ngrid),
            ymin:ymax:complex(ngrid)
        ]

        grid_z = griddata(centroids, vals, (grid_x, grid_y), method=method)

        if cut_direction.lower() == "x":
            cut_index = int(np.argmin(np.abs(grid_x[:, 0] - cut_position)))
            cut_vals = grid_z[cut_index, :]
            cut_coords = grid_y[cut_index, :]
            xlabel = "y"
            title = f"{field} along x={cut_position:.6g}"
        else:
            cut_index = int(np.argmin(np.abs(grid_y[0, :] - cut_position)))
            cut_vals = grid_z[:, cut_index]
            cut_coords = grid_x[:, cut_index]
            xlabel = "x"
            title = f"{field} along y={cut_position:.6g}"

        # NaNs rausmaskieren
        mask = np.isfinite(cut_vals)
        if mask.sum() < 5:
            print("WARNING: Almost no values on cut (NaNs). Try method='nearest' or choose another cut_position.")
            return

        plt.figure()
        plt.plot(cut_coords[mask], cut_vals[mask], label=title)
        plt.xlabel(xlabel)
        plt.ylabel(field)
        plt.grid(True)
        plt.legend()
        plt.title(title)
        plt.show()

    def plot_load_vector_interactive(self, scale0=1.0, scale_max=20.0, show_node_ids=False,
                                    show_springs=True, spring_scale=1.0, show_loaded_labels=True):
        import numpy as np
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        from matplotlib.widgets import Slider

        if not hasattr(self.A, "Load_Vector"):
            raise RuntimeError("Load_Vector not found. Call GenerateLoadVector() first.")

        # >>> EINHEITLICH: immer Meshing verwenden <<<
        NL = np.asarray(self.m.Meshing.NL, dtype=float)
        EL = np.asarray(self.m.Meshing.EL, dtype=int)

        Fx = self.A.Load_Vector[::2].astype(float)
        Fz = self.A.Load_Vector[1::2].astype(float)

        # Safety: falls Load_Vector länger/kürzer als NL*2 ist
        nN = NL.shape[0]
        if len(Fx) != nN or len(Fz) != nN:
            raise RuntimeError(
                f"Size mismatch: NL has {nN} nodes, but Load_Vector implies {len(Fx)} nodes. "
                "Check assembly / PD / Load_Vector creation."
            )

        Fmag = np.sqrt(Fx**2 + Fz**2)
        Fmax = float(np.max(Fmag)) if np.max(Fmag) > 0 else 1.0

        xmin, ymin = NL.min(axis=0)
        xmax, ymax = NL.max(axis=0)
        Lref = 0.15 * max(xmax - xmin, ymax - ymin, 1e-12)
        pad = 0.06 * Lref

        fig, ax = plt.subplots()
        plt.subplots_adjust(bottom=0.18)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True)
        ax.set_title("Nodal load vector")

        ax.set_xlim(xmin - pad, xmax + pad)
        ax.set_ylim(ymin - pad, ymax + pad)

        # mesh
        for el in EL:
            coords = [NL[nid - 1] for nid in el]
            ax.add_patch(patches.Polygon(coords, closed=True, fill=False, edgecolor="0.7", linewidth=1.0))

        # node ids
        if show_node_ids:
            for i, (x, y) in enumerate(NL, start=1):
                ax.text(x, y, str(i), fontsize=8, ha="right", va="bottom")

        # detect loaded nodes
        loaded = np.where((np.abs(Fx) > 1e-14) | (np.abs(Fz) > 1e-14))[0]

        # optional: label loaded nodes with values (super hilfreich zum Debuggen)
        if show_loaded_labels:
            for i in loaded:
                x, y = NL[i]
                ax.text(x, y, f"{i+1}\n({Fx[i]:.2g},{Fz[i]:.2g})", fontsize=7, ha="left", va="bottom")

        # arrows artists
        arrow_art = [None] * nN
        for i in loaded:
            x, y = NL[i]
            arrow_art[i] = ax.arrow(x, y, 0.0, 0.0,
                                    head_width=0.05*Lref, head_length=0.07*Lref,
                                    length_includes_head=True)

        # springs overlay (on same NL!)
        if show_springs:
            self._draw_springs(ax, NL, Lref, spring_scale=spring_scale)

        ax_info = ax.text(
            0.02, 0.98, "",
            transform=ax.transAxes, ha="left", va="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
            fontsize=9
        )

        ax_slider = plt.axes([0.15, 0.06, 0.70, 0.03])
        s_scale = Slider(ax_slider, "Scale", 0.0, scale_max, valinit=scale0)

        def _update(scale):
            for i in loaded:
                a = arrow_art[i]
                if a is None:
                    continue
                try:
                    a.remove()
                except Exception:
                    pass

                x, y = NL[i]
                dx = scale * Lref * Fx[i] / Fmax
                dy = scale * Lref * Fz[i] / Fmax

                arrow_art[i] = ax.arrow(
                    x, y, dx, dy,
                    head_width=0.05*Lref, head_length=0.07*Lref,
                    length_includes_head=True
                )

            ax_info.set_text(f"loaded nodes = {len(loaded)}\nmax |F| = {Fmax:.4g}\nscale = {scale:.3g}")
            fig.canvas.draw_idle()

        s_scale.on_changed(_update)
        _update(scale0)
        plt.show()

    def _draw_springs(self, ax, NL, Lref, spring_scale=0.05, show_k=False):
        """
        Draw spring symbols for boundary conditions from self.A.BC.
        Expects BC columns: No, DOF, cf in [MN/m]  (optional)
        """
        import numpy as np

        if not hasattr(self.A, "BC"):
            # falls BC noch nicht geladen wurde
            return []

        bc = self.A.BC
        arts = []

        # simple "zig-zag" spring polyline (local coordinates along +x, later rotated)
        def spring_poly(L=1.0, nzig=6, amp=0.15):
            xs = np.linspace(0, L, 2*nzig + 1)
            ys = np.zeros_like(xs)
            for k in range(1, len(xs)-1):
                ys[k] = amp * (1 if k % 2 else -1)
            return np.column_stack([xs, ys])

        # Draw for each bc row
        for i in range(len(bc)):
            node = bc["No"].iloc[i]
            dof = str(bc["DOF"].iloc[i]).strip().lower()

            # nur numerische nodes hier (left/right könntest du optional auch auflösen)
            if not str(node).isdigit():
                continue
            node = int(node)

            x, y = NL[node-1]

            # length of symbol
            Ls = spring_scale * 0.25 * Lref
            amp = 0.10 * Ls

            pts = spring_poly(L=Ls, nzig=5, amp=amp)

            # 방향: x -> nach links zeichnen, z -> nach unten zeichnen (optisch)
            if dof == "x":
                # spring points to left from node
                pts[:, 0] *= -1.0
                pts[:, 0] += x
                pts[:, 1] += y
                line, = ax.plot(pts[:,0], pts[:,1], linewidth=1.5)
                arts.append(line)

                # small wall line
                wall, = ax.plot([x - Ls, x - Ls], [y - 0.15*Ls, y + 0.15*Ls], linewidth=2.0)
                arts.append(wall)

                if show_k and "cf in [MN/m]" in bc.columns:
                    k = bc["cf in [MN/m]"].iloc[i]
                    txt = ax.text(x - 1.1*Ls, y + 0.18*Ls, f"k={k:g}", fontsize=8, ha="right")
                    arts.append(txt)

            elif dof == "z":
                # rotate spring to point downward
                # take x as "along", y as "amp" then rotate -90deg
                X = pts[:,0]
                Y = pts[:,1]
                pts2 = np.column_stack([ -Y, -X ])  # rotation -90deg
                pts2[:,0] += x
                pts2[:,1] += y
                line, = ax.plot(pts2[:,0], pts2[:,1], linewidth=1.5)
                arts.append(line)

                wall, = ax.plot([x - 0.15*Ls, x + 0.15*Ls], [y - Ls, y - Ls], linewidth=2.0)
                arts.append(wall)

                if show_k and "cf in [MN/m]" in bc.columns:
                    k = bc["cf in [MN/m]"].iloc[i]
                    txt = ax.text(x + 0.18*Ls, y - 1.1*Ls, f"k={k:g}", fontsize=8, va="top")
                    arts.append(txt)

        return arts

    def _add_springs_to_ax(self, ax, spring_scale=1.0):
        NL = np.asarray(self.m.Meshing.NL, dtype=float)
        xmin, xmax, ymin, ymax = self._mesh_bounds(pad_rel=0.0)
        Lref = 0.15 * max(xmax - xmin, ymax - ymin, 1e-12)
        self._draw_springs(ax, NL, Lref, spring_scale=spring_scale)
