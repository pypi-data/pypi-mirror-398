
import os
import matplotlib.pyplot as plt
import numpy as np

print(" ")
print("=========== Plotting the Projections (Matplotlib): ===========")

print(" ")
print(".........................")
print("..... Wait a moment .....")
print(".........................")  
print(" ")

#------------------------------------------------------------------------
# Test to know which directories must be correctly informed -------------
#------------------------------------------------------------------------
if os.path.isdir('src'):
   0 == 0
   dir_output = dir_files + '/output/Spin/'
else:
   dir_files = ''
   dir_output = ''
#-----------------

#======================================================================
#======================================================================
# File Structure for Plot via Matplotlib ==============================
#======================================================================
#======================================================================

banda = np.loadtxt(dir_output + 'Bandas.dat') 
banda.shape

spin = np.loadtxt(dir_output + 'Spin.dat') 
spin.shape

#----------------------------------------------------------------------

if (esc_fermi == 0):
   #---------------------
   dE_fermi = 0.0
   dest_fermi = Efermi
   #---------------------
   E_min = E_min + Efermi
   E_max = E_max + Efermi
   
if (esc_fermi == 1):
   #-----------------------
   dE_fermi = (Efermi)*(-1)
   dest_fermi = 0.0
   #-----------------------
   E_min = E_min
   E_max = E_max

dpi = 2*3.1415926535897932384626433832795

#----------------------------------------------------------------------

num_bands = 0
bands_sn = ["nao"]*(nb + 1)
selected_bands = bands_range.replace(':', ' ').replace('-', ' ').split()
loop = int(len(selected_bands)/2)
    
for i in range (1,(loop+1)):
    #-----------------------------------------
    loop_i = int(selected_bands[(i-1)*2])
    loop_f = int(selected_bands[((i-1)*2) +1])
    #----------------------------------------------------------------------------------------
    if ((loop_i > nb) or (loop_f > nb) or (loop_i < 0) or (loop_f < 0) or (loop_i > loop_f)):
       print (" ")
       print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
       print ("ERROR: The values of the informed bands are incorrect %%%%")
       print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
       confirmacao = input (" ")
       exit()
    #----------------------------------------------------------------------     
    for j in range(loop_i, (loop_f + 1)):
        num_bands += 1
        bands_sn[j] = "sim"  

#----------------------------------------------------------------------  

#===============================================================================================       
# RGB color standard: color = [Red, Green, Blue] with each component ranging from 0.0 to 1.0 ===       
#===============================================================================================

cRGB = [0]*16
f = 255

cRGB[0]  = (255/f, 255/f, 255/f)  # White (Red + Green + Blue)
cRGB[1]  = (  0/f,   0/f,   0/f)  # Black
cRGB[2]  = (255/f,   0/f,   0/f)  # Red
cRGB[3]  = (  0/f, 255/f,   0/f)  # Green
cRGB[4]  = (  0/f,   0/f, 255/f)  # Blue
cRGB[5]  = (255/f, 255/f,   0/f)  # Yellow (Red + Green)
cRGB[6]  = (188/f, 143/f, 143/f)  # Brown
cRGB[7]  = (220/f, 220/f, 220/f)  # Grey
cRGB[8]  = (148/f,   0/f, 211/f)  # Violet
cRGB[9]  = (  0/f, 255/f, 255/f)  # Cyan (Green + Blue)
cRGB[10] = (255/f,   0/f, 255/f)  # Magenta (Red + Blue)
cRGB[11] = (255/f, 165/f,   0/f)  # Orange
cRGB[12] = (114/f,  33/f, 188/f)  # Indigo
cRGB[13] = (103/f,   7/f,  72/f)  # Maroon
cRGB[14] = ( 64/f, 224/f, 208/f)  # Turquoise
cRGB[15] = (  0/f, 139/f,   0/f)  # Intense Green: Green 4 "Grace"


#===========================================================================
# Plot of the Sx|Sy|Sz (total) Component Projections individually: =========
#===========================================================================

rx = spin[:,0]
ry = spin[:,1] + dE_fermi

pSx_u = rx*0.0;  pSy_u = rx*0.0;  pSz_u = rx*0.0
pSx_d = rx*0.0;  pSy_d = rx*0.0;  pSz_d = rx*0.0

