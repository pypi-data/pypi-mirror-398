# VASProcar Copyright (C) 2023
# GNU GPL-3.0 license

def execute_python_file(filename: str):
    return exec(open(main_dir + str(filename)).read(), globals())

#-----------------------------------------------------------------------
# Check whether the folder 'Angular_Momentum' exists -------------------
#-----------------------------------------------------------------------
if os.path.isdir(dir_files + '/output/Angular_Momentum'):
   0 == 0
else:
   os.mkdir(dir_files + '/output/Angular_Momentum')
#--------------------------------------------------

#======================================================================
# Getting the input parameters ========================================
#======================================================================
execute_python_file(filename = DFT + '_info.py')

#======================================================================
# Get the input from user =============================================
#======================================================================

if (len(inputs) == 0):
   print ("######################################")
   print ("Projection of Total Angular Momentum J")
   print ("######################################")
   print (" ")

if (escolha == -1 and len(inputs) == 0):

   print ("###############################################################") 
   print ("Do you want to change the color pattern of J projections?      ")
   print ("[0] NOT                                                        ")
   print ("[1] YES                                                        ")
   print ("###############################################################") 
   esc_color = input (" "); esc_color = int(esc_color)
   print (" ")  

   if (esc_color == 1):

      print ("##############################################################")
      print ("Color code:                                                   ")
      print ("0  White   | 1  Black | 2  Red    | 3  Green  | 4  Blue       ")
      print ("5  Yellow  | 6  Borwn | 7  Grey   | 8  Violet | 9  Cyan       ")
      print ("10 Magenta |11 Orange | 12 Indigo | 13 Maroon | 14 Turquesa   ")
      print ("15 Dark_Green                                                 ")
      print ("##############################################################")       
      print ("VASProcar color pattern:                                      ")
      print ("                                                              ")
      print ("J >>  1/2,  3/2, 5/2,   7/2,     9/2,  11/2  >>  4 2 3 10 9 5 ")
      print ("      Blue, Red, Green, Magenta, Cyan, Yellow)                ")
      print ("##############################################################") 
      print (" ")

      print ("==============================================================") 
      print ("Type in sequence the colors of the Angular Momentum J:        ")
      cor_J = input ("Colors_of_J: ")
      #------------------------------
      tcor = cor_J.split()
      c_j1 = int(tcor[0]); c_j2 = int(tcor[1]); c_j3 = int(tcor[2]); c_j4 = int(tcor[3])
      #---------------------------------------------------------------------------------
      print (" ")

