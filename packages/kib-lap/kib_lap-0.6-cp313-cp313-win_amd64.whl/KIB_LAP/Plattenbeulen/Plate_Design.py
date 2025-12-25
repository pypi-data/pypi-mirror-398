

import numpy as np
import matplotlib.pyplot as plt

from pylatex import (
    Document,
    Section,
    Subsection,
    Command,
    Tabular,
    Math,
    TikZ,
    Axis,
    Plot,
    Figure,
    Matrix,
    Alignat,
    MultiRow,
    MultiColumn, 
    Tabularx,
    Tabu,
    ColumnType,
    LongTable,
    Table, 
    Center

)

from pylatex.utils import escape_latex, fix_filename, dumps_list, bold, \
    italic, verbatim, NoEscape



class Beulnachweise_Platten:
    """
    Das ist eine Klasse zur Berechnung einfacher Beulfelder.

    self.sigma_1_x =    Größte Druckspannung an einer Seite des Beulfeldes.
                        Hier wird üblicherweise ein positives Vorzeichen        
                        für Druckspannungen gewählt.



    """
    def __init__(self):
        # Spannungen aus Sofistik
        self.sigma_1_x = 387.5       # Druckspannung (Positiv)
        self.sigma_2_x = -262.9      # Zugspannung negativ
        self.sigma_1_v = 387.5
        self.sigma_2_v = 262.9
        self.tau_1 = 0
        self.tau_2 = 0

        # Materialkenngrößen
        self.fyd = 460
        self.E_s = 210e3 

        # Faktoren bis zum Erreichen der kritischen Beulvergleichsspannungen
        self.alpha_ult_k_1_x = self.fyd/self.sigma_1_x
        # Geometrie des Beulfeldes
        self.b = 5.00
        self.a = 1.90
        self.t = 0.02
        self.alpha = self.a/self.b

        self.chi_w  = 0
        self.rho    = 0

    def Nachweisfuehrung(self):
        # Ermittlung linear elastischer Beulspannungen

        self.sigma_e = 1.9*(100*self.t/self.b)**2*10
        self.psi = self.sigma_2_x/self.sigma_1_x       # Randspannungsverhältnis bezogen auf die größe Druckspannung (Druck positiv)

        self.k_sigma = (self.alpha + 1/self.alpha)**2 * (2.1)/(self.psi+1.1)

        self.sigma_cr = self.k_sigma*self.sigma_e
        self.alpha_cr = self.sigma_cr/self.sigma_1_x

        self.alpha_ult_k = self.fyd/self.sigma_1_v
    
        #____Abminderungsfaktoren für das Plattenbeulen für ein beidseitig gestützes Feld___#
        self.lambda_p = np.sqrt(self.alpha_ult_k/self.alpha_cr)

        # Abminderungsfaktor chi_w

        self.eta = 1.20
        if (self.fyd > 460):
            self.eta = 1.00
        if (self.lambda_p < 0.83/self.eta):
            self.chi_w = self.eta
        elif(self.lambda_p >= 0.83 / self.eta):
            self.chi_w = 0.83 / self.lambda_p
        
        print(self.chi_w)

        # Abminderungskenngröße rho_x
        # Für plattenartiges Versagen

        if (self.lambda_p <= 0.5 + np.sqrt(0.085 - 0.055 * self.psi)):
            self.rho = 1.0
        elif (self.lambda_p > 0.5 + np.sqrt(0.085 - 0.055 * self.psi)):
            self.rho = min((self.lambda_p - 0.055 * (3+self.psi))/(self.lambda_p**2),1.00)

        # Für Knickstabähnliches Verhalten

        self.alpha_e    = 0.21 # Für nicht ausgesteifte Blechfelder: alpha_e = 0.21

        self.phi        = 0.5*(1+self.alpha_e*(self.lambda_p -0.2) + self.lambda_p**2)

        self.chi_c      = 1/(self.phi + np.sqrt(self.phi**2 - self.lambda_p**2))

        # Knickspannung

        self.sigma_cr_r = (np.pi**2 * self.E_s * self.t**2)/(12 * (1-0.3)*self.a**2)
        self.sigma_cr_p_x = self.sigma_1_x

        # Interpolation zwischen plattenartigen / knickstabähnlichem Verhalten

        self.xi = self.sigma_cr_p_x/self.sigma_cr_r-1

        print(self.xi)

        self.xi = max(min(self.xi,1),0)

        print(self.xi)

        self.rho_x = (self.rho - self.chi_c)*self.xi*(2-self.xi) + self.chi_c

        print(self.rho_x)


        # Nachweisführung

        self.eta = (self.sigma_1_x/(self.fyd * self.rho_x / 1.10))

    def Ausgabe_Pdf_Latex(self,width ,*args, **kwargs):
        fname = "Beulnachweise"
        geometry_options = {"right": "2cm", "left": "2cm"}
        self.doc = Document(fname, geometry_options=geometry_options)

        with self.doc.create(Section("Berechnung der Beulnachweise nach DIN EN 1993-1-5")):
            self.doc.append("Take a look at this beautiful plot:")

            # with doc.create(Figure(position="htbp")) as plot:
            #     plot.add_plot(width=NoEscape(width), *args, **kwargs)
            #     plot.add_caption("I am a caption.")

            self.doc.create(Subsection("Materialkenngrößen"))
            self.doc.append("")
            #self.doc.append(Math(data=["2*3", "=", 3 * 2]))

        self.doc.create(Subsection("Geometrische und materielle Kenngrößen"))

        def Material_Properties():
            # Tabular

            self.doc.append(NoEscape(r"\centering"))
            
            table = Table(position="htb")

            self.doc.append(Command('centering'))
            table.add_caption("Material properties")


            t = Tabular(table_spec='|c|c|c|', data=None, pos=1, width=3)

            t.add_hline(start=None, end=None)

            t.add_row(("Kenngröße", "Wert", "Einheit"), escape=False, strict=True, mapper=[bold])
            t.add_hline(start=None, end=None)

            t.add_row(["Streckgrenze", self.fyd, "MN/m²"])
            t.add_row([NoEscape(r"Streckgrenze - $$\gamma_{\text{M1}}$$") , f"{self.fyd/1.10:.2f}", "MN/m²"])
            t.add_row(["E-Modul", self.E_s, "MN/m²"])
            t.add_hline(start=None, end=None)
            # t.add_row(1, 2, escape=False, strict=True, mapper=[bold])

            # # MultiColumn/MultiRow.
            # t.add_row((MultiColumn(size=2, align='|c|', data='MultiColumn'),),
            #         strict=True)

            # # One multiRow-cell in that table would not be proper LaTeX,
            # # so strict is set to False

            # t.add_row((MultiRow(size=2, width='*', data='MultiRow'),), strict=False)

            # append tabular to table
            table.append(t)

            table = self.doc.append(table)



        Material_Properties()

        def Section_Entry_Parameters():
            
            table = Table(position="htb")

            
            table.add_caption("Eingangsgrößen")

            t = Tabular(table_spec='|c|c|c|', data=None, pos=1, width=3)
            self.doc.append(Command('centering'))

            t.add_hline(start=None, end=None)

            t.add_row(("Kenngröße", "Wert", "Einheit"), escape=False, strict=True, mapper=[bold])
            t.add_hline(start=None, end=None)

            t.add_row(["Länge des Beulfeldes a", self.a, "m"])
            t.add_row(["Breite des Beulfeldes a", self.b, "m"])
            t.add_row(["Blechdicke t ", self.t, "m"])

            t.add_row([NoEscape(r"Seitenverhältnis $$\alpha $$"), f"{self.a/self.b:.2f}", "-"])
            t.add_row([NoEscape(r"Spannungsverhältnis  $$\psi $$"), f"{self.psi:.2f}", "-"])

            t.add_hline(start=None, end=None)
            # t.add_row(1, 2, escape=False, strict=True, mapper=[bold])

            # # MultiColumn/MultiRow.
            # t.add_row((MultiColumn(size=2, align='|c|', data='MultiColumn'),),
            #         strict=True)

            # # One multiRow-cell in that table would not be proper LaTeX,
            # # so strict is set to False

            # t.add_row((MultiRow(size=2, width='*', data='MultiRow'),), strict=False)

            # append tabular to table
            table.append(t)

            table = self.doc.append(table)

        Section_Entry_Parameters()

        self.doc.create(Subsection("Abminderungsfaktoren für die Streckgrenze"))

        def Abschnitt_Beulwerte():
            self.doc.append(NoEscape(f"Die Beulwerte werden zunächst in Abhängigkeit des Seitenverhältnisses {{\alpha}} bestimmt. "))
            self.doc.append(NoEscape(f"Für Seitenverhältnisse <= 1  sind die Beulwerte (rechnerisch) unabhängig vom Seitenverhältnis."))

                                
            if (self.alpha < 1.0):
                self.doc.append(Math(data=[NoEscape(f"k_{{\sigma}} = ({self.alpha:.2f} + 1/{self.alpha:.2f} ){{^2}} {{\cdot}} 2.1/({self.psi:.2f} +1.1) = {self.k_sigma:.2f}")])) 
            elif (self.alpha > 1.0):
                if (self.psi == -1):
                    self.doc.append(Math(data=[23.9]))
                elif(self.psi <0 and self.psi > -1):
                    self.res_biegung_normal = 7.81 - 6.29 * self.psi + 9.78 * self.psi**2
                    self.doc.append(Math(data=[NoEscape(f"k_{{\sigma}} = 7.81 - 6.29 {{\cdot \psi}} + 9.78 {{\cdot \psi^2 }} = {self.res_biegung_normal}")]))

        Abschnitt_Beulwerte()







        self.doc.generate_pdf(clean_tex=False)




        

# a = Beulnachweise_Platten()
# a.Nachweisfuehrung()
# a.Ausgabe_Pdf_Latex(10)

        

    