for l in range (1,(3+1)):

    fig, ax = plt.subplots()

    # Plot of Projections ==================================================

    if (l == 1):
       print ("Analyzing Spin's Sx_total Projection")
       palavra = r'$S_{x}$'; file = 'Spin_Sx_total'

    if (l == 2):
       print ("Analyzing Spin's Sy_total Projection")
       palavra = r'$S_{y}$'; file = 'Spin_Sy_total'

    if (l == 3):
       print ("Analyzing Spin's Sz_total Projection")
       palavra = r'$S_{z}$'; file = 'Spin_Sz_total'

    #------------------------------------------------
    Si_total  = ( spin[:,(2*l)] + spin[:,((2*l)+1)] )
    Si_u_total = rx*0.0;  Si_d_total = rx*0.0
    #------------------------------------------------------
    Si_ud = ( abs(spin[:,(2*l)]) + abs(spin[:,((2*l)+1)]) )
    Si_u = abs(spin[:,(2*l)])
    Si_d = abs(spin[:,((2*l)+1)])
    #------------------------------------------------------
    for i in range(len(rx)):
        if (Si_total[i] > 0.0): Si_u_total[i] = Si_total[i]
        if (Si_total[i] < 0.0): Si_d_total[i] = Si_total[i]
        #--------------------------------------------------
        if (l == 1):
           if (Si_ud[i] > 0.0): 
              pSx_u[i] = Si_u[i]/Si_ud[i]
              pSx_d[i] = Si_d[i]/Si_ud[i]
        if (l == 2):
           if (Si_ud[i] > 0.0): 
              pSy_u[i] = Si_u[i]/Si_ud[i]
              pSy_d[i] = Si_d[i]/Si_ud[i]
        if (l == 3):
           if (Si_ud[i] > 0.0): 
              pSz_u[i] = Si_u[i]/Si_ud[i]
              pSz_d[i] = Si_d[i]/Si_ud[i]
    #---------------------------------------------
    Si_u_total  = ((dpi*Si_u_total)**2)*peso_total
    Si_d_total  = ((dpi*Si_d_total)**2)*peso_total
    Si_ud = ((dpi*Si_ud)**2)*peso_total
    #----------------------------------
    if (l == 1): Sx_ud = Si_ud
    if (l == 2): Sy_ud = Si_ud
    if (l == 3): Sz_ud = Si_ud
    #-------------------------

    ax.scatter(rx, ry, s = Si_u_total, color = cRGB[c_spin_up], alpha = transp, edgecolors = 'none')
    ax.scatter(rx, ry, s = Si_d_total, color = cRGB[c_spin_down], alpha = transp, edgecolors = 'none')   

    # Inserting legend's spheres: =========================================
    ax.scatter([-1000.0], [-1000.0], s = [40.0], color = cRGB[c_spin_up], alpha = 1.0, edgecolors = 'none', label = palavra + r'$\uparrow$')
    ax.scatter([-1000.0], [-1000.0], s = [40.0], color = cRGB[c_spin_down], alpha = 1.0, edgecolors = 'none', label = palavra + r'$\downarrow$')
    
    # Plot of Bands =======================================================

    x = banda[:,0]

    for i in range (1,(nb+1)):
        if (bands_sn[i] == "sim"):
           y = banda[:,i] + dE_fermi
           plt.plot(x, y, color = 'black', linestyle = '-', linewidth = 0.25, alpha = 0.3)

    # Highlighting the Fermi energy in the Band structure =================

    plt.plot([x[0], x[(n_procar*nk)-1]], [dest_fermi, dest_fermi], color = 'red', linestyle = '-', linewidth = 0.1, alpha = 1.0)

    # Highlighting k-points of interest in the Band structure =============

    if (dest_k > 0): 
       for j in range (len(dest_pk)):
           plt.plot([dest_pk[j], dest_pk[j]], [E_min, E_max], color = 'gray', linestyle = '-', linewidth = 0.1, alpha = 1.0)

    # Labeling k-points of interest in the Band structure =================

    if (dest_k == 2): plt.xticks(dest_pk,label_pk)   
    
    #======================================================================

    plt.xlim((x[0], x[(n_procar*nk)-1]))
    plt.ylim((E_min, E_max))

    if (Dimensao == 1 and dest_k != 2): plt.xlabel('$2{\pi}/{a}$')
    if (Dimensao == 2 and dest_k != 2): plt.xlabel('${\AA}^{-1}$')
    if (Dimensao == 3 and dest_k != 2): plt.xlabel('${nm}^{-1}$')

    if (esc_fermi == 0):
       plt.ylabel('$E$ (eV)')
    if (esc_fermi == 1):
       plt.ylabel('$E-E_{f}$ (eV)')    

    ax.set_box_aspect(1.25/1)
    ax.legend(title="")
    ax.legend(loc="upper right")

    if (save_png == 1): plt.savefig(dir_output + file + '.png', dpi = 600, bbox_inches='tight', pad_inches = 0)
    if (save_pdf == 1): plt.savefig(dir_output + file + '.pdf', dpi = 600, bbox_inches='tight', pad_inches = 0)
    if (save_svg == 1): plt.savefig(dir_output + file + '.svg', dpi = 600, bbox_inches='tight', pad_inches = 0)
    if (save_eps == 1): plt.savefig(dir_output + file + '.eps', dpi = 600, bbox_inches='tight', pad_inches = 0)

    # plt.show()
    plt.close()


