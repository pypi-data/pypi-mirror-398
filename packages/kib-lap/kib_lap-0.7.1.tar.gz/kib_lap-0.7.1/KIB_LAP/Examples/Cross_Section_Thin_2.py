from KIB_LAP.Querschnittswerte import CrossSectionThin
import pandas as pd

# Lade die hochgeladenen CSV-Dateien
node_file_path = 'Querschnittswerte/Knoten.csv'
element_file_path = 'Querschnittswerte/Elemente.csv'

# Dateien einlesen
node_data = pd.read_csv(node_file_path)
element_data = pd.read_csv(element_file_path)

CS = CrossSectionThin(210000,0.30,node_param=node_data, element_param=element_data, Speichername = "Calculation_2")

CS.Calculation_Start()
