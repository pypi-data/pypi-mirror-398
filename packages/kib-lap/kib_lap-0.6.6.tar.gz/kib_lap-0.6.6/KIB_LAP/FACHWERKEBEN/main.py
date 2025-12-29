from Iteration import IterationClass
from Plotting import PlottingStructure


Iteration = IterationClass()
try:
    Iteration.Summarize()
except:
    Iteration.SummarizeLinear()

plotter = PlottingStructure(
    Iteration.UG_FINAL,
    Iteration.FI_FINAL,
    Iteration.EXTFORCES,
    Iteration.MBRFORCES,
    Iteration.Inp.nodes,
    Iteration.Inp.members,
    Iteration.Mat.P0,
    Iteration.Inp.restrainedIndex,
    _reactionsFlag=True,
)

plotter.Kspring_diag = Iteration.Kspring_diag  # (nDoF,)
# optional (noch besser, damit nur echte Federn geplottet werden)
# plotter.spring_dofs = Iteration.spring_dofs

plotter.create_structure_plot()