#=======================================================================================================================================
# Obtaining and recording the colors in the RGB pattern that designate the combination of the components of Spin_{x,y,z} up and down ===
#=======================================================================================================================================

# Initialization of Matrice to be used:
rgb_Sx = [0]*n_procar*nk*num_bands
rgb_Sy = [0]*n_procar*nk*num_bands
rgb_Sz = [0]*n_procar*nk*num_bands

#---------------------------------

number = -1
for Band_n in range (1, (num_bands+1)):
    for wp in range (1, (n_procar+1)):
        for point_k in range (1, (nk+1)):       
            number += 1

            #--------------------------------------------------------------------------------------------------
            # Summing the colors of the components of Spin_{x,y,z} up and down: -------------------------------
            #--------------------------------------------------------------------------------------------------

            color_Sx = [0]*3;  color_Sy = [0]*3;  color_Sz = [0]*3
           
            for i in range(3):
                color_Sx[i]  = pSx_u[number]*cRGB[c_spin_up][i] + pSx_d[number]*cRGB[c_spin_down][i]
                color_Sy[i]  = pSy_u[number]*cRGB[c_spin_up][i] + pSy_d[number]*cRGB[c_spin_down][i]
                color_Sz[i]  = pSz_u[number]*cRGB[c_spin_up][i] + pSz_d[number]*cRGB[c_spin_down][i]
                #-----------------------------------------------------------------------------------
                if (color_Sx[i]  > 1.0): color_Sx[i] = 1.0
                if (color_Sy[i]  > 1.0): color_Sy[i] = 1.0
                if (color_Sz[i]  > 1.0): color_Sz[i] = 1.0
            #-------------------------------------------------------
            rgb_Sx[number] = (color_Sx[0], color_Sx[1], color_Sx[2])
            rgb_Sy[number] = (color_Sy[0], color_Sy[1], color_Sy[2]) 
            rgb_Sz[number] = (color_Sz[0], color_Sz[1], color_Sz[2])
#-------------------------------------------------------------------
cRGB_overlap = [0]*3
cRGB_overlap[0] = 0.5*cRGB[c_spin_up][0] + 0.5*cRGB[c_spin_down][0]
cRGB_overlap[1] = 0.5*cRGB[c_spin_up][1] + 0.5*cRGB[c_spin_down][1]
cRGB_overlap[2] = 0.5*cRGB[c_spin_up][2] + 0.5*cRGB[c_spin_down][2]

#========================================================================================
# Plot with the Projections of the Sx|Sy|Sz merged via the sum of the color pattern: ====
#========================================================================================

rx = spin[:,0]
ry = spin[:,1] + dE_fermi

