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

from InputData import Input
from Materials import Material
from Elements import Rope_Elements_III
from Elements import BarElements_I

class IterationClass:
    def __init__(self, use_iteration=False):
        print("INIT")
        ##________ Subclasses __________##
        self.Inp = Input()
        self.Mat = Material()
        self.CableNonlinear = Rope_Elements_III(self.Inp)
        self.BarLinear = BarElements_I(self.Inp)


        self.swt = False

        ##___ Iteration parameters _________##

        self.nForceIncrements = 10
        self.convThreshold = 1  # (N) Threshold on average percentage increase in incremental deflection

        self.checkSlackAfter = 80

        # Member Types

        self.memberType = []
        self.ClassifyMemberType()

        ##____ Containers_____##
        # Initialise a container to hold the set of global displacements for each external load increment
        self.UG_FINAL = np.empty([self.Inp.nDoF, 0])

        # Initialise a container to hold the set of internal forces for each external load increment
        self.FI_FINAL = np.empty([self.Inp.nDoF, 0])

        # Initialise a container to hold the set of axial forces for each external load increment
        self.EXTFORCES = np.empty([self.Inp.nDoF, 0])

        # Initialise a container to hold the set of axial forces for each external load increment
        self.MBRFORCES = np.empty([len(self.Inp.members), 0])

        # Initialise global disp vector
        self.UG = np.zeros(
            [self.Inp.nDoF, 1]
        )  # Initialise global displacement vector to zero (undeformed state)

        # Calculate initial transformation matrices for all members based on undeformed position
        self.TMs = self.calculateTransMatrices(self.UG)

        # Init point loads to global force vector

        self.AddPointLoadsGlobal()


        # Calculate initial lengths

        self.calculateInitialLengths()
        self.SelfweigthLoadVector()

        # Calculate internal force system based on any pre-tension in members
        self.F_pre = self.initPretension()

        # Initialise a container to store incremental displacements calculated for each iteration [Xa], [Xb] etc.
        self.UG_inc = np.empty([self.Inp.nDoF, 0])
        self.UG_inc = np.append(
            self.UG_inc, self.UG, axis=1
        )  # Add the initial (zero) displacement record

        # Initialise a container to store incremental internal forces calculated for each iteration [Fa], [Fb] etc.
        self.F_inc = np.empty([self.Inp.nDoF, 0])
        print(self.F_inc)
        print(self.F_pre)
        self.F_inc = np.append(
            self.F_inc, self.F_pre, axis=1
        )  # Add the initial pre-tension force record

        if use_iteration:
            self.MainConvergenceLoop()
        else:
            self.SolveLinear_NoIteration(treat_cables_as_bars=True)

    def ClassifyMemberType(self):
        print("Classify Member type")
        for n,m in enumerate(self.Inp.members):   
            #Initially assume all members are bars 
            self.memberType.append('b')

                
            #Check if member is a cable
            for c in self.Inp.cables:         
                if(m[0] in c and m[1] in c):
                    self.memberType[n] = 'c' 

    def AddPointLoadsGlobal(self):
        self.forceVector = np.zeros((len(self.Inp.nodes) * 2, 1))

        if len(self.Inp.forceLocationData) > 0:
            # Split force location data
            try:
                forcedNodes = self.Inp.forceLocationData[:, 0].astype(
                    int
                )  # Ensure these are integers)
                xForceIndizes = 2 * forcedNodes - 2
                yForceIndizes = 2 * forcedNodes - 1

                ForceP = self.Inp.forceLocationData[:, 1].reshape(-1, 1)
                print("FORCE P")
                print(ForceP)

                # Assign forces to degrees of freedom
                for i in range(0,len(ForceP),1):

                    if self.Inp.forceDirections[i]  == "x":
                        self.forceVector[xForceIndizes[i]] = ForceP[i]
                    elif self.Inp.forceDirections[i] == "y":
                        self.forceVector[yForceIndizes[i]] = ForceP[i]
            except:
                pass

    def calculateInitialLengths(self):
        self.lengths = np.zeros(len(self.Inp.members))
        for n, mbr in enumerate(self.Inp.members):

            # Calculate undeformed length of member
            node_i = mbr[0]  # Node number for node i of this member
            node_j = mbr[1]  # Node number for node j of this member
            ix = self.Inp.nodes[node_i - 1][0]  # x-coord for node i
            iy = self.Inp.nodes[node_i - 1][1]  # y-coord for node i
            jx = self.Inp.nodes[node_j - 1][0]  # x-coord for node j
            jy = self.Inp.nodes[node_j - 1][1]  # y-coord for node j

            dx = jx - ix  # x-component of vector along member
            dy = jy - iy  # y-component of vector along member
            length = math.sqrt(dx**2 + dy**2)  # Magnitude of vector (length of member)
            if (length == 0):
                print("Length = 0 at index ",  n )
            self.lengths[n] = length

    def initPretension(self):
        """
        P = axial pre-tension specified for each bar
        Calculate the force vector [F_pre] for each bar [F_pre] = [T'][AA'][P]
        Combine into an overal vector representing the internal force system and return
        """
        self.F_pre = np.array(
            [np.zeros(len(self.forceVector))]
        ).T  # Initialse internal force vector

        for n, mbr in enumerate(self.Inp.members):
            node_i = mbr[0]  # Node number for node i of this member
            node_j = mbr[1]  # Node number for node j of this member

            # Index of DoF for this member
            ia = 2 * node_i - 2  # horizontal DoF at node i of this member
            ib = 2 * node_i - 1  # vertical DoF at node i of this member
            ja = 2 * node_j - 2  # horizontal DoF at node j of this member
            jb = 2 * node_j - 1  # vertical DoF at node j of this member

            # Determine internal pre-tension in global coords
            TM = self.TMs[n, :, :]
            AAp = np.array([[1], [0]])
            P = self.Mat.P0[n]
            F_pre_global = np.matmul(TM.T, AAp) * P

            # Add member pre-tension to overall record
            self.F_pre[ia, 0] = self.F_pre[ia, 0] + F_pre_global[0][0]
            self.F_pre[ib, 0] = self.F_pre[ib, 0] + F_pre_global[1][0]
            self.F_pre[ja, 0] = self.F_pre[ja, 0] + F_pre_global[2][0]
            self.F_pre[jb, 0] = self.F_pre[jb, 0] + F_pre_global[3][0]

        return self.F_pre

    def calculateTransMatrices(self, UG):
        """
        Optimized:
        - Bars ('b'): transformation is constant (undeformed geometry) -> keep initial TM
        - Cables ('c'): update TM each iteration based on deformed geometry

        Returns array shape (nMembers, 2, 4)
        """

        nM = len(self.Inp.members)

        # -------------------------------------------------------
        # Create constant (initial) TMs once (for bars AND cables)
        # -------------------------------------------------------
        if not hasattr(self, "TMs_const") or self.TMs_const is None:
            self.TMs_const = np.zeros((nM, 2, 4), dtype=float)

            for n, mbr in enumerate(self.Inp.members):
                node_i = int(mbr[0])
                node_j = int(mbr[1])

                ix = float(self.Inp.nodes[node_i - 1, 0])
                iy = float(self.Inp.nodes[node_i - 1, 1])
                jx = float(self.Inp.nodes[node_j - 1, 0])
                jy = float(self.Inp.nodes[node_j - 1, 1])

                TM0 = self.CableNonlinear.calculateTransMatrix([ix, iy], [jx, jy])
                self.TMs_const[n, :, :] = TM0

        # start from constant TMs
        TMs = self.TMs_const.copy()

        # -------------------------------------------------------
        # Update ONLY cables
        # -------------------------------------------------------
        for n, mbr in enumerate(self.Inp.members):
            if self.memberType[n] != "c":
                continue  # bars: keep constant TM

            node_i = int(mbr[0])
            node_j = int(mbr[1])

            ia = 2 * node_i - 2
            ib = 2 * node_i - 1
            ja = 2 * node_j - 2
            jb = 2 * node_j - 1

            # deformed positions = initial + cumulative displacements
            ix = float(self.Inp.nodes[node_i - 1, 0]) + float(UG[ia, 0])
            iy = float(self.Inp.nodes[node_i - 1, 1]) + float(UG[ib, 0])
            jx = float(self.Inp.nodes[node_j - 1, 0]) + float(UG[ja, 0])
            jy = float(self.Inp.nodes[node_j - 1, 1]) + float(UG[jb, 0])

            TM = self.CableNonlinear.calculateTransMatrix([ix, iy], [jx, jy])
            TMs[n, :, :] = TM

        return TMs

    def buildStructureStiffnessMatrix(self, UG,TMs):
        """
        Standard construction of Primary and Structure stiffness matrix
        Construction of non-linear element stiffness matrix handled in a child function
        """
        Kp = np.zeros(
            [self.Inp.nDoF, self.Inp.nDoF]
        )  # Initialise the primary stiffness matrix

        # store spring stiffness diagonal (for equilibrium check)
        self.Kspring_diag = np.zeros(self.Inp.nDoF, dtype=float)


        for n, mbr in enumerate(self.Inp.members):
            node_i = mbr[0]  # Node number for node i of this member
            node_j = mbr[1]  # Node number for node j of this member

            # Construct (potentially) non-linear element stiffness matrix

            # [K11, K12, K21, K22] = self.CableNonlinear.buildElementStiffnessMatrix(
            #     n, UG, TMs, self.lengths, self.Mat.P0, self.Mat.E, self.Mat.A
            # )

            if self.memberType[n] == 'c':
                # cable / nonlinear
                [K11, K12, K21, K22] = self.CableNonlinear.buildElementStiffnessMatrix(
                    n, UG, TMs, self.lengths, self.Mat.P0, self.Mat.E, self.Mat.A
                )
            else:
                # bar / linear (Theorie I. Ordnung)
                [K11, K12, K21, K22] = self.BarLinear.buildElementStiffnessMatrix(
                    n, UG, None, None, self.Mat.P0, self.Mat.E, self.Mat.A
                )


            # Primary stiffness matrix indices associated with each node
            # i.e. node 1 occupies indices 0 and 1 (accessed in Python with [0:2])
            ia = 2 * node_i - 2  # index 0
            ib = 2 * node_i - 1  # index 1
            ja = 2 * node_j - 2  # index 2
            jb = 2 * node_j - 1  # index 3
            
            Kp[ia : ib + 1, ia : ib + 1] = Kp[ia : ib + 1, ia : ib + 1] + K11
            Kp[ia : ib + 1, ja : jb + 1] = Kp[ia : ib + 1, ja : jb + 1] + K12
            Kp[ja : jb + 1, ia : ib + 1] = Kp[ja : jb + 1, ia : ib + 1] + K21
            Kp[ja : jb + 1, ja : jb + 1] = Kp[ja : jb + 1, ja : jb + 1] + K22

        # Add springs

        if len(self.Inp.springLocationData) > 0:
            # Split force location data
            try:
                forcedNodes = self.Inp.springLocationData[:, 1].astype(
                    int
                )  # Ensure these are integers)
                xSpringIndizes = 2 * forcedNodes - 2
                ySpringIndizes = 2 * forcedNodes -1

                # print("Indizes")
                # print(xSpringIndizes)
                # print(ySpringIndizes)

                SpringC = self.Inp.springLocationData[:, 2].reshape(-1, 1)


                # Assign forces to degrees of freedom
                for i in range(0,len(SpringC),1):

                    if self.Inp.SpringDirections[i]  == "x":
                        Kp[xSpringIndizes[i]][xSpringIndizes[i]] += SpringC[i]
                        self.Kspring_diag[xSpringIndizes[i]] += SpringC[i]
                    elif self.Inp.SpringDirections[i] == "y":
                        Kp[ySpringIndizes[i]][ySpringIndizes[i]] += SpringC[i]
                        self.Kspring_diag[ySpringIndizes[i]] += SpringC[i]
            except:
                pass

        # Reduce to structure stiffness matrix by deleting rows and columns for restrained DoF
        if (len(self.Inp.restrainedIndex)>0):
            # print("RESTRAINED INDEX")
            # print(self.Inp.restrainedIndex)
            Ks = np.delete(Kp, self.Inp.restrainedIndex, 0)  # Delete rows
            Ks = np.delete(Ks, self.Inp.restrainedIndex, 1)  # Delete columns
        else:
            Ks = Kp
        

        Ks = np.matrix(
            Ks
        )  # Convert Ks from numpy.ndarray to numpy.matrix to use build in inverter function

       


        return Ks

    def solveDisplacements(self, Ks, F_inequilibrium):
        """
        Standard solving for structural displacements
        """

        forceVectorRed = copy.copy(
            F_inequilibrium
        )  # Make a copy of forceVector so the copy can be edited, leaving the original unchanged
        if (len(self.Inp.restrainedIndex)>0):
            forceVectorRed = np.delete(
                forceVectorRed, self.Inp.restrainedIndex, 0
            )  # Delete rows corresponding to restrained DoF
        else:
            forceVectorRed =  forceVectorRed

        #U = Ks.I * forceVectorRed
        U = np.linalg.solve(Ks, forceVectorRed)


        # Build the global displacement vector inclusing zeros as restrained degrees of freedom
        UG = np.zeros(
            self.Inp.nDoF
        )  # Initialise an array to hold the global displacement vector
        c = 0  # Initialise a counter to track how many restraints have been imposed
        for i in np.arange(self.Inp.nDoF):
            if i in self.Inp.restrainedIndex:
                # Impose zero displacement
                UG[i] = 0
            else:
                # Assign actual displacement
                UG[i] = U[c]
                c = c + 1

        UG = np.array([UG]).T

        return UG

    def SelfweigthLoadVector(self):

        if(self.swt):
            self.SW_at_supports = np.empty((0,2))
            for n, mbr in enumerate(self.Inp.members):  
                node_i = mbr[0] #Node number for node i of this member
                node_j = mbr[1] #Node number for node j of this member
                length = self.lengths[n]     
                sw = length*self.Mat.gamma[n] #(N) Self-weight of the member
                F_node = sw/2   #(N) Self-weight distributed into each node  
                # print("FNODE")
                # print(F_node)
                iy = 2*node_i-1 #index of y-DoF for node i
                jy = 2*node_j-1 #index of y-DoF for node j         
                self.forceVector[iy] = self.forceVector[iy] -F_node
                self.forceVector[jy] = self.forceVector[jy]  -F_node  
                
                #Check if SW needs to be directly added to supports (if elements connect to supports)
                if(iy+1 in self.Inp.restrainedDoF):
                    supportSW = np.array([iy, F_node])
                    self.SW_at_supports = np.append(self.SW_at_supports, [supportSW], axis=0) #Store y-DoF at support and force to be added
                if(jy+1 in self.Inp.restrainedDoF):
                    supportSW = np.array([jy, F_node])
                    self.SW_at_supports = np.append(self.SW_at_supports, [supportSW], axis=0) #Store y-DoF at support and force to be added                    
            print(self.forceVector)
            print(len(self.forceVector))
        else:
            pass

    def updateInternalForceSystem(self, UG):
        """
        Build internal force vector F_int (global DoF order) for the CURRENT increment UG.

        - Cable elements ('c'): nonlinear (deformed geometry, AA-matrix, etc.) -> uses self.TMs[n]
        - Bar elements   ('b'): linear Theorie I. Ordnung -> uses constant direction cosines from BarLinear

        IMPORTANT:
        - Pretension P0 is already handled separately via self.F_pre / self.F_inc initial column.
        Therefore for BAR internal force increment we DO NOT add P0 again here (avoid double count).
        """

        F_int = np.zeros((self.Inp.nDoF, 1), dtype=float)

        for n, mbr in enumerate(self.Inp.members):
            node_i, node_j = int(mbr[0]), int(mbr[1])

            # global DoF indices for this member
            ia = 2 * node_i - 2
            ib = 2 * node_i - 1
            ja = 2 * node_j - 2
            jb = 2 * node_j - 1

            # -------------------------
            # CABLE (nonlinear)
            # -------------------------
            if self.memberType[n] == "c":
                # incremental displacements (global)
                d_ix = float(UG[ia, 0])
                d_iy = float(UG[ib, 0])
                d_jx = float(UG[ja, 0])
                d_jy = float(UG[jb, 0])

                # current transformation (computed for cumulative shape, stored in self.TMs)
                TM = self.TMs[n, :, :]  # shape (2,4)

                # local incremental displacements
                localDisp = TM @ np.array([[d_ix], [d_iy], [d_jx], [d_jy]], dtype=float)
                u = float(localDisp[0, 0])
                v = float(localDisp[1, 0])

                # extension from nonlinear geometry
                Lo = float(self.lengths[n])
                e = math.sqrt((Lo + u) ** 2 + v**2) - Lo

                # AA matrix
                denom = (Lo + e)
                if abs(denom) < 1e-14:
                    # numerical guard (should not really happen)
                    continue

                a1 = (Lo + u) / denom
                a2 = v / denom
                AA = np.array([[a1, a2]], dtype=float)  # (1,2)

                # axial load increment (no P0 here; P0 was handled via initPretension)
                P = (float(self.Mat.E[n]) * float(self.Mat.A[n]) / Lo) * e

                # back to global nodal forces (4x1)
                F_global = (TM.T @ AA.T) * P  # (4,1)

                F_int[ia, 0] += float(F_global[0, 0])
                F_int[ib, 0] += float(F_global[1, 0])
                F_int[ja, 0] += float(F_global[2, 0])
                F_int[jb, 0] += float(F_global[3, 0])

            # -------------------------
            # BAR (linear, Theorie I. Ordnung)
            # -------------------------
            else:
                # element axial force increment from linear truss theory:
                # N = (EA/L) * [-c -s c s] * u_e
                f_e = self.BarLinear.internal_nodal_forces_global(
                    n,
                    UG,
                    self.Mat.E,
                    self.Mat.A,
                    P0=None,  # do NOT add P0 here (already in self.F_pre)
                )  # shape (4,1)

                F_int[ia, 0] += float(f_e[0, 0])
                F_int[ib, 0] += float(f_e[1, 0])
                F_int[ja, 0] += float(f_e[2, 0])
                F_int[jb, 0] += float(f_e[3, 0])

        return F_int

    def testForConvergence(self, it, threshold, F_ineq):
        """
        Test if structure has converged by comparing the maximum force in the equilibrium
        force vector against a threshold for the simulation.
        """
        notConverged = True  # Initialise the convergence flag
        maxIneq = 0
        if it > 0:
            maxIneq = np.max(abs(F_ineq[self.Inp.freeDoF]))
            
            if maxIneq < threshold:
                notConverged = False

        return notConverged, maxIneq

    def calculateMbrForces(self, UG):
        """
        Calculates the member forces based on change in length of each member
        Takes in the cumulative global displacement vector as UG
        """

        mbrForces = np.zeros(
            len(self.Inp.members)
        )  # Initialise a container to hold axial forces

        for n, mbr in enumerate(self.Inp.members):
            node_i = mbr[0]  # Node number for node i of this member
            node_j = mbr[1]  # Node number for node j of this member

            # Index of DoF for this member
            ia = 2 * node_i - 2  # horizontal DoF at node i of this member
            ib = 2 * node_i - 1  # vertical DoF at node i of this member
            ja = 2 * node_j - 2  # horizontal DoF at node j of this member
            jb = 2 * node_j - 1  # vertical DoF at node j of this member

            # New positions = initial pos + cum deflection
            ix = self.Inp.nodes[node_i - 1, 0] + UG[ia, 0]
            iy = self.Inp.nodes[node_i - 1, 1] + UG[ib, 0]
            jx = self.Inp.nodes[node_j - 1, 0] + UG[ja, 0]
            jy = self.Inp.nodes[node_j - 1, 1] + UG[jb, 0]

            dx = jx - ix  # x-component of vector along member
            dy = jy - iy  # y-component of vector along member
            newLength = math.sqrt(
                dx**2 + dy**2
            )  # Magnitude of vector (length of member)

            deltaL = newLength - self.lengths[n]  # Change in length
            force = (
                self.Mat.P0[n]
                + deltaL * self.Mat.E[n] * self.Mat.A[n] / self.lengths[n]
            )  # Axial force due to change in length and any pre-tension
            mbrForces[n] = force  # Store member force

        return mbrForces

    def AdditionalSupportForce(self):
        self.reactionsFlag = False #Initialise a flag so we can plot a message re. reactions when necessary
        if(self.swt):
            if self.SW_at_supports.size>0:   
                self.reactionsFlag = True
                for SW in self.SW_at_supports:        
                    index = int(SW[0]) #Index of the global force vector 'FG' to update        
                    self.FI_FINAL[index,:] = self.FI_FINAL[index,:] + SW[1] #Add nodal SW force directly to FG 

    def MainConvergenceLoop(self):
        i = 0  # Initialise an iteration counter (zeros out for each load increment)
        inc = 0  # Initialise load increment counter
        notConverged = True  # Initialise convergence flag

        # Init kspring-diagonal for the first iteration
        # It's overwriten in the generation of the stiffness matrix 
        # in each loop. Here just for the first run, where the stiffness matrix isn't initialized
        self.Kspring_diag = np.zeros(self.Inp.nDoF, dtype=float)

    
        self.forceIncrement = (
            self.forceVector / self.nForceIncrements
        )  # Determine the force increment for each convergence test
        self.maxForce = (
            self.forceVector
        )  # Define a vector to store the total external force applied
        self.forceVector = (
            self.forceIncrement
        )  # Initialise the forceVector to the first increment of load

        # print("Force vector")
        # print(self.forceVector)


        while notConverged and i < 10000:

            # Calculate the cumulative internal forces Fi_total = Fa + Fb + Fc + ...
            Fi_total = np.matrix(
                np.sum(self.F_inc, axis=1)
            ).T  # Sum across columns of F_inc

            # Calculate the cumulative incremental displacements UG_total = Xa + Xb + Xc + ...
            UG_total = np.matrix(
                np.sum(self.UG_inc, axis=1)
            ).T  # Sum across columns of UG_inc

            # Inequilibrium force vector used in this iteration F_EXT - Fi_total or externalForces - (cumulative) InternalForceSystem
            
            # add spring forces to internal force balance
            # (springs are in K, so their resisting forces must appear in equilibrium)
            F_spring = self.Kspring_diag.reshape(-1, 1) * np.asarray(UG_total, dtype=float)


            self.F_inequilibrium = self.forceVector - Fi_total - F_spring

            # Build the structure stiffness matrix based on current position (using cumulative displacements)
            Ks = self.buildStructureStiffnessMatrix(UG_total,self.TMs)

            # Solve for global (incremental) displacement vector [Xn] for this iteration
            self.UG = self.solveDisplacements(Ks, self.F_inequilibrium)

            # Calculate a new transformation matrix for each member based on cum disp up to previous iteration
            self.TMs = self.calculateTransMatrices(UG_total)

            # if i == 0:
            #     print(self.TMs)

            # Calculate the internal force system based on new incremental displacements, [Fn]
            F_int = self.updateInternalForceSystem(self.UG)

            # Save incremental displacements and internal forces for this iteration
            self.UG_inc = np.append(self.UG_inc, self.UG, axis=1)
            self.F_inc = np.append(self.F_inc, F_int, axis=1)

            # Test for convergence
            notConverged, maxIneq = self.testForConvergence(
                i, self.convThreshold, self.F_inequilibrium
            )

            i += 1

            # If system has converged, save converged displacements, forces and increment external loading
            if not notConverged:
                self.hasSlackElements = False #Initialise a flag to indicate presence of new slack elements
                mbrForces = self.calculateMbrForces(UG_total) #Calculate member forces based on current set of displacements
                
                #Test for compression in cable elements if designated number of converged increments reached

                if inc > self.checkSlackAfter:
                    for m, mbr in enumerate(self.Inp.members):            
                        if self.memberType[m] == 'c' and mbrForces[m]<0:
                            print(f'Compression in cable element from from nodes {mbr[0]} to {mbr[1]}')
                            self.hasSlackElements = True #Switch slack elements flag
                            self.Mat.A[m] = 0 #Eliminate member stiffness by seting its cross-sectional area to zero


                
                print(
                    f"System has converged for load increment {inc} after {i-1} iterations"
                )
                

                self.UG_FINAL = np.append(
                    self.UG_FINAL, UG_total, axis=1
                )  # Add the converged displacement record
                self.UG_inc = np.empty(
                    [self.Inp.nDoF, 0]
                )  # Zero out the record of incremental displacements for the next load increment
                self.UG_inc = np.array(
                    np.append(self.UG_inc, UG_total, axis=1)
                )  # Add the initial displacement record for next load increment (manually cast as ndarray instead of matrix)

                self.FI_FINAL = np.append(
                    self.FI_FINAL, Fi_total, axis=1
                )  # Add the converged force record
                self.F_inc = np.empty(
                    [self.Inp.nDoF, 0]
                )  # Zero out the record of incremental forces for the next load increment
                self.F_inc = np.array(
                    np.append(self.F_inc, Fi_total, axis=1)
                )  # Add the initial force record for next load increment (manually cast as ndarray instead of matrix)


                self.mbrForces = self.calculateMbrForces(
                    self.UG_FINAL[:, -1]
                )  # Calculate the member forces based on change in mbr length
                self.MBRFORCES = np.append(
                    self.MBRFORCES, np.matrix(self.mbrForces).T, axis=1
                )  # Add the converged axial forces record

                self.EXTFORCES = np.append(
                    self.EXTFORCES, self.forceVector, axis=1
                )  # Add the external force vector for this load increment

                # Test if all external loading has been applied
                if abs(sum(self.forceVector).item()) < abs(sum(self.maxForce).item()):
                    i = 0  # Reset counter for next load increment
                    inc += 1
                    self.forceVector = (
                        self.forceVector + self.forceIncrement
                    )  # Increment the applied load
                    notConverged = (
                        True  # Reset notConverged flag for next load increment
                    )

        self.AdditionalSupportForce()

    def SolveLinear_NoIteration(self, treat_cables_as_bars=True):
        """
        Linear solve (no iteration, no deformed geometry):
            K * u = F

        - Builds global stiffness matrix once from undeformed geometry.
        - Solves once for displacements.
        - Computes reactions and member forces.

        treat_cables_as_bars:
            True  -> use linear bar stiffness also for members typed 'c'
            False -> raise error if cables exist (strict linear truss only)
        """

        # ---------------------------------------------------------
        # 1) Build external load vector (global) once
        # ---------------------------------------------------------
        self.forceVector = np.zeros((len(self.Inp.nodes) * 2, 1), dtype=float)
        self.AddPointLoadsGlobal()
        self.calculateInitialLengths()
        self.SelfweigthLoadVector()   # only acts if self.swt=True

        F = self.forceVector.copy()   # global full vector (nDoF,1)

        # ---------------------------------------------------------
        # 2) Build global stiffness Kp (full) from undeformed geometry
        # ---------------------------------------------------------
        nDoF = self.Inp.nDoF
        Kp = np.zeros((nDoF, nDoF), dtype=float)

        # Springs: store diagonal like before
        self.Kspring_diag = np.zeros(nDoF, dtype=float)

        for n, mbr in enumerate(self.Inp.members):
            node_i, node_j = int(mbr[0]), int(mbr[1])

            if (self.memberType[n] == "c") and (not treat_cables_as_bars):
                raise ValueError(
                    f"Member {n+1} (nodes {node_i}-{node_j}) is a cable. "
                    "Set treat_cables_as_bars=True or remove cable members for strict linear solve."
                )

            # Use linear bar element stiffness (undeformed)
            K11, K12, K21, K22 = self.BarLinear.buildElementStiffnessMatrix(
                n, None, None, None, self.Mat.P0, self.Mat.E, self.Mat.A
            )

            ia = 2 * node_i - 2
            ib = 2 * node_i - 1
            ja = 2 * node_j - 2
            jb = 2 * node_j - 1

            Kp[ia:ib+1, ia:ib+1] += K11
            Kp[ia:ib+1, ja:jb+1] += K12
            Kp[ja:jb+1, ia:ib+1] += K21
            Kp[ja:jb+1, ja:jb+1] += K22

        # ---------------------------------------------------------
        # 3) Add springs (same logic as your iterative build)
        # ---------------------------------------------------------
        if len(self.Inp.springLocationData) > 0:
            try:
                forcedNodes = self.Inp.springLocationData[:, 1].astype(int)
                xIdx = 2 * forcedNodes - 2
                yIdx = 2 * forcedNodes - 1
                SpringC = self.Inp.springLocationData[:, 2].reshape(-1)

                for i in range(len(SpringC)):
                    c = float(SpringC[i])
                    if self.Inp.SpringDirections[i] == "x":
                        Kp[xIdx[i], xIdx[i]] += c
                        self.Kspring_diag[xIdx[i]] += c
                    elif self.Inp.SpringDirections[i] == "y":
                        Kp[yIdx[i], yIdx[i]] += c
                        self.Kspring_diag[yIdx[i]] += c
            except:
                pass

        # ---------------------------------------------------------
        # 4) Reduce and solve
        # ---------------------------------------------------------
        if len(self.Inp.restrainedIndex) > 0:
            free = np.array([i for i in range(nDoF) if i not in self.Inp.restrainedIndex], dtype=int)
        else:
            free = np.arange(nDoF, dtype=int)

        Kff = Kp[np.ix_(free, free)]
        Ff  = F[free, :]

        uf = np.linalg.solve(Kff, Ff)

        # build full displacement vector u (restrained are 0)
        u = np.zeros((nDoF, 1), dtype=float)
        u[free, 0] = uf[:, 0]

        # Save like your usual output containers (single step)
        self.UG_FINAL = u.copy()
        self.EXTFORCES = F.copy()

        # ---------------------------------------------------------
        # 5) Reactions (full)
        # ---------------------------------------------------------
        R = (Kp @ u) - F  # includes spring reactions etc.
        self.FI_FINAL = (Kp @ u)  # "internal nodal forces" equivalent
        self.Reactions = R

        # ---------------------------------------------------------
        # 6) Member forces (linear)
        #    include pretension if you want: P0 added in axial_force(..., P0=self.Mat.P0)
        # ---------------------------------------------------------
        mbrN = np.zeros((len(self.Inp.members), 1), dtype=float)
        for n in range(len(self.Inp.members)):
            # linear axial force (tension +)
            N = self.BarLinear.axial_force(n, u, self.Mat.E, self.Mat.A, P0=self.Mat.P0)
            mbrN[n, 0] = N

        self.MBRFORCES = mbrN.copy()

        return u, R, mbrN



    def Summarize(self):
        #Generate output statements
        print(f"OUTSTANDING FORCE IMBALANCE")
        for i in np.arange(0,self.Inp.nDoF):     
            if i not in self.Inp.restrainedIndex:
                print(f"Remaining force imbalance at DoF {i} is {round(self.F_inequilibrium[i,0]/1000,3)} kN")  

        maxInequality = round(max(abs(self.F_inequilibrium[self.Inp.freeDoF,0])).item()/1000,3)
        print(f"(max = {maxInequality} kN)")

        print("")
        print("REACTIONS")

        f_int = self.FI_FINAL[:,-1]
        for i in np.arange(0,len(self.Inp.restrainedIndex)):           
            index = self.Inp.restrainedIndex[i]
            print(f"Reaction at DoF {index+1}: {round(f_int[index].item()/1000,2)} kN")

        # last converged displacement vector
        u_last = np.asarray(self.UG_FINAL[:, -1], dtype=float).reshape(-1, 1)   # (nDoF,1)

        # spring stiffness (diagonal) as vector
        k = np.asarray(self.Kspring_diag, dtype=float).reshape(-1, 1)           # (nDoF,1)

        # elementwise spring forces
        f_springs = k * u_last                                                  # (nDoF,1)


        try:
            # Federkräfte (letzter Lastschritt)
            f = np.asarray(f_springs, dtype=float).flatten()

            springno = self.Inp.springLocationData[:, 0].astype(int)
            forcedNodes = self.Inp.springLocationData[:, 1].astype(int)
            dirs = np.asarray(self.Inp.SpringDirections)

            print("\nSPRING FORCES (per spring):")
            for no, node, d in zip(springno, forcedNodes, dirs):
                d = str(d).strip().lower().replace('"', '')

                if d == "x":
                    dof = 2 * node - 2
                elif d in ("y", "z"):
                    dof = 2 * node - 1
                else:
                    raise ValueError(f"Unknown spring direction: {d}")

                print(
                    f"Spring {no} | Node {node} | Dir {d} | "
                    f"DoF {dof} | Force = {f[dof]/1000:.2f} kN"
                )

        except Exception as e:
            print("No springs in the system")
            # optional:
            # print(e)

        print("")   
        print("MEMBER FORCES (incl. any pre-tension)")    
        for n, mbr in enumerate(self.Inp.members):    
            print(f"Force in member {n+1} (nodes {mbr[0]} to {mbr[1]}) is {round(self.mbrForces[n]/1000,2)} kN")

        print("")   
        print("NODAL DISPLACEMENTS") 
        ug = self.UG_FINAL[:,-1]
        for n, node in enumerate(self.Inp.nodes):    
            ix = 2*(n+1)-2 #horizontal DoF for this node
            iy = 2*(n+1)-1 #vertical DoF for this node
            
            ux = round(ug[ix,0],5) #Horizontal nodal displacement
            uy = round(ug[iy,0],5) #Vertical nodal displacement
            print(f"Node {n+1}: Ux = {ux} m, Uy = {uy} m")

    def SummarizeLinear(self):
        print("LINEAR SOLVE (NO ITERATION)")

        # -------------------------------------------------
        # REACTIONS
        # -------------------------------------------------
        print("\nREACTIONS (at restrained DoF):")
        for idx in self.Inp.restrainedIndex:
            print(f"DoF {idx+1}: R = {self.Reactions[idx,0]/1000:.2f} kN")

        # -------------------------------------------------
        # MEMBER FORCES
        # -------------------------------------------------
        print("\nMEMBER FORCES (incl. P0):")
        for n, mbr in enumerate(self.Inp.members):
            print(
                f"Member {n+1} (nodes {mbr[0]}-{mbr[1]}): "
                f"N = {self.MBRFORCES[n,0]/1000:.2f} kN"
            )

        # -------------------------------------------------
        # NODAL DISPLACEMENTS
        # -------------------------------------------------
        print("\nNODAL DISPLACEMENTS:")
        for n in range(len(self.Inp.nodes)):
            ix = 2 * (n + 1) - 2
            iy = 2 * (n + 1) - 1
            print(
                f"Node {n+1}: "
                f"Ux = {self.UG_FINAL[ix,0]:.6e} m, "
                f"Uy = {self.UG_FINAL[iy,0]:.6e} m"
            )

        # -------------------------------------------------
        # SPRING FORCES
        # -------------------------------------------------
        if len(self.Inp.springLocationData) == 0:
            print("\nNO SPRINGS IN SYSTEM")
            return

        print("\nSPRING FORCES:")

        # displacement vector
        u = self.UG_FINAL.reshape(-1, 1)

        # diagonal spring stiffness vector
        kdiag = self.Kspring_diag.reshape(-1, 1)

        # spring forces per DoF
        f_spring = kdiag * u

        try:
            spring_no  = self.Inp.springLocationData[:, 0].astype(int)
            nodes      = self.Inp.springLocationData[:, 1].astype(int)
            k_values   = self.Inp.springLocationData[:, 2].astype(float)
            directions = np.asarray(self.Inp.SpringDirections)

            for no, node, k_i, d in zip(spring_no, nodes, k_values, directions):
                d = str(d).strip().lower().replace('"', '')

                if d == "x":
                    dof = 2 * node - 2
                elif d == "y":
                    dof = 2 * node - 1
                else:
                    raise ValueError(f"Unknown spring direction: {d}")

                print(
                    f"Spring {no} | Node {node} | Dir {d} | "
                    f"k = {k_i:.3e} N/m | "
                    f"u = {u[dof,0]:.6e} m | "
                    f"F = {f_spring[dof,0]/1000:.2f} kN"
                )

        except Exception as e:
            print("Error while printing spring forces")
            # print(e)