if (escolha == -1):

   if (len(inputs) == 0):
      print ("##############################################################")
      print ("Regarding the Plot of Bands, choose ==========================")
      print ("[0] Plot/Analyze all bands ===================================")
      print ("[1] Plot/Analyze selected bands ==============================")
      print ("##############################################################")
      esc_bands = input (" "); esc_bands = int(esc_bands)
      print(" ")

   if (esc_bands == 0):
      bands_range = '1:' + str(nb)

   if (esc_bands == 1):
      if (len(inputs) == 0):    
         print ("##############################################################")
         print ("Select the bands to be analyzed using intervals:              ")
         print ("Type as in the examples below =============================== ")
         print ("------------------------------------------------------------- ")
         print ("Bands can be added in any order ----------------------------- ")
         print ("------------------------------------------------------------- ")
         print ("bands_intervals  35:42                                        ")          
         print ("bands_intervals  1:15 27:69 18:19 76*                         ")
         print ("bands_intervals  7* 9* 11* 13* 14-15                          ")
         print ("##############################################################")
         bands_range = input ("bands_intervals  ")
         print (" ")
      #------------------------------------------------------------------------------------------
      selected_bands = bands_range.replace(':', ' ').replace('-', ' ').replace('*', ' *').split()
      loop = int(len(selected_bands)/2)
      #------------------------------------------------------------------------------------------
      
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

   if (len(inputs) == 0):
      print ("##############################################################") 
      print ("with respect to energy, would you like? ======================") 
      print ("[0] Use the default energy value from DFT output =============")
      print ("[1] Shift the Fermi level to 0.0 eV  =========================")
      print ("##############################################################") 
      esc_fermi = input (" "); esc_fermi = int(esc_fermi)
      print (" ")   

   if (len(inputs) == 0):
      print ("##############################################################") 
      print ("Do you want to modify the energy range to be plotted? ========")
      print ("[0] NOT                                                       ")
      print ("[1] YES                                                       ")
      print ("##############################################################")
      esc_range_E = input (" "); esc_range_E = int(esc_range_E)
      print (" ")

   if (esc_range_E == 1):
      if (len(inputs) == 0):
         print ("##############################################################") 
         print ("Enter the energy range to be plotted: ========================")
         print ("Note: Enter the lowest and highest energy value to be plotted ")
         print ("            in relation to the Fermi Level                    ")
         print ("Examples:                                                     ")
         print ("--------------------------------------------------------------")
         print ("E_min E_max: -3.0 15.0                                        ")
         print ("E_min E_max: -5.1 5.0                                         ")
         print ("##############################################################")      
         range_E = input ("E_min E_max:  ")
         print (" ")
      #--------------------------------------------------
      selected_energ = range_E.replace('-', ' -').replace('+', ' +').replace(':', ' ').split()
      E_min = float(selected_energ[0])
      E_max = float(selected_energ[1])

   if (len(inputs) == 0):
      print ("##############################################################")
      print ("What do you want to analyze? =================================")
      print ("[0] Analyze all ions in the lattice ==========================")
      print ("[1] Analyze selected Ions ====================================")
      print ("##############################################################")
      esc_ions = input (" "); esc_ions = int(esc_ions)
      print(" ")

   if (esc_ions == 1):
      
      #-------------------------
      sim_nao = ["nao"]*(ni + 1)  #  sim_nao vector initialization
      #-------------------------

      if (len(inputs) == 0):
         print ("################################################################")
         print ("Choose the ions_ranges to be analyzed: ======================== ")
         print ("Type as in the examples below ================================= ")
         print ("----------------------------------------------------------------")
         print ("The order in which the ions are added does not change the result")
         print ("----------------------------------------------------------------")
         print ("ions_ranges  1:5 3:9 11* 15:27                                  ")
         print ("ions_ranges  7:49 50:53                                         ")
         print ("ions_ranges  1* 3* 6:9                                          ")
         print ("################################################################")
         ion_range = input ("ions_ranges  ")
         print (" ")
      #---------------------------------------------------------------------------------------
      selected_ions = ion_range.replace(':', ' ').replace('-', ' ').replace('*', ' *').split()
      loop = int(len(selected_ions)/2)
      #---------------------------------------------------------------------------------------
      
      for i in range (1,(loop+1)):
          #------------------------------------------------------
          loop_i = int(selected_ions[(i-1)*2])
          if (selected_ions[((i-1)*2) +1] == "*"):
             selected_ions[((i-1)*2) +1] = selected_ions[(i-1)*2]
          loop_f = int(selected_ions[((i-1)*2) +1])
          #----------------------------------------------------------------------------------------
          if ((loop_i > ni) or (loop_f > ni) or (loop_i < 0) or (loop_f < 0) or (loop_i > loop_f)):
             print (" ")
             print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
             print ("ERROR: The informed ion values are incorrect %%%%%%%%%%%%%")
             print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
             confirmation = input (" ")
             exit()
          #----------------------------------------------------------------------           
          for j in range(loop_i, (loop_f + 1)):
              sim_nao[j] = "sim"    

   if (len(inputs) == 0):
      print ("##############################################################")
      print ("Would you like to label the k-points?                         ")
      print ("[0] DO NOT label the k-points  ===============================")
      print ("[1] highlight k-points present in KPOINTS file ===============")
      print ("[2] Customize: highlight and Label k-points   ================")
      print ("##############################################################") 
      dest_k = input (" "); dest_k = int(dest_k)
      print (" ")
   #--------------
   l_symmetry = 0

   if (DFT == '_QE/' and dest_k == 2 and len(inputs) == 0):
      print ("##############################################################")
      print ("Do you want to insert symmetries as k-point label?            ")
      print ("[0] NOT                                                       ")
      print ("[1] YES                                                       ")
      print ("##############################################################") 
      l_symmetry = input (" "); l_symmetry = int(l_symmetry)
      print (" ") 

   if (dest_k == 2):
      print ("##############################################################")
      print ("label.TXT file should be found inside the 'output' folder ====")
      print ("after reading the PROCAR file ================================")
      print ("##############################################################") 
      print (" ")
      #-----------
      Dimensao = 1

   if (dest_k != 2 and len(inputs) == 0):
      print ("##############################################################")
      print ("Would you like to choose k-axis units?                        ")
      print ("[1] 2pi/Param. (Param. in Angs.) =============================")
      print ("[2] 1/Angs. ==================================================")
      print ("[3] 1/nm.   ==================================================")
      print ("##############################################################")
      Dimensao = input (" "); Dimensao = int(Dimensao)
      print(" ")

   if (len(inputs) == 0):
      print ("##############################################################")
      print ("Enter the weight/size of the spheres in the projection: ======")
      print ("Enter a value between 0.0 and 1.0 ============================")
      print ("##############################################################")
      peso_total = input (" "); peso_total = float(peso_total)
      print(" ")

   if (len(inputs) == 0):
      print ("##############################################################")
      print ("Enter the transparency value to apply to the projections:     ")
      print ("This option is useful for checking the overlap of orbitals.   ")   
      print ("Enter a value between 0.0 and 1.0 ============================")
      print ("==============================================================")
      print ("Hint: The higher the k-point density, the lower the ==========") 
      print ("      transparency value used, start with 0.5 ================")
      print ("##############################################################")
      transp = input (" "); transp = float(transp)
      print(" ")         

