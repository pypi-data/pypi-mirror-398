# VASProcar Copyright (C) 2023
# GNU GPL-3.0 license

#######################################################
############## Analyzing the OUTCAR file ##############
########## Searching for System Information ###########
#######################################################

#----------------------------------------
outcar = open(dir_files + '/OUTCAR', "r")
#--------------------------------------------------------
inform = open(dir_files + '/output/informacoes.txt', "w")
#--------------------------------------------------------

inform.write(" \n")
inform.write("############################################################## \n")
inform.write(f'# {VASProcar_name} \n')
inform.write(f'# {url_1} \n')
inform.write(f'# {url_2} \n')
inform.write("############################################################## \n")
inform.write(" \n")

#----------------------------------------------------------------------
# Obtaining the number of k-points (nk), bands (nb) and ions (ni): ----
#----------------------------------------------------------------------

palavra = 'Dimension'                          # Dimension is a word present on a line before the lines containing information about the number of k-points (nk), bands (nb) and ions (ni).

for line in outcar:   
    if palavra in line: 
       break

VTemp = outcar.readline().split()
nk = int(VTemp[3])
nb = int(VTemp[14])

VTemp = outcar.readline().split()
ni = int(VTemp[11])

#-----------------------------------------------------------------------
# Check if the calculation was performed with or without SO coupling: --
#-----------------------------------------------------------------------

palavra = 'ICHARG'                             # ICHARG is a word present on a line before the line that contains information about the ISPIN variable.

for line in outcar:   
    if palavra in line: 
       break

VTemp = outcar.readline().split()
ispin = int(VTemp[2])                          # Reading the value associated with the ISPIN variable.

#------------
nb = nb*ispin
#------------
  
#-----------------------------------------------------------------------

VTemp = outcar.readline().split()
lnoncollinear = VTemp[2]                       # Reading the value associated with the LNONCOLLINEAR variable.

VTemp = outcar.readline().split()
lsorbit = VTemp[2]                             # Reading the value associated with the LSORBIT variable.

inform.write("---------------------------------------------------- \n")

if (lnoncollinear == "F"):
   LNC = 1
   inform.write("LNONCOLLINEAR = .FALSE. (Collinear Calculation) \n")
if (lnoncollinear == "T"):
   LNC = 2
   inform.write("LNONCOLLINEAR = .TRUE. (Non-collinear Calculation) \n")

if (lsorbit == "F"):
   SO = 1
   inform.write("LSORBIT = .FALSE. (Calculation without SO coupling) \n")
if (lsorbit == "T"):
   SO = 2
   inform.write("LSORBIT = .TRUE. (Calculation with SO coupling) \n")

#-----------------------------------------------------------------------
# Finding the number of electrons in the system: -----------------------
#---------------------------------------------------------------------- 
 
palavra = 'VCA'                                       # VCA is a word present on a line before the line containing information about the NELECT variable.

for line in outcar:   
    if palavra in line: 
       break

VTemp = outcar.readline().split()
n_eletrons = float(VTemp[2])                          # Reading the value associated with the NELECT variable.

inform.write("---------------------------------------------------- \n")

if (n_procar == 1):
   inform.write(f'nº k-points = {nk};  nº bands = {nb} \n')
if (n_procar > 1):
   inform.write(f'nº k-points = {nk*n_procar} (nº PROCAR files = {n_procar});  nº bands = {nb} \n')   

inform.write(f'nº ions = {ni};  nº electrons = {n_eletrons} \n')

#-----------------------------------------------------------------
# Obtaining the LORBIT used to generate the PROCAR file: ---------
#-----------------------------------------------------------------
 
palavra = 'LELF'                                    # LELF is a word present on a line before the line containing information about the LORBIT variable.

for line in outcar:   
    if palavra in line: 
       break

VTemp = outcar.readline().split()
lorbit = int(VTemp[2])                              # Reading the value associated with the LORBIT variable.

inform.write("--------------------------------------------------- \n")
inform.write(f'LORBIT = {lorbit};  ISPIN = {ispin} ')
if (ispin == 1): inform.write("(without spin polarization) \n")
if (ispin == 2): inform.write("(with spin polarization) \n")
inform.write("--------------------------------------------------- \n")

#-------------
outcar.close()
#-------------



