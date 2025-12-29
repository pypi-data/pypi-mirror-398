from beam_sub_section import *
from beam_rectangular import *


moment_ed = 1.00
normal_force_ed = 0
shear_force_ed = 0.5
effective_height = 0.55
effective_height_pressure = 0.05
elasticity_modulus_steel = 200000

Section_1 = BeamSubSection( moment_ed, 
normal_force_ed, 
shear_force_ed, 
effective_height, 
effective_height_pressure, 
elasticity_modulus_steel)

BEAM = BeamRectangular(1,1.00,0.60)
BEAM.calculate_beam_section(Section_1 , 30, 500, 0.296)
BEAM.calculate_beam_section_without_shearreinforcement(Section_1 , 16.3e-4,30,500)