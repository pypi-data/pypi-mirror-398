import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi




#---------------------------------------------------------
# Vetores da rede real (Supercélula S) -------------------
#---------------------------------------------------------
S1x = -4.8376251965;  S1y =  0.00000000000;  S1z = 0.000000000000
S2x =  0.0000000000;  S2y = -17.4125575085;  S2z = 0.000000000000
S3x =  0.0000000000;  S3y =  0.00000000000;  S3z = 34.87887456188 
#-----------------------------------------------------------------




#--------------------------------------------------------------------
# Vetores da rede real (Rede Pristina P) ----------------------------
#--------------------------------------------------------------------
P1x = -2.418812598250;  P1y =  0.0000000000000;  P1z = 0.000000000000
P2x = -1.209406299125;  P2y = -2.1765696885625;  P2z = 0.000000000000
P3x =  0.000000000000;  P3y =  0.0000000000000;  P3z = 34.87887456188
#--------------------------------------------------------------------
# k-points de interesse (Rede Pristina P) ---------------------------
#--------------------------------------------------------------------
K1u = [ [+0.5, +0.0], [+0.0, +0.5], [-0.5, +0.0], [+0.0, -0.5], [+0.5, +0.5], [-0.5, -0.5] ]
K1u += [ [-0.6666666666666666, -0.3333333333333333], [+0.6666666666666666, +0.3333333333333333] ]
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
#---------------------




#-----------------------
fig, ax = plt.subplots()
#-----------------------

#-------------------------------------------------------------
# Construindo a BZ 2D usando Voronoi (Supercélula S) ---------
#-------------------------------------------------------------
nx, ny = 12, 12  # Número de pontos na grade
points = np.dot(np.mgrid[-nx:nx+1, -ny:ny+1].reshape(2, -1).T, np.array([S1b, S2b]))
vor = Voronoi(points)
#--------------------------------
# Plotando a zona de Brillouin 2D
#--------------------------------
for simplex in vor.ridge_vertices:
    simplex = np.asarray(simplex)
    if np.all(simplex >= 0): ax.plot(vor.vertices[simplex, 0], vor.vertices[simplex, 1], color = 'black', linewidth = 0.25, alpha = 0.5, zorder=3)
#------------------------------------------------------------------------------------------------
plt.quiver(0, 0, S1b[0], S1b[1], angles='xy', scale_units='xy', scale=1.0, color='blue', alpha = 0.5, zorder=0)
plt.quiver(0, 0, S2b[0], S2b[1], angles='xy', scale_units='xy', scale=1.0, color='blue', alpha = 0.5, zorder=0)
plt.text((S1b[0] +0.005), (S1b[1] +0.005), "B$_1$", fontsize=10, alpha = 0.5, color="black")
plt.text((S2b[0] +0.010), (S2b[1] +0.010), "B$_2$", fontsize=10, alpha = 0.5, color="black")
#-------------------------------------------------------------------------------------------



#-------------------------------------------------------------
# Construindo a BZ 2D usando Voronoi (Rede Pristina P) -------
#-------------------------------------------------------------
nx, ny = 12, 12  # Número de pontos na grade
points = np.dot(np.mgrid[-nx:nx+1, -ny:ny+1].reshape(2, -1).T, np.array([P1b, P2b]))
vor = Voronoi(points)
#--------------------------------
# Plotando a zona de Brillouin 2D
#--------------------------------
for simplex in vor.ridge_vertices:
    simplex = np.asarray(simplex)
    if np.all(simplex >= 0): ax.plot(vor.vertices[simplex, 0], vor.vertices[simplex, 1], color = 'black', linewidth = 0.5, zorder=2)
#------------------------------------------------------------------------------------------------
plt.quiver(0, 0, P1b[0], P1b[1], angles='xy', scale_units='xy', scale=1.0, color='red', alpha = 0.5, zorder=1)
plt.quiver(0, 0, P2b[0], P2b[1], angles='xy', scale_units='xy', scale=1.0, color='red', alpha = 0.5, zorder=1)
plt.text((P1b[0] +0.005), (P1b[1] +0.005), "B$_1$", fontsize=10, alpha = 0.5, color="black")
plt.text((P2b[0] +0.010), (P2b[1] +0.010), "B$_2$", fontsize=10, alpha = 0.5, color="black")
#-------------------------------------------------------------------------------------------




#-----------------------------------------------------------------
# Ajustar os limites dos eixos para refletir os comprimentos reais
#-----------------------------------------------------------------
Sx_min, Sx_max = vor.vertices[:, 0].min(), vor.vertices[:, 0].max()
Sy_min, Sy_max = vor.vertices[:, 1].min(), vor.vertices[:, 1].max()

# Adicionar configuração do gráfico
plt.title("1º Brillouin Zone (2D)")
plt.xlabel("kx")
plt.ylabel("ky")

x_min = -3.0
x_max = +2.0
y_min = -3.2
y_max = +2.0

plt.xlim((x_min, x_max))
plt.ylim((y_min, y_max))

#----------------------------------------------------
# Ajustar aspect ratio para refletir proporções reais
#----------------------------------------------------
ax.set_box_aspect(abs((y_max - y_min) / (x_max - x_min)))   # Razão dos comprimentos dos eixos

plt.savefig('Brillouin_Zone_2D_Cr2Br2S2_C2.png', dpi = 600, bbox_inches='tight', pad_inches=0)
plt.savefig('Brillouin_Zone_2D_Cr2Br2S2_C2.eps', dpi = 600, bbox_inches='tight', pad_inches=0)
# plt.show()