#-----------------------------------------------------------------------
# searching for the fermi energy value in the CHGCAR file: -------------
#-----------------------------------------------------------------------
file_outcar = "OUTCAR"
if os.path.exists(dir_files + '/OUTCAR.scf'): file_outcar = "OUTCAR.scf"
#-----------------------------------------------------------------------
outcar = open(dir_files + '/' + file_outcar, "r")
Efermi = -1000.0
number = 0
#-------------------
palavra1 = 'E-fermi'
palavra2 = 'reached'
#------------------
for line in outcar:
    number += 1
    if (palavra1 or palavra2)  in line:
       Efermi_check = 1
       break
#-------------
outcar.close()
#------------------------------------------------
outcar = open(dir_files + '/' + file_outcar, "r")
#------------------------------------------------
for i in range(number):
    VTemp = outcar.readline()
VTemp = VTemp.split()
Efermi = float(VTemp[2])
#-----------------------
outcar.close()
#-------------



#-----------------------------------------------------------------------
# Finding the Fermi Energy of the System: ------------------------------
#-----------------------------------------------------------------------
outcar = open(dir_files + '/OUTCAR', "r") 
#----------------------------------------
palavra = 'average'                            # average is a word present on a line a little before the line that contains information about the E-fermi variable.
number = 0                                     # number represents which line contains information about the E-fermi variable.
#------------------
for line in outcar:
    number += 1    
    if palavra in line: 
       break
#------------------
palavra = 'E-fermi'
#------------------
for line in outcar:
    number += 1    
    if palavra in line: 
       break
#-------------
outcar.close()
#----------------------------------------
outcar = open(dir_files + '/OUTCAR', "r") 
#----------------------------------------
for i in range(number):
    VTemp = outcar.readline()
VTemp = VTemp.split()
# Efermi = float(VTemp[2])

#==========================================================================

if (ispin == 1):
    
   #-----------------------------------------------------------------------
   # Checking which bands correspond to the valence and conduction bands --
   # as well as the respective energy gap ---------------------------------
   # ----------------------------------------------------------------------
   # This check only makes sense for calculations performed in a single ---
   # step (n_procar = 1), since the analyzed OUTCAR file may or may not --- 
   # contain the lowest GAP region of the system --------------------------
   # ----------------------------------------------------------------------
   # This check also does not make sense for metallic system --------------
   #-----------------------------------------------------------------------

   VTemp = outcar.readline(); VTemp = outcar.readline().split()
   
   if ((len(VTemp) >= 3) and (VTemp[0] == 'Fermi')):
      if (Efermi == -1000.0): Efermi = float(VTemp[2])
      VTemp = outcar.readline()

   max_vbn = -100000.0
   min_cmb = +100000.0
   number = 0

   for i in range(nk):
       number += 1
       #------------------------
       VTemp = outcar.readline()
       VTemp = outcar.readline()
       #------------------------
       for j in range(nb):
           VTemp = outcar.readline().split()
           n1 = int(VTemp[0])
           n2 = float(VTemp[1])
           n3 = float(VTemp[2])
           if (n3 > 0.0):
              if (n2 > max_vbn):
                 max_vbn = n2
                 n1_valencia = n1
                 kp1 = number
           if (n3 == 0.0):
              if (n2 < min_cmb):
                 min_cmb = n2
                 n1_conducao = n1
                 kp2 = number

           if ((max_vbn <= Efermi) and (min_cmb >= Efermi)): GAP = (min_cmb - max_vbn)
           if ((max_vbn > Efermi) or (min_cmb < Efermi)): GAP = 0.0

       VTemp = outcar.readline() 

   if (n_procar == 1):
      inform.write(f'Last band occuped = {n1_valencia} \n')
      inform.write(f'First band empty = {n1_conducao} \n')
      #---------------------------------------------------
      inform.write(f'Conduction band minimum (CBM) = {min_cmb} eV  -  k-point {kp2} \n')
      inform.write(f'Valence band maximum (VBM)    = {max_vbn} eV  -  k-point {kp1} \n')
      #---------------------------------------------------------------
      if ((max_vbn <= Efermi) and (min_cmb >= Efermi)):
         if (kp1 == kp2): inform.write(f'GAP (direct) = {GAP:.4f} eV \n')
         if (kp1 != kp2): inform.write(f'GAP (indirect) = {GAP:.4f} eV \n')
      if ((max_vbn > Efermi) or (min_cmb < Efermi)):
         inform.write(f'GAP (No-Gap) = 0.0 eV \n')
      inform.write("---------------------------------------------------- \n")

#==========================================================================