if (escolha == 1):
   bands_range = '1:' + str(nb)
   esc_fermi = 1
   esc_range_E = 0  
   esc_ions = 0
   dest_k = 1
   Dimensao = 1
   l_symmetry = 0
   peso_total = 1.0
   transp = 1.0

#======================================================================
# Obtaining the results from DFT outpout files ========================
#======================================================================
read_proj_J = 1
execute_python_file(filename = DFT + '_nscf.py')    

#----------------------
if (Efermi == -1000.0):
   Efermi = 0.0
   esc_fermi = 0 

if (esc_fermi == 0):
   dE_fermi = 0.0
   dest_fermi = Efermi

if (esc_fermi == 1):
   dE_fermi = (Efermi)*(-1)
   dest_fermi = 0.0

if (esc_range_E == 0):
   E_min = energ_min - Efermi
   E_max = energ_max - Efermi
#----------------------------

#======================================================================
# Getting k-points / labels ===========================================
#======================================================================
execute_python_file(filename = DFT + '_label.py')

#======================================================================
# Copy Bandas.dat and Orbitais.dat to the output folder directory =====
#======================================================================

try: f = open(dir_files + '/output/Angular_Momentum/Bandas.dat'); f.close(); os.remove(dir_files + '/output/Angular_Momentum/Bandas.dat')
except: 0 == 0
  
source = dir_files + '/output/Bandas.dat'
destination = dir_files + '/output/Angular_Momentum/Bandas.dat'
shutil.copyfile(source, destination)

os.remove(dir_files + '/output/Bandas.dat')

#----------------------------------------------------------------------

try: f = open(dir_files + '/output/Angular_Momentum/Angular_Momentum.dat'); f.close(); os.remove(dir_files + '/output/Angular_Momentum/Angular_Momentum.dat')
except: 0 == 0
  
source = dir_files + '/output/Angular_Momentum.dat'
destination = dir_files + '/output/Angular_Momentum/Angular_Momentum.dat'
shutil.copyfile(source, destination)

os.remove(dir_files + '/output/Angular_Momentum.dat')

#========================================================================
#========================================================================
# Projections Plot using (GRACE) ========================================
#======================================================================== 
#========================================================================

