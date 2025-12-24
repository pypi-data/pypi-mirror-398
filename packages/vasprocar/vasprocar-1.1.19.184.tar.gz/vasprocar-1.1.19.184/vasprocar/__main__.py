# VASProcar Copyright (C) 2023
# GNU GPL-3.0 license

import os
import sys
import shutil
import requests

#----------------
main_dir = 'src/'
dir_files = os.getcwd()
os.chdir(os.path.dirname(os.path.realpath(__file__)))
dir_vasprocar = os.path.dirname(os.path.realpath(__file__))
print(f'{dir_vasprocar}')
#------------------------

version = '1.1.19.184'
VASProcar_name = 'VASProcar version ' + version

url_1 = 'https://pypi.org/project/vasprocar'
url_2 = 'https://doi.org/10.5281/zenodo.6343960'
url_3 = 'https://github.com/Augusto-de-Lelis-Araujo/VASProcar-Python-tools-VASP'

print(" ")
print("######################################################################")
print(f'# {VASProcar_name} Copyright (C) 2023')
print(f'# GNU GPL-3.0 license')
print("# ====================================================================")
print(f'# {url_1} ')
print(f'# {url_2} ')
print(f'# {url_3} ')
print("######################################################################")
print("# Authors:                                                            ")
print("# ====================================================================")
print("# Augusto de Lelis Araujo                                             ")
print("# [2025-2027] CNRS|CINaM|amU (Marseille/France),                      ")
print("# [2022-2025] CNPEM|Ilum|LNNano (Campinas-SP/Brazil),                 ")
print("# [2007-2022] Federal University of Uberlândia (Uberlândia-MG/Brazil) ")
print("# e-mail: augusto-lelis@outlook.com                                   ")
print("# ====================================================================")
print("# Renan da Paixao Maciel                                              ")
print("# [2020-2024] Uppsala University (Uppsala/Sweden),                    ")
print("# [2014-2020] Federal University of Uberlandia (Uberlândia-MG/Brazil) ")
# print("# e-mail: renan.maciel@physics.uu.se                                  ")
print("######################################################################")

print("                                                         ")
print(" _    _____   _____ ____  ____  ____  _________    ____  ")
print("| |  / /   | / ___// __ \/ __ \/ __ \/ ____/   |  / __ \ ")
print("| | / / /| | \__ \/ /_/ / /_/ / / / / /   / /| | / /_/ / ")
print("| |/ / ___ |___/ / ____/ _, _/ /_/ / /___/ ___ |/ _, _/  ")
print("|___/_/  |_/____/_/   /_/ |_|\____/\____/_/  |_/_/ |_|   ")
print(f'                                                      v{version}')
print("                                                         ")

#------------------------------------------------------------------------------
# Adding the contribution of all orbitals to the Spin components (Sx|Sy|Sz) ---
#------------------------------------------------------------------------------
Orb_spin = [1]*16

#----------------------------------------------------
# code execution ------------------------------------
#----------------------------------------------------

run = main_dir + '_dft.py'
exec(open(run).read())

run = main_dir + 'inputs/' + 'inputs.py'
exec(open(run).read())

if (len(inputs) == 0 and DFT == '_?/'):

   print("######################################################################")
   print("# Which package was used for the DFT calculations? ===================")
   print("# [1] VASP (Vienna Ab initio Simulation Package)                      ")
   print("# [2] QE   (Quantum ESPRESSO)                                         ")
   print("######################################################################")   
   pacote_dft = input(" "); pacote_dft = int(pacote_dft)
   print(" ")

   if (pacote_dft == 1): DFT = '_VASP/' 
   if (pacote_dft == 2): DFT = '_QE/'

if (DFT == '_VASP/'):
   print("######################################################################")
   print("## VASP (Vienna Ab initio Simulation Package) ===================== ##")
   print("## Tested versions: 5.4.4, 6.2, 6.4.3 ============================= ##")
   print("## ================================================================ ##")
   print("# Basic files to execute the code: CONTCAR, KPOINTS, OUTCAR, PROCAR ##")
   print("# For other features: DOSCAR, LOCPOT, WAVECAR or vasprun.xml        ##")
   print("######################################################################")   
   print(" ")

if (DFT == '_QE/'):
   print("######################################################################")
   print("## QE (Quantum ESPRESSO) >> Tested versions: 6.4.1 and 7.1 ======== ##")
   print("## ================================================================ ##")
   print("# Basic files to execute the code: scf.in, scf.out, nscf.in,        ##")
   print("#                                  nscf.out, bands.in, bands.out    ##")
   print("# For other features: projwfc.in, projwfc.out, 'filband',           ##")
   print("#                     'filproj'.projwfc_up and 'filpdos'.pdos_atm   ##")
   print("######################################################################")   
   print(" ")
   #---------------------
   read_contribuicao = 0
   read_projwfc_up = 0
   read_proj_J = 0

#------------------------------------------------
# Checking for updates for VASProcar ------------
#------------------------------------------------
try:
    url = f"https://pypi.org/pypi/{'vasprocar'}/json"
    response = requests.get(url)
    dados = response.json()
    current_version = dados['info']['version']; current_version = str(current_version)
    if (current_version != version):
       print(" ")
       print("--------------------------------------------------------------")
       print("         !!! Your VASProcar version is out of date !!!        ")
       print("--------------------------------------------------------------")
       print("To update, close the VASProcar and enter into the terminal:   ")
       print("              pip install --upgrade vasprocar                 ")
       print("--------------------------------------------------------------")
       print(" ")
       print(" ")
    ...
except Exception as e:
    print("--------------------------------------------------------------")
    print("   !!! Unable to verify the current version of VASProcar !!!  ")
    print("--------------------------------------------------------------") 
    print(" ")

if (len(inputs) == 0):
   run = main_dir + '_settings.py'
   exec(open(run).read())

if (len(inputs) > 0):
   for inp in range(len(inputs)): 
       #---------------------------------------------------------------------------
       exec(open(dir_files + '/inputs/' + 'input.vasprocar.' + inputs[inp]).read())
       #---------------------------------------------------------------------------
       if (inputs[inp] == 'bands'):         opcao = -10
       if (inputs[inp] == 'spin'):          opcao = -20
       if (inputs[inp] == 'orbitals'):      opcao = -30
       if (inputs[inp] == 'dos'):           opcao = -31
       if (inputs[inp] == 'location'):      opcao = -32
       if (inputs[inp] == 'locpot'):        opcao = -40
       if (inputs[inp] == 'chgcar'):        opcao = -41
       if (inputs[inp] == 'spin_video'):    opcao = -23
       if (inputs[inp] == 'fermi_surface'): opcao = -11
       #-----------------------------------------------
       run = main_dir + '_settings.py'
       exec(open(run).read())
