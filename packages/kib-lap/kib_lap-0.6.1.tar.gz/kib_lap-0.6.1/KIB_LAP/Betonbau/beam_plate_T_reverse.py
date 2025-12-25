import numpy as np
from scipy.integrate import simpson as simps
import math


class BeamPlateTReverse:

    def __init__(self, index, width_web, height, width_effective, height_plate):
        self.index = index
        self.width_web = width_web
        self.height = height
        self.width_effective = width_effective
        self.height_plate = height_plate
        self.cross_section_area = width_web * (height - height_plate) + height_plate * width_effective
        self.center_of_gravity = ((height_plate*width_effective)*((height-height_plate)+height_plate/2)+(width_web*(height-height_plate))*((height-height_plate)/2))/((height_plate*width_effective)+(width_web*(height-height_plate)))
        self.cross_section_inertia = (((width_effective*height_plate**3)/12)+(width_effective*height_plate) * ((height-(height_plate/2))-self.center_of_gravity)**2) + (((width_web*(height-height_plate)**3)/12) + (width_web*(height-height_plate))*((self.center_of_gravity-((height-height_plate)/2))**2))

    def check_if_beam_is_suitable_for_bending_calc(self, ed_i):
        check = ed_i/self.height
        return check

    def calculate_beam_section(self, beam_sub_section, strength_of_concrete, tensile_yield_strength, nu_limit):
        # _____________________ Center of a composite function - Bending design for reinforced concrete _________________________________________#
        M = beam_sub_section.moment_ed / 1000000  # Mnm
        N_f = beam_sub_section.normal_force_ed / 1000000  # Mn

        Mrds = 0
        Meds = 0
        Meds_lim = 0

        nu_eds = 0
        nu_eds_grenz = nu_limit  # 0.371 # 0.296

        fcd = strength_of_concrete  # N/mm²
        fyd = tensile_yield_strength  # MN/m²
        E = beam_sub_section.elasticity_modulus_steel  # MN/m²
        fck = (fcd * 1.5) / 0.85
        fctm = 0.3 * fck ** (2 / 3)
        fyk = fyd * 1.15

        epssyd = (fyd / E) * 1000

        As1erf = 0  # cm²
        As2erf = 0  # cm²   Druckbewehrung
        Asmin = 0  # cm²    Mindestbewehrung

        # Geometrie
        h = self.height  # gesamt Höhe
        b_eff = self.width_effective  # effective Breite
        b_w = self.width_web  # Stegbreite
        h_f = self.height_plate  # Plattenbalkenhöhe

        zs1 = self.center_of_gravity  # Schwerpunkt

        d = beam_sub_section.effective_height
        d2 = beam_sub_section.effective_height_pressure

        # Startwerte der Dehnungen und Stauchungen
        epss = 25
        steal_strain_1 = 0  # Falls Druckbewehrung, hier die neue Stahldehnung
        epss2 = 0
        epsc = 0.0001  # Darf nicht 0 sein, da sonst Teilung durch 0 in der Berechnung der Schwerpunkte -> Start mit 0,001

        epss_new = 0
        epss_2_new = 0

        num_iter = 0
        num_iter_grenz = 30000

        N = 50  # Numerische Integration der Spannungen ueber die Hoehe

        xi = 0
        x = 0
        z = 0

        # KENNWERTE
        # Querschnittslängen
        interval_start_1 = 0
        interval_end_1 = 0
        interval_start_2 = 0
        interval_end_2 = 0
        interval_start_3 = 0
        interval_end_3 = 0
        # Querschnittsbreiten
        concrete_width_1 = 0
        concrete_width_2 = 0
        concrete_width_3 = 0
        # Druckkräfte und Schwerpunkte
        A_1 = 0
        S_1 = 0
        A_2 = 0
        S_2 = 0
        A_3 = 0
        S_3 = 0
        while (Mrds <= abs(Meds) and num_iter < num_iter_grenz):
            xi = epsc / (epsc + epss)
            x = xi * d

            # Stahl fließt nicht
            if epss < epssyd:
                sigma_s = E * epss * 0.001
            # Stahl fließt
            else:
                sigma_s = fyd

            # Feldmoment
            if M >= 0:
                # Druckzone liegt im Steg -> Nullline im Steg
                if (x <= (h - h_f)):

                    # Grenzdehnung von 2 wird nicht erreicht
                    if (0 <= epsc < 2.0):
                        # Querschnittslängen Vergabe
                        interval_start_1 = 0
                        interval_end_1 = x
                        interval_start_2 = 0
                        interval_end_2 = 0
                        interval_start_3 = 0
                        interval_end_3 = 0
                        # Querschnittsbreiten Vergabe
                        concrete_width_1 = b_w
                        concrete_width_2 = 0
                        concrete_width_3 = 0
                    # Grenzdehnung von 2 wird im Steg erreicht
                    elif (2 / epsc * x <= (h - h_f)):
                        # Querschnittslängen Vergabe
                        interval_start_1 = 0
                        interval_end_1 = 2 / epsc * x  # 2 = Dehnung beim Erreichen der Druckfestigkeit
                        interval_start_2 = 2 / epsc * x
                        interval_end_2 = x
                        interval_start_3 = 0
                        interval_end_3 = 0
                        # Querschnittsbreiten Vergabe
                        concrete_width_1 = b_w
                        concrete_width_2 = b_w
                        concrete_width_3 = 0

                    # Abgrenzen der einzlnen Bereichsunterschiede
                    x1 = np.linspace(interval_start_1, interval_end_1, N)
                    x2 = np.linspace(interval_start_2, interval_end_2, N)
                    x3 = np.linspace(interval_start_3, interval_end_3, N)

                    # Definition der Spannungsfunktionen
                    y1 = []
                    y2 = []
                    y3 = []
                    # Grenzdehnung von 2 wird nicht erreicht
                    if (0 <= epsc < 2.0):
                        y1_list_with_all_sigma_c_values_promille = []
                        for i in range(N):
                            sigma_c = fcd * (1 - (1 - ((x1[i] * epsc) / (x * 2))) ** 2)

                            y1_list_with_all_sigma_c_values_promille.append(sigma_c)

                        y1_values = y1_list_with_all_sigma_c_values_promille
                        y2_values = fcd * np.zeros(N)
                        y3_values = fcd * np.zeros(N)

                        y1.append(y1_values)
                        y2.append(y2_values)
                        y3.append(y3_values)
                    # Grenzdehnung von 2 wird im Steg erreicht
                    elif (2 / epsc * x <= (h - h_f)):
                        y1_list_with_all_sigma_c_values_upto_2_promille = []
                        for i in range(N):
                            sigma_c = fcd * (1 - (1 - ((x1[i] * epsc) / (
                                        x * 2))) ** 2)  # Sigma c-Werte bis zum Erreichen der Druckfestigkeit -> Betondehnung = 2

                            y1_list_with_all_sigma_c_values_upto_2_promille.append(sigma_c)

                        y1_values = y1_list_with_all_sigma_c_values_upto_2_promille  # sigma_concrete_at_given_intervals(x1)
                        y2_values = fcd * np.ones(N)
                        y3_values = fcd * np.ones(N)

                        y1.append(y1_values)
                        y2.append(y2_values)
                        y3.append(y3_values)

                    # Integration der einzelnen Spannungsfunktionen
                    if (0 <= epsc < 2.0):
                        M_1 = simps(y1 * x1, x = x1)
                        A_1 = simps(y1, x = x1)
                        S_1 = M_1 / A_1

                    elif (2 / epsc * x <= (h - h_f)):
                        M_1 = simps(y1 * x1, x = x1)  # moment 1
                        A_1 = simps(y1, x = x1)  # pressure force 1
                        S_1 = M_1 / A_1  # centroid of area 1

                        M_2 = simps(y2 * x2, x =  x2)
                        A_2 = simps(y2, x =  x2)
                        S_2 = M_2 / A_2

                    # concrete pressure
                    Fc_1 = A_1 * concrete_width_1
                    Fc_2 = A_2 * concrete_width_2
                    Fc_3 = 0

                    # centroid of compressive stress in concrete
                    S_ges = (S_1 * Fc_1 + S_2 * Fc_2 + S_3 * Fc_3) / (
                                Fc_1 + Fc_2 + Fc_3)  # Bei der Berechnung der Gesamtschwerpunkte der Druckkraefte muss die Querschnittsbreite der einzelnen Querschnitte einfliessen
                    z = S_ges + d - x  # Innerer Hebelarm

                    Meds = abs(M - N_f * (d - zs1))
                    Mrds = (Fc_1 + Fc_2 + Fc_3) * z

                    nu_eds = Meds / (b_w * (d ** 2) * fcd)
                    if nu_eds_grenz <= nu_eds:
                        Meds_lim = nu_eds_grenz * b_w * (d ** 2) * fcd

                        zeta_lim = 0
                        concrete_strain_2 = 3.5
                        if nu_eds_grenz == 0.296:
                            zeta_lim = 0.813
                            steal_strain_1 = 4.28
                        elif nu_eds_grenz == 0.371:
                            zeta_lim = 0.743
                            steal_strain_1 = 2.174

                        #epss2 = ((x - d2) / x) * abs(-3.5)
                        epss2 = ((steal_strain_1 + concrete_strain_2) / d) * (d - d2) - steal_strain_1

                        sigma_s_2 = 0
                        if epssyd <= epss2:
                            sigma_s_2 = fyd
                        elif epss2 < epssyd:
                            sigma_s_2 = fyd * (epss / epssyd)

                        z_nu_eds_grenz = zeta_lim * d

                        delta_Med = abs(M) - Meds_lim
                        As1erf_nu_lim = (1 / fyd) * (Meds_lim / z_nu_eds_grenz + N_f) * 100 ** 2
                        As2erf = (1 / sigma_s_2) * (delta_Med / (d - d2)) * 100 ** 2
                        As1erf = As1erf_nu_lim + As2erf
                    else:
                        As1erf = (1 / sigma_s) * (Fc_1 + Fc_2 + Fc_3 + N_f) * 100 ** 2

                    if (0 <= epsc < 3.5):
                        epsc += 0.001

                    else:
                        epss -= 0.001

                    num_iter += 1
                # Druckzone im Steg und Flasch -> Nullline im Flansch
                elif (x > (h - h_f)):
                    # Grenzdehnung von 2 wird nicht erreicht
                    if (0 <= epsc < 2.0):
                        # Querschnittslängen Vergabe
                        interval_start_1 = 0
                        interval_end_1 = x - (h - h_f)
                        interval_start_2 = x - (h - h_f)
                        interval_end_2 = x
                        interval_start_3 = 0
                        interval_end_3 = 0
                        # Querschnittsbreiten Vergabe
                        concrete_width_1 = b_w
                        concrete_width_2 = b_eff
                        concrete_width_3 = 0
                    # Grenzdehnung von 2 wird schon im FLansch erreicht
                    elif (2 / epsc * x <= x - (h - h_f)):
                        # Querschnittslängen Vergabe
                        interval_start_1 = 0
                        interval_end_1 = 2 / epsc * x  # 2 = Dehnung beim Erreichen der Druckfestigkeit
                        interval_start_2 = 2 / epsc * x
                        interval_end_2 = x - (h - h_f)
                        interval_start_3 = x - (h - h_f)
                        interval_end_3 = x
                        # Querschnittsbreiten Vergabe
                        concrete_width_1 = b_eff
                        concrete_width_2 = b_eff
                        concrete_width_3 = b_w
                    # Grenzdehnung von 2 wird im Steg erreicht
                    elif (2 / epsc * x > x - (h - h_f)):
                        # Querschnittslängen Vergabe
                        interval_start_1 = 0
                        interval_end_1 = x - (h - h_f)
                        interval_start_2 = x - (h - h_f)
                        interval_end_2 = 2 / epsc * x
                        interval_start_3 = 2 / epsc * x
                        interval_end_3 = x
                        # Querschnittsbreiten Vergabe
                        concrete_width_1 = b_eff
                        concrete_width_2 = b_w
                        concrete_width_3 = b_w

                    # Abgrenzen der einzlnen Bereichsunterschiede
                    x1 = np.linspace(interval_start_1, interval_end_1, N)
                    x2 = np.linspace(interval_start_2, interval_end_2, N)
                    x3 = np.linspace(interval_start_3, interval_end_3, N)

                    # Definition der Spannungsfunktionen
                    y1 = []
                    y2 = []
                    y3 = []
                    # Grenzdehnung von 2 wird nicht erreicht
                    if (0 <= epsc < 2.0):
                        y1_list_with_all_sigma_c_values_promille = []
                        y2_list_with_all_sigma_c_values_upto_2_promille = []
                        for i in range(N):
                            sigma_c = fcd * (1 - (1 - ((x1[i] * epsc) / (x * 2))) ** 2)
                            sigma_c_2 = fcd * (1 - (1 - ((x2[i] * epsc) / (x * 2))) ** 2)

                            y1_list_with_all_sigma_c_values_promille.append(sigma_c)
                            y2_list_with_all_sigma_c_values_upto_2_promille.append(sigma_c_2)

                        y1_values = y1_list_with_all_sigma_c_values_promille
                        y2_values = y2_list_with_all_sigma_c_values_upto_2_promille
                        y3_values = fcd * np.zeros(N)

                        y1.append(y1_values)
                        y2.append(y2_values)
                        y3.append(y3_values)
                    # Grenzdehnung von 2 wird im Steg erreicht
                    elif (2 / epsc * x <= x - (h - h_f)):
                        y1_list_with_all_sigma_c_values_upto_2_promille = []
                        for i in range(N):
                            sigma_c = fcd * (1 - (1 - ((x1[i] * epsc) / (
                                        x * 2))) ** 2)  # Sigma c-Werte bis zum Erreichen der Druckfestigkeit -> Betondehnung = 2

                            y1_list_with_all_sigma_c_values_upto_2_promille.append(sigma_c)

                        y1_values = y1_list_with_all_sigma_c_values_upto_2_promille  # sigma_concrete_at_given_intervals(x1)
                        y2_values = fcd * np.ones(N)
                        y3_values = fcd * np.ones(N)

                        y1.append(y1_values)
                        y2.append(y2_values)
                        y3.append(y3_values)
                    # Grenzdehnung von 2 wird im Flansch erreicht
                    elif (2 / epsc * x > x - (h - h_f)):
                        y1_list_with_all_sigma_c_values_promille = []
                        y2_list_with_all_sigma_c_values_upto_2_promille = []
                        for i in range(N):
                            sigma_c = fcd * (1 - (1 - ((x1[i] * epsc) / (x * 2))) ** 2)
                            sigma_c_2 = fcd * (1 - (1 - ((x2[i] * epsc) / (x * 2))) ** 2)

                            y1_list_with_all_sigma_c_values_promille.append(sigma_c)
                            y2_list_with_all_sigma_c_values_upto_2_promille.append(sigma_c_2)

                        y1_values = y1_list_with_all_sigma_c_values_promille
                        y2_values = y2_list_with_all_sigma_c_values_upto_2_promille
                        y3_values = fcd * np.ones(N)

                        y1.append(y1_values)
                        y2.append(y2_values)
                        y3.append(y3_values)

                    # Integration der einzelnen Spannungsfunktionen
                    if (0 <= epsc < 2.0):
                        M_1 = simps(y1 * x1, x = x1)
                        A_1 = simps(y1, x =  x1)
                        S_1 = M_1 / A_1

                        M_2 = simps(y2 * x2, x = x2)
                        A_2 = simps(y2, x = x2)
                        S_2 = M_2 / A_2

                    elif (2 / epsc * x <= x - (h - h_f)):
                        M_1 = simps(y1 * x1, x = x1)  # moment 1
                        A_1 = simps(y1, x = x1)  # pressure force 1
                        S_1 = M_1 / A_1  # centroid of area 1

                        M_2 = simps(y2 * x2, x = x2)
                        A_2 = simps(y2, x = x2)
                        S_2 = M_2 / A_2

                        M_3 = simps(y3 * x3, x= x3)
                        A_3 = simps(y3, x = x3)
                        S_3 = M_3 / A_3

                    elif (2 / epsc * x > x - (h - h_f)):
                        M_1 = simps(y1 * x1, x= x1)
                        A_1 = simps(y1, x= x1)
                        S_1 = M_1 / A_1

                        M_2 = simps(y2 * x2, x=  x2)
                        A_2 = simps(y2, x = x2)
                        S_2 = M_2 / A_2

                        M_3 = simps(y3 * x3, x= x3)
                        A_3 = simps(y3, x = x3)
                        S_3 = M_3 / A_3

                    # concrete pressure
                    Fc_1 = A_1 * concrete_width_1
                    Fc_2 = A_2 * concrete_width_2
                    Fc_3 = A_3 * concrete_width_3

                    # centroid of compressive stress in concrete
                    S_ges = (S_1 * Fc_1 + S_2 * Fc_2 + S_3 * Fc_3) / (
                                Fc_1 + Fc_2 + Fc_3)  # Bei der Berechnung der Gesamtschwerpunkte der Druckkraefte muss die Querschnittsbreite der einzelnen Querschnitte einfliessen
                    z = S_ges + d - x  # Innerer Hebelarm

                    Meds = abs(M - N_f * (d - zs1))
                    Mrds = (Fc_1 + Fc_2 + Fc_3) * z

                    nu_eds = Meds / (b_w * (d ** 2) * fcd)
                    if nu_eds_grenz <= nu_eds:
                        Meds_lim = nu_eds_grenz * b_w * (d ** 2) * fcd

                        zeta_lim = 0
                        concrete_strain_2 = 3.5
                        if nu_eds_grenz == 0.296:
                            zeta_lim = 0.813
                            steal_strain_1 = 4.28
                        elif nu_eds_grenz == 0.371:
                            zeta_lim = 0.743
                            steal_strain_1 = 2.174

                        #epss2 = ((x - d2) / x) * abs(-3.5)
                        epss2 = ((steal_strain_1 + concrete_strain_2) / d) * (d - d2) - steal_strain_1

                        sigma_s_2 = 0
                        if epssyd <= epss2:
                            sigma_s_2 = fyd
                        elif epss2 < epssyd:
                            sigma_s_2 = fyd * (epss / epssyd)

                        z_nu_eds_grenz = zeta_lim * d

                        delta_Med = abs(M) - Meds_lim
                        As1erf_nu_lim = (1 / fyd) * (Meds_lim / z_nu_eds_grenz + N_f) * 100 ** 2
                        As2erf = (1 / sigma_s_2) * (delta_Med / (d - d2)) * 100 ** 2
                        As1erf = As1erf_nu_lim + As2erf
                    else:
                        As1erf = (1 / sigma_s) * (Fc_1 + Fc_2 + Fc_3 + N_f) * 100 ** 2

                    if (0 <= epsc < 3.5):
                        epsc += 0.001
                    else:
                        epss -= 0.001

                    num_iter += 1

            # Stützmoment
            elif 0 > M:
                # Druckzone liegt im FLANSCH -> Nullline im Steg
                if (x <= h_f):
                    # Grenzdehnung von 2 wird nicht erreicht
                    if (0 <= epsc < 2.0):
                        # Querschnittslängen Vergabe
                        interval_start_1 = 0
                        interval_end_1 = x
                        interval_start_2 = 0
                        interval_end_2 = 0
                        interval_start_3 = 0
                        interval_end_3 = 0
                        # Querschnittsbreiten Vergabe
                        concrete_width_1 = b_eff
                        concrete_width_2 = 0
                        concrete_width_3 = 0
                    # Grenzdehnung von 2 wird erreicht
                    elif (2 / epsc * x <= h_f):
                        # Querschnittslängen Vergabe
                        interval_start_1 = 0
                        interval_end_1 = 2 / epsc * x  # 2 = Dehnung beim Erreichen der Druckfestigkeit
                        interval_start_2 = 2 / epsc * x
                        interval_end_2 = x
                        interval_start_3 = 0
                        interval_end_3 = 0
                        # Querschnittsbreiten Vergabe
                        concrete_width_1 = b_eff
                        concrete_width_2 = b_eff
                        concrete_width_3 = 0

                    # Abgrenzen der einzlnen Bereichsunterschiede
                    x1 = np.linspace(interval_start_1, interval_end_1, N)
                    x2 = np.linspace(interval_start_2, interval_end_2, N)
                    x3 = np.linspace(interval_start_3, interval_end_3, N)

                    # Definition der Spannungsfunktionen
                    y1 = []
                    y2 = []
                    y3 = []
                    # Grenzdehnung von 2 wird nicht erreicht
                    if (0 <= epsc < 2.0):
                        y1_list_with_all_sigma_c_values_promille = []
                        for i in range(N):
                            sigma_c = fcd * (1 - (1 - ((x1[i] * epsc) / (x * 2))) ** 2)

                            y1_list_with_all_sigma_c_values_promille.append(sigma_c)

                        y1_values = y1_list_with_all_sigma_c_values_promille
                        y2_values = fcd * np.zeros(N)
                        y3_values = fcd * np.zeros(N)

                        y1.append(y1_values)
                        y2.append(y2_values)
                        y3.append(y3_values)
                    # Grenzdehnung von 2 wird erreicht
                    elif (2 / epsc * x <= h_f):
                        y1_list_with_all_sigma_c_values_upto_2_promille = []
                        for i in range(N):
                            sigma_c = fcd * (1 - (1 - ((x1[i] * epsc) / (
                                        x * 2))) ** 2)  # Sigma c-Werte bis zum Erreichen der Druckfestigkeit -> Betondehnung = 2

                            y1_list_with_all_sigma_c_values_upto_2_promille.append(sigma_c)

                        y1_values = y1_list_with_all_sigma_c_values_upto_2_promille  # sigma_concrete_at_given_intervals(x1)
                        y2_values = fcd * np.ones(N)
                        y3_values = fcd * np.zeros(N)

                        y1.append(y1_values)
                        y2.append(y2_values)
                        y3.append(y3_values)

                    # Integration der einzelnen Spannungsfunktionen
                    if (0 <= epsc < 2.0):
                        M_1 = simps(y1 * x1, x= x1)
                        A_1 = simps(y1, x = x1)
                        S_1 = M_1 / A_1

                    elif (2 / epsc * x <= h_f):
                        M_1 = simps(y1 * x1, x = x1)  # moment 1
                        A_1 = simps(y1, x = x1)  # pressure force 1
                        S_1 = M_1 / A_1  # centroid of area 1

                        M_2 = simps(y2 * x2, x = x2)
                        A_2 = simps(y2, x = x2)
                        S_2 = M_2 / A_2

                    # concrete pressure
                    Fc_1 = A_1 * concrete_width_1
                    Fc_2 = A_2 * concrete_width_2
                    Fc_3 = 0

                    # centroid of compressive stress in concrete
                    S_ges = (S_1 * Fc_1 + S_2 * Fc_2 + S_3 * Fc_3) / (
                                Fc_1 + Fc_2 + Fc_3)  # Bei der Berechnung der Gesamtschwerpunkte der Druckkraefte muss die Querschnittsbreite der einzelnen Querschnitte einfliessen
                    z = S_ges + d - x  # Innerer Hebelarm

                    Meds = abs(M - N_f * (zs1 - (h - d)))
                    Mrds = (Fc_1 + Fc_2 + Fc_3) * z

                    nu_eds = Meds / (b_eff * (d ** 2) * fcd)
                    if nu_eds_grenz <= nu_eds:
                        Meds_lim = nu_eds_grenz * b_eff * (d ** 2) * fcd

                        zeta_lim = 0
                        concrete_strain_2 = 3.5
                        if nu_eds_grenz == 0.296:
                            zeta_lim = 0.813
                            steal_strain_1 = 4.28
                        elif nu_eds_grenz == 0.371:
                            zeta_lim = 0.743
                            steal_strain_1 = 2.174

                        #epss2 = ((x - d2) / x) * abs(-3.5)
                        epss2 = ((steal_strain_1 + concrete_strain_2) / d) * (d - d2) - steal_strain_1

                        sigma_s_2 = 0
                        if epssyd <= epss2:
                            sigma_s_2 = fyd
                        elif epss2 < epssyd:
                            sigma_s_2 = fyd * (epss / epssyd)

                        z_nu_eds_grenz = zeta_lim * d

                        delta_Med = abs(M) - Meds_lim
                        As1erf_nu_lim = (1 / fyd) * (Meds_lim / z_nu_eds_grenz + N_f) * 100 ** 2
                        As2erf = (1 / sigma_s_2) * (
                                    delta_Med / (d - d2)) * 100 ** 2
                        As1erf = As1erf_nu_lim + As2erf
                    else:
                        As1erf = (1 / sigma_s) * (Fc_1 + Fc_2 + Fc_3 + N_f) * 100 ** 2

                    if (0 <= epsc < 3.5):
                        epsc += 0.001

                    else:
                        epss -= 0.001

                    num_iter += 1
                # Druckzone im Steg und Flasch -> Nullline im Flansch
                elif (x > h_f):
                    # Grenzdehnung von 2 wird nicht erreicht
                    if (0 <= epsc < 2.0):
                        # Querschnittslängen Vergabe
                        interval_start_1 = 0
                        interval_end_1 = x - h_f
                        interval_start_2 = x - h_f
                        interval_end_2 = x
                        interval_start_3 = 0
                        interval_end_3 = 0
                        # Querschnittsbreiten Vergabe
                        concrete_width_1 = b_w
                        concrete_width_2 = b_eff
                        concrete_width_3 = 0
                    # Grenzdehnung von 2 wird im STEG erreicht
                    elif (2 / epsc * x <= (x - h_f)):
                        # Querschnittslängen Vergabe
                        interval_start_1 = 0
                        interval_end_1 = 2 / epsc * x  # 2 = Dehnung beim Erreichen der Druckfestigkeit
                        interval_start_2 = 2 / epsc * x
                        interval_end_2 = x - h_f
                        interval_start_3 = x - h_f
                        interval_end_3 = x
                        # Querschnittsbreiten Vergabe
                        concrete_width_1 = b_w
                        concrete_width_2 = b_w
                        concrete_width_3 = b_eff
                    # Grenzdehnung von 2 wird im FLANSCH erreicht
                    elif (2 / epsc * x > (x - h_f)):
                        # Querschnittslängen Vergabe
                        interval_start_1 = 0
                        interval_end_1 = x - h_f
                        interval_start_2 = x - h_f
                        interval_end_2 = 2 / epsc * x
                        interval_start_3 = 2 / epsc * x
                        interval_end_3 = x
                        # Querschnittsbreiten Vergabe
                        concrete_width_1 = b_w
                        concrete_width_2 = b_eff
                        concrete_width_3 = b_eff

                    # Abgrenzen der einzlnen Bereichsunterschiede
                    x1 = np.linspace(interval_start_1, interval_end_1, N)
                    x2 = np.linspace(interval_start_2, interval_end_2, N)
                    x3 = np.linspace(interval_start_3, interval_end_3, N)

                    # Definition der Spannungsfunktionen
                    y1 = []
                    y2 = []
                    y3 = []
                    # Grenzdehnung von 2 wird nicht erreicht
                    if (0 <= epsc < 2.0):
                        y1_list_with_all_sigma_c_values_promille = []
                        y2_list_with_all_sigma_c_values_upto_2_promille = []
                        for i in range(N):
                            sigma_c = fcd * (1 - (1 - ((x1[i] * epsc) / (x * 2))) ** 2)
                            sigma_c_2 = fcd * (1 - (1 - ((x2[i] * epsc) / (x * 2))) ** 2)

                            y1_list_with_all_sigma_c_values_promille.append(sigma_c)
                            y2_list_with_all_sigma_c_values_upto_2_promille.append(sigma_c_2)

                        y1_values = y1_list_with_all_sigma_c_values_promille
                        y2_values = y2_list_with_all_sigma_c_values_upto_2_promille
                        y3_values = fcd * np.zeros(N)

                        y1.append(y1_values)
                        y2.append(y2_values)
                        y3.append(y3_values)
                    # Grenzdehnung von 2 wird im STEG erreicht
                    elif (2 / epsc * x <= (x - h_f)):
                        y1_list_with_all_sigma_c_values_upto_2_promille = []
                        for i in range(N):
                            sigma_c = fcd * (1 - (1 - ((x1[i] * epsc) / (
                                        x * 2))) ** 2)  # Sigma c-Werte bis zum Erreichen der Druckfestigkeit -> Betondehnung = 2

                            y1_list_with_all_sigma_c_values_upto_2_promille.append(sigma_c)

                        y1_values = y1_list_with_all_sigma_c_values_upto_2_promille  # sigma_concrete_at_given_intervals(x1)
                        y2_values = fcd * np.ones(N)
                        y3_values = fcd * np.ones(N)

                        y1.append(y1_values)
                        y2.append(y2_values)
                        y3.append(y3_values)
                    # Grenzdehnung von 2 wird im FLANSCH erreicht
                    elif (2 / epsc * x > (x - h_f)):
                        y1_list_with_all_sigma_c_values_promille = []
                        y2_list_with_all_sigma_c_values_upto_2_promille = []
                        for i in range(N):
                            sigma_c = fcd * (1 - (1 - ((x1[i] * epsc) / (x * 2))) ** 2)
                            sigma_c_2 = fcd * (1 - (1 - ((x2[i] * epsc) / (x * 2))) ** 2)

                            y1_list_with_all_sigma_c_values_promille.append(sigma_c)
                            y2_list_with_all_sigma_c_values_upto_2_promille.append(sigma_c_2)

                        y1_values = y1_list_with_all_sigma_c_values_promille
                        y2_values = y2_list_with_all_sigma_c_values_upto_2_promille
                        y3_values = fcd * np.ones(N)

                        y1.append(y1_values)
                        y2.append(y2_values)
                        y3.append(y3_values)

                    # Integration der einzelnen Spannungsfunktionen
                    if (0 <= epsc < 2.0):
                        M_1 = simps(y1 * x1, x= x1)
                        A_1 = simps(y1, x = x1)
                        S_1 = M_1 / A_1

                        M_2 = simps(y2 * x2, x=  x2)
                        A_2 = simps(y2, x = x2)
                        S_2 = M_2 / A_2
                    # Grenzdehnung von 2 wird im STEG erreicht
                    elif (2 / epsc * x <= x - h_f):
                        M_1 = simps(y1 * x1, x = x1)  # moment 1
                        A_1 = simps(y1, x = x1)  # pressure force 1
                        S_1 = M_1 / A_1  # centroid of area 1

                        M_2 = simps(y2 * x2, x= x2)
                        A_2 = simps(y2, x= x2)
                        S_2 = M_2 / A_2

                        M_3 = simps(y3 * x3, x= x3)
                        A_3 = simps(y3, x= x3)
                        S_3 = M_3 / A_3
                    # Grenzdehnung von 2 wird im FLANSCH erreicht
                    elif (2 / epsc * x > x - h_f):
                        M_1 = simps(y1 * x1, x= x1)
                        A_1 = simps(y1, x=x1)
                        S_1 = M_1 / A_1

                        M_2 = simps(y2 * x2, x=x2)
                        A_2 = simps(y2, x=x2)
                        S_2 = M_2 / A_2

                        M_3 = simps(y3 * x3, x=x3)
                        A_3 = simps(y3, x=x3)
                        S_3 = M_3 / A_3

                    # concrete pressure
                    Fc_1 = A_1 * concrete_width_1
                    Fc_2 = A_2 * concrete_width_2
                    Fc_3 = A_3 * concrete_width_3

                    # centroid of compressive stress in concrete
                    S_ges = (S_1 * Fc_1 + S_2 * Fc_2 + S_3 * Fc_3) / (
                                Fc_1 + Fc_2 + Fc_3)  # Bei der Berechnung der Gesamtschwerpunkte der Druckkraefte muss die Querschnittsbreite der einzelnen Querschnitte einfliessen
                    z = S_ges + d - x

                    Meds = abs(M - N_f * (d - (h - zs1)))
                    Mrds = (Fc_1 + Fc_2 + Fc_3) * z

                    nu_eds = Meds / (b_w * (d ** 2) * fcd)
                    if nu_eds_grenz <= nu_eds:
                        Meds_lim = nu_eds_grenz * b_w * (d ** 2) * fcd

                        zeta_lim = 0
                        concrete_strain_2 = 3.5
                        if nu_eds_grenz == 0.296:
                            zeta_lim = 0.813
                            steal_strain_1 = 4.28
                        elif nu_eds_grenz == 0.371:
                            zeta_lim = 0.743
                            steal_strain_1 = 2.174

                        #epss2 = ((x - d2) / x) * abs(-3.5)
                        epss2 = ((steal_strain_1 + concrete_strain_2) / d) * (d - d2) - steal_strain_1

                        sigma_s_2 = 0
                        if epssyd <= epss2:
                            sigma_s_2 = fyd
                        elif epss2 < epssyd:
                            sigma_s_2 = fyd * (epss / epssyd)

                        z_nu_eds_grenz = zeta_lim * d

                        delta_Med = abs(M) - Meds_lim
                        As1erf_nu_lim = (1 / fyd) * (Meds_lim / z_nu_eds_grenz + N_f) * 100 ** 2
                        As2erf = (1 / sigma_s_2) * (
                                    delta_Med / (d - d2)) * 100 ** 2
                        As1erf = As1erf_nu_lim + As2erf
                    else:
                        As1erf = (1 / sigma_s) * (Fc_1 + Fc_2 + Fc_3 + N_f) * 100 ** 2

                    if (0 <= epsc < 3.5):
                        epsc += 0.001

                    else:
                        epss -= 0.001

                    num_iter += 1

            else:
                print("Limit reached!")
                break

        #DIN 1045-1:2008-08
        amax = 0
        a1 = self.center_of_gravity
        a2 = h - self.center_of_gravity
        if a1 > a2:
            amax = a1 * 100
        else:
            amax = a2 * 100
        Wc = (self.cross_section_inertia*100*100*100*100)/amax
        Asmin = ((fctm*10**2) * Wc)/(fyk*10**2*(d*0.9)*100)

        needed_reinforcement = []
        if Asmin < As1erf:
            print("Iteration steps: ", num_iter)
            print("Med: ", np.around(M, 3), "MN")
            print("Ned: ", np.around(N_f, 3), "MN")
            print("Affecting moment: ", np.around(Meds, 3), "MN")
            print("Marginal moment: ", np.around(Meds_lim, 3), "MN")
            print("Modulus of section : ", np.around(Mrds, 3), "MN")
            print("Required bending reinforcement: ", np.around(As1erf, 3), "cm²")
            if As2erf != 0:
                print("Required compressive reinforcement : ", np.around(As2erf, 3), "cm²")
            print("Pressure zone height x =  ", np.around(x, 3), "m")
            print("Retrieved pressure zone ξ = ", np.around(xi, 3))
            print("Edge concrete compression εc = ", np.around(epsc, 3), "‰")
            if epss >= 2.17:
                print("Steel strain of bending reinforcement εs: Yield strength is reached.")
                if As2erf != 0:
                    print("εs = ", np.around(steal_strain_1, 3), "‰")
                else:
                    print("εs = ", np.around(epss, 3), "‰")
            else:
                if As2erf != 0:
                    print("Steel strain of bending reinforcement εs: Yield strength is reached.")
                    print("εs = ", np.around(steal_strain_1, 3), "‰")
                else:
                    print("Steel strain of bending reinforcement εs: Yield strength is not reached.")
                    print("εs = ", np.around(epss, 3), "‰")

            if As2erf != 0:
                if As2erf != 0:
                    print("Steel strain of compressive reinforcement εs2: Yield strength is reached.")
                    print("εs2 = ", np.around(epss2, 3), "‰")
                else:
                    print("Steel strain of compressive reinforcement εs2: Yield strength is not reached.")
                    print("εs2 = ", np.around(epss2, 3), "‰")

            print("Inner lever arm z = ", np.around(z, 3), "m")

            reinforcement = [float(As1erf), float(As2erf)]
            needed_reinforcement.append(reinforcement)
        else:
            print("Minimum reinforcement is dominant!")
            print("Required bending reinforcement: ", np.around(Asmin, 3), "cm²")
            reinforcement = [float(Asmin), float(0.0)]
            needed_reinforcement.append(reinforcement)

        return needed_reinforcement

    def calculate_beam_section_stirrup(self, beam_sub_section, strength_of_concrete, tensile_yield_strength, strut_angle_choice):
        Ved = beam_sub_section.shear_force_ed / 1000000
        Vedr = abs(Ved)  # reduzierte Querkraft, da direkte Lagerung
        N_f = beam_sub_section.normal_force_ed / 1000000

        A = self.cross_section_area  # QS-Fläche

        h = self.height
        b = self.width_web  # kleinste QS-breite -> bw aus Biegebemessung

        d1 = beam_sub_section.effective_height_pressure  # cnom + dsl*0.5
        d = h - d1
        z = 0.9 * d

        fcd = strength_of_concrete  # N/mm²
        fck = (fcd * 1.5) / 0.85
        fctm = 0.3 * fck ** (2 / 3)
        yc = 1.5

        fyd = tensile_yield_strength  # MN/m²
        fyk = fyd * 1.15

        a_sw_correct = 0

        # Berechnung des Druckstrebenwinkels
        c = 0.5
        sigma_cd = abs(N_f / A)
        Vrd_cc = c * 0.48 * (fck ** (1 / 3)) * (1 - 1.2 * (sigma_cd / fcd)) * b * z

        cot_teta = abs((1.2 + 1.4 * (sigma_cd / fcd)) / (1 - (Vrd_cc / Vedr)))
        strut_angle = math.degrees(math.atan(1 / cot_teta))

        if strut_angle_choice == 0:
            if 1.0 <= cot_teta <= 3.0:
                cot_teta = cot_teta
            elif 3.0 < cot_teta:
                cot_teta = 3.0
                strut_angle = 18.43
            elif 0 <= cot_teta < 1.0:
                cot_teta = 1.0
                strut_angle = 45
        else:
            if N_f > 0:
                cot_teta = 1.0
                strut_angle = 45
            else:
                cot_teta = 1.2
                strut_angle = 40

        # Nachweis der Druckstrebentragfähigkeit
        alpha_cw = 1.0
        v2 = 1.1 - (fck / 500)
        v1 = 0.75 * v2
        tan_teta = math.tan(math.radians(strut_angle))
        Vrd_max = (alpha_cw * b * z * v1 * fcd) / ((tan_teta) + (cot_teta))
        proof = abs(Vedr / Vrd_max)

        # Ermittlung der stat. erforderlichen Bewehrung, für vertikale Bügel
        a_sw = (Vedr / (z * fyd)) * tan_teta * 100 ** 2

        # Konstruktive Durchbiegung
        a_sw_min = 0.16 * (fctm / fyk) * b * 1.0 * 100 ** 2  # Mindestquerkraftbewehrung, vertikale Bügel

        needed_reinforcement = []

        if a_sw <= a_sw_min:
            a_sw_correct = a_sw_min
        else:
            a_sw_correct = a_sw

        if proof <= 1.0:
            print("Proof that the strut sturdiness is complied =  ", np.around(proof, 3), "%")
        else:
            print("Proof that the strut sturdiness is NOT complied =  ", np.around(proof, 3), "%")

        print("Compression strut angle =  ", np.around(strut_angle, 2), "°")

        if a_sw <= a_sw_min:
            print("Minimum reinforcement is required for the shear force =  ", np.around(a_sw_correct, 3), " cm²/m")
        else:
            print("Required shear force reinforcement =  ", np.around(a_sw_correct, 3), " cm²/m")

        needed_reinforcement.append(float(np.around(a_sw_correct, 3)))

        return needed_reinforcement
