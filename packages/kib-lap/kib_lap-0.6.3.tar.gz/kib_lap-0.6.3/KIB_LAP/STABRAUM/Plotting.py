# ============================================================
# Plotting.py
# Reines Plotting-Modul für STABRAUM
# Erwartet ein AnalysisResults-Objekt:  res = calc.run()
# ============================================================

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
from matplotlib.widgets import Slider
from mpl_toolkits.mplot3d.art3d import Line3DCollection


# ------------------------------------------------------------
# Hilfsfunktion: gleiche Achsenskalierung im 3D
# ------------------------------------------------------------
def set_axes_equal_3d(ax, extra: float = 0.0):
    x_limits = np.array(ax.get_xlim3d(), dtype=float)
    y_limits = np.array(ax.get_ylim3d(), dtype=float)
    z_limits = np.array(ax.get_zlim3d(), dtype=float)

    ranges = np.array([np.ptp(lim) for lim in (x_limits, y_limits, z_limits)], dtype=float)
    max_range = float(max(ranges.max(), 1e-9))

    mids = np.array([lim.mean() for lim in (x_limits, y_limits, z_limits)], dtype=float)
    half = (1.0 + float(extra)) * max_range / 2.0

    ax.set_xlim3d(mids[0] - half, mids[0] + half)
    ax.set_ylim3d(mids[1] - half, mids[1] + half)
    ax.set_zlim3d(mids[2] - half, mids[2] + half)

    try:
        ax.set_box_aspect((1, 1, 1))
    except Exception:
        pass


