from KIB_LAP.Betonbau import BeamRectangular
from KIB_LAP.Betonbau import BeamSubSection

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import pandas as pd
import time
import os


Beam = BeamRectangular(1,1.00,0.60)

moment_ed = 0.20
normal_force_ed = 0.20
shear_force_ed  = 0.30
effective_height = 0.65
effective_height_pressure = 0.08
elasticity_modulus_steel = 200000 

BeamSection = BeamSubSection(moment_ed, normal_force_ed,shear_force_ed, effective_height,effective_height_pressure, elasticity_modulus_steel)


Beam.calculate_beam_section_without_shearreinforcement(BeamSection,30*0.01**2,35,500)


print(Beam.v_rdcs * 1000)
print(Beam.v_rdcmin * 1000)