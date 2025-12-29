from KIB_LAP.Plattentragwerke import PlateBendingKirchhoffClass
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import pandas as pd
import time
import os


a = 10.5
b = 10

Plate = PlateBendingKirchhoffClass(
    35000, 0.35, a, b, 1, 0.5, 0.5, 0.5, 0.5, 0.0, 0, 0, n_inte=50, loading="Liste", support = "hhff",reihen = 8)


# Daten als Liste von Listen
new_data = [
    ["No.","x0[m]","x1[m]","y0[m]","y1[m]","p0[MN/m**2]"],
    [1,2-0.2,2+0.2,0.5,0.9,150/0.4**2/1000],
    [2,3.2-0.2,3.2+0.2,0.5,0.9,150/0.4**2/1000],
    [3,3.2-0.2,3.2+0.2,2.5,2.9,150/0.4**2/1000],
    [4,2-0.2,2+0.2,2.5,2.9,150/0.4**2/1000], 

    [6,2-0.2,2+0.2,3.5,3.9,100/0.4**2/1000],
    [7,3.2-0.2,3.2+0.2,3.5,3.9,100/0.4**2/1000],
    [8,3.2-0.2,3.2+0.2,5.5,5.9,100/0.4**2/1000],
    [9,2-0.2,2+0.2,5.5,5.9,100/0.4**2/1000],

    [10,2-0.2,2+0.2,6.5,6.9,100/0.4**2/1000],
    [11,3.2-0.2,3.2+0.2,6.5,6.9,100/0.4**2/1000],
    [12,3.2-0.2,3.2+0.2,8.5,8.9,100/0.4**2/1000],
    [13,2-0.2,2+0.2,8.5,8.9,100/0.4**2/1000]

]

# Konvertiere die Daten in ein DataFrame
df = pd.DataFrame(new_data[1:], columns=new_data[0])

# Dateipfad zur CSV-Datei
file_path = 'Loading/Constant_Loading.csv'

# Schreibe das DataFrame in eine CSV-Datei
df.to_csv(file_path, index=False)


Plate.CalculateAll()

Plate.SolutionPointDisp(0.5,0.5)
Plate.SolutionPointMomentx(0.5,0.5)
Plate.SolutionPointMomenty(0.5,0.5)


Plate.PlotLoad()
print("BENDING MOMENTS")
Plate.PlotMomentGrid()
print("SHEAR FORCES")
Plate.PlotShearForceGrid()
print("DRILL MOMENTS")
Plate.PlotTorsionalMomentGrid()