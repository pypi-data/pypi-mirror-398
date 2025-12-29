# ============================================================
# FULL, RUNNABLE SCRIPT (UPDATED)
#   - Loads + reactions + spring reactions + member forces
#   - Sliders + CheckButtons
#   - Optional node numbers + element numbers
#   - Springs plotted ONLY where k>0 (or spring_dofs provided)
# ============================================================

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, CheckButtons
from matplotlib.patches import FancyArrowPatch
from matplotlib.lines import Line2D
from matplotlib import transforms


class PlottingStructure:
    def __init__(
        self,
        _UG_FINAL,
        _FI_FINAL,
        _EXTFORCES,
        _MBRFORCES,
        _nodes,
        _members,
        _P0,
        _restrainedIndex,
        _reactionsFlag=True,
        _forceVector=None,
        _memberType=None,
    ):
        self.UG_FINAL = np.asarray(_UG_FINAL, dtype=float)          # (2*nNodes, nSteps)
        self.FI_FINAL = np.asarray(_FI_FINAL, dtype=float)          # (2*nNodes, nSteps)
        self.EXTFORCES = np.asarray(_EXTFORCES, dtype=float)        # (2*nNodes, nSteps)
        self.MBRFORCES = np.asarray(_MBRFORCES, dtype=float)        # (nMembers, nSteps)

        self.nodes = np.asarray(_nodes, dtype=float)                # (nNodes, 2)
        self.members = list(_members)                               # [(i,j), ...] with 1-based node indices
        self.P0 = np.asarray(_P0, dtype=float)                      # (nMembers,)
        self.restrainedIndex = set(int(i) for i in _restrainedIndex)  # dof indices (0-based)
        self.reactionsFlag = bool(_reactionsFlag)

        self.forceVector = _forceVector
        self.memberType = _memberType if _memberType is not None else ["b"] * len(self.members)

        # Optional (set from outside):
        # self.Kspring_diag : (nDoF,) diagonal spring stiffness in global DOFs
        # self.spring_dofs  : set[int] DOFs that truly have springs (optional)
        self.Kspring_diag = None
        self.spring_dofs = None

        # Tunable parameters
        self.params = {
            "Axial_Forces": False,
            "Show_Loads": True,
            "Show_Reactions": True,
            "Show_Springs": True,          # NEW
            "Show_MemberVectors": True,
            "Show_Legend": True,

            "Show_NodeNumbers": True,      # NEW
            "Show_ElementNumbers": False,  # NEW

            "label_offset": 0.02,          # node number offset (data coords)
            "elem_label_offset": 0.00,     # extra offset for element labels (data coords)
            "xMargin": 0.2,
            "yMargin": 0.4,

            "scaleFactor": 1.0,            # deformation scale
            "Load_Increment": self.UG_FINAL.shape[1] - 1,
            "Final_config": True,

            # label & arrow tuning
            "textScale": 1.0,
            "arrowLenMin": 0.03,           # relative to span
            "arrowLenMax": 0.12,           # relative to span
            "arrowHeadScale": 12.0,        # points
            "labelOffsetPts": 10,          # points
            "refQuantile": 0.95,           # reference force quantile for scaling
            "softPower": 0.65,             # 0.5..0.9 (lower => more compression)
            "collisionIters": 25,
            "collisionRadiusPts": 14,
            "vectorScaleFactor": 1.0,      # member vector scale

            # NEW: spring filter thresholds
            "springK_tol": 1e-12,
            "springF_tol": 1e-9,
        }

    # -----------------------
    # Helpers
    # -----------------------
    @staticmethod
    def _soft_scale(value, ref, Lmin, Lmax, p=0.65):
        if ref <= 0:
            return 0.0
        x = abs(value) / ref
        s = x**p
        s = min(max(s, 0.0), 1.0)
        return Lmin + (Lmax - Lmin) * s

    @staticmethod
    def _auto_fontsize(ax, base=10, min_fs=7, max_fs=13, textScale=1.0):
        bbox = ax.get_window_extent().transformed(ax.figure.dpi_scale_trans.inverted())
        width_inch = bbox.width
        fs = base * (width_inch / 6.0) ** 0.4
        fs *= textScale
        return float(np.clip(fs, min_fs, max_fs))

    def _add_force_arrow(
        self,
        ax,
        x, y,
        vx, vy,
        magnitude,
        color="blue",
        label=None,
        Lmin=0.1, Lmax=0.5,
        ref=1.0,
        lw=1.2,
        fontsize=10,
        text_offset_pts=10,
        head_scale=12.0,
        zorder=5,
    ):
        dir_vec = np.array([vx, vy], dtype=float)
        nrm = np.linalg.norm(dir_vec)
        if nrm < 1e-12:
            return None

        dir_vec /= nrm
        L = self._soft_scale(magnitude, ref, Lmin, Lmax, p=self.params["softPower"])
        dx, dy = dir_vec[0] * L, dir_vec[1] * L

        arrow = FancyArrowPatch(
            (x, y), (x + dx, y + dy),
            arrowstyle="-|>",
            mutation_scale=head_scale,
            linewidth=lw,
            color=color,
            zorder=zorder
        )
        ax.add_patch(arrow)

        txt_artist = None
        if label:
            perp = np.array([-dir_vec[1], dir_vec[0]])
            perp_sign = 1.0
            if (dir_vec[0] < 0) or (dir_vec[1] < 0):
                perp_sign = -1.0

            offset = perp_sign * perp * text_offset_pts
            trans = ax.transData + transforms.ScaledTranslation(
                offset[0] / 72.0, offset[1] / 72.0, ax.figure.dpi_scale_trans
            )

            txt_artist = ax.text(
                x + dx, y + dy, label,
                transform=trans,
                fontsize=fontsize,
                weight="bold",
                va="center", ha="center",
                color=color,
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.80, pad=1.5),
                zorder=zorder + 1
            )

        return txt_artist

    def _resolve_text_collisions(self, ax, text_artists, iters=25, min_dist_pts=14):
        text_artists = [t for t in text_artists if t is not None]
        if not text_artists:
            return

        fig = ax.figure
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()

        min_dist_px = (min_dist_pts / 72.0) * fig.dpi

        for _ in range(int(iters)):
            moved = False

            centers = []
            for t in text_artists:
                bb = t.get_window_extent(renderer=renderer).expanded(1.05, 1.10)
                centers.append(np.array([bb.x0 + bb.width / 2, bb.y0 + bb.height / 2]))

            for i in range(len(text_artists)):
                for j in range(i + 1, len(text_artists)):
                    d = centers[j] - centers[i]
                    dist = float(np.linalg.norm(d))
                    if dist < min_dist_px:
                        if dist < 1e-6:
                            d = np.array([1.0, 0.0])
                            dist = 1.0
                        push = (min_dist_px - dist) * 0.5
                        step = (d / dist) * push

                        for idx, sgn in [(i, -1.0), (j, +1.0)]:
                            t = text_artists[idx]
                            x, y = t.get_position()
                            p_disp = ax.transData.transform((x, y))
                            p_disp = p_disp + sgn * step
                            p_data = ax.transData.inverted().transform(p_disp)
                            t.set_position((p_data[0], p_data[1]))

                        moved = True

            if not moved:
                break

        fig.canvas.draw_idle()

    def _apply_legend(self, ax):
        proxies = [
            Line2D([0], [0], color="blue", lw=2, label="Loads"),
            Line2D([0], [0], color="black", lw=2, label="Reactions (BC)"),
            Line2D([0], [0], color="purple", lw=2, label="Springs"),
            Line2D([0], [0], color="purple", lw=2, linestyle=":", label="Member vectors"),
            Line2D([0], [0], color="#33cc99", lw=2, linestyle="--", label="Undeformed"),
            Line2D([0], [0], color="#1f77b4", lw=3, label="Deformed (tension)"),
            Line2D([0], [0], color="#d62728", lw=3, label="Deformed (compression)"),
        ]
        ax.legend(handles=proxies, loc="upper right", framealpha=0.9)

    # -----------------------
    # Main plot on axis
    # -----------------------
    def _plot_on_axis(self, ax, **kwargs):
        # params
        Axial_Forces = kwargs["Axial_Forces"]
        Show_Loads = kwargs["Show_Loads"]
        Show_Reactions = kwargs["Show_Reactions"]
        Show_Springs = kwargs["Show_Springs"]
        Show_MemberVectors = kwargs["Show_MemberVectors"]
        Show_Legend = kwargs["Show_Legend"]
        Show_NodeNumbers = kwargs["Show_NodeNumbers"]
        Show_ElementNumbers = kwargs["Show_ElementNumbers"]

        label_offset = kwargs["label_offset"]
        elem_label_offset = kwargs["elem_label_offset"]
        xMargin = kwargs["xMargin"]
        yMargin = kwargs["yMargin"]
        scaleFactor = kwargs["scaleFactor"]
        Load_Increment = int(kwargs["Load_Increment"])
        Final_config = kwargs["Final_config"]

        textScale = kwargs["textScale"]
        arrowLenMin = kwargs["arrowLenMin"]
        arrowLenMax = kwargs["arrowLenMax"]
        arrowHeadScale = kwargs["arrowHeadScale"]
        labelOffsetPts = kwargs["labelOffsetPts"]
        refQuantile = kwargs["refQuantile"]
        collisionIters = kwargs["collisionIters"]
        collisionRadiusPts = kwargs["collisionRadiusPts"]
        vectorScaleFactor = kwargs["vectorScaleFactor"]

        springK_tol = kwargs["springK_tol"]
        springF_tol = kwargs["springF_tol"]

        if Final_config:
            Load_Increment = -1

        ug = np.asarray(self.UG_FINAL[:, Load_Increment]).flatten()
        fi = np.asarray(self.FI_FINAL[:, Load_Increment]).flatten()
        forceVector = np.asarray(self.EXTFORCES[:, Load_Increment]).flatten()
        mbrForces = np.asarray(self.MBRFORCES[:, Load_Increment]).flatten()

        ax.clear()
        ax.set_aspect("equal", adjustable="datalim")
        ax.grid(True)

        # span for relative arrow lengths
        min_x, max_x = self.nodes[:, 0].min(), self.nodes[:, 0].max()
        min_y, max_y = self.nodes[:, 1].min(), self.nodes[:, 1].max()
        span = max(max_x - min_x, max_y - min_y)
        Lmin = max(1e-9, arrowLenMin * span)
        Lmax = max(Lmin * 1.05, arrowLenMax * span)

        # reference force
        allF = np.concatenate([np.abs(forceVector), np.abs(fi), np.abs(mbrForces)])
        allF = allF[allF > 1e-9]
        ref_force = float(np.quantile(allF, refQuantile)) if allF.size else 1.0

        # fontsize
        fs = self._auto_fontsize(ax, base=10, textScale=textScale)

        # --- SPRINGS computed ONCE ---
        u_vec = ug  # same as UG_FINAL[:, step]
        if hasattr(self, "Kspring_diag") and self.Kspring_diag is not None:
            k_diag = np.asarray(self.Kspring_diag, dtype=float).flatten()
            f_spring = -k_diag * u_vec
        else:
            k_diag = None
            f_spring = np.zeros_like(u_vec)

        # DOFs which truly have springs
        if self.spring_dofs is not None:
            spring_dofs = set(int(d) for d in self.spring_dofs)
        elif k_diag is not None:
            spring_dofs = set(np.where(k_diag > springK_tol)[0].tolist())
        else:
            spring_dofs = set()

        # nodes + node labels
        node_texts = []
        for i, (x, y) in enumerate(self.nodes):
            ax.plot(x, y, "o", color="#33cc99", zorder=3)

            if Show_NodeNumbers:
                t = ax.text(
                    x + label_offset, y + label_offset, str(i + 1),
                    fontsize=fs, weight="bold",
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.6, pad=1.0),
                    zorder=10
                )
                node_texts.append(t)

        # undeformed members
        print(self.members)
        for (ni, nj) in self.members:
            ix, iy = self.nodes[ni - 1]
            jx, jy = self.nodes[nj - 1]
            ax.plot([ix, jx], [iy, jy], "--", color="#33cc99", linewidth=1.5, zorder=1)

        # deformed members (thickness by abs force, color by sign)
        max_force_abs = float(np.max(np.abs(mbrForces))) if np.max(np.abs(mbrForces)) != 0 else 1.0
        member_texts = []

        for e, (ni, nj) in enumerate(self.members):
            ix, iy = self.nodes[ni - 1]
            jx, jy = self.nodes[nj - 1]

            ia = 2 * ni - 2
            ib = 2 * ni - 1
            ja = 2 * nj - 2
            jb = 2 * nj - 1

            ixN = ix + ug[ia] * scaleFactor
            iyN = iy + ug[ib] * scaleFactor
            jxN = jx + ug[ja] * scaleFactor
            jyN = jy + ug[jb] * scaleFactor

            force_abs = abs(mbrForces[e])
            line_width = 1.0 + 4.0 * (force_abs / max_force_abs)

            col = "#1f77b4" if mbrForces[e] >= 0 else "#d62728"
            ax.plot([ixN, jxN], [iyN, jyN], "-", linewidth=line_width, color=col, zorder=2)

            # element numbering (NEW)
            if Show_ElementNumbers:
                mx = 0.5 * (ixN + jxN)
                my = 0.5 * (iyN + jyN)
                t_el = ax.text(
                    mx + elem_label_offset, my + elem_label_offset, f"E{e+1}",
                    fontsize=max(7, fs - 1),
                    weight="bold",
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.65, pad=1.0),
                    zorder=12,
                    color="purple"
                )
                member_texts.append(t_el)

            if Axial_Forces:
                preTen = self.P0[e] / 1000.0
                axialForce = mbrForces[e] / 1000.0 - preTen
                label = f"{axialForce:.2f} kN\n(+{preTen:.2f} PT)"
                mx = 0.5 * (ixN + jxN)
                my = 0.5 * (iyN + jyN)
                t = ax.text(
                    mx, my, label,
                    fontsize=max(7, fs - 1),
                    weight="bold",
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.75, pad=1.5),
                    zorder=11
                )
                member_texts.append(t)

        # loads + reactions + springs
        force_texts = []
        nNodes = self.nodes.shape[0]

        for n in range(nNodes):
            node_num = n + 1
            i_hor = 2 * node_num - 2
            i_ver = 2 * node_num - 1

            ix, iy = self.nodes[n]
            ixN = ix + ug[i_hor] * scaleFactor
            iyN = iy + ug[i_ver] * scaleFactor

            # loads
            if Show_Loads:
                if abs(forceVector[i_hor]) > 1e-9:
                    t = self._add_force_arrow(
                        ax, ixN, iyN,
                        np.sign(forceVector[i_hor]), 0.0,
                        magnitude=forceVector[i_hor],
                        color="blue",
                        label=f"{forceVector[i_hor]/1000:.2f} kN",
                        Lmin=Lmin, Lmax=Lmax, ref=ref_force,
                        lw=1.2, fontsize=fs,
                        text_offset_pts=labelOffsetPts,
                        head_scale=arrowHeadScale,
                        zorder=6
                    )
                    if t is not None:
                        force_texts.append(t)

                if abs(forceVector[i_ver]) > 1e-9:
                    t = self._add_force_arrow(
                        ax, ixN, iyN,
                        0.0, np.sign(forceVector[i_ver]),
                        magnitude=forceVector[i_ver],
                        color="blue",
                        label=f"{forceVector[i_ver]/1000:.2f} kN",
                        Lmin=Lmin, Lmax=Lmax, ref=ref_force,
                        lw=1.2, fontsize=fs,
                        text_offset_pts=labelOffsetPts,
                        head_scale=arrowHeadScale,
                        zorder=6
                    )
                    if t is not None:
                        force_texts.append(t)

            # reactions (BC)
            if Show_Reactions:
                if (i_hor in self.restrainedIndex) and abs(fi[i_hor]) > 1e-9:
                    t = self._add_force_arrow(
                        ax, ixN, iyN,
                        np.sign(fi[i_hor]), 0.0,
                        magnitude=fi[i_hor],
                        color="black",
                        label=f"{fi[i_hor]/1000:.2f} kN",
                        Lmin=Lmin, Lmax=Lmax, ref=ref_force,
                        lw=1.4, fontsize=fs,
                        text_offset_pts=labelOffsetPts,
                        head_scale=arrowHeadScale,
                        zorder=7
                    )
                    if t is not None:
                        force_texts.append(t)

                if (i_ver in self.restrainedIndex) and abs(fi[i_ver]) > 1e-9:
                    t = self._add_force_arrow(
                        ax, ixN, iyN,
                        0.0, np.sign(fi[i_ver]),
                        magnitude=fi[i_ver],
                        color="black",
                        label=f"{fi[i_ver]/1000:.2f} kN",
                        Lmin=Lmin, Lmax=Lmax, ref=ref_force,
                        lw=1.4, fontsize=fs,
                        text_offset_pts=labelOffsetPts,
                        head_scale=arrowHeadScale,
                        zorder=7
                    )
                    if t is not None:
                        force_texts.append(t)

            # springs (NEW, independent of reactions)
            if Show_Springs and (k_diag is not None):
                # x spring at this node?
                if (i_hor in spring_dofs) and abs(f_spring[i_hor]) > springF_tol:
                    t = self._add_force_arrow(
                        ax, ixN, iyN,
                        np.sign(f_spring[i_hor]), 0.0,
                        magnitude=f_spring[i_hor],
                        color="purple",
                        label=f"{f_spring[i_hor]/1000:.2f} kN",
                        Lmin=Lmin, Lmax=Lmax, ref=ref_force,
                        lw=1.4, fontsize=fs,
                        text_offset_pts=labelOffsetPts,
                        head_scale=arrowHeadScale,
                        zorder=7
                    )
                    if t is not None:
                        force_texts.append(t)

                # y spring at this node?
                if (i_ver in spring_dofs) and abs(f_spring[i_ver]) > springF_tol:
                    t = self._add_force_arrow(
                        ax, ixN, iyN,
                        0.0, np.sign(f_spring[i_ver]),
                        magnitude=f_spring[i_ver],
                        color="purple",
                        label=f"{f_spring[i_ver]/1000:.2f} kN",
                        Lmin=Lmin, Lmax=Lmax, ref=ref_force,
                        lw=1.4, fontsize=fs,
                        text_offset_pts=labelOffsetPts,
                        head_scale=arrowHeadScale,
                        zorder=7
                    )
                    if t is not None:
                        force_texts.append(t)

        # member vectors (purple, orthogonal)
        if Show_MemberVectors:
            for e, (ni, nj) in enumerate(self.members):
                ix, iy = self.nodes[ni - 1]
                jx, jy = self.nodes[nj - 1]

                ia = 2 * ni - 2
                ib = 2 * ni - 1
                ja = 2 * nj - 2
                jb = 2 * nj - 1

                ixN = ix + ug[ia] * scaleFactor
                iyN = iy + ug[ib] * scaleFactor
                jxN = jx + ug[ja] * scaleFactor
                jyN = jy + ug[jb] * scaleFactor

                direction = np.array([jx - ix, jy - iy], dtype=float)
                L = np.linalg.norm(direction)
                if L < 1e-12:
                    continue

                dir_norm = direction / L
                orth = np.array([-dir_norm[1], dir_norm[0]])

                vec_L = self._soft_scale(mbrForces[e], ref_force, Lmin * 0.7, Lmax * 0.7, p=self.params["softPower"])
                vec_L *= np.sign(mbrForces[e]) * vectorScaleFactor
                vec = orth * vec_L

                for (x0, y0) in [(ixN, iyN), (jxN, jyN)]:
                    a = FancyArrowPatch(
                        (x0, y0), (x0 + vec[0], y0 + vec[1]),
                        arrowstyle="-|>",
                        mutation_scale=max(8.0, 0.8 * arrowHeadScale),
                        linewidth=1.0,
                        color="purple",
                        alpha=0.75,
                        zorder=4
                    )
                    ax.add_patch(a)

                ax.plot(
                    [ixN + vec[0], jxN + vec[0]],
                    [iyN + vec[1], jyN + vec[1]],
                    color="purple",
                    linestyle=":",
                    linewidth=1.0,
                    alpha=0.75,
                    zorder=3
                )

        # axis limits / labels
        ax.set_xlim(min_x - xMargin, max_x + xMargin)
        ax.set_ylim(min_y - yMargin, max_y + yMargin)
        ax.set_xlabel("Distance (m)", fontsize=fs)
        ax.set_ylabel("Distance (m)", fontsize=fs)
        ax.set_title("Deflected shape, forces & reactions", fontsize=fs + 2, weight="bold")

        if Show_Legend:
            self._apply_legend(ax)

        # collision reduction
        self._resolve_text_collisions(
            ax,
            node_texts + member_texts + force_texts,
            iters=collisionIters,
            min_dist_pts=collisionRadiusPts
        )

    # -----------------------
    # Interactive window
    # -----------------------
    def create_structure_plot(self):
        fig = plt.figure(figsize=(11, 9))
        ax_main = fig.add_axes([0.25, 0.35, 0.70, 0.60])
        fig.suptitle("Structure Plot (optimized)", fontsize=14)

        slider_left = 0.25
        slider_width = 0.65
        slider_height = 0.03
        slider_y = 0.28

        def add_slider(label, vmin, vmax, vinit, vstep):
            nonlocal slider_y
            ax_s = fig.add_axes([slider_left, slider_y, slider_width, slider_height])
            s = Slider(ax=ax_s, label=label, valmin=vmin, valmax=vmax, valinit=vinit, valstep=vstep)
            slider_y -= 0.04
            return s

        # Sliders
        s_xMargin = add_slider("xMargin", 0.0, 5.0, self.params["xMargin"], 0.1)
        s_yMargin = add_slider("yMargin", 0.0, 5.0, self.params["yMargin"], 0.1)
        s_scaleFactor = add_slider("scaleFactor", 0.0, 10.0, self.params["scaleFactor"], 0.1)

        s_textScale = add_slider("textScale", 0.6, 1.8, self.params["textScale"], 0.05)
        s_arrowMin = add_slider("arrowLenMin", 0.005, 0.10, self.params["arrowLenMin"], 0.005)
        s_arrowMax = add_slider("arrowLenMax", 0.02, 0.30, self.params["arrowLenMax"], 0.01)
        s_head = add_slider("arrowHeadScale", 6.0, 26.0, self.params["arrowHeadScale"], 1.0)
        s_lblPts = add_slider("labelOffsetPts", 0.0, 25.0, self.params["labelOffsetPts"], 1.0)
        s_vecScale = add_slider("vectorScaleFactor", 0.0, 5.0, self.params["vectorScaleFactor"], 0.1)

        max_load = self.UG_FINAL.shape[1] - 1
        s_load = add_slider("Load_Increment", 0, max_load, self.params["Load_Increment"], 1)

        s_collRad = add_slider("collisionRadiusPts", 6, 30, self.params["collisionRadiusPts"], 1)
        s_collIt = add_slider("collisionIters", 0, 60, self.params["collisionIters"], 1)

        # CheckButtons
        ax_check = fig.add_axes([0.05, 0.38, 0.18, 0.32])
        labels = [
            "Loads", "Reactions", "Springs",
            "MemberVectors", "Axial_Forces",
            "NodeNumbers", "ElementNumbers",
            "Final_config", "Legend"
        ]
        actives = [
            self.params["Show_Loads"],
            self.params["Show_Reactions"],
            self.params["Show_Springs"],
            self.params["Show_MemberVectors"],
            self.params["Axial_Forces"],
            self.params["Show_NodeNumbers"],
            self.params["Show_ElementNumbers"],
            self.params["Final_config"],
            self.params["Show_Legend"]
        ]
        check = CheckButtons(ax_check, labels=labels, actives=actives)

        def redraw():
            self._plot_on_axis(ax_main, **self.params)
            fig.canvas.draw_idle()

        def slider_update(_):
            self.params["xMargin"] = float(s_xMargin.val)
            self.params["yMargin"] = float(s_yMargin.val)
            self.params["scaleFactor"] = float(s_scaleFactor.val)

            self.params["textScale"] = float(s_textScale.val)
            self.params["arrowLenMin"] = float(s_arrowMin.val)
            self.params["arrowLenMax"] = float(s_arrowMax.val)
            self.params["arrowHeadScale"] = float(s_head.val)
            self.params["labelOffsetPts"] = float(s_lblPts.val)
            self.params["vectorScaleFactor"] = float(s_vecScale.val)

            self.params["Load_Increment"] = int(s_load.val)

            self.params["collisionRadiusPts"] = int(s_collRad.val)
            self.params["collisionIters"] = int(s_collIt.val)

            redraw()

        def check_update(label):
            if label == "Loads":
                self.params["Show_Loads"] = not self.params["Show_Loads"]
            elif label == "Reactions":
                self.params["Show_Reactions"] = not self.params["Show_Reactions"]
            elif label == "Springs":
                self.params["Show_Springs"] = not self.params["Show_Springs"]
            elif label == "MemberVectors":
                self.params["Show_MemberVectors"] = not self.params["Show_MemberVectors"]
            elif label == "Axial_Forces":
                self.params["Axial_Forces"] = not self.params["Axial_Forces"]
            elif label == "NodeNumbers":
                self.params["Show_NodeNumbers"] = not self.params["Show_NodeNumbers"]
            elif label == "ElementNumbers":
                self.params["Show_ElementNumbers"] = not self.params["Show_ElementNumbers"]
            elif label == "Final_config":
                self.params["Final_config"] = not self.params["Final_config"]
            elif label == "Legend":
                self.params["Show_Legend"] = not self.params["Show_Legend"]

            redraw()

        # connect events
        for s in [
            s_xMargin, s_yMargin, s_scaleFactor,
            s_textScale, s_arrowMin, s_arrowMax,
            s_head, s_lblPts, s_vecScale,
            s_load, s_collRad, s_collIt
        ]:
            s.on_changed(slider_update)

        check.on_clicked(check_update)

        redraw()
        plt.show()
