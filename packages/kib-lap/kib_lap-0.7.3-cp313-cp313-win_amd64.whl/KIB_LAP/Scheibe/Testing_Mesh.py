from Meshing import *
_num_x = 10
_num_y = 10


A = MeshingClass(d1=10, d2=10, num_x=_num_x, num_y=_num_y, elem_type="rect"); A.generating_rectangular_mesh()

B = MeshingClass(d1=10, d2=10, num_x=_num_x, num_y=_num_y, elem_type="rect"); B.generating_rectangular_mesh()
B.NL[:,1] += A.NL[:,1].max()  # rechts an A

C = MeshingClass(d1=10, d2=10, num_x=_num_x, num_y=_num_y, elem_type="rect"); C.generating_rectangular_mesh()
C.NL[:,1] += A.NL[:,1].max()  # oben auf A
C.NL[:,0] += B.NL[:,0].max()

A.merge_with_mesh(B)
A.merge_with_mesh(C)

BottomNodes = A.get_bottom_border_nodes()
print(BottomNodes)

A.plot_mesh()




