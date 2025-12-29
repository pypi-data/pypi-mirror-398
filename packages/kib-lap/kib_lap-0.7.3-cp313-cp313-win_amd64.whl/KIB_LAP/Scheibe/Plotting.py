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
        self.A = self.m.AssembleMatrix  # Assembled_Matrices

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

    def _point_in_poly(self, x, y, poly):
        """
        Ray casting: True wenn Punkt (x,y) im Polygon (convex/concave) liegt.
        poly: shape (n,2)
        """
        inside = False
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            cond = ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-30) + x1)
            if cond:
                inside = not inside
        return inside

    def _mask_points_in_mesh(self, xy_points):
        """
        xy_points: array shape (N,2)
        returns: bool mask shape (N,) -> True if point lies inside any element polygon
        """
        NL = np.asarray(self.m.Meshing.NL, float)
        EL = np.asarray(self.m.Meshing.EL, int)

        mask = np.zeros((xy_points.shape[0],), dtype=bool)

        # Optional: Precompute polygons once (speed-up)
        polys = []
        for el in EL:
            poly = np.array([NL[nid - 1] for nid in el], dtype=float)
            polys.append(poly)

        for k, (x, y) in enumerate(xy_points):
            inside_any = False
            for poly in polys:
                if self._point_in_poly(float(x), float(y), poly):
                    inside_any = True
                    break
            mask[k] = inside_any

        return mask

    def _mask_cut_points_in_mesh(self, cut_direction, cut_position, coords_1d):
        """
        coords_1d: array der Koordinate entlang der Cut-Achse
                  (y bei x=const, x bei y=const)
        returns: bool mask gleicher Länge, True wenn Punkt in irgendeinem Element liegt
        """
        if cut_direction.lower() == "x":
            xy = np.column_stack([np.full_like(coords_1d, float(cut_position)), coords_1d.astype(float)])
        else:
            xy = np.column_stack([coords_1d.astype(float), np.full_like(coords_1d, float(cut_position))])
        return self._mask_points_in_mesh(xy)

    # ---------- plots ----------
    def plot_mesh(self, show_node_ids=False, show_elem_ids=False, show_springs=True, spring_scale=1.0):
        fig, ax = plt.subplots()
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True)

        # elements
        for e, el in enumerate(self.m.Meshing.EL):
            coords = self._element_coords(el)
            ax.add_patch(patches.Polygon(coords, closed=True, fill=False, edgecolor="r", linewidth=1.0))

            if show_elem_ids:
                c = coords.mean(axis=0)
                ax.text(c[0], c[1], str(e + 1), fontsize=9, ha="center", va="center")

        # nodes
        if show_node_ids:
            NL = np.asarray(self.m.Meshing.NL, float)
            ax.scatter(NL[:, 0], NL[:, 1], s=15)
            for i, (x, y) in enumerate(NL, start=1):
                ax.text(x, y, str(i), fontsize=9, ha="right", va="bottom")

        xmin, xmax, ymin, ymax = self._mesh_bounds()
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)

        if show_springs:
            self._add_springs_to_ax(ax, spring_scale=spring_scale)

        plt.show()

    def plot_deflected_interactive(self, factor0=1000.0, factor_max=5000.0, show_undeformed=True,
                                  show_springs=True, spring_scale=1.0):
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
                    ux = ue[2 * local_i + 0]
                    uy = ue[2 * local_i + 1]
                    coords_def.append([x0 + ux * factor, y0 + uy * factor])
                coords_def.append(coords_def[0])
                poly_def[e].set_xy(coords_def)
            fig.canvas.draw_idle()

        s_factor.on_changed(_update)
        _update(factor0)

        if show_springs:
            self._add_springs_to_ax(ax, spring_scale=spring_scale)

        plt.show()

    def plot_inner_element_forces(self, field="sigma_x", show_principal=False, show_springs=True, spring_scale=1.0):
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
                R = np.sqrt((0.5 * (sx - sy)) ** 2 + txy ** 2)
                s1 = s_avg + R
                s2 = s_avg - R
                theta = 0.5 * np.arctan2(2.0 * txy, (sx - sy))

                c = coords.mean(axis=0)
                L = 0.15 * max((coords[:, 0].max() - coords[:, 0].min()),
                               (coords[:, 1].max() - coords[:, 1].min()), 1e-9)
                c1 = "b" if s1 > 0 else "r"
                c2 = "b" if s2 > 0 else "r"
                ax.arrow(c[0], c[1], L * np.cos(theta), L * np.sin(theta),
                         head_width=0.03 * L, head_length=0.03 * L, fc=c1, ec=c1)
                ax.arrow(c[0], c[1], L * np.cos(theta + np.pi / 2), L * np.sin(theta + np.pi / 2),
                         head_width=0.03 * L, head_length=0.03 * L, fc=c2, ec=c2)

        xmin, xmax, ymin, ymax = self._mesh_bounds(pad_rel=0.05)
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_title(field)

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        fig.colorbar(sm, ax=ax, orientation="vertical", label=field)

        if show_springs:
            self._add_springs_to_ax(ax, spring_scale=spring_scale)

        plt.show()

    def plot_stress_along_cut(self, cut_position, cut_direction="x", field="sigma_x",
                              ngrid=250, method="linear",
                              restrict_to_mesh=True, show_cut_line=False):
        """
        Plot along a straight cut line with interpolation of element-center values.

        IMPORTANT FIX:
          If restrict_to_mesh=True, points on the cut that lie outside the actual mesh
          (e.g. holes / gaps in multi-patch) are removed by geometric masking.

        cut_direction:
            "x" -> vertical line x = cut_position (plot vs y)
            "y" -> horizontal line y = cut_position (plot vs x)

        field:
            "sigma_x" | "sigma_y" | "tau_xy" | "n_x" | "n_y" | "n_xy"
        """
        if not hasattr(self.m, "stress_elem_avg"):
            self.m.CalculateInnerElementForces_Gauss()

        field_idx = {
            "sigma_x": 0, "sigma_y": 1, "tau_xy": 2,
            "n_x": 0, "n_y": 1, "n_xy": 2
        }
        if field not in field_idx:
            raise ValueError(f"Unknown field '{field}'. Choose from {list(field_idx.keys())}")

        use_n = field.startswith("n_")
        j = field_idx[field]

        # Element centers and values
        n_elem = len(self.m.Meshing.EL)
        centroids = np.zeros((n_elem, 2), dtype=float)
        vals = np.zeros(n_elem, dtype=float)

        for e, el in enumerate(self.m.Meshing.EL):
            coords = self._element_coords(el)
            centroids[e, :] = coords.mean(axis=0)
            vals[e] = float(self.m.n_elem_avg[e, j] if use_n else self.m.stress_elem_avg[e, j])

        # Interpolation bounds (centroid-based)
        xmin, ymin = centroids.min(axis=0)
        xmax, ymax = centroids.max(axis=0)

        # clamp cut_position
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

        # Extract cut
        if cut_direction.lower() == "x":
            cut_index = int(np.argmin(np.abs(grid_x[:, 0] - cut_position)))
            cut_vals = grid_z[cut_index, :]
            cut_coords = grid_y[cut_index, :]
            xlabel = "y"
            title = f"{field} along x = {cut_position:.6g}"
        else:
            cut_index = int(np.argmin(np.abs(grid_y[0, :] - cut_position)))
            cut_vals = grid_z[:, cut_index]
            cut_coords = grid_x[:, cut_index]
            xlabel = "x"
            title = f"{field} along y = {cut_position:.6g}"

        # Remove NaNs
        mask = np.isfinite(cut_vals)
        if mask.sum() < 5:
            print("WARNING: Almost no values on cut (NaNs). Try method='nearest' or choose another cut_position.")
            return

        xplot = cut_coords[mask]
        yplot = cut_vals[mask]

        # IMPORTANT: remove points outside actual mesh (holes / gaps)
        if restrict_to_mesh:
            geom_mask = self._mask_cut_points_in_mesh(cut_direction, cut_position, xplot)
            xplot = xplot[geom_mask]
            yplot = yplot[geom_mask]

            if len(xplot) < 5:
                print("WARNING: Cut is mostly outside mesh (after geometric masking). Choose another cut_position.")
                return

        vmin = float(np.min(yplot))
        vmax = float(np.max(yplot))

        plt.figure()
        plt.plot(xplot, yplot, label=title)

        # Min / Max lines
        plt.axhline(vmin, linestyle="--", linewidth=1, label=f"min = {vmin:.4g}")
        plt.axhline(vmax, linestyle="--", linewidth=1, label=f"max = {vmax:.4g}")

        # Info box
        info = f"min = {vmin:.4g}\nmax = {vmax:.4g}"
        plt.gca().text(
            0.02, 0.98, info,
            transform=plt.gca().transAxes,
            va="top",
            ha="left",
            bbox=dict(boxstyle="round", alpha=0.8)
        )

        plt.xlabel(xlabel)
        plt.ylabel(field)
        plt.grid(True)
        plt.legend()
        plt.title(title)
        plt.tight_layout()
        plt.show()

        # Optional: show cut line on mesh (quick visual check)
        if show_cut_line:
            fig, ax = plt.subplots()
            ax.set_aspect("equal", adjustable="box")
            ax.grid(True)

            # mesh outline
            NL = np.asarray(self.m.Meshing.NL, float)
            EL = np.asarray(self.m.Meshing.EL, int)
            for el in EL:
                coords = np.array([NL[nid - 1] for nid in el], float)
                ax.add_patch(patches.Polygon(coords, closed=True, fill=False, edgecolor="0.7", linewidth=1.0))

            xmin2, xmax2, ymin2, ymax2 = self._mesh_bounds(pad_rel=0.05)
            ax.set_xlim(xmin2, xmax2)
            ax.set_ylim(ymin2, ymax2)

            if cut_direction.lower() == "x":
                ax.axvline(cut_position, linestyle="--")
            else:
                ax.axhline(cut_position, linestyle="--")

            plt.show()

    # ---------- springs overlay ----------
    def _draw_springs(self, ax, NL, Lref, spring_scale=0.05, show_k=False):
        """
        Draw spring symbols for boundary conditions from self.A.BC.
        Expects BC columns: No, DOF, cf in [MN/m]  (optional)
        """
        if not hasattr(self.A, "BC"):
            return []

        bc = self.A.BC
        arts = []

        def spring_poly(L=1.0, nzig=6, amp=0.15):
            xs = np.linspace(0, L, 2 * nzig + 1)
            ys = np.zeros_like(xs)
            for k in range(1, len(xs) - 1):
                ys[k] = amp * (1 if k % 2 else -1)
            return np.column_stack([xs, ys])

        for i in range(len(bc)):
            node = bc["No"].iloc[i]
            dof = str(bc["DOF"].iloc[i]).strip().lower()

            if not str(node).isdigit():
                continue
            node = int(node)

            x, y = NL[node - 1]

            Ls = spring_scale * 0.25 * Lref
            amp = 0.10 * Ls
            pts = spring_poly(L=Ls, nzig=5, amp=amp)

            if dof == "x":
                pts[:, 0] *= -1.0
                pts[:, 0] += x
                pts[:, 1] += y
                line, = ax.plot(pts[:, 0], pts[:, 1], linewidth=1.5)
                arts.append(line)

                wall, = ax.plot([x - Ls, x - Ls], [y - 0.15 * Ls, y + 0.15 * Ls], linewidth=2.0)
                arts.append(wall)

                if show_k and "cf in [MN/m]" in bc.columns:
                    k = bc["cf in [MN/m]"].iloc[i]
                    txt = ax.text(x - 1.1 * Ls, y + 0.18 * Ls, f"k={k:g}", fontsize=8, ha="right")
                    arts.append(txt)

            elif dof == "z":
                X = pts[:, 0]
                Y = pts[:, 1]
                pts2 = np.column_stack([-Y, -X])  # rotation -90deg
                pts2[:, 0] += x
                pts2[:, 1] += y
                line, = ax.plot(pts2[:, 0], pts2[:, 1], linewidth=1.5)
                arts.append(line)

                wall, = ax.plot([x - 0.15 * Ls, x + 0.15 * Ls], [y - Ls, y - Ls], linewidth=2.0)
                arts.append(wall)

                if show_k and "cf in [MN/m]" in bc.columns:
                    k = bc["cf in [MN/m]"].iloc[i]
                    txt = ax.text(x + 0.18 * Ls, y - 1.1 * Ls, f"k={k:g}", fontsize=8, va="top")
                    arts.append(txt)

        return arts

    def _add_springs_to_ax(self, ax, spring_scale=1.0):
        NL = np.asarray(self.m.Meshing.NL, dtype=float)
        xmin, xmax, ymin, ymax = self._mesh_bounds(pad_rel=0.0)
        Lref = 0.15 * max(xmax - xmin, ymax - ymin, 1e-12)
        self._draw_springs(ax, NL, Lref, spring_scale=spring_scale)

    def plot_mesh_with_node_ids(self,
                            show_node_ids=True,
                            show_elem_ids=False,
                            show_springs=True,
                            spring_scale=1.0):
        """
        Backward compatibility wrapper.
        """
        return self.plot_mesh(
            show_node_ids=show_node_ids,
            show_elem_ids=show_elem_ids,
            show_springs=show_springs,
            spring_scale=spring_scale
        )


    def plot_load_vector_interactive(self,
                                    scale0=1.0,
                                    scale_max=20.0,
                                    show_node_ids=False,
                                    show_springs=True,
                                    spring_scale=1.0,
                                    show_loaded_labels=True):
        """
        Backward-compatible wrapper for interactive nodal load plotting.
        """
        import numpy as np
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        from matplotlib.widgets import Slider

        if not hasattr(self.A, "Load_Vector"):
            raise RuntimeError("Load_Vector not found. Call GenerateLoadVector() first.")

        NL = np.asarray(self.m.Meshing.NL, dtype=float)
        EL = np.asarray(self.m.Meshing.EL, dtype=int)

        Fx = self.A.Load_Vector[::2].astype(float)
        Fy = self.A.Load_Vector[1::2].astype(float)

        nN = NL.shape[0]
        if len(Fx) != nN:
            raise RuntimeError("Load_Vector size does not match number of nodes.")

        Fmag = np.sqrt(Fx**2 + Fy**2)
        Fmax = float(np.max(Fmag)) if np.max(Fmag) > 0 else 1.0

        xmin, ymin = NL.min(axis=0)
        xmax, ymax = NL.max(axis=0)
        Lref = 0.15 * max(xmax - xmin, ymax - ymin, 1e-12)

        fig, ax = plt.subplots()
        plt.subplots_adjust(bottom=0.18)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True)
        ax.set_title("Nodal load vector")

        ax.set_xlim(xmin - 0.1*Lref, xmax + 0.1*Lref)
        ax.set_ylim(ymin - 0.1*Lref, ymax + 0.1*Lref)

        # mesh
        for el in EL:
            coords = [NL[nid - 1] for nid in el]
            ax.add_patch(patches.Polygon(coords, closed=True, fill=False,
                                        edgecolor="0.7", linewidth=1.0))

        if show_node_ids:
            for i, (x, y) in enumerate(NL, start=1):
                ax.text(x, y, str(i), fontsize=8, ha="right", va="bottom")

        loaded = np.where((np.abs(Fx) > 1e-14) | (np.abs(Fy) > 1e-14))[0]

        arrow_art = [None] * nN
        for i in loaded:
            x, y = NL[i]
            arrow_art[i] = ax.arrow(x, y, 0.0, 0.0,
                                    head_width=0.05*Lref,
                                    head_length=0.07*Lref,
                                    length_includes_head=True)

            if show_loaded_labels:
                ax.text(x, y, f"{i+1}\n({Fx[i]:.2g},{Fy[i]:.2g})",
                        fontsize=7, ha="left", va="bottom")

        if show_springs:
            self._add_springs_to_ax(ax, spring_scale=spring_scale)

        ax_slider = plt.axes([0.15, 0.06, 0.70, 0.03])
        s_scale = Slider(ax_slider, "Scale", 0.0, scale_max, valinit=scale0)

        def _update(scale):
            for i in loaded:
                try:
                    arrow_art[i].remove()
                except Exception:
                    pass

                x, y = NL[i]
                dx = scale * Lref * Fx[i] / Fmax
                dy = scale * Lref * Fy[i] / Fmax

                arrow_art[i] = ax.arrow(
                    x, y, dx, dy,
                    head_width=0.05*Lref,
                    head_length=0.07*Lref,
                    length_includes_head=True
                )

            fig.canvas.draw_idle()

        s_scale.on_changed(_update)
        _update(scale0)

        plt.show()



    def plot_principal_membrane_forces(self,
                                    which="n1",
                                    mode="elem",
                                    draw_dirs=True,
                                    dir_scale=1.0,
                                    show_springs=True,
                                    spring_scale=1.0):
        """
        Plot principal membrane forces.
        which: "n1" or "n2"
        mode : "elem" (uses self.m.n_princ_elem_avg) or "node" (uses self.m.n_princ_node + nodal interpolation)
        draw_dirs: draw principal directions (theta)
        dir_scale: scale factor for direction arrows (relative)
        """

        import numpy as np
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        import matplotlib.cm as cm
        import matplotlib.colors as colors

        # ensure principal results exist
        if not hasattr(self.m, "n_princ_elem_avg"):
            # call solver with principal enabled
            self.m.CalculateInnerElementForces_Gauss(compute_nodal=(mode == "node"), compute_principal=True)

        NL = np.asarray(self.m.Meshing.NL, float)
        EL = np.asarray(self.m.Meshing.EL, int)

        idx = 0 if which == "n1" else 1
        title = f"principal membrane force {which}"

        # ----------------------------
        # values per element (preferred)
        # ----------------------------
        if mode.lower() == "elem":
            data = np.asarray(self.m.n_princ_elem_avg, float)  # (n_elem,3) [n1,n2,theta]
            vals = data[:, idx]
            thetas = data[:, 2]

            vmin, vmax = float(np.min(vals)), float(np.max(vals))
            if np.isclose(vmin, vmax):
                vmin -= 1.0
                vmax += 1.0

            norm = colors.Normalize(vmin=vmin, vmax=vmax)
            cmap = cm.viridis

            fig, ax = plt.subplots()
            ax.set_aspect("equal", adjustable="box")
            ax.grid(True)

            # reference length for arrows
            xmin, xmax, ymin, ymax = self._mesh_bounds(pad_rel=0.0)
            Lref = 0.12 * max(xmax - xmin, ymax - ymin, 1e-12) * dir_scale

            for e, el in enumerate(EL):
                coords = np.array([NL[nid - 1] for nid in el], float)
                poly = patches.Polygon(coords, closed=True, edgecolor="k", facecolor=cmap(norm(vals[e])))
                ax.add_patch(poly)

                if draw_dirs:
                    c = coords.mean(axis=0)
                    th = float(thetas[e])

                    # principal direction (theta) and orthogonal direction
                    dx1, dy1 = Lref*np.cos(th), Lref*np.sin(th)
                    dx2, dy2 = -Lref*np.sin(th), Lref*np.cos(th)

                    ax.arrow(c[0], c[1], dx1, dy1, head_width=0.12*Lref, head_length=0.12*Lref,
                            length_includes_head=True)
                    ax.arrow(c[0], c[1], dx2, dy2, head_width=0.12*Lref, head_length=0.12*Lref,
                            length_includes_head=True)

            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)
            ax.set_title(title)

            sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])
            fig.colorbar(sm, ax=ax, orientation="vertical", label=which)

            if show_springs:
                self._add_springs_to_ax(ax, spring_scale=spring_scale)

            plt.show()
            return

        # ----------------------------
        # nodal mode (smooth): node values -> element facecolor via averaging
        # ----------------------------
        if mode.lower() == "node":
            if not hasattr(self.m, "n_princ_node"):
                self.m.CalculateInnerElementForces_Gauss(compute_nodal=True, compute_principal=True)

            nnode = np.asarray(self.m.n_princ_node, float)  # (n_nodes,3)
            node_vals = nnode[:, idx]

            # element value = mean of its node values (simple, stable)
            vals = np.zeros((EL.shape[0],), float)
            thetas = np.zeros((EL.shape[0],), float)
            for e, el in enumerate(EL):
                ids = np.array(el, int) - 1
                vals[e] = float(np.mean(node_vals[ids]))
                thetas[e] = float(np.mean(nnode[ids, 2]))  # averaged theta (ok for structured meshes)

            vmin, vmax = float(np.min(vals)), float(np.max(vals))
            if np.isclose(vmin, vmax):
                vmin -= 1.0
                vmax += 1.0

            norm = colors.Normalize(vmin=vmin, vmax=vmax)
            cmap = cm.viridis

            fig, ax = plt.subplots()
            ax.set_aspect("equal", adjustable="box")
            ax.grid(True)

            xmin, xmax, ymin, ymax = self._mesh_bounds(pad_rel=0.0)
            Lref = 0.12 * max(xmax - xmin, ymax - ymin, 1e-12) * dir_scale

            for e, el in enumerate(EL):
                coords = np.array([NL[nid - 1] for nid in el], float)
                poly = patches.Polygon(coords, closed=True, edgecolor="k", facecolor=cmap(norm(vals[e])))
                ax.add_patch(poly)

                if draw_dirs:
                    c = coords.mean(axis=0)
                    th = float(thetas[e])
                    dx1, dy1 = Lref*np.cos(th), Lref*np.sin(th)
                    dx2, dy2 = -Lref*np.sin(th), Lref*np.cos(th)
                    ax.arrow(c[0], c[1], dx1, dy1, head_width=0.12*Lref, head_length=0.12*Lref,
                            length_includes_head=True)
                    ax.arrow(c[0], c[1], dx2, dy2, head_width=0.12*Lref, head_length=0.12*Lref,
                            length_includes_head=True)

            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)
            ax.set_title(title)

            sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])
            fig.colorbar(sm, ax=ax, orientation="vertical", label=which)

            if show_springs:
                self._add_springs_to_ax(ax, spring_scale=spring_scale)

            plt.show()
            return

        raise ValueError("mode must be 'elem' or 'node'")
