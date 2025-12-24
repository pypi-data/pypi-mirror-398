import os
import numpy as np
from scipy.spatial import Voronoi
#--------------------------------
import matplotlib as mpl
from matplotlib import cm
from matplotlib import pyplot as plt
import matplotlib.ticker as ticker
from mpl_toolkits.mplot3d.axes3d import Axes3D
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import matplotlib.colors as mcolors




#---------------------------------------------------------
# Vetores da rede real (Supercélula S) -------------------
#---------------------------------------------------------
S1x = -4.8376251965;  S1y =  0.00000000000;  S1z = 0.000000000000
S2x =  0.0000000000;  S2y = -17.4125575085;  S2z = 0.000000000000
S3x =  0.0000000000;  S3y =  0.00000000000;  S3z = 34.87887456188 
#-----------------------------------------------------------------




#----------------------------------------------------------------
# Vetores da rede real (Rede Pristina P) ------------------------
#----------------------------------------------------------------
P1x = -2.418812598250;  P1y =  0.0000000000000;  P1z = 0.000000000000
P2x = -1.209406299125;  P2y = -2.1765696885625;  P2z = 0.000000000000
P3x =  0.000000000000;  P3y =  0.0000000000000;  P3z = 34.87887456188
#-------------------------------------------------------------------
# k-points de interesse (Rede Pristina P) --------------------------
#-------------------------------------------------------------------
K1 = [ [+0.5, +0.0], [+0.0, +0.5], [-0.5, +0.0], [+0.0, -0.5], [+0.5, +0.5], [-0.5, -0.5] ]
K1 += [ [-0.6666666666666666, -0.3333333333333333], [+0.6666666666666666, +0.3333333333333333] ]
#-----------------------------------------------------------------------------------------------




#------------------------------------------------------
# Obtendo a rede recíproca da Supercélula S -----------
#------------------------------------------------------
ss1 = S1x*((S2y*S3z) - (S2z*S3y))
ss2 = S1y*((S2z*S3x) - (S2x*S3z))
ss3 = S1z*((S2x*S3y) - (S2y*S3x))
ss =  ss1 + ss2 + ss3
#-------------------------------
B1x = ((S2y*S3z) - (S2z*S3y))/ss
B1y = ((S2z*S3x) - (S2x*S3z))/ss 
B1z = ((S2x*S3y) - (S2y*S3x))/ss
B2x = ((S3y*S1z) - (S3z*S1y))/ss                             
B2y = ((S3z*S1x) - (S3x*S1z))/ss
B2z = ((S3x*S1y) - (S3y*S1x))/ss
B3x = ((S1y*S2z) - (S1z*S2y))/ss
B3y = ((S1z*S2x) - (S1x*S2z))/ss
B3z = ((S1x*S2y) - (S1y*S2x))/ss
#-------------------------------
ft = 6.2831853071795860
S1b = [B1x*ft, B1y*ft]
S2b = [B2x*ft, B2y*ft]
#---------------------




#------------------------------------------------------
# Obtendo a rede recíproca da Rede Pristina P ---------
# Obtendo as coord. cart. dos k-points de interesse ---
#------------------------------------------------------
ss1 = P1x*((P2y*P3z) - (P2z*P3y))
ss2 = P1y*((P2z*P3x) - (P2x*P3z))
ss3 = P1z*((P2x*P3y) - (P2y*P3x))
ss =  ss1 + ss2 + ss3
#-------------------------------
B1x = ((P2y*P3z) - (P2z*P3y))/ss
B1y = ((P2z*P3x) - (P2x*P3z))/ss 
B1z = ((P2x*P3y) - (P2y*P3x))/ss
B2x = ((P3y*P1z) - (P3z*P1y))/ss                             
B2y = ((P3z*P1x) - (P3x*P1z))/ss
B2z = ((P3x*P1y) - (P3y*P1x))/ss
B3x = ((P1y*P2z) - (P1z*P2y))/ss
B3y = ((P1z*P2x) - (P1x*P2z))/ss
B3z = ((P1x*P2y) - (P1y*P2x))/ss
#-------------------------------
ft = 6.2831853071795860
P1b = [B1x*ft, B1y*ft]
P2b = [B2x*ft, B2y*ft]
#---------------------------------------
# KPOINTS de interesse (Rede Pristina P)
#---------------------------------------
K1_new = []
for i in range(len(K1)):
    #-------------------
    coord_x = (K1[i][0]*P1b[0]) + (K1[i][1]*P2b[0])
    coord_y = (K1[i][0]*P1b[1]) + (K1[i][1]*P2b[1])
    temp_xy = []
    temp_xy.append(coord_x);  temp_xy.append(coord_y)
    #------------------------------------------------
    K1_new.append(temp_xy)
