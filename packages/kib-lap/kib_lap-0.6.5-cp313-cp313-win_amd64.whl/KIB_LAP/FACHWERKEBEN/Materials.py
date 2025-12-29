# DEPENDENCIES
import copy #Allows us to create copies of objects in memory
import math #Math functionality
import numpy as np #Numpy for working with arrays
import matplotlib.pyplot as plt #Plotting functionality 
import matplotlib.colors #For colormap functionality
import ipywidgets as widgets
from glob import glob #Allows check that file exists before import
from numpy import genfromtxt #For importing structure data from csv
import pandas as pd

class Material:
    def __init__(self):
        print("Material Class")
        self.MaterialData()

    def MaterialData(self):
        #MANDATORY IMPORT: nodal coordinates
        if glob('data/Material.csv'): 
            self.Materials = pd.read_csv('data/Material.csv') 
            print('1. 🟢 Material.csv imported')
        else: 
            print('1. 🛑 STOP: Material.csv not found')

        print(self.Materials)
        self.N = self.Materials['No'].to_numpy()
        self.E = self.Materials['E'].to_numpy()
        self.A = self.Materials['A'].to_numpy()
        self.gamma = self.Materials['gamma'].to_numpy()
        self.P0 = self.Materials['P0'].to_numpy()