if (save_agr == 1):
    
   print(" ")
   print ("============== Plotting the Projections (Grace): ==============")

   execute_python_file(filename = '_QE/angular_momentum_plot/plot_projecao_angular_momentum_grace.py')

   print ("Plot of projections via Grace (.agr files) completed ----------")
  
#========================================================================
#========================================================================
# Projections Plot using (Matplotlib) ===================================
#========================================================================
#========================================================================

#----------------------------------------------------------------------
# Copy Orbitais.py to the output folder directory ---------------------
#----------------------------------------------------------------------

try: f = open(dir_files + '/output/Angular_Momentum/Angular_Momentum.py'); f.close(); os.remove(dir_files + '/output/Angular_Momentum/Angular_Momentum.py')
except: 0 == 0
   
source = main_dir + '_QE/angular_momentum_plot/plot_projecao_angular_momentum.py'
destination = dir_files + '/output/Angular_Momentum/Angular_Momentum.py'
shutil.copyfile(source, destination)

#--------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------
# Allowing Bandas.py to be executed separatedly ---------------------------------------
#--------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------

file = open(dir_files + '/output/Angular_Momentum/Angular_Momentum.py', 'r')
lines = file.readlines()
file.close()

linha = 4

lines.insert(linha, '\n')
linha += 1; lines.insert(linha, '###################################################################### \n')
linha += 1; lines.insert(linha, f'# {VASProcar_name} Copyright (C) 2023 \n')
linha += 1; lines.insert(linha, f'# GNU GPL-3.0 license \n')
linha += 1; lines.insert(linha, f'# {url_1} \n')
linha += 1; lines.insert(linha, f'# {url_2} \n')
linha += 1; lines.insert(linha, f'# {url_3} \n')
linha += 1; lines.insert(linha, '###################################################################### \n')
linha += 1; lines.insert(linha, '# Authors:                                                             \n')
linha += 1; lines.insert(linha, '# ==================================================================== \n')
linha += 1; lines.insert(linha, '# Augusto de Lelis Araujo                                              \n')
linha += 1; lines.insert(linha, '# [2022-2023] CNPEM|Ilum|LNNano (Campinas-SP/Brazil)                   \n')
linha += 1; lines.insert(linha, '# [2007-2022] Federal University of Uberlandia (Uberlândia-MG/Brazil)  \n')
linha += 1; lines.insert(linha, '# e-mail: augusto-lelis@outlook.com                                    \n')
linha += 1; lines.insert(linha, '# ==================================================================== \n')
linha += 1; lines.insert(linha, '# Renan da Paixao Maciel                                               \n')
linha += 1; lines.insert(linha, '# Uppsala University (Uppsala/Sweden)                                  \n')
linha += 1; lines.insert(linha, '# e-mail: renan.maciel@physics.uu.se                                   \n')
linha += 1; lines.insert(linha, '###################################################################### \n')
linha += 1; lines.insert(linha, '\n')

linha += 1; lines.insert(linha, '#===================================================================== \n')
linha += 1; lines.insert(linha, '# These are the parameters that allows the code to run separatedly === \n')
linha += 1; lines.insert(linha, '#===================================================================== \n')
linha += 1; lines.insert(linha, '\n')
linha += 1; lines.insert(linha, f'n_procar = {n_procar}  #  Total Number of PROCAR files \n')
linha += 1; lines.insert(linha, f'nk = {nk}              #  Total Number of k-points \n')
linha += 1; lines.insert(linha, f'nb = {nb}              #  Total Number of bands \n')
linha += 1; lines.insert(linha, f'n_j = 4                #  Number of Orbitals \n')
linha += 1; lines.insert(linha, f'bands_range = "{bands_range}"  # Bands to be Plotted/Analyzed \n')
linha += 1; lines.insert(linha, f'E_min = {E_min}        #  Lower energy value of the bands in the plot (in relation to the Fermi level) \n')
linha += 1; lines.insert(linha, f'E_max = {E_max}        #  Higher energy value of the bands in the plot (in relation to the Fermi level) \n')
linha += 1; lines.insert(linha, f'Efermi = {Efermi}        #  Fermi energy from DFT outpout files \n')
linha += 1; lines.insert(linha, f'esc_fermi = {esc_fermi}  #  Would you like to shift the Fermi level? [0] No, use the value obtained from VASP [1] Yes, shift the Fermi level to 0.0 eV \n')
linha += 1; lines.insert(linha, f'lorbit = {lorbit}        #  Value of the lorbit variable adopted in the calculation \n')
linha += 1; lines.insert(linha, f'Dimensao = {Dimensao}    #  [1] (kx,ky,kz) in 2pi/Param.; [2] (kx,ky,kz) in 1/Angs.; [3] (kx,ky,kz) in 1/nm.; [4] (k1,k2,k3) \n')
linha += 1; lines.insert(linha, f'peso_total = {peso_total}  #  weight/size of spheres in the projections plot \n')
linha += 1; lines.insert(linha, f'transp = {transp}          #  Transparency applied to the plot of projections \n')
linha += 1; lines.insert(linha, f'dest_k = {dest_k}          #  [0] DO NOT label the k-points; [1] highlight k-points present in KPOINTS file; [2] Customize: highlight and Label k-points \n')
linha += 1; lines.insert(linha, f'dest_pk = {dest_pk}        #  K-points coordinates to be highlighted in the band structure \n')

