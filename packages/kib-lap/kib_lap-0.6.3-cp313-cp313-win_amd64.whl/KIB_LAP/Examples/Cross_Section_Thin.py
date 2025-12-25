
import pandas as pd
import os
import sys
import numpy as np

# Absoluten Pfad des Projekts und des KIB-Ordners berechnen
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
kib_directory = os.path.join(project_root, "KIB_LAP")

# Debug-Ausgabe, um die Pfade zu überprüfen
print("Project Root:", project_root)
print("KIB Directory:", kib_directory)

# Füge das KIB-Verzeichnis zum sys.path hinzu, falls es nicht vorhanden ist
if kib_directory not in sys.path:
    sys.path.insert(0, kib_directory)

# Importieren des Moduls
try:
    from KIB_LAP.Querschnittswerte import CrossSectionThin 
    print("Import erfolgreich!")
except ModuleNotFoundError as e:
    print("Fehler beim Import:", e)


Node_Cords = pd.DataFrame({
    "Nr.": [1, 2, 3, 4, 5, 6],
    "y": [-0.35, 0, 0.35, 0, -0.30, 0.30],
    "z": [0, 0, 0, 0.400, 0.400, 0.400]
})


CrossSectionElements = pd.DataFrame({
    "nr": [1, 2, 3, 4, 5],
    "npa": [1, 2, 2, 4, 4],
    "npe": [2, 3, 4, 5, 6],
    "t [m]": [0.02, 0.02, 0.01, 0.02, 0.02]
})

Class = CrossSectionThin(
    2.1e5,
    0.3,
    Node_Cords,
    CrossSectionElements,
    "Calculation"
)


Class.read_node_input()
Class.CalculateElementStiffness()
Class.Calculate_GesMat()
Class.SolverTorsion()
Class.CalculateAyzw()
Class.Update_SMP()
Class.Calculate_IwIt()
Class.Calculate_WoWu()
Class.Calculate_ShearStress_Vz()
Class.Calculate_imryrzrw()
Class.Export_Controll_Data()
Class.Export_Cross_Section_Data()