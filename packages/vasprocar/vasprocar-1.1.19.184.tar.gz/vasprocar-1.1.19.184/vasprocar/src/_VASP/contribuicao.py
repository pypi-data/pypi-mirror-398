# VASProcar Copyright (C) 2023
# GNU GPL-3.0 license

from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import numpy as np
import os

def execute_python_file(filename: str):
    return exec(open(main_dir + str(filename)).read(), globals())

#-----------------------------------------------------------------------
# Check whether the 'Contributions folder exists -----------------------
#-----------------------------------------------------------------------
if os.path.isdir(dir_files + '/output/Contributions'):
   0 == 0
else:
   os.mkdir(dir_files + '/output/Contributions')
#----------------------------------------------------

#======================================================================
# Get VASP/QE outpout files information ===============================
#======================================================================
execute_python_file(filename = DFT + '_info.py')

#======================================================================
# Getting the input parameters ========================================
#======================================================================

print ("##############################################################")
print ("################ Orbital & ions contribution: ################")
print ("##############################################################")
print (" ")

if (escolha == -1 or escolha == 1):

   print ("##############################################################")
   print ("Use for confined systems =====================================")
   print ("Want to plot the penetration length of the states ============")
   print ("--------------------------------------------------------------")
   print ("[0] NOT                                                       ")
   print ("[1] YES                                                       ")
   print ("##############################################################")
   penetration_plot = input (" "); penetration_plot = int(penetration_plot)
   print (" ")

   if (penetration_plot == 1):
      #------------------------------------------------------------------------
      p_length = [[0]*(nb+1) for i in range(nk*n_procar+1)]  # p_length[nk][nb]
      #------------------------------------------------------------------------

      print ("##############################################################")
      print ("To define the penetration length, set a maximum contribution  ")
      print ("percentage for the states, ranging between [0.0 and 1.0]      ")
      print ("--------------------------------------------------------------")
      print ("For example:                                                  ")
      print ("contribution_percentage 0.9                                   ")
      print ("##############################################################")
      contrib_perc = input ("contribution_percentage  ")
      print (" ")
      #-------------------------------------
      contrib_perc = float(contrib_perc)*100
      if (contrib_perc <= 0.0 or contrib_perc > 100.0): contrib_perc = 90

      print ("##############################################################")
      print ("What is the direction relative to the penetration length?     ")
      print ("[1] (X)      [2] (Y)      [3] (Z)                             ")
      print ("##############################################################")
      dirc_p_length = input (" "); dirc_p_length = int(dirc_p_length)
      print (" ")

   print ("##############################################################")
   print ("Regarding the Plot of Bands, choose: =========================")
   print ("[0] Plot all bands (not recommended) =========================")
   print ("[1] Plot selected bands ======================================")
   print ("##############################################################")
   esc_bands = input (" "); esc_bands = int(esc_bands)
   print(" ")

   if (esc_bands == 0):
      bands_range = '1:' + str(nb)

   if (esc_bands == 1):
      print ("##############################################################")
      print ("Select the bands to be analyzed using intervals:              ")
      print ("Type as in the examples below =============================== ")
      print ("------------------------------------------------------------- ")
      print ("Bands can be added in any order ----------------------------- ")
      print ("------------------------------------------------------------- ")
      print ("bands_intervals  35:42                                        ")          
      print ("bands_intervals  1:15 27:69 18:19 76*                         ")
      print ("bands_intervals  7* 9* 11* 13* 14:15                          ")
      print ("##############################################################")
      bands_range = input ("bands_intervals  ")
      print (" ")

   #------------------------------------------------
   temp_bands = bands_range.replace(':',' ').split()
   bands_i = int(temp_bands[0])
   bands_f = int(temp_bands[1])
   n_bands = (bands_f -bands_i) +1
   #------------------------------------------------------------------------------------------
   selected_bands = bands_range.replace(':', ' ').replace('-', ' ').replace('*', ' *').split()
   loop = int(len(selected_bands)/2)
   #------------------------------------------------------------------------------------------  
   bands_sn = ["nao"]*(nb + 1)
   #---------------------------
   for i in range (1,(loop+1)):
       #--------------------------------------------------------
       loop_i = int(selected_bands[(i-1)*2])
       if (selected_bands[((i-1)*2) +1] == "*"):
          selected_bands[((i-1)*2) +1] = selected_bands[(i-1)*2]
       loop_f = int(selected_bands[((i-1)*2) +1])
       #----------------------------------------------------------------------------------------
       if ((loop_i > nb) or (loop_f > nb) or (loop_i < 0) or (loop_f < 0) or (loop_i > loop_f)):
          print (" ")
          print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
          print ("ERROR: The values of the informed bands are incorrect %%%%")
          print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
          confirmation = input (" ")
          exit() 
       #----------------------------------------------------------------------     
       for j in range(loop_i, (loop_f + 1)):
           bands_sn[j] = "sim"  

   print ("##############################################################")
   print ("Regarding the Plot of Bands, choose: =========================")
   print ("[0] Plot all k-points ========================================")
   print ("[1] Plot selected k-points ===================================")
   print ("##############################################################")
   esc_kpoints = input (" "); esc_kpoints = int(esc_kpoints)
   print(" ")
      
   if (esc_kpoints == 0):
      points_range = '1:' + str(nk)

   if (esc_kpoints == 1):
      print ("##############################################################")
      print ("Select by the k-points to be analyzed:                        ")
      print ("Type as in the examples below =============================== ")
      print ("------------------------------------------------------------- ")
      print ("The k-points can be added in any order ---------------------- ")
      print ("------------------------------------------------------------- ")
      print ("k-points_intervals  1:50                                      ")          
      print ("k-points_intervals  15:25 27:100 150:180 200*                 ")
      print ("k-points_intervals  70* 90* 110* 130* 140:150                 ")
      print ("##############################################################")
      points_range = input ("k-points_intervals  ")
      print (" ")

   #--------------------------------------------------------------------------------------------
   selected_points = points_range.replace(':', ' ').replace('-', ' ').replace('*', ' *').split()
   loop = int(len(selected_points)/2)
   #--------------------------------------------------------------------------------------------      
   points_sn = ["nao"]*(nk +1)
   #--------------------------
   for i in range (1,(loop+1)):
       #--------------------------------------------------------
       loop_i = int(selected_points[(i-1)*2])
       if (selected_points[((i-1)*2) +1] == "*"):
          selected_points[((i-1)*2) +1] = selected_points[(i-1)*2]
       loop_f = int(selected_points[((i-1)*2) +1])
       #----------------------------------------------------------------------------------------
       if ((loop_i > nk) or (loop_f > nk) or (loop_i < 0) or (loop_f < 0) or (loop_i > loop_f)):
          print (" ")
          print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
          print ("ERROR: The entered k-point values are incorrect %%%%%%%%%%%")
          print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
          confirmation = input (" ")
          exit() 
       #-----------------------------------------------------------------------     
       for j in range(loop_i, (loop_f + 1)):
           points_sn[j] = "sim"  