if (ispin == 2):
   for nspin in range(1,(2+1)):
 
      #-----------------------------------------------------------------------
      # Checking which bands correspond to the valence and conduction bands --
      # as well as the respective energy gap ---------------------------------
      # ----------------------------------------------------------------------
      # This check only makes sense for calculations performed in a single ---
      # step (n_procar = 1), since the analyzed OUTCAR file may or may not --- 
      # contain the lowest GAP region of the system --------------------------
      # ----------------------------------------------------------------------
      # This check also does not make sense for metallic system --------------
      #-----------------------------------------------------------------------

      if (nspin == 1):
         VTemp = outcar.readline()
         VTemp = outcar.readline().split()
         if ((len(VTemp) >= 3) and (VTemp[0] == 'Fermi') and (Efermi == -1000.0)): Efermi = float(VTemp[2])
         VTemp = outcar.readline()
         VTemp = outcar.readline()
         VTemp = outcar.readline()
         #------------------------------------------------------------------------------
         max_vbn = -100000.0
         min_cmb = +100000.0
         number = 0
         #---------

      if (nspin == 2):
         number = 0
         VTemp = outcar.readline()
         VTemp = outcar.readline()
         VTemp = outcar.readline()

      for i in range(nk):
          number += 1
          VTemp = outcar.readline()
          VTemp = outcar.readline()
          for j in range(int(nb/2)):
              VTemp = outcar.readline().split()
              if (nspin == 1): n1 = int(VTemp[0])
              if (nspin == 2): n1 = int(VTemp[0]) + nb
              n2 = float(VTemp[1])
              n3 = float(VTemp[2])
              if (n3 > 0.0):
                 if (n2 > max_vbn):
                    max_vbn = n2
                    n1_valencia = n1
                    kp1 = number
              if (n3 == 0.0):
                 if (n2 < min_cmb):
                    min_cmb = n2
                    n1_conducao = n1
                    kp2 = number

          VTemp = outcar.readline()

      if ((max_vbn <= Efermi) and (min_cmb >= Efermi)): GAP = (min_cmb - max_vbn)
      if ((max_vbn > Efermi) or (min_cmb < Efermi)): GAP = 0.0

      if (n_procar == 1 and nspin == 2):
         if (n1_valencia <= nb): inform.write(f'Last band occuped = {n1_valencia} up \n')
         if (n1_valencia > nb):  inform.write(f'Last band occuped = {n1_valencia -nb} dw \n')
         if (n1_conducao <= nb): inform.write(f'First band empty = {n1_conducao} up \n')
         if (n1_conducao > nb):  inform.write(f'First band empty = {n1_conducao -nb} dw \n')
         #---------------------------------------------------
         inform.write(f'Conduction band minimum (CBM) = {min_cmb} eV  -  k-point {kp1} \n')
         inform.write(f'Valence band maximum (VBM)    = {max_vbn} eV  -  k-point {kp2} \n')
         #---------------------------------------------------------------
         if ((max_vbn <= Efermi) and (min_cmb >= Efermi)):
            if (kp1 == kp2): inform.write(f'GAP (direct) = {GAP:.4f} eV \n')
            if (kp1 != kp2): inform.write(f'GAP (indirect) = {GAP:.4f} eV \n')
         if ((max_vbn > Efermi) or (min_cmb < Efermi)):
            inform.write(f'GAP (No-Gap) = 0.0 eV \n')

         inform.write("---------------------------------------------------- \n")

#=======================================================================

inform.write(f'Fermi energy = {Efermi} eV \n')
inform.write("--------------------------------------------------- \n")

#-----------------------------------------------------------------------
# Finding the total energy of the system: ------------------------------
#-----------------------------------------------------------------------

palavra = 'FREE'                               # FREE is a word present on a line that is four lines before the line that contains information about the variable (free energy TOTEN).
number = 0                                     # number represents which line contains the information about the variable (free energy TOTEN).

for line in outcar:
    number += 1     
    if palavra in line: 
       break

for i in range(3):
    VTemp = outcar.readline()
    
VTemp = outcar.readline().split()
energ_tot = float(VTemp[3])                     

inform.write(f'free energy TOTEN = {energ_tot} eV \n')
inform.write("--------------------------------------------------- \n")

#==========================================================================