for l in range (1,(3+1)):

    fig, ax = plt.subplots()

    # Plot of Projections ==================================================

    if (l == 1):
       print ("-------------------------------------------------")
       print ("Analyzing Spin's Sx Projection (sum of the color)")
       palavra = r'$S_{x}$'; file = 'Spin_Sx_[sum_colors]'

    if (l == 2):
       print ("Analyzing Spin's Sy Projection (sum of the color)")
       palavra = r'$S_{y}$'; file = 'Spin_Sy_[sum_colors]'

    if (l == 3):
       print ("Analyzing Spin's Sz Projection (sum of the color)")
       palavra = r'$S_{z}$'; file = 'Spin_Sz_[sum_colors]'

    if (l == 1):  ax.scatter(rx, ry, s = Sx_ud, color = rgb_Sx, alpha = transp, edgecolors = 'none')
    if (l == 2):  ax.scatter(rx, ry, s = Sy_ud, color = rgb_Sy, alpha = transp, edgecolors = 'none') 
    if (l == 3):  ax.scatter(rx, ry, s = Sz_ud, color = rgb_Sz, alpha = transp, edgecolors = 'none') 

    # Inserting legend's spheres: =========================================
    ax.scatter([-1000.0], [-1000.0], s = [40.0], color = cRGB[c_spin_up], alpha = 1.0, edgecolors = 'none', label = palavra + r'$\uparrow$')
    ax.scatter([-1000.0], [-1000.0], s = [40.0], color = cRGB[c_spin_down], alpha = 1.0, edgecolors = 'none', label = palavra + r'$\downarrow$')
    ax.scatter([-1000.0], [-1000.0], s = [40.0], color = cRGB_overlap, alpha = 1.0, edgecolors = 'none', label = 'overlap')

    # Plot of Bands =======================================================

    x = banda[:,0]

    for i in range (1,(nb+1)):
        if (bands_sn[i] == "sim"):
           y = banda[:,i] + dE_fermi
           plt.plot(x, y, color = 'black', linestyle = '-', linewidth = 0.25, alpha = 0.3)

    # Highlighting the Fermi energy in the Band structure =================

    plt.plot([x[0], x[(n_procar*nk)-1]], [dest_fermi, dest_fermi], color = 'red', linestyle = '-', linewidth = 0.1, alpha = 1.0)

    # Highlighting k-points of interest in the Band structure =============

    if (dest_k > 0): 
       for j in range (len(dest_pk)):
           plt.plot([dest_pk[j], dest_pk[j]], [E_min, E_max], color = 'gray', linestyle = '-', linewidth = 0.1, alpha = 1.0)

    # Labeling k-points of interest in the Band structure =================

    if (dest_k == 2): plt.xticks(dest_pk,label_pk)   
    
    #======================================================================

    plt.xlim((x[0], x[(n_procar*nk)-1]))
    plt.ylim((E_min, E_max))

    if (Dimensao == 1 and dest_k != 2): plt.xlabel('$2{\pi}/{a}$')
    if (Dimensao == 2 and dest_k != 2): plt.xlabel('${\AA}^{-1}$')
    if (Dimensao == 3 and dest_k != 2): plt.xlabel('${nm}^{-1}$')

    if (esc_fermi == 0):
       plt.ylabel('$E$ (eV)')
    if (esc_fermi == 1):
       plt.ylabel('$E-E_{f}$ (eV)')    

    ax.set_box_aspect(1.25/1)
    ax.legend(title="")
    ax.legend(loc="upper right")

    if (save_png == 1): plt.savefig(dir_output + file + '.png', dpi = 600, bbox_inches='tight', pad_inches = 0)
    if (save_pdf == 1): plt.savefig(dir_output + file + '.pdf', dpi = 600, bbox_inches='tight', pad_inches = 0)
    if (save_svg == 1): plt.savefig(dir_output + file + '.svg', dpi = 600, bbox_inches='tight', pad_inches = 0)
    if (save_eps == 1): plt.savefig(dir_output + file + '.eps', dpi = 600, bbox_inches='tight', pad_inches = 0)

    # plt.show()
    plt.close()


#===========================================================================

print(" ")
print ("Plot of projections via Matplotlib completed ----------------")

#---------------------------------------------------------------------------
if (dir_output == ''):
   print(" ")
   print("========================== Concluded! ==========================")
#---------------------------------------------------------------------------

# VASProcar Copyright (C) 2023
# GNU GPL-3.0 license