#*****************************************************************
# k-axis units ===================================================
# Dimensao = 1 >> 2pi/Param. (Param. in Angs.) *******************
# Dimensao = 2 >> 1/Angs. ****************************************
# Dimensao = 3 >> 1/nm *******************************************
#*****************************************************************
Dimensao = 1
#---------------------------------------------------
if (Dimensao == 1 or Dimensao == 4):  fator_zb = 1.0
if (Dimensao == 2):                   fator_zb = (2*3.1415926535897932384626433832795)/Parametro
if (Dimensao == 3):                   fator_zb = (10*2*3.1415926535897932384626433832795)/Parametro
#--------------------------
B1x = B1x*fator_zb;  B1y = B1y*fator_zb;  B1z = B1z*fator_zb
B2x = B2x*fator_zb;  B2y = B2y*fator_zb;  B2z = B2z*fator_zb
B3x = B3x*fator_zb;  B3y = B3y*fator_zb;  B3z = B3z*fator_zb

linha_1 = "================================================"
linha_2 = "=========================================================================================================================================================================" 

atomo = [0]*(ni+1)
separacao = [0.0]*((nk*n_procar) +1)
Orb_tot = 0.0
n_point_k = 0


if (penetration_plot == 1):
   #------------------------------------------
   contcar = open(dir_files + '/CONTCAR', "r")
   Coord = [0.0]*(ni+1)
   #---------------------------------------------
   for i in range(8):  VTemp = contcar.readline()
   for i in range(1,(ni+1)):
       VTemp = contcar.readline().split()
       C1 = float(VTemp[0]); C2 = float(VTemp[1]); C3 = float(VTemp[2])
       if (dirc_p_length == 1): Coord[i] = ((C1*A1x) + (C2*A2x) + (C3*A3x))*Parametro
       if (dirc_p_length == 2): Coord[i] = ((C1*A1y) + (C2*A2y) + (C3*A3y))*Parametro
       if (dirc_p_length == 3): Coord[i] = ((C1*A1z) + (C2*A2z) + (C3*A3z))*Parametro
   #------------------------------------
   p_max = abs( max(Coord) -min(Coord) )
   #------------------------------------

#######################################################################
# Obtaining the results from DFT outpout files ########################
#######################################################################

