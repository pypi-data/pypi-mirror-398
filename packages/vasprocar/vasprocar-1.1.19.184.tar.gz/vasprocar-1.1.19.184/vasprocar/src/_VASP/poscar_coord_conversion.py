# VASProcar Copyright (C) 2023
# GNU GPL-3.0 license


import numpy as np


print ("###############################################################")
print ("## Type the name of the POSCAR/CONTCAR file to be converted: ##")
print ("## --------------------------------------------------------- ##")
print ("## Don't worry, the definition of your lattice vectors will  ##")
print ("##                                             be preserved  ##")
print ("###############################################################") 
name = input ("name: "); name = str(name)
print (" ")


#======================================================================
# Conversion of POSCAR/CONTCAR file to Cartesian/Direct coordinates ===
#======================================================================


#------------------------------
file_i = dir_files + '/' + name
#---------------------------
poscar_i = open(file_i, "r")
for i in range(8): VTemp = poscar_i.readline()
poscar_i.close()
#------------------
string = str(VTemp)
if (string[0] == 'c' or string[0] == 'C'):  file_o = dir_files + '/output/' + name.replace('.vasp','').replace('.poscar','').replace('.txt','') + '_Direct.vasp'
if (string[0] == 'd' or string[0] == 'D'):  file_o = dir_files + '/output/' + name.replace('.vasp','').replace('.poscar','').replace('.txt','') + '_Cartesian.vasp'
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
poscar_i  = open(file_i, "r")
poscar_o  = open(file_o, "w")
VTemp = poscar_i.readline();  poscar_o.write(f'{VTemp}')
VTemp = poscar_i.readline();  poscar_o.write(f'{VTemp}');  param = float(VTemp)
VTemp = poscar_i.readline();  poscar_o.write(f'{VTemp}');  VTemp = VTemp.split();  A = [float(VTemp[0]), float(VTemp[1]), float(VTemp[2])]  
VTemp = poscar_i.readline();  poscar_o.write(f'{VTemp}');  VTemp = VTemp.split();  B = [float(VTemp[0]), float(VTemp[1]), float(VTemp[2])]
VTemp = poscar_i.readline();  poscar_o.write(f'{VTemp}');  VTemp = VTemp.split();  C = [float(VTemp[0]), float(VTemp[1]), float(VTemp[2])]
VTemp = poscar_i.readline();  poscar_o.write(f'{VTemp}')
VTemp = poscar_i.readline();  poscar_o.write(f'{VTemp}')
#-------------------------------------------------------
nions = 0;  VTemp = VTemp.split()
for k in range(len(VTemp)): nions += int(VTemp[k])
#-------------------------------------------------
VTemp = poscar_i.readline()
#--------------------------


if (string[0] == 'd' or string[0] == 'D'):
   #---------------------------
   poscar_o.write(f'Cartesian \n')
   #-----------------------------------------------------------
   # Writing Cartesian coordinates ----------------------------
   #-----------------------------------------------------------
   for k in range(nions):
       VTemp = poscar_i.readline().split()
       k1 = float(VTemp[0]); k2 = float(VTemp[1]); k3 = float(VTemp[2])
       coord_x = ((k1*A[0]) + (k2*B[0]) + (k3*C[0]))
       coord_y = ((k1*A[1]) + (k2*B[1]) + (k3*C[1]))
       coord_z = ((k1*A[2]) + (k2*B[2]) + (k3*C[2]))
       poscar_o.write(f'{coord_x} {coord_y} {coord_z} \n')
       #--------------------------------------------------


if (string[0] == 'c' or string[0] == 'C'):
   #---------------------------
   poscar_o.write(f'Direct \n')
   #--------------------------------------------------
   A1 = np.array([A[0]*param, A[1]*param, A[2]*param])
   A2 = np.array([B[0]*param, B[1]*param, B[2]*param])
   A3 = np.array([C[0]*param, C[1]*param, C[2]*param])
   #-----------------------------------
   # Defining the transformation matrix
   T = np.linalg.inv(np.array([A1, A2, A3]).T)
   #------------------------------------------
   for k in range(nions):
       VTemp = poscar_i.readline().split()
       x = float(VTemp[0])*param
       y = float(VTemp[1])*param
       z = float(VTemp[2])*param     
       r = np.array([x, y, z]) # Cartesian position of atoms
       #-----------------------------------------------------------
       # Writing Direct Coordinates -------------------------------
       #-----------------------------------------------------------
       f = np.dot(T, r)
       f = np.where(f < 0, f + 1, f)
       #------------------------------------
       if ((f[0] >= 0.0) and (f[0] <= 1.0)):
          if ((f[1] >= 0.0) and (f[1] <= 1.0)):
             if ((f[2] >= 0.0) and (f[2] <= 1.0)):
                for m in range(3):
                    f[m] = round(f[m], 6)
                    if (f[m] > 0.99999 or f[m] < 0.00001):
                       f[m] = 0.0
                poscar_o.write(f'{f[0]} {f[1]} {f[2]} \n')

#---------------
poscar_i.close()   
poscar_o.close()
#---------------


if (string[0] == 's' or string[0] == 'S'):
   print("=============================================================================================")
   print(f'The code does not (currently) accept POSCAR/CONTCAR files with the "Selective dynamics" line.')
   print("=============================================================================================")


#------------------------------------------------------------------------
print("========================== Finished ! ==========================")
#------------------------------------------------------------------------

#=======================================================================
# User option to perform another calculation or finished the code ======
#=======================================================================
execute_python_file(filename = '_loop.py')
