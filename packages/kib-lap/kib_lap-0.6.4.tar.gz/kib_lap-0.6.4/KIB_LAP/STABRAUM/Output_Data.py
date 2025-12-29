import pandas as pd
import numpy as np

class OutputData:
    def __init__(self):
        print("Init OutputData")

    def support_reactions_from_springs_table(self, res, u0_default=0.0):
        # --- robuster Typ-/Attribut-Check ---
        needed = ("Inp", "GesMat", "u_ges", "FGes")
        missing = [a for a in needed if not hasattr(res, a)]
        if missing:
            raise TypeError(
                "Du musst ein AnalysisResults-Objekt übergeben (res = mainloop().run()). "
                f"Übergeben wurde: {type(res)}; fehlende Attribute: {missing}"
            )

        dfR = res.Inp.RestraintData.copy()

        # u als 1D
        u = np.asarray(res.u_ges, dtype=float).reshape(-1)

        # DOF Mapping (7 dof/node)
        dof_name = {
            0: ("Fx", "MN"),
            1: ("Fy", "MN"),
            2: ("Mz", "MNm"),
            3: ("Fz", "MN"),
            4: ("My", "MNm"),
            5: ("Mx", "MNm"),
            6: ("W",  "-"),
        }

        rows = []
        for _, row in dfR.iterrows():
            node = int(row["Node"])
            dof  = int(row["Dof"])
            k    = float(row["Cp[MN/m]/[MNm/m]"])

            gdof = 7 * (node - 1) + dof
            ui   = float(u[gdof])
            u0   = float(u0_default)

            Ri = k * (ui - u0)

            name, unit = dof_name.get(dof, (f"DOF{dof}", ""))

            rows.append({
                "Node": node,
                "DOF": dof,
                "Type": name,
                "k": k,
                "u": ui,
                "R_spring": Ri,
                "Unit": unit
            })

        return pd.DataFrame(rows).sort_values(["Node", "DOF"]).reset_index(drop=True)
