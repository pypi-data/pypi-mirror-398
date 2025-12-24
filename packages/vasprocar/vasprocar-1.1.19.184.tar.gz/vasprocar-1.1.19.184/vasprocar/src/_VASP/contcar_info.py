# VASProcar Copyright (C) 2023
# GNU GPL-3.0 license

#======================================================================
# Check if CONTCAR file exist =========================================
#======================================================================

try:
    f = open(dir_files + '/CONTCAR')
    f.close()
except:
    print ("--------------------------------------------------------------")
    print ("Missing the file CONTCAR in the current directory ------------")
    print ("Please, fix it! and press ENTER to continue ------------------")
    print ("--------------------------------------------------------------")
    confirmacao = input (" "); confirmacao = str(confirmacao)

#---------------------------------------------------------------------------
contcar = open(dir_files + '/CONTCAR', "r")
if (opcao == 32 or opcao == -32):
   new_contcar = open(dir_files + '/output/Localizacao/POSCAR_Regions', "w")
#---------------------------------------------------------------------------

#===============================================
# Copying the initial lines of the CONTCAR file:
#===============================================

for ii in range(5):
    VTemp = contcar.readline()
    VTemp = str(VTemp)
    if (opcao == 32 or opcao == -32):
       new_contcar.write(f'{VTemp}')

#======================================================================
# Getting the total number of different types of ions from the lattice:
# Storing the labels of the different types of ions:
#======================================================================

VTemp = contcar.readline().split()
n_tipo = len(VTemp)

rotulo = []

for i in range(n_tipo):
    rotulo.append(str(VTemp[i]))

#================================================================
# Getting the total number of ions in the lattice:
# Storing the number of ions for each type of ion in the lattice:
#================================================================

ni = 0
n_ion = [0]*n_tipo

VTemp = contcar.readline().split()

for ii in range(n_tipo):
    ni += int(VTemp[ii])
    n_ion[ii] = int(VTemp[ii])

label = [0]*ni
contador = -1

for ii in range(n_tipo):
    name = rotulo[ii]
    for j in range(n_ion[ii]):
        contador += 1
        label[contador] = name

#==========================================================
# Storing the type of coordinates used in the CONTCAR file:
#==========================================================

VTemp = contcar.readline()
t_coord = str(VTemp[0])

#====================================================
# Storing the coordinates of all ions in the lattice:
#====================================================

ni_coord = [[0]*(4) for ii in range(ni)]  # ni_coord[ni][4]
Ax = [A1x*Parametro, A2x*Parametro, A3x*Parametro]
Ay = [A1y*Parametro, A2y*Parametro, A3y*Parametro]
Az = [A1z*Parametro, A2z*Parametro, A3z*Parametro]

for ii in range(ni):
    VTemp = contcar.readline().split()
    #---------------------------------
    c_kx = 0; c_ky = 0; c_kz = 0
    #---------------------------
    for j in range(4):
        #-----------------------------------------------
        if (j <= 2):
           if (t_coord == 'c' or t_coord == 'C'):
              ni_coord[ii][j] = float(VTemp[j])*Parametro
           if (t_coord == 'd' or t_coord == 'D'):
              c_kx += float(VTemp[j])*Ax[j]
              c_ky += float(VTemp[j])*Ay[j]
              c_kz += float(VTemp[j])*Az[j]
        if (t_coord == 'd' or t_coord == 'D'):
           ni_coord[ii][0] = c_kx
           ni_coord[ii][1] = c_ky
           ni_coord[ii][2] = c_kz

        #-----------------------------------------------
        if (j == 3):
           ni_coord[ii][j] = label[ii]

#====================================================
#====================================================
#====================================================