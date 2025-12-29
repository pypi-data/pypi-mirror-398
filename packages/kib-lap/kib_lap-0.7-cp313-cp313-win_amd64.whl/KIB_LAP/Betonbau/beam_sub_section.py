class BeamSubSection:

    def __init__(self, moment_ed, normal_force_ed, shear_force_ed, effective_height, effective_height_pressure, elasticity_modulus_steel):
        self.moment_ed = moment_ed
        self.normal_force_ed = normal_force_ed
        self.shear_force_ed = shear_force_ed
        self.effective_height = effective_height
        self.effective_height_pressure = effective_height_pressure
        self.elasticity_modulus_steel = elasticity_modulus_steel