if (ispin == 1):

   #-----------------------------------------------------------------------
   #  ---------------------------------
   #-----------------------------------------------------------------------

   if (LNC == 2):
      temp_xk = 4 + ni

      #------------------------- Magnetization (X): ---------------------------

      palavra = 'magnetization'                   # magnetization is a word present on a line that is above the lines that contain information about the magnetization of the system.
      number = 0 

      for line in outcar:
          number += 1     
          if palavra in line: 
             break

      for i in range(temp_xk):
          VTemp = outcar.readline()   

      VTemp = outcar.readline().split()
      mag_s_x = float(VTemp[1])
      mag_p_x = float(VTemp[2])
      mag_d_x = float(VTemp[3])
      mag_tot_x = float(VTemp[4])

      #------------------------- Magnetization (y): ---------------------------

      palavra = 'magnetization'                   # magnetization is a word present on a line that is above the lines that contain information about the magnetization of the system.
      number = 0 

      for line in outcar:
          number += 1
     
          if palavra in line: 
             break

      for i in range(temp_xk):
          VTemp = outcar.readline()

      VTemp = outcar.readline().split()
      mag_s_y = float(VTemp[1])
      mag_p_y = float(VTemp[2])
      mag_d_y = float(VTemp[3])
      mag_tot_y = float(VTemp[4])

      #------------------------- Magnetization (z): ---------------------------

      palavra = 'magnetization'                   # magnetization is a word present on a line that is above the lines that contain information about the magnetization of the system.
      number = 0 

      for line in outcar:
          number += 1
     
          if palavra in line: 
             break

      for i in range(temp_xk):
          VTemp = outcar.readline()

      VTemp = outcar.readline().split()
      mag_s_z = float(VTemp[1])
      mag_p_z = float(VTemp[2])
      mag_d_z = float(VTemp[3])
      mag_tot_z = float(VTemp[4])
   
      #-----------------------------------------------------------------------

      inform.write(" \n")
      inform.write("################ Total Magnetization ################ \n")     
      inform.write(f'X axis:  total = {mag_tot_x:.4f} \n')
      inform.write(f'Y axis:  total = {mag_tot_y:.4f} \n')
      inform.write(f'Z axis:  total = {mag_tot_z:.4f} \n')
      inform.write("##################################################### \n")

#-------------
outcar.close()
#-------------

#######################################################################
######################## CONTCAR File Reading: ########################
#######################################################################
 
#------------------------------------------
contcar = open(dir_files + '/CONTCAR', "r")
#------------------------------------------

VTemp = contcar.readline().split()
VTemp = contcar.readline().split()

Parametro = float(VTemp[0])                                 # Reading the System Lattice Parameter.

A1 = contcar.readline().split()
A1x = float(A1[0]); A1y = float(A1[1]); A1z = float(A1[2])  # Reading the coordinates (X, Y and Z) of the primitive vector (A1) of the unit cell in real space.

A2 = contcar.readline().split()
A2x = float(A2[0]); A2y = float(A2[1]); A2z = float(A2[2])  # Reading the coordinates (X, Y and Z) of the primitive vector (A2) of the unit cell in real space.

A3 = contcar.readline().split()
A3x = float(A3[0]); A3y = float(A3[1]); A3z = float(A3[2])  # Reading the coordinates (X, Y and Z) of the primitive vector (A3) of the unit cell in real space.

#--------------
contcar.close()
#--------------

#-----------------------------------------------------------------------
# Obtaining the labels of the ions present in the CONTCAR file ---------
#-----------------------------------------------------------------------

#------------------------------------------
contcar = open(dir_files + '/CONTCAR', "r")
#------------------------------------------

for i in range(6):
    VTemp = contcar.readline().split() 
types = len(VTemp)                                                     # Obtaining the number of different types of ions that make up the lattice.

#----------------------------------------------

label = [0]*(types+1)
ion_label = [0]*(ni+1)
rotulo = [0]*(ni+1)
rotulo_temp = [0]*(ni+1)

#----------------------------------------------

for i in range (1,(types+1)):
    label[i] = VTemp[(i-1)]                                            # Obtaining the labels/abbreviations that label each type of ion in the lattice.

VTemp = contcar.readline().split()                                    

for i in range (1,(types+1)):            
    ion_label[i] = int(VTemp[(i-1)])                                   # Obtaining the number of ions corresponding to each label/abbreviation.

#----------------------------------------------

contador = 0

for i in range (1,(types+1)):
    number = ion_label[i]
    for j in range (1,(number+1)):
        contador += 1
        rotulo[contador] = label[i]

#--------------
contcar.close()
#--------------

#------------------------------------------------------------------------
#---- Estimation of the correct value of the Network Parameter as the ---
#------ smallest value between the modulus of vectors A1, A2 and A3 -----
#------------------------------------------------------------------------

