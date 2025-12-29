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
        self.RestraintData()
        self.NodalForces()
        self.TemperatureLoads()
        self.ElementLoads()
        self.MaterialData()
        self.CrossSectionData()

    def MaterialData(self):
        try:
            df = pd.read_csv("data/Material.csv")
        except:
            df = pd.DataFrame([0])

        self.Material = df

    def CrossSectionData(self):
        try:
            df = pd.read_csv("data/CrossSection.csv")
        except:
            df = pd.DataFrame([0])

        self.CrossSection = df

    def NodalData(self):
        if glob("data/Vertices.csv"):
            # Annahme: Die erste Zeile enthält Header
            df = pd.read_csv("data/Vertices.csv")

            # Wähle nur die numerischen Spalten aus (z.B. 'Node' und 'P[N]')
            numeric_columns = ['x[m]', 'y[m]','z[m]']
            df_numeric = df[numeric_columns]

            self.nodes = df_numeric
            self.nDoF = (len(self.nodes))*7
            print("1. 🟢 Vertices.csv imported")
        else:
            self.forceLocationData = []
            print("1. ⚠️ Vertices.csv not found")

    def EdgeData(self):
        # MANDATORY IMPORT: member definitions
        if glob("data/Edges.csv"):
            df = pd.read_csv("data/Edges.csv")
            numeric_columns = ['na', 'ne',"cs"]
            df_numeric = df[numeric_columns]
            self.members = df_numeric
            
            print("2. 🟢 Edges.csv imported")
        else:
            print("2. 🛑 STOP: Edges.csv not found")

    def RestraintData(self):
        df = pd.read_csv("data/Restraint_Data.csv")
        # Wähle nur die numerischen Spalten aus (z.B. 'Node' und 'P[N]')
        numeric_columns = ['Node', 'Dof','Cp[MN/m]/[MNm/m]']
        df_numeric = df[numeric_columns]
        self.RestraintData = df_numeric

    def NodalForces(self):
        df = pd.read_csv("data/NodalForces.csv")
        self.NodalForces = df

    def ElementLoads(self):
        try:
            df = pd.read_csv("data/Linienlasten.csv")
        except:
            df = pd.DataFrame([0])

        self.ElementLoads = df

    def TemperatureLoads(self):
        try:
            df = pd.read_csv("data/TemperatureLoading.csv")
        except:
            df = pd.DataFrame([0])
        self.TemperatureForces = df