#-------------------------




#-----------------------------------
# Definirndo matriz de transformação 
#-----------------------------------
a = np.array([S1b[0], S1b[1]])
b = np.array([S2b[0], S2b[1]])
T = np.linalg.inv(np.array([a, b]).T)
#------------------------------------




#-------------------------------------------------------------
# Construindo a BZ 2D usando Voronoi (Supercélula S) ---------
#-------------------------------------------------------------
nx, ny = 12, 12  # Número de pontos na grade
points = np.dot(np.mgrid[-nx:nx+1, -ny:ny+1].reshape(2, -1).T, np.array([S1b, S2b]))
vor = Voronoi(points)
#--------------------------------
# Plotando a zona de Brillouin 2D
#--------------------------------
fig, ax = plt.subplots()
#-----------------------
for simplex in vor.ridge_vertices:
    simplex = np.asarray(simplex)
    if np.all(simplex >= 0): ax.plot(vor.vertices[simplex, 0], vor.vertices[simplex, 1], color = 'black', linewidth = 0.25, alpha = 0.5, zorder=3)
#------------------------------------------------------------------------------------------------
plt.quiver(0, 0, S1b[0], S1b[1], angles='xy', scale_units='xy', scale=1.0, color='blue', alpha = 0.5, zorder=0)
plt.quiver(0, 0, S2b[0], S2b[1], angles='xy', scale_units='xy', scale=1.0, color='blue', alpha = 0.5, zorder=0)
plt.text((S1b[0] +0.005), (S1b[1] +0.005), "B$_1$", fontsize=10, alpha = 0.5, color="black")
plt.text((S2b[0] +0.010), (S2b[1] +0.010), "B$_2$", fontsize=10, alpha = 0.5, color="black")
#-------------------------------------------------------------------------------------------




#--------------------------------------------------------
# Convertendo as posições cartesianas para a forma direta
#--------------------------------------------------------
Kpoints = K1_new
Kpoints_f = []
#----------------------------
for i in range(len(Kpoints)):
    #-----------------------
    kx = float(Kpoints[i][0])
    ky = float(Kpoints[i][1])
    r = np.array([kx, ky])
    #----------------------------------------------------------------
    # Calculandos as posições fracionárias com relação a supercélula:
    #----------------------------------------------------------------
    f = np.dot(T, r)
    for n in range(9):
        for m in range(2):
            f[m] = np.where(f[m] < -0.5, f[m] +1, f[m])
            f[m] = np.where(f[m] > +0.5, f[m] -1, f[m])
            if (f[m] > -0.00001 and f[m] < 0.00001):  f[m] =  0.0
            if (f[m] >  0.49999 and f[m] <  0.50001): f[m] =  0.5
            if (f[m] > -0.50001 and f[m] < -0.49999): f[m] = -0.5
    #------------------------------------------------------------
    temp_k = [];  temp_k.append(f[0]);  temp_k.append(f[1])
    Kpoints_f.append(temp_k)
    print(temp_k)
#---------------------------
Kpoints_f_cart = []
#------------------
for i in range(len(Kpoints_f)):
    #--------------------
    coord_x = (Kpoints_f[i][0]*S1b[0]) + (Kpoints_f[i][1]*S2b[0])
    coord_y = (Kpoints_f[i][0]*S1b[1]) + (Kpoints_f[i][1]*S2b[1])
    temp_k = [];  temp_k.append(coord_x);  temp_k.append(coord_y)
    #------------------------------------------------------------
    Kpoints_f_cart.append(temp_k)
#--------------------------------




#=======================================================
# Plot (k-points projected) ============================
#=======================================================
#----------------------------------------------------------------------------------------------------------------------------------
for i in range(len(Kpoints_f_cart)): plt.scatter(Kpoints_f_cart[i][0], Kpoints_f_cart[i][1], c='black', marker='o', s=60, zorder=1)
#----------------------------------------------------------------------------------------------------------------------------------
plt.title('k-points projection')
plt.xlabel('$k_x$')
plt.ylabel('$k_y$')
#----------------------
x_min = -1.5
x_max = +0.75
y_min = -0.4
y_max = +0.25
plt.xlim((x_min, x_max))
plt.ylim((y_min, y_max))
#----------------------------------------------------
# Ajustar aspect ratio para refletir proporções reais
#----------------------------------------------------
ax.set_box_aspect(abs((y_max - y_min) / (x_max - x_min)))   # Razão dos comprimentos dos eixos
#------------------------------------------------------------------------------------
plt.savefig('k-points_projected.png', dpi = 600, bbox_inches='tight', pad_inches = 0)
plt.savefig('k-points_projected.eps', dpi = 600, bbox_inches='tight', pad_inches = 0)
#------------------------------------------------------------------------------------