#----------------------------------------------------------------------------------
contrib_ions = open(dir_files + '/output/Contributions/Contribution_ions.txt', 'w')
#----------------------------------------------------------------------------------
contrib_orbitais = open(dir_files + '/output/Contributions/Contribution_Orbitals.txt', 'w')
#------------------------------------------------------------------------------------------
  
contrib_ions.write("================================================================ \n")
contrib_ions.write("Note: ions with highest contribution are listed first ---------- \n")
contrib_ions.write("================================================================ \n")
contrib_ions.write(" \n")

#######################################################################
############################# PROCAR loop #############################
#######################################################################

for wp in range(1, (n_procar+1)):

    if (n_procar == 1):
       print("=========================")
       print("Analyzing the PROCAR file")
       print("=========================")

    if (n_procar > 1):
       print("==========================")
       print("Analyzing the PROCAR files")
       print("==========================")

    try: f = open(dir_files + '/PROCAR'); f.close(); teste = 'sim'
    except: teste = 'nao'   
   
    if (teste == 'sim' and n_procar == 1):
       procar = open(dir_files + '/PROCAR', "r")
      
    if (teste == 'nao' and n_procar >= 1):
       procar = open(dir_files + '/PROCAR.' + str(wp), "r")

    for n_spin in range(1,(ispin+1)):
     
        #######################################################################
        ############################ k-points loop ############################
        #######################################################################
        
        temp = 1.0; number = 0

        for point_k in range(1, (nk+1)):                       

            #---------------------------------------------------
            if (n_procar == 1 and n_spin == 1): temp_string = ''
            if (n_procar == 1 and n_spin == 2): temp_string = 'Spin Component ' + 'str(n_spin)' + ': '
            #-----------------------------------------------------------------------------------------
            if (n_procar > 1  and n_spin == 1): temp_string = 'PROCAR file ' + str(wp) + ': '
            if (n_procar > 1  and n_spin  > 1): temp_string = 'PROCAR file ' + str(wp) + ' (Spin Component ' + 'str(n_spin)' + '): '
            #-----------------------------------------------------------------------------------------------------------------------

            #----------------------------------------------------------------------
            # Calculating the PROCAR file reading percentage ----------------------
            #----------------------------------------------------------------------

            #----------
            number += 1
            porc = (point_k/nk)*100        
            #----------------------
            if porc >= temp:
               bar_length = 50
               filled_length = int(bar_length * porc // 100)
               bar = '#' * filled_length + '-' * (bar_length - filled_length)
               print(f'\r{temp_string}Progress: |{bar}| {porc:.1f}%', end="")
               sys.stdout.flush()
               temp += 1   # updates every 1%
              
            #----------------------------------------------------------------------
            # Reading the k1, k2 and k3 coordinates of each k-point ---------------
            #---------------------------------------------------------------------- 

            #-----------
            test = 'nao'
            #-----------
            while (test == 'nao'):             
                  #------------------------
                  VTemp = procar.readline()
                  Teste = VTemp.split() 
                  #---------------------------------------------
                  if (len(Teste) > 0 and Teste[0] == 'k-point'):
                     test = 'sim'
                     for i in range(10):
                         VTemp = VTemp.replace('-' + str(i) + '.', ' -' + str(i) + '.')
                     VTemp = VTemp.split()                         
                     #-----------------------------------------------------------------

            if (n_spin == 1):        #  Note: In VASP k1, k2 and k3 correspond to the direct coordinates of each k-point in the ZB, that is,  
               k1 = float(VTemp[3])  #  K = (k1*B1 + k2*B2 + k3*b3), its Cartesian coordinates are obtained through the relations below, 
               k2 = float(VTemp[4])  #  which give us kx = Coord_X, ky = Coord_Y and kz = Coord_Z, however, we should note that these kx,   
               k3 = float(VTemp[5])  #  ky and kz coordinates are written in units of 2pi/lattice_parameter.

            VTemp = procar.readline()

            if (n_spin == 1): 
               #----------------------------------------------------------------------
               # Obtaining the separation distance between the k-points --------------
               #----------------------------------------------------------------------
               Coord_X = ((k1*B1x) + (k2*B2x) + (k3*B3x))
               Coord_Y = ((k1*B1y) + (k2*B2y) + (k3*B3y))
               Coord_Z = ((k1*B1z) + (k2*B2z) + (k3*B3z))
               #-----------------------------------------
               if (wp == 1) and (point_k == 1):
                  comp = 0.0
               #------------------------------
               if (wp != 1) or (point_k != 1):
                  delta_X = Coord_X_antes - Coord_X
                  delta_Y = Coord_Y_antes - Coord_Y
                  delta_Z = Coord_Z_antes - Coord_Z
                  comp = (delta_X**2 + delta_Y**2 + delta_Z**2)**0.5
                  comp = comp + comp_antes
               #--------------------------
               Coord_X_antes = Coord_X
               Coord_Y_antes = Coord_Y
               Coord_Z_antes = Coord_Z
               #----------------------
               comp_antes = comp
               #------------------------
               n_point_k = n_point_k + 1
               if (penetration_plot == 1): separacao[n_point_k] = comp
               #------------------------------------------------------

            # Criterion to define which k-points will be analyzed
            if (points_sn[point_k] == 'sim'):                      

               contrib_ions.write("---------------------------------------------------------------- \n")
               contrib_ions.write(f'K-point {n_point_k}: Direct coord. ({k1}, {k2}, {k3}) \n')
               contrib_ions.write("---------------------------------------------------------------- \n")
               contrib_ions.write(" \n")

               contrib_orbitais.write("---------------------------------------------------------------- \n")
               contrib_orbitais.write(f'K-point {n_point_k}: Direct coord. ({k1}, {k2}, {k3}) \n')
               contrib_orbitais.write("---------------------------------------------------------------- \n")
               contrib_orbitais.write(" \n") 
          
            #######################################################################
            ############################# bands loop ##############################
            #######################################################################

            for Band_n in range (1, (int(nb/ispin) +1)):
                #-----------------------------------------
                Band = Band_n + (n_spin - 1)*int(nb/ispin)
                #-----------------------------------------

                soma = 0.0
            
                # Criterion to define which k-points and bands will be analyzed 
                if ( (bands_sn[Band] == 'sim') and (points_sn[point_k] == 'sim') ):   

                   contrib_ions.write(f'Band {Band_n} \n')
                   contrib_ions.write(f'{linha_1}====== \n')

                   contrib_orbitais.write(f'Band {Band_n:<3} \n')             
               
                   if (lorbit >= 11): 
                      contrib_orbitais.write(f'{linha_2} \n')
                   if (lorbit == 10):
                      contrib_orbitais.write(f'{linha_1}==== \n') 

                #-----------
                test = 'nao'
                #-----------
                while (test == 'nao'):             
                      VTemp = procar.readline().split()
                      #------------------------------------------
                      if (len(VTemp) > 0 and VTemp[0] == 'band'):
                         test = 'sim'
                         #---------------------------------------
             
                #-----------
                test = 'nao'
                #-----------
                while (test == 'nao'):             
                      VTemp = procar.readline().split()
                      #-----------------------------------------
                      if (len(VTemp) > 0 and VTemp[0] == 'ion'):
                         test = 'sim'              
                         #--------------------------------------
            
                #######################################################################
                ############################## ions loop ##############################
                #######################################################################

                #======================================================================
                #======================== Reading the Orbitals ========================
                #======================================================================

                for ion_n in range (1, (ni+1)):
                    VTemp = procar.readline().split()

                    # Criterion to define which k-points and bands will be analyzed 
                    if ( (bands_sn[Band] == 'sim') and (points_sn[point_k] == 'sim') ): 

                       atomo[ion_n] = ion_n

                       #--------------------------------------------------------------------------
                       # Zeroing the variables at the beginning of each ion loop -----------------
                       #--------------------------------------------------------------------------

                       if (ion_n == 1 and lorbit < 11):
                          #------------------- 
                          Orb_S = [0.0]*(ni+1)
                          Orb_P = [0.0]*(ni+1)
                          Orb_D = [0.0]*(ni+1)
                          Orb_F = [0.0]*(ni+1)
                          #-------------------                       
                          Orb_tot = 0.0

                       if (ion_n == 1 and lorbit >= 11):
                          #-------------------
                          Orb_S = [0.0]*(ni+1)
                          Orb_P = [0.0]*(ni+1)
                          Orb_D = [0.0]*(ni+1)
                          Orb_F = [0.0]*(ni+1)
                          #--------------------
                          Orb_Px = [0.0]*(ni+1)
                          Orb_Py = [0.0]*(ni+1)
                          Orb_Pz = [0.0]*(ni+1)
                          #---------------------
                          Orb_Dxy = [0.0]*(ni+1)
                          Orb_Dyz = [0.0]*(ni+1)
                          Orb_Dz2 = [0.0]*(ni+1)
                          Orb_Dxz = [0.0]*(ni+1)
                          Orb_Dx2 = [0.0]*(ni+1)
                          #----------------------
                          Orb_Fyx2 = [0.0]*(ni+1)
                          Orb_Fxyz = [0.0]*(ni+1)
                          Orb_Fyz2 = [0.0]*(ni+1)
                          Orb_Fzz2 = [0.0]*(ni+1)
                          Orb_Fxz2 = [0.0]*(ni+1)
                          Orb_Fzx2 = [0.0]*(ni+1)
                          Orb_Fxx2 = [0.0]*(ni+1)                        
                          #----------------------
                          Orb_tot = 0.0

                       ###########################################################################
                       # Summing the orbital contribution of each selected ion ###################
                       ###########################################################################                

                       # Ordering Orbitals:
                       #       1 | 2  | 3  | 4  |  5  |  6  |  7  |  8  |  9  |  10  |  11  |  12  |  13  |  14  |  15  |  16  |
                       # VASP: S | Py | Pz | Px | Dxy | Dyz | Dz2 | Dxz | Dx2 | Fyx2 | Fxyz | Fyz2 | Fzz2 | Fxz2 | Fzx2 | Fxx2 |
                       # QE:   S | Pz | Px | Py | Dz2 | Dxz | Dyz | Dx2 | Dxy | ???? | ???? | ???? | ???? | ???? | ???? | ???? |

                       if (n_orb <= 4):
                          Orb_S[ion_n] += float(VTemp[1])
                          Orb_P[ion_n] += float(VTemp[2])
                          Orb_D[ion_n] += float(VTemp[3])
                          #---------------------------------
                          if (n_orb == 4):
                             Orb_F[ion_n] += float(VTemp[4])

                       if (n_orb >= 9):
                          Orb_S[ion_n]   += float(VTemp[1])
                          Orb_Py[ion_n]  += float(VTemp[2])
                          Orb_Pz[ion_n]  += float(VTemp[3])
                          Orb_Px[ion_n]  += float(VTemp[4])
                          Orb_P[ion_n]   += float(VTemp[2]) + float(VTemp[3]) + float(VTemp[4])
                          Orb_Dxy[ion_n] += float(VTemp[5])
                          Orb_Dyz[ion_n] += float(VTemp[6])
                          Orb_Dz2[ion_n] += float(VTemp[7])
                          Orb_Dxz[ion_n] += float(VTemp[8])
                          Orb_Dx2[ion_n] += float(VTemp[9])
                          Orb_D[ion_n]   += float(VTemp[5]) + float(VTemp[6]) + float(VTemp[7]) + float(VTemp[8]) + float(VTemp[9])  
                          #--------------------------------------------------------------------------------------------------------     
                          if (n_orb == 16):
                             Orb_Fyx2[ion_n] += float(VTemp[10])
                             Orb_Fxyz[ion_n] += float(VTemp[11])
                             Orb_Fyz2[ion_n] += float(VTemp[12])
                             Orb_Fzz2[ion_n] += float(VTemp[13])
                             Orb_Fxz2[ion_n] += float(VTemp[14])
                             Orb_Fzx2[ion_n] += float(VTemp[15])
                             Orb_Fxx2[ion_n] += float(VTemp[16]) 
                             Orb_F[ion_n] += float(VTemp[10]) + float(VTemp[11]) + float(VTemp[12]) + float(VTemp[13]) + float(VTemp[14]) + float(VTemp[15]) + float(VTemp[16])

                       for orb in range(1,(n_orb+1)):
                           Orb_tot += float(VTemp[orb])

                ###########################################################################
                # Calculating the contribution percentage of each Orbital: ################
                ###########################################################################

                soma_s = 0.0; soma_p = 0.0; soma_d = 0.0; soma_f = 0.0
                soma_px = 0.0; soma_py = 0.0; soma_pz = 0.0
                soma_dxy = 0.0; soma_dyz = 0.0; soma_dz2 = 0.0; soma_dxz = 0.0; soma_dx2 = 0.0
                soma_fyx2 = 0.0; soma_fxyz = 0.0; soma_fyz2 = 0.0; soma_fzz2 = 0.0; soma_fxz2 = 0.0; soma_fzx2 = 0.0; soma_fxx2 = 0.0
                total = 0.0; soma = 0.0
                tot_ion = [0.0]*(ni+1)

                for ion_n in range (1, (ni+1)):
                    
                    # Criterion to define which k-points and bands will be analyzed 
                    if ( (bands_sn[Band] == 'sim') and (points_sn[point_k] == 'sim') ): 
                   
                       if (Orb_tot > 0.01 and DFT == '_VASP/'):
                          if (n_orb <= 4):
                             #------------------------------------------
                             s = (Orb_S[ion_n]/Orb_tot)*100; soma_s += s
                             p = (Orb_P[ion_n]/Orb_tot)*100; soma_p += p
                             d = (Orb_D[ion_n]/Orb_tot)*100; soma_d += d
                             f = (Orb_F[ion_n]/Orb_tot)*100; soma_f += f
                             #------------------------------------------

                          if (n_orb >= 9):
                             #------------------------------------------
                             s = (Orb_S[ion_n]/Orb_tot)*100; soma_s += s
                             p = (Orb_P[ion_n]/Orb_tot)*100; soma_p += p
                             d = (Orb_D[ion_n]/Orb_tot)*100; soma_d += d
                             f = (Orb_F[ion_n]/Orb_tot)*100; soma_f += f
                             #----------------------------------------------
                             px = (Orb_Px[ion_n]/Orb_tot)*100; soma_px += px
                             py = (Orb_Py[ion_n]/Orb_tot)*100; soma_py += py
                             pz = (Orb_Pz[ion_n]/Orb_tot)*100; soma_pz += pz
                             #--------------------------------------------------
                             dxy = (Orb_Dxy[ion_n]/Orb_tot)*100; soma_dxy += dxy
                             dyz = (Orb_Dyz[ion_n]/Orb_tot)*100; soma_dyz += dyz
                             dz2 = (Orb_Dz2[ion_n]/Orb_tot)*100; soma_dz2 += dz2
                             dxz = (Orb_Dxz[ion_n]/Orb_tot)*100; soma_dxz += dxz
                             dx2 = (Orb_Dx2[ion_n]/Orb_tot)*100; soma_dx2 += dx2
                             #------------------------------------------------------
                             fyx2 = (Orb_Fyx2[ion_n]/Orb_tot)*100; soma_fyx2 += fyx2
                             fxyz = (Orb_Fxyz[ion_n]/Orb_tot)*100; soma_fxyz += fxyz
                             fyz2 = (Orb_Fyz2[ion_n]/Orb_tot)*100; soma_fyz2 += fyz2
                             fzz2 = (Orb_Fzz2[ion_n]/Orb_tot)*100; soma_fzz2 += fzz2
                             fxz2 = (Orb_Fxz2[ion_n]/Orb_tot)*100; soma_fxz2 += fxz2
                             fzx2 = (Orb_Fzx2[ion_n]/Orb_tot)*100; soma_fzx2 += fzx2
                             fxx2 = (Orb_Fxx2[ion_n]/Orb_tot)*100; soma_fxx2 += fxx2
                             #------------------------------------------------------

                       tot_ion[ion_n] = (s + p + d + f)
                       total += tot_ion[ion_n]

                       if (Orb_tot >= 0 and lorbit >= 11):
                          contrib_orbitais.write(f'{rotulo[ion_n]:>2}: ion {atomo[ion_n]:<3} | S = {s:5,.2f}% | P = {p:5,.2f}% | D = {d:5,.2f}% ')
                          if (n_orb == 16):
                             contrib_orbitais.write(f'| F = {f:5,.2f}% ')
                          contrib_orbitais.write(f'| Px = {px:5,.2f}% | Py = {py:5,.2f}% | Pz = {pz:5,.2f}% ')           
                          contrib_orbitais.write(f'| Dxy = {dxy:5,.2f}% | Dyz = {dyz:5,.2f}% | Dz2 = {dz2:5,.2f}% | Dxz = {dxz:5,.2f}% | Dx2 = {dx2:5,.2f}% | ')                     
                          if (n_orb == 16):
                             contrib_orbitais.write(f'Fyx2 = {fyx2:5,.2f}% | Fxyz = {fxyz:5,.2f}% | Fyz2 = {fyz2:5,.2f}% | Fzz2 = {fzz2:5,.2f}% | Fxz2 = {fxz2:5,.2f}% | ')
                             contrib_orbitais.write(f'Fzx2 = {fzx2:5,.2f}% | Fxx2 = {fxx2:5,.2f}% | ') 
                          contrib_orbitais.write(f' \n') 

                       if (Orb_tot >= 0 and lorbit == 10):
                          contrib_orbitais.write(f'{rotulo[ion_n]:>2}: ion {atomo[ion_n]:<3} | S = {s:5,.2f}% | P = {p:5,.2f}% | D = {d:5,.2f}% | ')
                          if (n_orb == 4):            
                             contrib_orbitais.write(f'F = {d:5,.2f}% | ')  
                          contrib_orbitais.write(f' \n')  

                if ( (bands_sn[Band] == 'sim') and (points_sn[point_k] == 'sim') ):

                   if (lorbit >= 11):             
                      contrib_orbitais.write(f'{linha_2} \n')
                      contrib_orbitais.write(f'Sum:        | S = {soma_s:5,.2f}% | P = {soma_p:5,.2f}% | D = {soma_d:5,.2f}% ')
                      if (n_orb == 16):
                         contrib_orbitais.write(f'| F = {soma_f:5,.2f}% ')
                      contrib_orbitais.write(f'| Px = {soma_px:5,.2f}% | Py = {soma_py:5,.2f}% | Pz = {soma_pz:5,.2f}% ')
                      contrib_orbitais.write(f'| Dxy = {soma_dxy:5,.2f}% | Dyz = {soma_dyz:5,.2f}% | Dz2 = {soma_dz2:5,.2f}% | Dxz = {soma_dxz:5,.2f}% | Dx2 = {soma_dx2:5,.2f}% ')
                      if (n_orb == 16):
                         contrib_orbitais.write(f'| Fyx2 = {soma_fyx2:5,.2f}% | Fxyz = {soma_fxyz:5,.2f}% | Fyz2 = {soma_fyz2:5,.2f}% | Fzz2 = {soma_fzz2:5,.2f}% ')
                         contrib_orbitais.write(f'| Fxz2 = {soma_fxz2:5,.2f}% | Fzx2 = {soma_fzx2:5,.2f}% | Fxx2 = {soma_fxx2:5,.2f}% ')    
                      contrib_orbitais.write(f' \n')
 
                   if (lorbit == 10):           
                      contrib_orbitais.write(f'{linha_1}==== \n')
                      contrib_orbitais.write(f'Sum:        | S = {soma_s:5,.2f}% | P = {soma_p:5,.2f}% | D = {soma_d:5,.2f}% | ')  
                      if (n_orb == 4):
                         contrib_orbitais.write(f'F = {soma_f:5,.2f}% | ') 
                      contrib_orbitais.write(f' \n') 

                VTemp = procar.readline()

                ###########################################################################
                # Calculating the percentage contribution of each ion: ####################
                ###########################################################################               

                for j in range (1,(ni+1)):
                    rotulo_temp[j] = rotulo[j]

                nj = (ni - 1)
                
                for k in range (1,(nj+1)):
                    w = (ni - k)
                    for l in range (1,(w+1)):
                        if (tot_ion[l] < tot_ion[l+1]):
                           #--------------------------------
                           tp1 = tot_ion[l]
                           tot_ion[l] = tot_ion[l+1]
                           tot_ion[l+1] = tp1                        
                           #--------------------------------
                           tp2 = atomo[l]
                           atomo[l] = atomo[l+1]
                           atomo[l+1] = tp2                   
                           #--------------------------------
                           tp4 = rotulo_temp[l]
                           rotulo_temp[l] = rotulo_temp[l+1]
                           rotulo_temp[l+1] = tp4                          
                           #--------------------------------

                if (penetration_plot == 1):
                   vector_length = []

                for ion_n in range (1,(ni+1)):
                    #---------------------------
                    soma = soma + tot_ion[ion_n]          
                    #---------------------------
                    if (total != 0):
                       #-----------------------------------------------------------------------------------------------------------------------------------------
                       contrib_ions.write(f'{rotulo_temp[ion_n]:>2}: ion {atomo[ion_n]:<3} | Contribution: {tot_ion[ion_n]:>6,.3f}% | Sum:  {soma:>7,.3f}% | \n')
                       #-----------------------------------------------------------------------------------------------------------------------------------------
                       if ((penetration_plot == 1) and (soma <= contrib_perc)):
                          vector_length.append(Coord[ion_n])

                if ((total != 0) and (penetration_plot == 1) and (len(vector_length) > 0)):
                   #-----------------------------------------------------------------------
                   max_vector_length = max(vector_length)
                   min_vector_length = min(vector_length)
                   p_length[n_point_k][Band] = abs(max_vector_length -min_vector_length)
                   #--------------------------------------------------------------------

                if ((bands_sn[Band] == 'sim') and (points_sn[point_k] == 'sim') and (ion_n == ni)):
                   #----------------------------------------
                   contrib_ions.write(f'{linha_1}====== \n')
                   contrib_ions.write(" \n")
                   #------------------------
                   if (lorbit >= 11): 
                      contrib_orbitais.write(f'{linha_2} \n')
                   if (lorbit == 10):
                      contrib_orbitais.write(f'{linha_1}==== \n')
                   #---------------------------------------------
                   contrib_orbitais.write(" \n")

                #======================================================================
                #============= Analyzing Spin's Sx, Sy, and Sz Components =============
                #======================================================================

                if (LNC == 2):      # Condition for calculation with Spin-orbit coupling
            
                   #======================================================================
                   #================ Reading the Sx component of the Spin ================
                   #======================================================================

                   for ion_n in range (1, (ni+1)):
                       VTemp = procar.readline()
                   VTemp = procar.readline()
              
                   #======================================================================
                   #================ Reading the Sy component of the Spin ================
                   #======================================================================

                   for ion_n in range (1, (ni+1)):
                       VTemp = procar.readline()
                   VTemp = procar.readline()

                   #======================================================================
                   #================ Reading the Sz component of the Spin ================
                   #======================================================================            

                   for ion_n in range (1, (ni+1)):
                       VTemp = procar.readline()
                   VTemp = procar.readline()

                ########################################################################## 
                ### End of ions Loop #####################################################
            ### End of bands Loop ########################################################     
        ### End of k-points Loop #########################################################
        #-------------------------------------------------------
        print(f"\r{temp_string}Progress: completed !{' ' * 60}")
        print(" ")
        #---------
    ### End of n_spin Loop ###############################################################
    ###################################################################################### 

    #-------------
    procar.close()
    #-------------

##########################################################################################
### End of PROCAR files Loop #############################################################
##########################################################################################

#-------------------
contrib_ions.close()
#-----------------------
contrib_orbitais.close()
#-----------------------

#=========================================================================================
# p_length.dat file writing ==============================================================
#=========================================================================================

if (penetration_plot == 1):
   #-------------------------------------------------------------------
   p_file = open(dir_files + '/output/Contributions/p_length.dat', 'w')
   #-------------------------------------------------------------------
   number_k = 0
   #-----------
   for wp in range(n_procar):
      for i in range(1, (nk +1)):
          #----------------------
          number_k += 1
          #------------
          for j in range (1, (nb+1)):
              if ((points_sn[i] == 'sim') and (bands_sn[j] == 'sim')):          
                 if (j == bands_i): p_file.write(f'{separacao[number_k]} ')
                 p_file.write(f'{p_length[number_k][j]} ')
              if (j == bands_f): p_file.write(f' \n')
   #-------------
   p_file.close()
   #-------------


print(" ")
print ("========== Plotting the penetration length (GRACE) ==========")

if (penetration_plot == 1):
   #-------------------------------------------------------------------------------
   plot_agr = open(dir_files + '/output/Contributions/penetration_length.agr', 'w')
   #-------------------------------------------------------------------------------
   for j in range (1, (nb+1)):
       #-----------
       number_k = 0
       #-----------
       for wp in range(n_procar):
           for i in range(1, (nk +1)):
               #----------------------
               number_k += 1
               #------------
               if ((points_sn[i] == 'sim') and (bands_sn[j] == 'sim')):  plot_agr.write(f'{separacao[number_k]} {p_length[number_k][j]} \n')
       if ((points_sn[i] == 'sim') and (bands_sn[j] == 'sim')):  plot_agr.write(f' \n')
   #---------------
   plot_agr.close()
   #---------------


if (penetration_plot == 1):
   print(" ")
   print ("======== Plotting the penetration length (Matplotlib) ========")

   print(" ")
   print(".........................")
   print("..... Wait a moment .....")
   print(".........................")

   #======================================================================
   #======================================================================
   # File Structure for Plot via Matplotlib ==============================
   #======================================================================
   #======================================================================   

   p_length = np.loadtxt(dir_files + '/output/Contributions/p_length.dat') 
   p_length.shape

   x = p_length[:,0]

   fig, ax = plt.subplots()

   # Plot of Bands =======================================================

   for i in range (1,((bands_f -bands_i)+1)):
       y = p_length[:,i]

       """
       # Interpolando os dados ======================================
       grau_polinomio = 12;  nd = 250
       # Calcula os coeficientes do polinômio -----------------------
       coeficientes = np.polyfit(x, y, grau_polinomio)
       # Criando a função de interpolação ---------------------------
       polinomio_interpolador = np.poly1d(coeficientes)
       # Gerando mais pontos por interpolação -----------------------
       x_interp = np.linspace(min(x), max(x), nd)
       y_interp = polinomio_interpolador(x_interp)
       #=============================================================
       """

       plt.plot(x, y, color = 'black', linestyle = '-', linewidth = 0.25) 
       # plt.plot(x_interp, y_interp, color = 'black', linestyle = '-', linewidth = 0.25)
       # plt.scatter(x, y, s = 5, color = 'black', marker='o', alpha = 1.0, edgecolors = 'none')

   #======================================================================

   plt.xlim((x[0], x[(n_procar*nk)-1]))
   plt.ylim((0.0, p_max*(1.05)))

   if (Dimensao == 1): plt.xlabel('$2{\pi}/{a}$')
   if (Dimensao == 2): plt.xlabel('${\AA}^{-1}$')
   if (Dimensao == 3): plt.xlabel('${nm}^{-1}$')
   #--------------------------------------------
   plt.ylabel('penetration length (${\AA}$)')

   ax.set_box_aspect(1.25/1.0)
    
   plt.savefig(dir_files + '/output/Contributions/penetration_length.png', dpi = 600, bbox_inches='tight', pad_inches=0)
   # plt.show()


#---------
print(" ")
print("====================== Finished ! =======================")
#-----------------------------------------------------------------

#=======================================================================
# User option to perform another calculation or finished the code ======
#=======================================================================
execute_python_file(filename = '_loop.py')