if (dest_k != 2):
   label_pk = ['null']*len(dest_pk) 
#-------------------------------------------------------------------------------
if (dest_k == 2): 
   for i in range(contador2):
       for j in range(34):
           if (label_pk[i] == '#' + str(j+1)):
              label_pk[i] = r_matplot[j]    
       if (DFT == '_QE/' and l_symmetry == 1):
          label_pk[i] = label_pk[i] + '$_{(' + symmetry_pk[i] + ')}$' 
#------------------------------------------------------------------------------ 
linha += 1; lines.insert(linha, f'label_pk = {label_pk}  #  K-points label \n')
#------------------------------------------------------------------------------

if (sum_save == 0): save_png = 1
linha += 1; lines.insert(linha, f'save_png = {save_png}; save_pdf = {save_pdf}; save_svg = {save_svg}; save_eps = {save_eps}  #  Plotting output format, where [0] = NOT and [1] = YES \n')                         
linha += 1; lines.insert(linha, '\n')
linha += 1; lines.insert(linha, '#======================================================================== \n')
linha += 1; lines.insert(linha, '# Color code:                                                             \n')
linha += 1; lines.insert(linha, '# 0  White  | 1  Black  | 2  Red    | 3  Green    | 4  Blue    | 5 Yellow \n')
linha += 1; lines.insert(linha, '# 6  Borwn  | 7  Grey   | 8  Violet | 9  Cyan     | 10 Magenta |          \n')
linha += 1; lines.insert(linha, '# 11 Orange | 12 Indigo | 13 Maroon | 14 Turquesa | 15 Green   |          \n')
linha += 1; lines.insert(linha, '#------------------------------------------------------------------------ \n')
linha += 1; lines.insert(linha, '# Colors applied to the total Angular Momentum j:                         \n')
linha += 1; lines.insert(linha, f'c_j1 = {c_j1}; c_j2 = {c_j2}; c_j3 = {c_j3}; c_j4 = {c_j4}               \n')
linha += 1; lines.insert(linha, '#======================================================================== \n')

file = open(dir_files + '/output/Angular_Momentum/Angular_Momentum.py', 'w')
file.writelines(lines)
file.close()

#------------------
if (sum_save != 0):
   exec(open(dir_files + '/output/Angular_Momentum/Angular_Momentum.py').read())
#-------------------------------------------------------------------------------

#=======================================================================

print(" ")
print("========================================================================")
print("= Edit the Plot of the projections through Angular_Momentum.py files or ")
print("= .agr files (Grace) generated in the output/Angular_Momentum folder    ")
print("========================================================================")
   
#-----------------------------------------------------------------------
print(" ")
print("-------------------------- Completed --------------------------")
print(" ")
#-----------------------------------------------------------------------

#=======================================================================
# User option to perform another calculation or finished the code ======
#=======================================================================
if (len(inputs) == 0):
   execute_python_file(filename = '_loop.py')
