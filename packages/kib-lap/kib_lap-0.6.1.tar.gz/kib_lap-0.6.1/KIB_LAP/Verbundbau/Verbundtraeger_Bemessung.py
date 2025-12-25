import matplotlib.pyplot as plt
import numpy as np
import pandas as pd



class Verbundtraeger:
    def __init__(self,hc, b_c, t_a_flu, b_a_flu,t_a_flo, b_a_flo, t_a_w, h_aw, l ,fck,_fy ,  
                 _traeger = "FT", zement = "I42.5N", _LF = 80, t0 = 3, _t_ausbau = 30):
        """_summary_

        Args:
            hc (_type_, optional): _description_. Defaults to _h_c.
            b_c (_type_, optional): _description_. Defaults to _b_c.
            t_a_flu (_type_, optional): _description_. Defaults to _t_fl_o.
            b_a_flu (_type_, optional): _description_. Defaults to _b_fl_o.
            t_a_w (_type_, optional): _description_. Defaults to _t_aw.
            h_aw (_type_, optional): _description_. Defaults to _h_aw.
            l (_type_, optional): _description_. Defaults to _l.
            _traeger (str, optional): _description_. Defaults to "FT". \n
                                                                 "Normal"
        """
        # Betonquerschnitt
        self.hc, self.b_c = hc,b_c
        # Stahlquerschnitt
        self.t_a_flu,self.b_a_flu = t_a_flu,b_a_flu
        self.t_a_flo, self.b_a_flo = t_a_flo,b_a_flo

        self.t_a_w, self.h_aw = t_a_w,h_aw
        # Systemparameter
        self.length = l
        self.e_qt = 4.00
        self.traeger = _traeger
        self.Zement = zement
        self.LF = _LF
        
        self.t0 = t0


        self.fck = fck
        self.fy = _fy

        self.t_ausbau = _t_ausbau

        # self.Spannungen_Eigengewicht()
        # self.Spannungen_Ausbaulasten()
        # self.Spannungen_Verkehr()
        # self.Spannungen_Schwinden()
        # self.Spannungsplot_Ausbaulasten()
        # self.Spannungsplot_Verkehr()
        # self.Spannungsplot_Schwinden()
        # self.Spannungen_GZT()

    def AllgemeinerBlock(self):
        self.Baustoffe()
        self.Berechnung_Plattenbreite_MW()
        self.Querschnittswerte()

        self.Einstufung_Querschnittsklasse()
        self.Berechnung_Kriechzahlen_Schwinden()
        self.Berechnung_Kriechzahlen_Ausbau()

        self.Berechnung_Schwinddehnung()
        self.Reduktionszahlen()
        self.Ideel_Verkehr()
        self.Ideel_Ausbaulasten()
        self.Ideel_Schwinden()
        self.Einwirkungen_Schwinden()

    def Baustoffe(self):

        self.fcm = self.fck + 8
        self.fctm = 0.30*self.fck**0.666667
        self.Ecm = 22000 * (self.fcm * 0.10)**0.30
        self.fyk = 500
        self.E_s = 200000

        
        self.fy_druck = self.fy/1.1
        self.fy_tau = self.fy / np.sqrt(3)
        self.E_a= 210000
        
        self.fcd = self.fck*0.85 / 1.5
        self.fyd = self.fyk / 1.15

    def Berechnung_Plattenbreite_MW(self):
        self.le = self.length
        self.b_e = self.le/8

        self.b_eff = min(2 * self.b_e + self.b_a_flo, self.b_c)

    def Querschnittswerte(self):
        # Querschnittswerte für Kriechen / Schwinden
        self.A = self.b_c * self.hc
        if (self.traeger == "FT"):
            self.u = self.b_c
        elif (self.traeger == "Normal"):
            self.u = self.b_c * 2                   # Zur Trocknung freigesetzter Umfang
        else:
            self.u = self.b_c * 2

        self.h_0 = 2 * self.A / self.u

        # Querschnittswerte für E-E-Nachweise (Schwerpunkte in den Mitten)
        self.I_c = self.b_eff * self.hc**3 / 12
        self.A_c = self.b_eff * self.hc
        self.A_a = self.b_a_flo*self.t_a_flo + self.b_a_flu * self.t_a_flu + self.h_aw * self.t_a_w

        self.A_aflo = self.b_a_flo*self.t_a_flo
        self.delta_zflo = self.t_a_flo / 2
        self.A_aflu = self.b_a_flu * self.t_a_flu
        self.delta_zflu = self.h_aw + self.t_a_flo + self.t_a_flu/2
        self.A_w = self.h_aw * self.t_a_w
        self.delta_zw = self.t_a_flo + self.h_aw/2

        print(self.A_aflo)
        print(self.delta_zflo)
        print(self.A_aflu)
        print(self.delta_zflu)

        print(self.A_a)


        self.z_aso = (self.A_aflo * self.delta_zflo + self.A_aflu * self.delta_zflu + self.A_w * self.delta_zw) * self.A_a**(-1)
        self.z_asu = self.t_a_flo+self.t_a_flu+self.h_aw - self.z_aso



        print(self.z_aso)
        print(self.z_asu)

        self.I_a =  (self.b_a_flu * self.t_a_flu**3 /12) \
                    + (self.b_a_flo * self.t_a_flo**3 /12) \
                    + self.h_aw**3 * self.t_a_w / 12 \
                    + self.A_w * (self.z_aso - self.t_a_flo - self.h_aw/2)**2 \
                    + self.A_aflo * (self.z_aso - self.t_a_flo/2)**2 \
                    + self.A_aflu * (self.z_asu - self.t_a_flu/2)**2
        
        self.W_au = self.I_a / (self.z_asu)
        self.W_ao = self.I_a / (self.z_aso)

        # Berechnung des statischen Moments des Stahlquerschnitts

        self.delta_hawsy = (self.h_aw + self.t_a_flu - self.z_asu)
        self.S_ymax = self.A_aflo * (self.z_aso-self.t_a_flo/2) + self.delta_hawsy * self.t_a_w * self.delta_hawsy/2


        def Plotting_Cross_Section():
            # Concrete Coordinates
            y_Beton = [0,self.b_eff/2 , self.b_eff/2 , 0,-self.b_eff/2,-self.b_eff/2,0]
            z_Beton = [0,0,self.hc,self.hc,self.hc,0,0]
            # Steel coordinates
            self.y_1a = 0
            self.y_2a = self.b_a_flo/2
            self.y_3a = self.t_a_w/2
            self.y_4a = self.b_a_flu/2

            y_steel = [self.y_1a,self.y_2a,self.y_2a,self.y_3a,self.y_3a,self.y_4a,self.y_4a,-self.y_4a,-self.y_4a,-self.y_3a,-self.y_3a,-self.y_2a,-self.y_2a,self.y_1a]

            self.z_1a = self.hc
            self.z_2a = self.hc+self.t_a_flo
            self.z_3a = self.hc + self.t_a_flo + self.h_aw
            self.z_4a = self.hc + self.t_a_flo + self.t_a_flu+ self.h_aw


            z_steel = [self.z_1a,self.z_1a,self.z_2a,self.z_2a,self.z_3a,self.z_3a,self.z_4a,self.z_4a,self.z_3a,self.z_3a,self.z_2a,self.z_2a,self.z_1a,self.z_1a]

            # Plotting
            fig = plt.figure(figsize = (8,5))

            plt.plot(y_Beton,z_Beton,color = "black")
            plt.plot(y_steel,z_steel,color = "black")
            plt.xlim(-self.b_eff/2-1, self.b_eff+2)
            plt.ylim(-1, 2.3)

            # Parameters
            plt.text(self.b_eff/2 + 0.5, -1.00, r'$\bf{Betonparameter:}$', fontsize=10)
            plt.text(self.b_eff/2  + 0.5, -0.50, r"$h_{\mathrm{c,eff}} $"  +  f"= {self.hc:.3f} [m]", fontsize=8)
            plt.text(self.b_eff/2  + 0.5, -0.50, r"$b_{\mathrm{eff}} $"  +  f"= {self.b_eff:.3f} [m]", fontsize=8)
            plt.text(self.b_eff/2  + 0.5, -0.25, r"$A_{\mathrm{c,eff}} $"  +  f"= {self.A_c:.3f} [m²]", fontsize=8)

            plt.text(self.b_eff/2 + 0.5, 0.25, r'$\bf{Stahlparameter:}$', fontsize=10)
            plt.text(self.b_eff/2  + 0.5, 0.50, r"$b_{\mathrm{a,fl,o}} $"  +  f"= {self.b_a_flo:.3f} [m]", fontsize=8)
            plt.text(self.b_eff/2  + 0.5, 0.75, r"$t_{\mathrm{a,fl,o}} $"  +  f"= {self.t_a_flo:.3f} [m]", fontsize=8)
            plt.text(self.b_eff/2  + 0.5, 1.00, r"$b_{\mathrm{a,fl,u}} $"  +  f"= {self.b_a_flu:.3f} [m]", fontsize=8)
            plt.text(self.b_eff/2  + 0.5, 1.25, r"$t_{\mathrm{a,fl,u}} $"  +  f"= {self.t_a_flu:.3f} [m]", fontsize=8)
            plt.text(self.b_eff/2  + 0.5, 1.50, r"$h_{\mathrm{a,w}} $"  +  f"= {self.h_aw:.3f} [m]", fontsize=8)
            plt.text(self.b_eff/2  + 0.5, 1.75, r"$t_{\mathrm{a,w}} $"  +  f"= {self.t_a_w:.3f} [m]", fontsize=8)
            plt.text(self.b_eff/2  + 0.5, 2.00, r"$A_{\mathrm{a}} $"  +  f"= {self.A_a:.3f} [m]", fontsize=8)

            
            ax = plt.gca()
            ax.set_aspect('equal')
            ax.invert_yaxis()

            try:
                plt.savefig("Querschnittsbilder/Querschnitt_Effektiv.eps" ,bbox_inches='tight')
            except:
                pass

            plt.show(block=False)  # Zeigt das Fenster ohne Blockierung des Codes
            plt.pause(1)  # Pausiert für 3 Sekunden
            plt.close()  # Schließt das Plot-Fenster nach 3 Sekunden

        Plotting_Cross_Section()

        def Plotting_Cross_Section_Brutto():
            # Concrete Coordinates
            y_Beton = [0,self.b_c/2 , self.b_c/2 , 0,-self.b_c/2,-self.b_c/2,0]
            z_Beton = [0,0,self.hc,self.hc,self.hc,0,0]
            # Steel coordinates
            self.y_1a = 0
            self.y_2a = self.b_a_flo/2
            self.y_3a = self.t_a_w/2
            self.y_4a = self.b_a_flu/2

            y_steel = [self.y_1a,self.y_2a,self.y_2a,self.y_3a,self.y_3a,self.y_4a,self.y_4a,-self.y_4a,-self.y_4a,-self.y_3a,-self.y_3a,-self.y_2a,-self.y_2a,self.y_1a]
            
            self.z_1a = self.hc
            self.z_2a = self.hc+self.t_a_flo
            self.z_3a = self.hc + self.t_a_flo + self.h_aw
            self.z_4a = self.hc + self.t_a_flo + self.t_a_flu+ self.h_aw

            z_steel = [self.z_1a,self.z_1a,self.z_2a,self.z_2a,self.z_3a,self.z_3a,self.z_4a,self.z_4a,self.z_3a,self.z_3a,self.z_2a,self.z_2a,self.z_1a,self.z_1a]

            # Plotting
            plt.plot(y_Beton,z_Beton,color = "black")
            plt.plot(y_steel,z_steel,color = "black")
            plt.xlim(-self.b_eff/2-1, self.b_eff+2)
            plt.ylim(-1, 2.3)

            # Parameters
            plt.text(self.b_c/2 + 0.5, -0.75, r'$\bf{Betonparameter:}$', fontsize=10)
            plt.text(self.b_c/2  + 0.5, -0.50, r"$b_{\mathrm{c}} $"  +  f"= {self.b_c:.3f} [m]", fontsize=8)
            plt.text(self.b_c/2  + 0.5, -0.25, r"$A_{\mathrm{c,ges}} $"  +  f"= {self.A_c:.3f} [m²]", fontsize=8)

            plt.text(self.b_c/2 + 0.5, 0.25, r'$\bf{Stahlparameter:}$', fontsize=10)
            plt.text(self.b_c/2  + 0.5, 0.50, r"$b_{\mathrm{a,fl,o}} $"  +  f"= {self.b_a_flo:.3f} [m²]", fontsize=8)
            plt.text(self.b_c/2  + 0.5, 0.75, r"$t_{\mathrm{a,fl,o}} $"  +  f"= {self.t_a_flo:.3f} [m²]", fontsize=8)
            plt.text(self.b_c/2  + 0.5, 1.00, r"$b_{\mathrm{a,fl,u}} $"  +  f"= {self.b_a_flu:.3f} [m²]", fontsize=8)
            plt.text(self.b_c/2  + 0.5, 1.25, r"$t_{\mathrm{a,fl,u}} $"  +  f"= {self.t_a_flu:.3f} [m²]", fontsize=8)
            plt.text(self.b_c/2  + 0.5, 1.50, r"$h_{\mathrm{a,w}} $"  +  f"= {self.h_aw:.3f} [m²]", fontsize=8)
            plt.text(self.b_c/2  + 0.5, 1.75, r"$t_{\mathrm{a,w}} $"  +  f"= {self.t_a_w:.3f} [m²]", fontsize=8)
            plt.text(self.b_c/2  + 0.5, 2.00, r"$A_{\mathrm{a}} $"  +  f"= {self.A_a:.3f} [m²]", fontsize=8)


            
            ax = plt.gca()
            ax.set_aspect('equal')
            ax.invert_yaxis()

            try:
                plt.savefig("Querschnittsbilder/Querschnitt_Brutto.eps" ,bbox_inches='tight')
            except:
                pass

            plt.show(block=False)  # Zeigt das Fenster ohne Blockierung des Codes
            plt.pause(1)  # Pausiert für 3 Sekunden
            plt.close()  # Schließt das Plot-Fenster nach 3 Sekunden


        Plotting_Cross_Section_Brutto()

    def Einstufung_Querschnittsklasse(self):
        self.c_t_flansch  = (self.b_a_flo/2 - self.t_a_w/2) / self.t_a_flo
        self.c_t_web = self.h_aw / self.t_a_w

        if (self.c_t_web <= 72 * 0.814):
            self.QK = 1

        if (self.c_t_flansch <= 10 * 0.814):
            self.QK = 2

    def Berechnung_Kriechzahlen_Schwinden(self):
        # Kriechzahl für Schwinden
        if (self.Zement == "I42.5N" or self.Zement == "I32.5R"):
            self.alpha = 0
        elif(self.Zement == "I42.5R" or self.Zement == "I52.5N" or self.Zement == "I52.5R" ):
            self.alpha = 1
        else:
            self.alpha = -1

        self.t_0 = self.t0

        self.t_0_eff = max(self.t_0 * (1 + 9 / (2 +self.t_0**(1.2) ))**self.alpha ,0.5)
        
        self.t_infty = 70 * 365 

        self.RH = self.LF                # Außenliegendes Bauteil

        # Fallunterscheidung für Druckfestigkeit
        self.alpha_1 = min((35 / self.fcm)**0.7,1)
        self.alpha_2 = min((35 / self.fcm)**0.2,1)
        self.alpha_3 = min((35 / self.fcm)**0.5,1)

        # Einfluss der Luftfeuchte und wirksamer Bauteildicke
        if (self.fcm <= 35):
            self.phi_rh = 1+ (1-self.RH/100) / (0.1 * (self.h_0*1000)**(0.3333333))
        else:
            self.phi_rh = (1+ (1-self.RH/100) / (0.1 * (self.h_0*1000)**(0.3333333)) * self.alpha_1 ) * self.alpha_2

        # Einfluss der Betondruckfestigkeit
        self.beta_fcm = 16.8 / np.sqrt(self.fcm)
        # Einfluss des Belastungsbeginns
        self.beta_t0 = 1 / (0.1 + self.t_0_eff**0.2)
        # Einfluss der Luftfeuchte - Beta-Beiwert
        if (self.fcm <= 35):
            self.beta_h = min(1.5 * (1 + (0.012 * self.RH)**18) * self.h_0*1000 + 250 , 1500)
        else:
            self.beta_h = min(1.5 * (1 + (0.012 * self.RH)**18) * self.h_0 * 1000 + 250 * self.alpha_3 , 1500  *self.alpha_3)
        # Einfluss der Belastungsdauer und Belastungsbeginn
        self.beta_c_t_t0 = ((self.t_infty - self.t_0) / (self.beta_h + self.t_infty-self.t_0))**0.30

        self.phi_infty = self.phi_rh * self.beta_fcm * self.beta_t0 * self.beta_c_t_t0

    def Berechnung_Kriechzahlen_Ausbau(self):
        # Kriechzahl für Ausbaulasten

        if (self.Zement == "I42.5N" or self.Zement == "I32.5R"):
            self.alpha = 0
        elif(self.Zement == "I42.5R" or self.Zement == "I52.5N" or self.Zement == "I52.5R" ):
            self.alpha = 1
        else:
            self.alpha = -1

        self.t_0ab = self.t_ausbau

        self.t_0_effab = max(self.t_0ab* (1 + 9 / (2 +self.t_0ab**(1.2) ))**self.alpha ,0.5)
        
        self.t_infty = 70 * 365 

        self.RH = self.LF                # Außenliegendes Bauteil

        # Fallunterscheidung für Druckfestigkeit
        self.alpha_1 = min((35 / self.fcm)**0.7,1)
        self.alpha_2 = min((35 / self.fcm)**0.2,1)
        self.alpha_3 = min((35 / self.fcm)**0.5,1)

        # Einfluss der Luftfeuchte und wirksamer Bauteildicke
        if (self.fcm <= 35):
            self.phi_rh = 1+ (1-self.RH/100) / (0.1 * (self.h_0*1000)**(0.3333333))
        else:
            self.phi_rh = (1+ (1-self.RH/100) / (0.1 * (self.h_0*1000)**(0.3333333)) * self.alpha_1 ) * self.alpha_2

        # Einfluss der Betondruckfestigkeit
        self.beta_fcm = 16.8 / np.sqrt(self.fcm)
        # Einfluss des Belastungsbeginns
        self.beta_t0ab = 1 / (0.1 + self.t_0_effab**0.2)
        # Einfluss der Luftfeuchte - Beta-Beiwert
        if (self.fcm <= 35):
            self.beta_h = min(1.5 * (1 + (0.012 * self.RH)**18) * self.h_0*1000 + 250 , 1500)
        else:
            self.beta_h = min(1.5 * (1 + (0.012 * self.RH)**18) * self.h_0 * 1000 + 250 * self.alpha_3 , 1500  *self.alpha_3)
        # Einfluss der Belastungsdauer und Belastungsbeginn
        self.beta_c_t_t0ab = ((self.t_infty - self.t_0ab) / (self.beta_h + self.t_infty-self.t_0ab))**0.30

        self.phi_infty_ab = self.phi_rh * self.beta_fcm * self.beta_t0ab * self.beta_c_t_t0ab
 
    def Berechnung_Schwinddehnung(self):


        # Trocknungsschwinden

        self.beta_rh = 1.55 * (1-(self.RH/100)**3)

        if (self.Zement == "I42.5N" or self.Zement == "I32.5R"):
            self.alpha_as = 700
            self.alpha_ds1 = 4
            self.alpha_ds2 = 0.12
        elif(self.Zement == "I42.5R" or self.Zement == "I52.5N" or self.Zement == "I52.5R" ):
            self.alpha_as = 600
            self.alpha_ds1 = 6
            self.alpha_ds2 = 0.12
        else:
            self.alpha_as = 800
            self.alpha_ds1 = 3
            self.alpha_ds2 = 0.12

        self.epsilon_cd_0 = 0.85 * ((220+110*self.alpha_ds1) * np.exp(-self.alpha_ds2 * self.fcm/10)) * 1e-6 * self.beta_rh

        ts = 3          # Nachbehandlung des Betons
        self.t_s = ts

        t = self.t_infty
        self.t_infty_s = t

        self.beta_ds = np.sqrt((t-ts) / ((t-ts) +0.04 * np.sqrt(self.h_0**3)))

        if (self.h_0 * 1000 <=100):
            self.k_h = 1.00
        elif(self.h_0*1000 > 100 and self.h_0*1000 <= 200):
            self.k_h = 1.00 - 0.15 / 100 * (self.h_0*1000-100)
        elif(self.h_0*1000 > 200 and self.h_0*1000 <= 300):
            self.k_h = 0.85 - 0.10 / 100 * (self.h_0*1000-200)
        elif(self.h_0*1000 > 300 and self.h_0*1000 <= 500):
            self.k_h = 0.75 - 0.05 / 100 * (self.h_0*1000-300)
        elif(self.h_0*1000 > 500 ):
            self.k_h = 0.70


        self.epsilon_cd = self.beta_ds * self.epsilon_cd_0 * self.k_h

        # Autogenes Schwinden
        self.epsilon_ca_infty = 2.5 * (self.fck - 10 ) * 1e-6
        self.beta_as = 1 - np.exp(-0.2 * np.sqrt(t))

        self.epsilon_ca = self.beta_as * self.epsilon_ca_infty

        # Gesamtschwinden
        self.epsilon_cs = self.epsilon_cd+ self.epsilon_ca

    def Reduktionszahlen(self):
        self.n_0 = self.E_a / self.Ecm
        self.n_P = self.n_0 * (1+1.1*self.phi_infty_ab)            # Ausbaulasten
        self.n_s = self.n_0 * (1+self.phi_infty *0.55)          # Kriechen
        
    def Ideel_Verkehr(self):
        self.elast_zentrum_0 = False
        self.A_c0_lm = self.A_c / self.n_0
        self.I_c0_lm = self.I_c / self.n_0
        self.a_lm = self.z_aso + self.hc*0.5
        self.A_i_0_lm = self.A_a + self.A_c0_lm
        self.a_c0_lm = self.a_lm * self.A_a / self.A_i_0_lm
        if (self.a_c0_lm + self.hc*0.5 < self.hc and (self.hc-self.a_c0_lm-self.hc*0.5 >0.01)):
            print("Elastisches Zentrum im Betongurt - Abminderung Betonfläche (Zugzone)")
            self.elast_zentrum_0 = True
            self.diff_hc0 = self.hc - (self.a_c0_lm + self.hc*0.5)
            self.h_c_red_0 = self.hc - self.diff_hc0 
            self.A_c0_lm = self.A_c0_lm / self.hc * self.h_c_red_0
            self.I_c0_lm = self.I_c0_lm / self.hc**3 * self.h_c_red_0**3
            self.a_lm = self.z_aso + self.diff_hc0 + self.h_c_red_0/2
            self.A_i_0_lm = self.A_a + self.A_c0_lm
            self.a_c0_lm = self.a_lm * self.A_a/self.A_i_0_lm

        self.a_a0_lm = self.a_lm - self.a_c0_lm
        self.I_i0_lm = self.I_c0_lm + self.I_a + self.A_a * self.a_a0_lm**2+self.A_c0_lm * self.a_c0_lm**2
        
        # Berechnung der Widerstandsmomente
        self.z_A0 = self.a_a0_lm + self.z_asu
        self.z_B0 = (-self.a_c0_lm + self.hc / 2)
        self.z_C0 = (-self.a_c0_lm - self.hc / 2)

        self.W_A0 = self.I_i0_lm / self.z_A0
        self.W_B0 = self.I_i0_lm / self.z_B0
        self.W_C0 = self.I_i0_lm / self.z_C0

    def Ideel_Ausbaulasten(self):
        self.elast_zentrum_al = False
        self.A_cp_al = self.A_c / self.n_P
        self.I_cp_al = self.I_c / self.n_P
        self.a_al = self.z_aso+ self.hc  * 0.5 
        self.A_i_p_al = self.A_a + self.A_cp_al
        self.a_cp_al = self.a_al * self.A_a / self.A_i_p_al
        self.a_ap_al = self.a_al - self.a_cp_al
        self.I_ip_al = self.I_cp_al + self.I_a + self.A_a * self.a_ap_al**2 + self.A_cp_al * self.a_cp_al**2

        if (self.a_cp_al + self.hc*0.5 < self.hc and (self.hc-self.a_cp_al-self.hc*0.5 >0.01)):
            print("Elastisches Zentrum für Ausbaulasten im Betongurt - Abminderung Betonfläche (Zugzone)")
            self.elast_zentrum_al = True
            self.diff_hcal = self.hc - (self.a_cp_al + self.hc*0.5)
            self.h_c_red_al = self.hc - self.diff_hcal 
            self.A_cp_al = self.A_cp_al / self.hc * self.h_c_red_al
            self.I_cp_al = self.I_cp_al / self.hc**3 * self.h_c_red_al**3
            self.a_al = self.z_aso + self.diff_hcal + self.h_c_red_al/2
            self.A_i_p_al = self.A_a + self.A_cp_al
            self.a_cp_al = self.a_al * self.A_a/self.A_i_p_al


        # Berechnung der Widerstandsmomente
        self.z_A_al = self.a_ap_al + self.z_asu
        self.z_B_al = (-self.a_cp_al + self.hc / 2)
        self.z_C_al = (-self.a_cp_al - self.hc / 2)

        self.W_A_al = self.I_ip_al / self.z_A_al
        self.W_B_al = self.I_ip_al / self.z_B_al
        self.W_C_al = self.I_ip_al / self.z_C_al

    def Ideel_Schwinden(self):
        self.A_cs_s = self.A_c / self.n_s
        self.I_cs_s = self.I_c / self.n_s
        self.a_s = self.z_aso+ self.hc  * 0.5
        self.A_i_cs_s = self.A_a + self.A_cs_s
        self.a_cs_s = self.a_s * self.A_a / self.A_i_cs_s
        self.a_as_s = self.a_s - self.a_cp_al
        self.I_ip_s = self.I_cs_s + self.I_a + self.A_a * self.a_as_s**2 + self.A_cp_al * self.a_cs_s**2

        # Berechnung der Widerstandsmomente
        self.z_A_s = self.a_as_s + self.z_asu
        self.z_B_s = (-self.a_cs_s + self.hc / 2)
        self.z_C_s = (-self.a_cs_s  -self.hc / 2)

        self.W_A_s = self.I_ip_s / self.z_A_s
        self.W_B_s = self.I_ip_s / self.z_B_s
        self.W_C_s = self.I_ip_s / self.z_C_s

    def Einwirkungen_Schwinden(self):
        # Zwangsschnittgrößen / Primär 
        self.N_sch = - self.epsilon_cs * self.Ecm / (1+ self.phi_infty * 0.55) * self.A 
        self.N_sch_cal = - self.epsilon_cs * self.Ecm / (1+ self.phi_infty * 0.55) * self.A 
        self.M_sch = abs(self.N_sch * self.a_cs_s )

    def Spannungen_Eigengewicht(self):
        self.sigma_A_a_g1k = self.M_gk1 / self.W_au
        self.sigma_B_a_g1k = -self.M_gk1 / self.W_ao
        self.sigma_B_c_g1k = 0
        self.sigma_C_c_g1k = 0

        self.list_sigma_g1k = [self.sigma_A_a_g1k, self.sigma_B_a_g1k,self.sigma_B_c_g1k, self.sigma_C_c_g1k]
        
    def Spannungen_Ausbaulasten(self, Mgk2):
        self.M_gk2  = Mgk2
        self.sigma_A_a_g2k = self.M_gk2 / self.W_A_al
        self.sigma_B_a_g2k = self.M_gk2 / self.W_B_al
        self.sigma_B_c_g2k = self.sigma_B_a_g2k  * 1 / self.n_P
        self.sigma_C_c_g2k = self.M_gk2 / self.W_C_al * 1 / self.n_P

        self.list_sigma_g2k = [self.sigma_A_a_g2k, self.sigma_B_a_g2k,self.sigma_B_c_g2k, self.sigma_C_c_g2k]

    def Spannungen_Verkehr(self, M_Verkehr):
        self.M_Verkehr = M_Verkehr
        self.sigma_A_a_lm = self.M_Verkehr / self.W_A0
        self.sigma_B_a_lm = self.M_Verkehr / self.W_B0
        self.sigma_B_c_lm = self.M_Verkehr / self.W_B0 * 1/self.n_0
        self.sigma_C_c_lm = self.M_Verkehr / self.W_C0 * 1/self.n_0

        self.list_sigma_lm = [self.sigma_A_a_lm, self.sigma_B_a_lm,self.sigma_B_c_lm, self.sigma_C_c_lm]

    def Spannungen_Schwinden(self):
        self.sigma_A_a_s = self.N_sch /self.A_i_cs_s + self.M_sch / self.W_A_s
        self.sigma_B_a_s = self.N_sch /self.A_i_cs_s + self.M_sch / self.W_B_s
        self.sigma_B_c_s = self.N_sch /self.A_i_cs_s * (1/self.n_s) + abs(self.N_sch) / self.A_c + self.M_sch / self.W_B_s * (1/self.n_s)
        self.sigma_C_c_s = self.N_sch /self.A_i_cs_s * (1/self.n_s) + abs(self.N_sch) / self.A_c + self.M_sch / self.W_C_s * (1/self.n_s)

        self.list_sigma_s = [self.sigma_A_a_s, self.sigma_B_a_s,self.sigma_B_c_s, self.sigma_C_c_s]

    def Spannungen_GZT(self):
        # Spannungen am Punkt A: Alle Einwirkungen erzeugen Zugspannungen
        self.sigma_A_a_ges = 1.35 * self.sigma_A_a_g1k + 1.35 * self.sigma_A_a_g2k + 1.45 *  self.sigma_A_a_lm  + 1.50 * self.sigma_A_a_s 
        # Spannungen am Punkt B
        if (self.sigma_B_a_g2k <= 0 and self.sigma_B_a_g1k <= 0):
            if ( self.sigma_B_a_lm <= 0 and self.sigma_B_a_s <= 0):         # Eigengewicht und Ausbaulasten erzeugen am Punkt B maximale Druckspannungen
                self.sigma_B_a_ges = 1.35 * self.sigma_B_a_g1k + 1.35 * self.sigma_B_a_g2k + 1.45 *  self.sigma_B_a_lm  + 1.50 * self.sigma_B_a_s                
            elif (self.sigma_B_a_lm <= 0 ):
                self.sigma_B_a_ges = 1.35 * self.sigma_B_a_g1k + 1.35 * self.sigma_B_a_g2k + 1.45 *  self.sigma_B_a_lm  + 0 * self.sigma_B_a_s 
                
            elif (self.sigma_B_a_s <= 0 ):
                self.sigma_B_a_ges = 1.35 * self.sigma_B_a_g1k + 1.35 * self.sigma_B_a_g2k + 0 *  self.sigma_B_a_lm  + 1.50 * self.sigma_B_a_s 
                
            # Betonspannungen: Maximaler Druck

            if (self.sigma_B_c_lm <= 0 and self.sigma_B_c_s <= 0):
                self.sigma_B_c_ges = 1.35 * self.sigma_B_c_g1k + 1.35 * self.sigma_B_c_g2k + 1.45 *  self.sigma_B_c_lm  + 1.50 * self.sigma_B_c_s
            elif (self.sigma_B_c_lm <= 0):
                self.sigma_B_c_ges = 1.35 * self.sigma_B_c_g1k + 1.35 * self.sigma_B_c_g2k + 1.45 *  self.sigma_B_c_lm  + 0 * self.sigma_B_c_s 
            elif (self.sigma_B_c_s <= 0):
                self.sigma_B_c_ges = 1.35 * self.sigma_B_c_g1k + 1.35 * self.sigma_B_c_g2k + 0 *  self.sigma_B_c_lm  + 1.50 * self.sigma_B_c_s
            else:
                self.sigma_B_c_ges = 1.35 * self.sigma_B_c_g1k + 1.35 * self.sigma_B_c_g2k

        elif ( self.sigma_B_a_g1k <= 0):
            if ( self.sigma_B_a_lm <= 0 and self.sigma_B_a_s <= 0):         # Eigengewicht und Ausbaulasten erzeugen am Punkt B maximale Druckspannungen
                self.sigma_B_a_ges = 1.35 * self.sigma_B_a_g1k + 0.90 * self.sigma_B_a_g2k + 1.45 *  self.sigma_B_a_lm  + 1.50 * self.sigma_B_a_s 

            elif (self.sigma_B_a_lm <= 0 ):
                self.sigma_B_a_ges = 1.35 * self.sigma_B_a_g1k + 0.90 * self.sigma_B_a_g2k + 1.45 *  self.sigma_B_a_lm  + 0 * self.sigma_B_a_s 

            elif (self.sigma_B_a_s <= 0 ):
                self.sigma_B_a_ges = 1.35 * self.sigma_B_a_g1k + 0.90 * self.sigma_B_a_g2k + 0 *  self.sigma_B_a_lm  + 1.50 * self.sigma_B_a_s 
            
            # Betonspannungen: Maximaler Druck
            if (self.sigma_B_c_lm <= 0 and self.sigma_B_c_s<= 0):
                self.sigma_B_c_ges = 1.35 * self.sigma_B_c_g1k + 0.90 * self.sigma_B_c_g2k + 1.45 *  self.sigma_B_c_lm  + 1.50 * self.sigma_B_c_s
            elif (self.sigma_B_c_lm <= 0):
                self.sigma_B_c_ges = 1.35 * self.sigma_B_c_g1k + 0.90 * self.sigma_B_c_g2k + 1.45 *  self.sigma_B_c_lm  + 0 * self.sigma_B_c_s 
            elif (self.sigma_B_c_s <= 0):
                self.sigma_B_c_ges = 1.35 * self.sigma_B_c_g1k + 0.90 * self.sigma_B_c_g2k + 0 *  self.sigma_B_c_lm  + 1.50 * self.sigma_B_c_s

        # Spannungen am Punkt C: Einwirkungen erzeugen alle Druckspannungen

        self.sigma_C_c_ges = 1.35 * self.sigma_C_c_g1k + 1.35 * self.sigma_C_c_g2k + 1.45 *  self.sigma_C_c_lm  + 1.50 * self.sigma_C_c_s 

    def Spannungsplot_Ausbaulasten(self):            
        # Concrete Coordinates
        y_Beton = [0,self.b_eff/2 , self.b_eff/2 , 0,-self.b_eff/2,-self.b_eff/2,0]
        z_Beton = [0,0,self.hc,self.hc,self.hc,0,0]
        # Steel coordinates
        self.y_1a = 0
        self.y_2a = self.b_a_flo/2
        self.y_3a = self.t_a_w/2

        y_steel = [self.y_1a,self.y_2a,self.y_2a,self.y_3a,self.y_3a,self.y_2a,self.y_2a,-self.y_2a,-self.y_2a,-self.y_3a,-self.y_3a,-self.y_2a,-self.y_2a,self.y_1a]

        self.z_1a = self.hc
        self.z_2a = self.hc+self.t_a_flo
        self.z_3a = self.hc + self.t_a_flo + self.h_aw
        self.z_4a = self.hc + 2 * self.t_a_flo + self.h_aw

        z_steel = [self.z_1a,self.z_1a,self.z_2a,self.z_2a,self.z_3a,self.z_3a,self.z_4a,self.z_4a,self.z_3a,self.z_3a,self.z_2a,self.z_2a,self.z_1a,self.z_1a]

        # Plotting the stresses

        list_sigma_g2k = [self.list_sigma_g2k[i] / 25 + self.b_eff for i in range(0,len(self.list_sigma_g2k),1)]
        list_sigma_g2k.insert(0,self.b_eff)
        list_sigma_g2k.append(self.b_eff)
        list_sigma_boundary = [self.b_eff,self.b_eff,self.b_eff,self.b_eff,self.b_eff,self.b_eff]
        list_sigma_height = [self.z_4a,self.z_4a,self.z_1a,self.z_1a,0,0]

        # Plotting circles
        draw_circle_1 = plt.Circle(( self.b_eff , self.z_4a), 0.05 , label = "Punkt A", color = "blue")
        draw_circle_2 = plt.Circle(( self.b_eff , self.z_1a ), 0.05 , label = "Punkt B", color = "black")
        draw_circle_3 = plt.Circle(( self.b_eff , 0 ), 0.05 , label = "Punkt C", color = "green")
        plt.gcf().gca().add_artist(draw_circle_1)
        plt.gcf().gca().add_artist(draw_circle_2)
        plt.gcf().gca().add_artist(draw_circle_3)



        # Plotting
        plt.plot(y_Beton,z_Beton,color = "black")
        plt.plot(y_steel,z_steel,color = "black")
        plt.plot(list_sigma_g2k,list_sigma_height,color = "red")
        plt.plot(list_sigma_boundary,list_sigma_height ,color = "black")
        plt.xlim(-self.b_eff/2-1, self.b_eff+2)

        plt.ylim(-1, 2)

        plt.legend()

        # Parameters

        ax = plt.gca()
        ax.set_aspect('equal')
        ax.invert_yaxis()

        try:
            plt.savefig("Latex/Bilder/Verbundquerschnitt/Spannungen_Ausbaulasten.png", dpi = 250 ,bbox_inches='tight')
        except:
            plt.savefig("../Latex/Bilder/Verbundquerschnitt/Spannungen_Ausbaulasten.png", dpi = 250 ,bbox_inches='tight')

        #plt.show()
        plt.close()

    def Spannungsplot_Verkehr(self):            
        # Concrete Coordinates
        y_Beton = [0,self.b_eff/2 , self.b_eff/2 , 0,-self.b_eff/2,-self.b_eff/2,0]
        z_Beton = [0,0,self.hc,self.hc,self.hc,0,0]
        # Steel coordinates
        self.y_1a = 0
        self.y_2a = self.b_a_flo/2
        self.y_3a = self.t_a_w/2

        y_steel = [self.y_1a,self.y_2a,self.y_2a,self.y_3a,self.y_3a,self.y_2a,self.y_2a,-self.y_2a,-self.y_2a,-self.y_3a,-self.y_3a,-self.y_2a,-self.y_2a,self.y_1a]

        self.z_1a = self.hc
        self.z_2a = self.hc+self.t_a_flo
        self.z_3a = self.hc + self.t_a_flo + self.h_aw
        self.z_4a = self.hc + 2 * self.t_a_flo + self.h_aw

        z_steel = [self.z_1a,self.z_1a,self.z_2a,self.z_2a,self.z_3a,self.z_3a,self.z_4a,self.z_4a,self.z_3a,self.z_3a,self.z_2a,self.z_2a,self.z_1a,self.z_1a]

        # Plotting the stresses

        list_sigma_g2k = [self.list_sigma_lm[i] / 125 + self.b_eff for i in range(0,len(self.list_sigma_g2k),1)]
        list_sigma_g2k.insert(0,self.b_eff)
        list_sigma_g2k.append(self.b_eff)
        list_sigma_boundary = [self.b_eff,self.b_eff,self.b_eff,self.b_eff,self.b_eff,self.b_eff]
        list_sigma_height = [self.z_4a,self.z_4a,self.z_1a,self.z_1a,0,0]

        # Plotting circles
        draw_circle_1 = plt.Circle(( self.b_eff , self.z_4a), 0.05 , label = "Punkt A", color = "blue")
        draw_circle_2 = plt.Circle(( self.b_eff , self.z_1a ), 0.05 , label = "Punkt B", color = "black")
        draw_circle_3 = plt.Circle(( self.b_eff , 0 ), 0.05 , label = "Punkt C", color = "green")
        plt.gcf().gca().add_artist(draw_circle_1)
        plt.gcf().gca().add_artist(draw_circle_2)
        plt.gcf().gca().add_artist(draw_circle_3)



        # Plotting
        plt.plot(y_Beton,z_Beton,color = "black")
        plt.plot(y_steel,z_steel,color = "black")
        plt.plot(list_sigma_g2k,list_sigma_height,color = "red")
        plt.plot(list_sigma_boundary,list_sigma_height ,color = "black")
        plt.xlim(-self.b_eff/2-1, self.b_eff+2)

        plt.ylim(-1, 2)

        plt.legend()

        # Parameters

        ax = plt.gca()
        ax.set_aspect('equal')
        ax.invert_yaxis()

        try:
            plt.savefig("Latex/Bilder/Verbundquerschnitt/Spannungen_Verkehr.png", dpi = 250 ,bbox_inches='tight')
        except:
            plt.savefig("../Latex/Bilder/Verbundquerschnitt/Spannungen_Verkehr.png", dpi = 250 ,bbox_inches='tight')

        #plt.show()
        plt.close()

    def Spannungsplot_Schwinden(self):            
        # Concrete Coordinates
        y_Beton = [0,self.b_eff/2 , self.b_eff/2 , 0,-self.b_eff/2,-self.b_eff/2,0]
        z_Beton = [0,0,self.hc,self.hc,self.hc,0,0]
        # Steel coordinates
        self.y_1a = 0
        self.y_2a = self.b_a_flo/2
        self.y_3a = self.t_a_w/2

        y_steel = [self.y_1a,self.y_2a,self.y_2a,self.y_3a,self.y_3a,self.y_2a,self.y_2a,-self.y_2a,-self.y_2a,-self.y_3a,-self.y_3a,-self.y_2a,-self.y_2a,self.y_1a]

        self.z_1a = self.hc
        self.z_2a = self.hc+self.t_a_flo
        self.z_3a = self.hc + self.t_a_flo + self.h_aw
        self.z_4a = self.hc + 2 * self.t_a_flo + self.h_aw

        z_steel = [self.z_1a,self.z_1a,self.z_2a,self.z_2a,self.z_3a,self.z_3a,self.z_4a,self.z_4a,self.z_3a,self.z_3a,self.z_2a,self.z_2a,self.z_1a,self.z_1a]

        # Plotting the stresses

        list_sigma_g2k = [self.list_sigma_s[i] / 125 + self.b_eff for i in range(0,len(self.list_sigma_g2k),1)]
        list_sigma_g2k.insert(0,self.b_eff)
        list_sigma_g2k.append(self.b_eff)
        list_sigma_boundary = [self.b_eff,self.b_eff,self.b_eff,self.b_eff,self.b_eff,self.b_eff]
        list_sigma_height = [self.z_4a,self.z_4a,self.z_1a,self.z_1a,0,0]

        # Plotting circles
        draw_circle_1 = plt.Circle(( self.b_eff , self.z_4a), 0.05 , label = "Punkt A", color = "blue")
        draw_circle_2 = plt.Circle(( self.b_eff , self.z_1a ), 0.05 , label = "Punkt B", color = "black")
        draw_circle_3 = plt.Circle(( self.b_eff , 0 ), 0.05 , label = "Punkt C", color = "green")
        plt.gcf().gca().add_artist(draw_circle_1)
        plt.gcf().gca().add_artist(draw_circle_2)
        plt.gcf().gca().add_artist(draw_circle_3)



        # Plotting
        plt.plot(y_Beton,z_Beton,color = "black")
        plt.plot(y_steel,z_steel,color = "black")
        plt.plot(list_sigma_g2k,list_sigma_height,color = "red")
        plt.plot(list_sigma_boundary,list_sigma_height ,color = "black")
        plt.xlim(-self.b_eff/2-1, self.b_eff+2)

        plt.ylim(-1, 2)

        plt.legend()

        # Parameters

        ax = plt.gca()
        ax.set_aspect('equal')
        ax.invert_yaxis()

        try:
            plt.savefig("Latex/Bilder/Verbundquerschnitt/Spannungen_Schwinden.png", dpi = 250 ,bbox_inches='tight')
        except:
            plt.savefig("../Latex/Bilder/Verbundquerschnitt/Spannungen_Schwinden.png", dpi = 250 ,bbox_inches='tight')

        #plt.show()
        plt.close()



