# DEPENDENCIES
import copy  # Allows us to create copies of objects in memory
import math  # Math functionality
import numpy as np  # Numpy for working with arrays
import matplotlib.pyplot as plt  # Plotting functionality
import matplotlib.colors  # For colormap functionality
import ipywidgets as widgets
from glob import glob  # Allows check that file exists before import
from numpy import genfromtxt  # For importing structure data from csv
import pandas as pd

class Input:
    def __init__(self):
        print("Input-Class")
        self.NodalData()
        self.EdgeData()
        self.CableData()
        self.RestraintData()
        self.SpringData()
        self.ForceData()


    # =================================START OF DATA IMPORT================================
    def NodalData(self):
        # MANDATORY IMPORT: nodal coordinates
        if glob("data/Vertices.csv"):
            self.nodes = genfromtxt("data/Vertices.csv", delimiter=",")
            print("1. 🟢 Vertices.csv imported")
        else:
            print("1. 🛑 STOP: Vertices.csv not found")

    def EdgeData(self):
        # MANDATORY IMPORT: member definitions
        if glob("data/Edges.csv"):
            self.members = genfromtxt("data/Edges.csv", delimiter=",")
            self.members = np.int_(self.members)
            self.nDoF = (
                np.amax(self.members) * 2
            )  # Total number of degrees of freedom in the problem
            print("2. 🟢 Edges.csv imported")
        else:
            print("2. 🛑 STOP: Edges.csv not found")

    def RestraintData(self):
        # Prüfen, ob die Datei existiert
        if glob("data/Restraint-Data.csv"):
            # CSV einlesen; da es sich um eine einzelne Spalte handelt, reicht der Standard
            self.restraintData = genfromtxt("data/Restraint-Data.csv")
            # Sicherstellen, dass die Daten mindestens ein 1D-Array sind
            self.restraintData = np.atleast_1d(self.restraintData)
            # In Integer umwandeln (falls als float gelesen)
            self.restraintData = np.int_(self.restraintData)
            # Daten flach machen (bei einer einzelnen Spalte ist das optional)
            flatData = self.restraintData.flatten()
            # 0-Werte entfernen (0 = kein Einspannen)
            self.restrainedDoF = flatData[flatData != 0].tolist()
            # Von den in der CSV angegebenen Freiheitsgraden (beginnend bei 1)
            # zu Python-Index (beginnend bei 0) konvertieren
            self.restrainedIndex = [x - 1 for x in self.restrainedDoF]
            # Unbeschränkte Freiheitsgrade berechnen
            self.freeDoF = np.delete(np.arange(0, self.nDoF), self.restrainedIndex)
            print("3. 🟢 Restraint-Data.csv imported")
        else:
            print("3. 🛑 STOP: Restraint-Data.csv not found")

    def SpringData(self):
        if glob("data/springs.csv"):
            # Annahme: Die erste Zeile enthält Header
            df = pd.read_csv("data/springs.csv")
            # Numerische Spalten
            numeric_columns = ['no','Node', 'c_const[N/m]']
            df_numeric = df[numeric_columns]
            # Konvertiere das DataFrame zu einem NumPy-Array vom Typ int
            self.springLocationData = df_numeric.to_numpy(dtype=int)
            # Save the spring directions
            self.SpringDirections = df['Dir'].to_numpy()
            print("4. 🟢 springs.csv imported")
        else:
            self.forceLocationData = []
            print("4. ⚠️ springs.csv not found")

    def ForceData(self):
        # OPTIONAL IMPORT: force location data
        if glob("data/Force-Data.csv"):
            # Annahme: Die erste Zeile enthält Header
            df = pd.read_csv("data/Force-Data.csv")
            
            # Wähle nur die numerischen Spalten aus (z.B. 'Node' und 'P[N]')
            numeric_columns = ['Node', 'P[N]']
            df_numeric = df[numeric_columns]
            
            # Konvertiere das DataFrame zu einem NumPy-Array vom Typ int
            self.forceLocationData = df_numeric.to_numpy(dtype=int)
            
            # Bestimme die Anzahl der Dimensionen des Arrays
            self.nForces = self.forceLocationData.ndim
            
            # Falls das Array weniger als 2-dimensional ist, füge eine zusätzliche Dimension hinzu
            if self.nForces < 2:
                self.forceLocationData = np.expand_dims(self.forceLocationData, axis=0)

            # (Optional) Verarbeite die 'Dir'-Spalte, falls benötigt
            # Beispiel: Speichere die Richtungen separat
            self.forceDirections = df['Dir'].to_numpy()
            
            print("4. 🟢 Force-Data.csv imported")
        else:
            self.forceLocationData = []
            print("4. ⚠️ Force-Data.csv not found")

    def CableData(self):
        #MANDATORY IMPORT: cable definitions
        if glob('data/Cables.csv'): 
            self.cables = genfromtxt('data/Cables.csv', delimiter=',') 
            print('3. 🟢 Cables.csv imported')
        else: 
            self.cables = []
            print('3. 🛑 STOP: Cables.csv not found')