if (param_estim == 2):

   A1x = A1x*Parametro; A1y = A1y*Parametro; A1z = A1z*Parametro
   A2x = A2x*Parametro; A2y = A2y*Parametro; A2z = A2z*Parametro
   A3x = A3x*Parametro; A3y = A3y*Parametro; A3z = A3z*Parametro

   Parametro_1 = ((A1x*A1x) + (A1y*A1y) + (A1z*A1z))**0.5
   Parametro = Parametro_1

   Parametro_2 = ((A2x*A2x) + (A2y*A2y) + (A2z*A2z))**0.5
   if (Parametro_2 < Parametro):
      Parametro = Parametro_2

   Parametro_3 = ((A3x*A3x) + (A3y*A3y) + (A3z*A3z))**0.5
   if (Parametro_3 < Parametro):
      Parametro = Parametro_3

   A1x = A1x/Parametro; A1y = A1y/Parametro; A1z = A1z/Parametro
   A2x = A2x/Parametro; A2y = A2y/Parametro; A2z = A2z/Parametro
   A3x = A3x/Parametro; A3y = A3y/Parametro; A3z = A3z/Parametro

#-----------------------------------------------------------------------

V_real  = A1x*((A2y*A3z) - (A2z*A3y))   # I just divide this sum into three parts, since it is very long, and it exceeded the length of the line.
V_real += A1y*((A2z*A3x) - (A2x*A3z))
V_real += A1z*((A2x*A3y) - (A2y*A3x))
V_real  =  abs(V_real*(Parametro**3))   # Cell volume in real space (in Angs^3)
V_real  = round(V_real, 6)

#-----------------------------------------------------------------------

inform.write(" \n")
inform.write("***************************************************** \n")
inform.write("Primitive Vectors of the Crystalline Lattice: ******* \n")
inform.write(f'Param. = {Parametro} Angs \n')
inform.write(f'A1 = Param.({A1x}, {A1y}, {A1z}) \n')
inform.write(f'A2 = Param.({A2x}, {A2y}, {A2z}) \n')
inform.write(f'A3 = Param.({A3x}, {A3y}, {A3z}) \n')
inform.write(f'Volume_cell = {V_real} Angs^3 \n')
inform.write("***************************************************** \n")
inform.write(" \n")

#-----------------------------------------------------------------------

ss1 = A1x*((A2y*A3z) - (A2z*A3y))
ss2 = A1y*((A2z*A3x) - (A2x*A3z))
ss3 = A1z*((A2x*A3y) - (A2y*A3x))
ss =  ss1 + ss2 + ss3                                        # I just divide this sum into three parts, since it is very long, and it exceeded the length of the line.

B1x = ((A2y*A3z) - (A2z*A3y))/ss                             # To understand these operations on the X, Y and Z components of the primitive vectors of the crystalline 
B1y = ((A2z*A3x) - (A2x*A3z))/ss                             # lattice (A1, A2 and A3), you must perform the standard operation of building the primitive vectors of 
B1z = ((A2x*A3y) - (A2y*A3x))/ss                             # the reciprocal lattice based on the primitive vectors of the lattice crystal clear. Such an operation 
B2x = ((A3y*A1z) - (A3z*A1y))/ss                             # is available in any solid-state book.
B2y = ((A3z*A1x) - (A3x*A1z))/ss
B2z = ((A3x*A1y) - (A3y*A1x))/ss
B3x = ((A1y*A2z) - (A1z*A2y))/ss
B3y = ((A1z*A2x) - (A1x*A2z))/ss
B3z = ((A1x*A2y) - (A1y*A2x))/ss

#-----------------------------------------------------------------------

dpi = 2*3.1415926535897932384626433832795
V_rec  = B1x*((B2y*B3z) - (B2z*B3y))     # I just divide this sum into three parts, since it is very long, and it exceeded the length of the line.
V_rec += B1y*((B2z*B3x) - (B2x*B3z))
V_rec += B1z*((B2x*B3y) - (B2y*B3x))
V_rec  = abs(V_rec*((dpi/Parametro)**3))   # Cell volume in reciprocal space (in Angs^-3)
V_rec  = round(V_rec, 6)

#-----------------------------------------------------------------------

inform.write("***************************************************** \n")
inform.write("Primitive Vectors of the Reciprocal Lattice: ******** \n")
inform.write(f'2pi/Param. = {dpi/Parametro} Angs^-1 \n')
inform.write(f'B1 = 2pi/Param.({B1x}, {B1y}, {B1z}) \n')
inform.write(f'B2 = 2pi/Param.({B2x}, {B2y}, {B2z}) \n')
inform.write(f'B3 = 2pi/Param.({B3x}, {B3y}, {B3z}) \n')
inform.write(f'Volume_ZB = {V_rec} Angs^-3 \n')
inform.write("***************************************************** \n")
inform.write(" \n")

#-------------
inform.close()
#-------------
