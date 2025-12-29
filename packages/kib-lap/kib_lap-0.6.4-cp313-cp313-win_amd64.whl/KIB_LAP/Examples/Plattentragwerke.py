# Beispielhafte Nutzung der Klasse
from KIB_LAP.Plattentragwerke import PlateBendingKirchhoffClass
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import pandas as pd
import time
import os

if __name__ == "__main__":
    a = 14
    b = 4.5

    Plate = PlateBendingKirchhoffClass(
        E=35000,
        t=0.35,
        a=a,
        b=b,
        p0=1,
        x0=0.5,
        u=0.5,
        y0=0.5,
        v=0.5,
        nu=0.0,
        n_inte=30,
        loading="Regular",
        support="hhhh",
        reihen=20
    )

    start_time = time.time()
    Plate.CalculateAll()
    end_time = time.time()
    duration = end_time - start_time

    print("Berechnungszeit:", duration, "Sekunden")

    Plate.PlotLoad()
    Plate.PlotMomentGrid()