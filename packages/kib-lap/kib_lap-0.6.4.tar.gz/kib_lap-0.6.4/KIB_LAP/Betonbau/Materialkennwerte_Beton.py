
import numpy as np
class Baustoffe:
    def __init__(self, liste_baustoffe, h_c=0.13, b_c=4, traeger="FT", t0=1, t=365,ts = 1):
        """
        Klasse zur Berechnung der Baustoffparameter: Eingabe in [MN/m², m , MN, etc.]
        liste_baustoffe: Eingabe von [fck,fyk] \n
        h_c = Höhe des Betonträgers zur Berechnung von h0 in [m] \n
        b_c = Bezugsbreite in [m] \n
        traeger = Eingabe des Umfangs, welcher der freien Trocknung ausgesetzt ist \n
                   Für Fertigteile ergibt sich hier: h0 = 2*h   ("FT")
                   Für Ortbetonplatten folgt:        h0 = h     ("Ortbeton")
        t0 = Tatsächliches Betonalter beim Belastungsbeginn  \n
        t  = Betrachteter Zeitpunkt für die ermittelte Kriechzahl
        """
        # Teilsicherheitsbeiwerte für Baustoffe
        self.gamma_c = 1.5
        self.gamma_s = 1.15
        # Stahlbeton
        self.fck = liste_baustoffe[0]
        self.fcd = self.fck / self.gamma_c * 0.85
        self.fctm = 0.30 * self.fck ** (2 / 3)  # Nach Eurocode 2 Tabelle 3.1
        self.fctk_005 = 0.7 * self.fctm
        self.fcm = self.fck + 8
        self.Ecm = 22000 * (0.1 * self.fcm) ** (0.3)

        self.alpha_T = 1.2e-5

        # Kriechen und Schwinden

        self.traeger = traeger
        self.Zement = "I42.5N"
        self.LF = 80

        self.t0 = t0  # Annahme: Belastungsbeginn der Fertigteile nach 28 d
        self.t = t
        self.ts = ts

        # Querschnittswerte für Kriechen / Schwinden

        self.b_c = b_c
        self.h_c = h_c

        self.A = self.b_c * self.h_c
        if self.traeger == "FT":
            self.u = self.b_c
        elif self.traeger == "Normal":
            self.u = self.b_c * 2  # Zur Trocknung freigesetzter Umfang
        else:
            self.u = self.b_c * 2

        self.h_0 = 2 * self.A / self.u

        # Stahl
        self.fyk = liste_baustoffe[1]
        self.fyd = self.fyk / self.gamma_s
        self.Es = 2e5
        self.Materialgesetz_Beton()
        self.Kriechzahlen()
        self.Schwindzahlen()

    def Materialgesetz_Beton(self):
        self.eps_c1 = 0.7 * self.fcm**0.31
        self.eps_c1 = min(self.eps_c1, 2.8)  # Sicherstellen, dass eps_c1 <= 2.8

    def Kriechzahlen(self):
        self.Zement = "I42.5N"

        if self.Zement == "I42.5N" or self.Zement == "I32.5R":
            self.alpha = 0
        elif (
            self.Zement == "I42.5R"
            or self.Zement == "I52.5N"
            or self.Zement == "I52.5R"
        ):
            self.alpha = 1
        else:
            self.alpha = -1

        self.t_0 = self.t0

        self.t_0_eff = max(
            self.t_0 * (1 + 9 / (2 + self.t_0 ** (1.2))) ** self.alpha, 0.5
        )

        self.t_infty = (
            self.t
        )  # self.t_0+15       #70 * 365  Annahme: 15 Tage nach der Betonage

        self.RH = self.LF  # Außenliegendes Bauteil

        # Fallunterscheidung für Druckfestigkeit
        self.alpha_1 = min((35 / self.fcm) ** 0.7, 1)
        self.alpha_2 = min((35 / self.fcm) ** 0.2, 1)
        self.alpha_3 = min((35 / self.fcm) ** 0.5, 1)

        # Einfluss der Luftfeuchte und wirksamer Bauteildicke
        if self.fcm <= 35:
            self.phi_rh = 1 + (1 - self.RH / 100) / (
                0.1 * (self.h_0 * 1000) ** (0.3333333)
            )
        else:
            self.phi_rh = (
                1
                + (1 - self.RH / 100)
                / (0.1 * (self.h_0 * 1000) ** (0.3333333))
                * self.alpha_1
            ) * self.alpha_2

        # Einfluss der Betondruckfestigkeit
        self.beta_fcm = 16.8 / np.sqrt(self.fcm)
        # Einfluss des Belastungsbeginns
        self.beta_t0 = 1 / (0.1 + self.t_0_eff**0.2)

        # Einfluss der Luftfeuchte - Beta-Beiwert
        if self.fcm <= 35:
            self.beta_h = min(
                1.5 * (1 + (0.012 * self.RH) ** 18) * self.h_0 * 1000 + 250, 1500
            )
        else:
            self.beta_h = min(
                1.5 * (1 + (0.012 * self.RH) ** 18) * self.h_0 * 1000
                + 250 * self.alpha_3,
                1500 * self.alpha_3,
            )

        # Einfluss der Belastungsdauer und Belastungsbeginn

        self.beta_c_t_t0 = (
            (self.t_infty - self.t_0) / (self.beta_h + self.t_infty - self.t_0)
        ) ** 0.30

        self.phi_infty = (
            self.phi_rh * self.beta_fcm * self.beta_t0 * self.beta_c_t_t0
        )  # Kriechzahl zum Zeitpunkt t

        print("Kriechzahl phi ", self.phi_infty)

    def Schwindzahlen(self):
        self.beta_rh = 1.55 * (1 - (self.RH / 100) ** 3)

        if self.Zement == "I42.5N" or self.Zement == "I32.5R":
            self.alpha_as = 700
            self.alpha_ds1 = 4
            self.alpha_ds2 = 0.12
        elif (
            self.Zement == "I42.5R"
            or self.Zement == "I52.5N"
            or self.Zement == "I52.5R"
        ):
            self.alpha_as = 600
            self.alpha_ds1 = 6
            self.alpha_ds2 = 0.12
        else:
            self.alpha_as = 800
            self.alpha_ds1 = 3
            self.alpha_ds2 = 0.12

        self.epsilon_cd_0 = (
            0.85
            * ((220 + 110 * self.alpha_ds1) * np.exp(-self.alpha_ds2 * self.fcm / 10))
            * 1e-6
            * self.beta_rh
        )

        ts = self.ts
        
        t = self.t_infty
        self.t_infty_s = t

        self.beta_ds = (t - ts) / ((t - ts) + 0.04 * np.sqrt(self.h_0**3))

        if self.h_0 * 1000 <= 100:
            self.k_h = 1.00
        elif self.h_0 * 1000 > 100 and self.h_0 * 1000 <= 200:
            self.k_h = 1.00 - 0.15 / 100 * self.h_0 * 1000
        elif self.h_0 * 1000 > 200 and self.h_0 * 1000 <= 300:
            self.k_h = 0.85 - 0.10 / 100 * self.h_0 * 1000
        elif self.h_0 * 1000 > 300 and self.h_0 * 1000 <= 500:
            self.k_h = 0.75 - 0.05 / 100 * self.h_0 * 1000
        elif self.h_0 * 1000 > 500:
            self.k_h = 0.70

        self.epsilon_cd = self.beta_ds * self.epsilon_cd_0 * self.k_h

        # Autogenes Schwinden
        self.epsilon_ca_infty = 2.5 * (self.fck - 10) * 1e-6
        self.beta_as = 1 - np.exp(-0.2 * np.sqrt(t))

        self.epsilon_ca = self.beta_as * self.epsilon_ca_infty

        # Gesamtschwinden
        self.epsilon_cs = self.epsilon_cd + self.epsilon_ca

        print("Gesamtschwindmaß ", self.epsilon_cs)