# ============================================================
# StructurePlotter
# ============================================================
class StructurePlotter:
    """
    Reines Plotting.
    Erwartet ein AnalysisResults-Objekt (res = calc.run()).
    """

    def __init__(self, res):
        self.res = res
        self.Inp = res.Inp

        self.nodes = self.Inp.nodes
        self.na = self.Inp.members["na"]
        self.ne = self.Inp.members["ne"]

    # --------------------------------------------------------
    # Geometrie-Helfer
    # --------------------------------------------------------
    def _pt(self, n: int) -> np.ndarray:
        return np.array(
            [
                float(self.nodes["x[m]"][n - 1]),
                float(self.nodes["y[m]"][n - 1]),
                float(self.nodes["z[m]"][n - 1]),
            ],
            dtype=float,
        )

    def _tangent(self, a: int, e: int):
        Pi, Pj = self._pt(int(a)), self._pt(int(e))
        v = Pj - Pi
        L = float(np.linalg.norm(v))
        if L < 1e-15:
            raise ValueError("Elementlänge ~ 0")
        return Pi, Pj, v / L, L

    def _stable_normal(self, t: np.ndarray, prefer="y") -> np.ndarray:
        axes = {
            "x": np.array([1.0, 0.0, 0.0]),
            "y": np.array([0.0, 1.0, 0.0]),
            "z": np.array([0.0, 0.0, 1.0]),
        }
        u = axes.get(prefer, axes["y"])
        if abs(float(np.dot(t, u))) > 0.95:
            u = axes["z"] if prefer != "z" else axes["x"]

        w = np.cross(t, u)
        n = float(np.linalg.norm(w))
        if n < 1e-15:
            raise ValueError("Kein Orthogonalvektor")
        return w / n

    def _orth_unit_2d(self, xi, zi, xj, zj) -> np.ndarray:
        """
        Orthogonaler Einheitsvektor zur Stabachse in x-z-Ebene.
        """
        v = np.array([float(xj - xi), 0.0, float(zj - zi)], dtype=float)
        y_unit = np.array([0.0, 1.0, 0.0], dtype=float)
        perp = np.cross(v, y_unit)[[0, 2]]
        n = float(np.linalg.norm(perp))
        if n < 1e-15:
            raise ValueError("Elementlänge ~ 0")
        return perp / n

    def _field_map(self):
        return {
            "N": self.res.N_el_i_store,
            "VY": self.res.VY_el_i_store,
            "VZ": self.res.VZ_el_i_store,
            "MX": self.res.MX_el_i_store,
            "MY": self.res.MY_el_i_store,
            "MZ": self.res.MZ_el_i_store,
        }

    # ========================================================
    # 2D Struktur (x-z) + Nummerierung
    # ========================================================
    def plot_structure_2d(self, node_labels: bool = False, elem_labels: bool = False):
        fig, ax = plt.subplots(figsize=(10, 6))

        # Stäbe zeichnen
        for idx, (a, e) in enumerate(zip(self.na, self.ne), start=1):
            Pi, Pj = self._pt(int(a)), self._pt(int(e))
            ax.plot([Pi[0], Pj[0]], [Pi[2], Pj[2]], color="black", lw=1.0)

            # Elementnummer am Mittelpunkt
            if elem_labels:
                xm = 0.5 * (Pi[0] + Pj[0])
                zm = 0.5 * (Pi[2] + Pj[2])
                ax.text(
                    xm,
                    zm,
                    f"E{idx}",
                    fontsize=9,
                    ha="center",
                    va="center",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="gray", lw=0.5),
                )

        # Knotennummern
        if node_labels:
            n_nodes = len(self.nodes["x[m]"])
            for n in range(1, n_nodes + 1):
                P = self._pt(n)
                ax.plot(P[0], P[2], marker="o", markersize=3, color="black")
                ax.text(
                    P[0],
                    P[2],
                    f"N{n}",
                    fontsize=9,
                    ha="left",
                    va="bottom",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="gray", lw=0.5),
                )

        ax.set_xlabel("X [m]")
        ax.set_ylabel("Z [m]")
        ax.set_title("Unverformte Struktur (x-z)")
        ax.grid(True)
        ax.set_aspect("equal", adjustable="datalim")
        ax.relim()
        ax.autoscale_view()
        return fig, ax

    # ========================================================
    # 2D Endwerte (statisch)
    # ========================================================
    def plot_endforces_2d(
        self,
        kind="MY",
        scale=5.0,
        invert_y=False,
        node_labels=False,
        elem_labels=False,
    ):
        fig, ax = self.plot_structure_2d(node_labels=node_labels, elem_labels=elem_labels)
        Q = self._field_map()[kind.upper()]  # (nElem,2,1)

        for i, (a, e) in enumerate(zip(self.na, self.ne)):
            Pi, Pj = self._pt(int(a)), self._pt(int(e))
            ix, iz = Pi[0], Pi[2]
            jx, jz = Pj[0], Pj[2]

            try:
                u = self._orth_unit_2d(ix, iz, jx, jz)
            except ValueError:
                continue

            qa = float(Q[i, 0, 0])
            qb = float(Q[i, 1, 0])

            def endpt(x, z, val):
                if abs(val) < 1e-15:
                    return x, z
                col = "blue" if val >= 0 else "red"
                link = 0.05 * float(scale)
                cx = x + link * u[0] * val * float(scale)
                cz = z + link * u[1] * val * float(scale)
                ax.plot([x, cx], [z, cz], color=col, lw=1)
                ax.text(cx, cz, f"{kind}={val:.3f}", color=col, fontsize=8)
                return cx, cz

            ca = endpt(ix, iz, qa)
            cb = endpt(jx, jz, qb)

            # Verbindungslinie immer zeichnen
            ax.plot([ca[0], cb[0]], [ca[1], cb[1]], color="black", lw=1)

        ax.legend(
            handles=[
                mpatches.Patch(color="blue", label=f"{kind} ≥ 0"),
                mpatches.Patch(color="red", label=f"{kind} < 0"),
            ]
        )

        if invert_y:
            ax.invert_yaxis()

        ax.relim()
        ax.autoscale_view()
        return fig, ax

    # ========================================================
    # 2D Endwerte (DYNAMISCH, Slider für scale)
    # ========================================================
    def plot_endforces_2d_interactive(
        self,
        kind="MY",
        scale_init=5.0,
        invert_y=False,
        node_labels=False,
        elem_labels=False,
        robust_ref=True,
    ):
        fig, ax = self.plot_structure_2d(node_labels=node_labels, elem_labels=elem_labels)
        Q = self._field_map()[kind.upper()]  # (nElem,2,1)

        # Referenz (nur für sinnvolle Slider-Grenzen)
        vals = np.abs(Q[:, :, 0]).ravel()
        if vals.size == 0:
            qref = 1.0
        else:
            qref = float(np.percentile(vals, 95)) if robust_ref else float(vals.max())
            qref = max(qref, 1e-12)

        smin = 0.0
        smax = max(float(scale_init) * 50.0, 10.0)

        ax.legend(
            handles=[
                mpatches.Patch(color="blue", label=f"{kind} ≥ 0"),
                mpatches.Patch(color="red", label=f"{kind} < 0"),
            ]
        )

        def _mark_dyn(artist):
            try:
                artist._dyn = True
            except Exception:
                pass
            return artist

        def _clear_dyn():
            for ln in list(getattr(ax, "lines", [])):
                if getattr(ln, "_dyn", False):
                    ln.remove()
            for p in list(getattr(ax, "patches", [])):
                if getattr(p, "_dyn", False):
                    p.remove()
            for t in list(getattr(ax, "texts", [])):
                if getattr(t, "_dyn", False):
                    t.remove()

        def draw(scale):
            _clear_dyn()
            scale = float(scale)

            for i, (a, e) in enumerate(zip(self.na, self.ne)):
                Pi, Pj = self._pt(int(a)), self._pt(int(e))
                ix, iz = Pi[0], Pi[2]
                jx, jz = Pj[0], Pj[2]

                try:
                    u = self._orth_unit_2d(ix, iz, jx, jz)
                except ValueError:
                    continue

                qa = float(Q[i, 0, 0])
                qb = float(Q[i, 1, 0])

                def endpt(x, z, val):
                    if abs(val) < 1e-15:
                        return x, z
                    col = "blue" if val >= 0 else "red"
                    link = 0.05 * scale
                    cx = x + link * u[0] * val * scale
                    cz = z + link * u[1] * val * scale
                    ln = ax.plot([x, cx], [z, cz], color=col, lw=1)[0]
                    _mark_dyn(ln)
                    txt = ax.text(cx, cz, f"{kind}={val:.3f}", color=col, fontsize=8)
                    _mark_dyn(txt)
                    return cx, cz

                ca = endpt(ix, iz, qa)
                cb = endpt(jx, jz, qb)

                ln2 = ax.plot([ca[0], cb[0]], [ca[1], cb[1]], color="black", lw=1)[0]
                _mark_dyn(ln2)

            ax.relim()
            ax.autoscale_view()
            ax.set_aspect("equal", adjustable="datalim")
            if invert_y:
                ax.invert_yaxis()
            fig.canvas.draw_idle()

        fig.subplots_adjust(bottom=0.20)
        ax_scale = fig.add_axes([0.15, 0.08, 0.70, 0.03])
        s_scale = Slider(ax_scale, "Scale", smin, smax, valinit=float(scale_init))

        s_scale.on_changed(lambda _: draw(s_scale.val))
        draw(scale_init)

        return fig, ax, s_scale

    # ========================================================
    # 3D verformte Struktur (interaktiv) + Nummerierung
    # ========================================================
    def plot_structure_deformed_3d_interactive(
        self,
        scale_init=1.0,
        show_undeformed=True,
        node_labels=False,
        elem_labels=False,
    ):
        def ux(n): return float(self.res.u_ges[7 * (n - 1) + 0])
        def uy(n): return float(self.res.u_ges[7 * (n - 1) + 1])
        def uz(n): return float(self.res.u_ges[7 * (n - 1) + 3])

        fig = plt.figure(figsize=(9, 7))
        ax = fig.add_subplot(projection="3d")

        # unverformte Stäbe
        if show_undeformed:
            segs = []
            for a, e in zip(self.na, self.ne):
                segs.append([self._pt(int(a)), self._pt(int(e))])
            ax.add_collection3d(Line3DCollection(segs, colors="lightgray", linewidths=1, zorder=0))

        # deformierte Linien
        deformed_lines = []
        for a, e in zip(self.na, self.ne):
            a, e = int(a), int(e)
            Pi, Pj = self._pt(a), self._pt(e)

            xd = [Pi[0] + float(scale_init) * ux(a), Pj[0] + float(scale_init) * ux(e)]
            yd = [Pi[1] + float(scale_init) * uy(a), Pj[1] + float(scale_init) * uy(e)]
            zd = [Pi[2] + float(scale_init) * uz(a), Pj[2] + float(scale_init) * uz(e)]
            (ld,) = ax.plot(xd, yd, zd, lw=2, zorder=3)
            deformed_lines.append((a, e, ld))

        # Texte
        node_texts = []
        elem_texts = []

        if node_labels:
            n_nodes = len(self.nodes["x[m]"])
            for n in range(1, n_nodes + 1):
                P = self._pt(n)
                txt = ax.text(
                    P[0] + float(scale_init) * ux(n),
                    P[1] + float(scale_init) * uy(n),
                    P[2] + float(scale_init) * uz(n),
                    f"N{n}",
                    fontsize=8,
                    zorder=4,
                )
                node_texts.append((n, txt))

        if elem_labels:
            for idx, (a, e) in enumerate(zip(self.na, self.ne), start=1):
                a, e = int(a), int(e)
                Pi, Pj = self._pt(a), self._pt(e)
                xm = 0.5 * (Pi[0] + Pj[0]) + float(scale_init) * 0.5 * (ux(a) + ux(e))
                ym = 0.5 * (Pi[1] + Pj[1]) + float(scale_init) * 0.5 * (uy(a) + uy(e))
                zm = 0.5 * (Pi[2] + Pj[2]) + float(scale_init) * 0.5 * (uz(a) + uz(e))
                txt = ax.text(xm, ym, zm, f"E{idx}", fontsize=8, zorder=4)
                elem_texts.append((idx, a, e, txt))

        ax.set_xlabel("X [m]")
        ax.set_ylabel("Y [m]")
        ax.set_zlabel("Z [m]")
        ax.set_title("Verformte Struktur 3D (interaktiv)")

        set_axes_equal_3d(ax, extra=0.05)

        fig.subplots_adjust(bottom=0.18)
        ax_scale = fig.add_axes([0.15, 0.08, 0.7, 0.03])
        s_scale = Slider(ax_scale, "Scale", 0.0, float(scale_init) * 10000.0, valinit=float(scale_init))

        def update(_):
            s = float(s_scale.val)

            for a, e, line in deformed_lines:
                Pi, Pj = self._pt(a), self._pt(e)
                line.set_data_3d(
                    [Pi[0] + s * ux(a), Pj[0] + s * ux(e)],
                    [Pi[1] + s * uy(a), Pj[1] + s * uy(e)],
                    [Pi[2] + s * uz(a), Pj[2] + s * uz(e)],
                )

            for n, txt in node_texts:
                P = self._pt(n)
                txt.set_position((P[0] + s * ux(n), P[1] + s * uy(n)))
                txt.set_3d_properties(P[2] + s * uz(n), zdir="z")

            for idx, a, e, txt in elem_texts:
                Pi, Pj = self._pt(a), self._pt(e)
                xm = 0.5 * (Pi[0] + Pj[0]) + s * 0.5 * (ux(a) + ux(e))
                ym = 0.5 * (Pi[1] + Pj[1]) + s * 0.5 * (uy(a) + uy(e))
                zm = 0.5 * (Pi[2] + Pj[2]) + s * 0.5 * (uz(a) + uz(e))
                txt.set_position((xm, ym))
                txt.set_3d_properties(zm, zdir="z")

            set_axes_equal_3d(ax, extra=0.05)
            fig.canvas.draw_idle()

        s_scale.on_changed(update)
        update(None)
        return fig, ax, s_scale

    # ========================================================
    # 3D Schnittgrößen-Diagramm entlang der Stäbe (DYNAMISCH)
    # ========================================================
    def plot_diagram_3d_interactive(
        self,
        kind="MY",
        n_stations=30,
        scale_init=1.0,
        prefer_axis="y",
        show_structure=True,
        robust_ref=True,
        title=None,
    ):
        fig = plt.figure(figsize=(9, 7))
        ax = fig.add_subplot(projection="3d")
        Q = self._field_map()[kind.upper()]  # (nElem,2,1)

        vals = np.abs(Q[:, :, 0]).ravel()
        qref = float(np.percentile(vals, 95)) if (robust_ref and vals.size) else float(vals.max() if vals.size else 1.0)
        qref = max(qref, 1e-12)

        if show_structure:
            segs = []
            for a, e in zip(self.na, self.ne):
                segs.append([self._pt(int(a)), self._pt(int(e))])
            ax.add_collection3d(Line3DCollection(segs, colors="lightgray", linewidths=1, zorder=0))

        diagram_lines = []
        elem_cache = []
        prev_w = None

        for i, (a, e) in enumerate(zip(self.na, self.ne)):
            a, e = int(a), int(e)
            Pi, Pj, t, L = self._tangent(a, e)
            w = self._stable_normal(t, prefer=prefer_axis)
            if prev_w is not None and float(np.dot(w, prev_w)) < 0.0:
                w = -w
            prev_w = w

            qa = float(Q[i, 0, 0])
            qb = float(Q[i, 1, 0])

            s = np.linspace(0.0, L, int(n_stations))
            q = np.linspace(qa, qb, int(n_stations))
            elem_cache.append({"Pi": Pi, "t": t, "w": w, "s": s, "q": q})

            alpha0 = float(scale_init) / qref
            pts0 = Pi[None, :] + s[:, None] * t[None, :] + (alpha0 * q)[:, None] * w[None, :]
            (ln,) = ax.plot(pts0[:, 0], pts0[:, 1], pts0[:, 2], lw=2, zorder=3)
            diagram_lines.append(ln)

        ax.set_xlabel("X [m]")
        ax.set_ylabel("Y [m]")
        ax.set_zlabel("Z [m]")
        ax.set_title(title or f"{kind}-Diagramm 3D (interaktiv)  |  ref={qref:.3g}")
        set_axes_equal_3d(ax, extra=0.05)

        fig.subplots_adjust(bottom=0.18)
        ax_scale = fig.add_axes([0.15, 0.08, 0.7, 0.03])
        s_scale = Slider(ax_scale, "Scale", 0.0, float(scale_init) * 200.0, valinit=float(scale_init))

        def update(_):
            scale = float(s_scale.val)
            alpha = scale / qref
            for ln, cache in zip(diagram_lines, elem_cache):
                Pi = cache["Pi"]
                t = cache["t"]
                w = cache["w"]
                s = cache["s"]
                q = cache["q"]
                pts = Pi[None, :] + s[:, None] * t[None, :] + (alpha * q)[:, None] * w[None, :]
                ln.set_data_3d(pts[:, 0], pts[:, 1], pts[:, 2])

            set_axes_equal_3d(ax, extra=0.05)
            fig.canvas.draw_idle()

        s_scale.on_changed(update)
        update(None)
        return fig, ax, s_scale

    # ========================================================
    # Robust: dynamische Artists markieren/aufräumen (global)
    # ========================================================
    def _mark_dyn(self, artist):
        try:
            artist._dyn = True
        except Exception:
            pass
        return artist

    def _clear_dyn(self, ax):
        for coll in list(getattr(ax, "collections", [])):
            if getattr(coll, "_dyn", False):
                coll.remove()
        for ln in list(getattr(ax, "lines", [])):
            if getattr(ln, "_dyn", False):
                ln.remove()
        for p in list(getattr(ax, "patches", [])):
            if getattr(p, "_dyn", False):
                p.remove()
        for t in list(getattr(ax, "texts", [])):
            if getattr(t, "_dyn", False):
                t.remove()

    # ========================================================
    # Auflagerreaktionen: r = K u - F
    # ========================================================
    def _reaction_vector(self) -> np.ndarray:
        return np.asarray(self.res.GesMat @ self.res.u_ges - self.res.FGes, dtype=float)

    def _draw_force_arrow(self, ax, x, z, dx, dz, color="green", lw=2):
        arr = FancyArrowPatch(
            (x, z),
            (x + float(dx), z + float(dz)),
            arrowstyle="-|>",
            mutation_scale=12,
            lw=lw,
            color=color,
        )
        ax.add_patch(arr)
        return self._mark_dyn(arr)

    def _draw_moment_double_arrow(self, ax, x, z, m, radius, color="purple", lw=2):
        sign = 1.0 if float(m) >= 0.0 else -1.0
        r = float(radius)

        a1 = FancyArrowPatch(
            (x - r, z),
            (x + r, z),
            connectionstyle=f"arc3,rad={0.6*sign}",
            arrowstyle="<->",
            mutation_scale=12,
            lw=lw,
            color=color,
        )
        ax.add_patch(a1)
        return self._mark_dyn(a1)

    def _support_nodes(self):
        dfR = getattr(self.Inp, "RestraintData", None)
        if dfR is None:
            return []
        if "Node" not in dfR.columns:
            return []
        return sorted(set(int(n) for n in dfR["Node"].values))

    def _length_ref_xz(self, frac=0.03):
        xs = np.asarray(self.nodes["x[m]"], dtype=float)
        zs = np.asarray(self.nodes["z[m]"], dtype=float)
        span = max(float(xs.max() - xs.min()), float(zs.max() - zs.min()), 1e-9)
        return float(frac) * span

    # ========================================================
    # Auflagerreaktionen 2D (interaktiv) + Tabelle + Lasten
    # ========================================================
    def plot_support_reactions_table_2d(
        self,
        moment_components=("Mx", "My", "Mz"),
        title="Auflagerreaktionen (Tabelle)",
        fmt_force="{:+.3f}",
        fmt_moment="{:+.3f}",
    ):
        r = self._reaction_vector()
        support_nodes = self._support_nodes()

        if not support_nodes:
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.axis("off")
            ax.text(0.5, 0.5, "Keine Auflagerknoten in RestraintData gefunden.", ha="center", va="center")
            return fig, ax

        mom_set = set(m.upper() for m in moment_components)
        show_Mx = "MX" in mom_set
        show_My = "MY" in mom_set
        show_Mz = "MZ" in mom_set

        cols = ["Node", "Rx [MN]", "Rz [MN]"]
        if show_Mx: cols.append("Mx [MNm]")
        if show_My: cols.append("My [MNm]")
        if show_Mz: cols.append("Mz [MNm]")

        rows = []
        for n in support_nodes:
            gdof = 7 * (n - 1)
            Rx = float(r[gdof + 0])
            Rz = float(r[gdof + 3])
            Mz = float(r[gdof + 2])
            My = float(r[gdof + 4])
            Mx = float(r[gdof + 5])

            row = [str(n), fmt_force.format(Rx), fmt_force.format(Rz)]
            if show_Mx: row.append(fmt_moment.format(Mx))
            if show_My: row.append(fmt_moment.format(My))
            if show_Mz: row.append(fmt_moment.format(Mz))
            rows.append(row)

        nrows = len(rows) + 1
        fig_h = max(2.2, 0.35 * nrows)
        fig, ax = plt.subplots(figsize=(10, fig_h))
        ax.axis("off")
        ax.set_title(title)

        table = ax.table(cellText=rows, colLabels=cols, loc="center", cellLoc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.0, 1.2)

        return fig, ax

    def plot_support_reactions_2d_interactive(
        self,
        invert_y=False,
        node_labels=True,
        elem_labels=False,
        show_forces=True,
        show_moments=True,
        scale_force_init=0.8,
        moment_radius_init=0.08,
        moment_scale_init=1.0,
        moment_kind_prefer="MY",
        robust_ref=True,
        Lref_frac=0.03,
        slider_force_max=10.0,
    ):
        fig, ax = self.plot_structure_2d(node_labels=node_labels, elem_labels=elem_labels)
        ax.set_title("Auflagerreaktionen (interaktiv)")

        r = self._reaction_vector()
        support_nodes = self._support_nodes()
        if not support_nodes:
            ax.text(0.5, 0.5, "Keine Auflagerknoten in RestraintData gefunden.", transform=ax.transAxes,
                    ha="center", va="center")
            return fig, ax, None

        Lref = self._length_ref_xz(frac=Lref_frac)

        Fvals = []
        for n in support_nodes:
            gdof = 7 * (n - 1)
            Fvals += [abs(float(r[gdof + 0])), abs(float(r[gdof + 3]))]
        Fvals = np.asarray(Fvals, dtype=float)
        if Fvals.size == 0:
            Fref = 1.0
        else:
            Fref = float(np.percentile(Fvals, 95)) if robust_ref else float(Fvals.max())
            Fref = max(Fref, 1e-12)

        def pick_moment_components(gdof_base):
            Mz = float(r[gdof_base + 2])
            My = float(r[gdof_base + 4])
            Mx = float(r[gdof_base + 5])
            return Mx, My, Mz

        def choose_moment(Mx, My, Mz):
            pref = moment_kind_prefer.upper()
            if pref == "MX": return Mx, "Mx"
            if pref == "MZ": return Mz, "Mz"
            return My, "My"

        def draw(scale_force, moment_radius, moment_scale):
            self._clear_dyn(ax)

            scale_force = float(scale_force)
            moment_radius = float(moment_radius)
            moment_scale = float(moment_scale)

            alphaF = (scale_force * Lref) / Fref

            for n in support_nodes:
                P = self._pt(int(n))
                x, z = float(P[0]), float(P[2])
                gdof = 7 * (int(n) - 1)

                Rx = float(r[gdof + 0])
                Rz = float(r[gdof + 3])

                Mx, My, Mz = pick_moment_components(gdof)
                Mplot, Mlab = choose_moment(Mx, My, Mz)

                if show_forces and (abs(Rx) > 1e-15 or abs(Rz) > 1e-15):
                    self._draw_force_arrow(ax, x, z, alphaF * Rx, alphaF * Rz, color="green")
                    self._mark_dyn(ax.text(x, z, f"R{n}", fontsize=8, color="green", ha="right", va="top"))
                    self._mark_dyn(ax.text(x, z, f"\nRx={Rx:+.3f} MN\nRz={Rz:+.3f} MN",
                                           fontsize=8, color="green", ha="left", va="top"))

                if show_moments and abs(Mplot) > 1e-15:
                    rr = moment_radius * moment_scale
                    self._draw_moment_double_arrow(ax, x, z, Mplot, radius=rr, color="purple")
                    self._mark_dyn(ax.text(x + rr, z + rr, f"{Mlab}={Mplot:+.3f} MNm",
                                           fontsize=8, color="purple"))

            ax.relim()
            ax.autoscale_view()
            ax.set_aspect("equal", adjustable="datalim")
            if invert_y:
                ax.invert_yaxis()
            fig.canvas.draw_idle()

        fig.subplots_adjust(bottom=0.25)

        ax_sF = fig.add_axes([0.15, 0.14, 0.70, 0.03])
        s_force = Slider(ax_sF, "Scale Force", 0.0, float(slider_force_max), valinit=float(scale_force_init))

        ax_sR = fig.add_axes([0.15, 0.09, 0.70, 0.03])
        s_rad = Slider(ax_sR, "Moment Radius", 0.0, float(moment_radius_init) * 20.0, valinit=float(moment_radius_init))

        ax_sM = fig.add_axes([0.15, 0.04, 0.70, 0.03])
        s_msc = Slider(ax_sM, "Moment Scale", 0.0, float(moment_scale_init) * 20.0, valinit=float(moment_scale_init))

        def update(_):
            draw(s_force.val, s_rad.val, s_msc.val)

        s_force.on_changed(update)
        s_rad.on_changed(update)
        s_msc.on_changed(update)

        draw(scale_force_init, moment_radius_init, moment_scale_init)
        return fig, ax, (s_force, s_rad, s_msc)

    def plot_nodal_loads_2d_interactive(
        self,
        invert_y=False,
        node_labels=True,
        elem_labels=False,
        show_forces=True,
        show_moments=True,
        scale_force_init=0.8,
        moment_radius_init=0.08,
        moment_scale_init=1.0,
        moment_kind_prefer="MY",
        robust_ref=True,
        Lref_frac=0.03,
        slider_force_max=10.0,
    ):
        fig, ax = self.plot_structure_2d(node_labels=node_labels, elem_labels=elem_labels)
        ax.set_title("Knotenlasten (interaktiv) – aus NodalForces.csv")

        # --- Lasttabelle holen (EXAKT dein Input) ---
        dfL = self.Inp.NodalForces 

        print(dfL)

        if dfL is None:
            # falls du sie doch "NodalForces" genannt hast:
            dfL = getattr(self.Inp, "NodalForces", None)

        if dfL is None:
            ax.text(0.5, 0.5, "Keine NodalForces Tabelle in Inp gefunden.", transform=ax.transAxes,
                    ha="center", va="center")
            return fig, ax, None

        # --- in Node -> FX,FY,FZ,MX,MY,MZ aggregieren (langes Format) ---
        data = {}  # node -> dict

        for _, row in dfL.iterrows():
            n   = int(row["Node"])
            dof = str(row["Dof"]).strip().upper()
            val = float(row["Value[MN/MNm]"])

            if n not in data:
                data[n] = {"FX": 0.0, "FY": 0.0, "FZ": 0.0, "MX": 0.0, "MY": 0.0, "MZ": 0.0}

            if dof in data[n]:
                data[n][dof] += val
            else:
                print(f"Warnung: unbekannter Dof '{dof}' in NodalForces (Node {n})")


        nodes = sorted(data.keys())
        Fx = np.array([data[n]["FX"] for n in nodes], dtype=float)
        Fz = np.array([data[n]["FZ"] for n in nodes], dtype=float)
        Mx = np.array([data[n]["MX"] for n in nodes], dtype=float)
        My = np.array([data[n]["MY"] for n in nodes], dtype=float)
        Mz = np.array([data[n]["MZ"] for n in nodes], dtype=float)

        print("nodes:", nodes)
        print("Fx:", Fx)
        print("Fz:", Fz)
        # --- Skalierung ---
        Lref = self._length_ref_xz(frac=Lref_frac)
        Fabs = np.hstack([np.abs(Fx), np.abs(Fz)])
        if Fabs.size == 0:
            Fref = 1.0
        else:
            Fref = float(np.percentile(Fabs, 95)) if robust_ref else float(Fabs.max())
            Fref = max(Fref, 1e-12)

        def choose_moment(mx, my, mz):
            pref = str(moment_kind_prefer).upper()
            if pref == "MX":
                return float(mx), "Mx"
            if pref == "MZ":
                return float(mz), "Mz"
            return float(my), "My"

        def draw(scale_force, moment_radius, moment_scale):
            self._clear_dyn(ax)

            scale_force = float(scale_force)
            moment_radius = float(moment_radius)
            moment_scale = float(moment_scale)

            alphaF = (scale_force * Lref) / Fref

            for n, fx, fz, mx, my, mz in zip(nodes, Fx, Fz, Mx, My, Mz):
                P = self._pt(int(n))
                x, z = float(P[0]), float(P[2])

                # Kräfte
                if show_forces and (abs(fx) > 1e-15 or abs(fz) > 1e-15):
                    self._draw_force_arrow(ax, x, z, alphaF * fx, alphaF * fz, color="orange")
                    self._mark_dyn(ax.text(x, z, f"F{n}", fontsize=8, color="orange", ha="right", va="top"))
                    self._mark_dyn(ax.text(x, z, f"\nFx={fx:+.3f} MN\nFz={fz:+.3f} MN",
                                        fontsize=8, color="orange", ha="left", va="top"))

                # Momente
                Mplot, Mlab = choose_moment(mx, my, mz)
                if show_moments and abs(Mplot) > 1e-15:
                    rr = moment_radius * moment_scale
                    self._draw_moment_double_arrow(ax, x, z, Mplot, radius=rr, color="brown")
                    self._mark_dyn(ax.text(x + rr, z + rr, f"{Mlab}={Mplot:+.3f} MNm",
                                        fontsize=8, color="brown"))

            ax.relim()
            ax.autoscale_view()
            ax.set_aspect("equal", adjustable="datalim")
            if invert_y:
                ax.invert_yaxis()
            fig.canvas.draw_idle()

        # --- Slider ---
        fig.subplots_adjust(bottom=0.25)

        ax_sF = fig.add_axes([0.15, 0.14, 0.70, 0.03])
        s_force = Slider(ax_sF, "Scale Force", 0.0, float(slider_force_max), valinit=float(scale_force_init))

        ax_sR = fig.add_axes([0.15, 0.09, 0.70, 0.03])
        s_rad = Slider(ax_sR, "Moment Radius", 0.0, float(moment_radius_init) * 20.0, valinit=float(moment_radius_init))

        ax_sM = fig.add_axes([0.15, 0.04, 0.70, 0.03])
        s_msc = Slider(ax_sM, "Moment Scale", 0.0, float(moment_scale_init) * 20.0, valinit=float(moment_scale_init))

        def update(_):
            draw(s_force.val, s_rad.val, s_msc.val)

        s_force.on_changed(update)
        s_rad.on_changed(update)
        s_msc.on_changed(update)

        draw(scale_force_init, moment_radius_init, moment_scale_init)
        return fig, ax, (s_force, s_rad, s_msc)

