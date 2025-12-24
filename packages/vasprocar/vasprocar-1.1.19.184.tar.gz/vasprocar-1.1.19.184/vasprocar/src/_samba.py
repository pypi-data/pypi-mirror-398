# VASProcar Copyright (C) 2023
# GNU GPL-3.0 license

import os
import sys
import site
import shutil
import subprocess                                                   

print("#############################################################################")
print("# SAMBA: Simulation and Automated Methods for Bilayer Analysis              #")
print("# ------------------------------------------------------------------------- #")
print("# SAMBA is an open-source Python 3 code capable of:                         #")
print("# Generate Twisted homo- and hetero bilayers;                               #")
print("# Automating DFT calculations through a high-throughput approach;           #")
print("# Automate the analysis of results (via VASProcar code).                    #")
print("# ========================================================================= #")
print("# Authors: Augusto de Lelis Araujo, Adalberto Fazzio,                       #")
print("#          Felipe Crasto de Lima, Pedro Henrique Sophia                     #")
print("# ========================================================================= #")
print("# For more information, visit the link:                                     #")
print("# https://github.com/Augusto-de-Lelis-Araujo/SAMBA-ilum/blob/main/README.md #")
print("#############################################################################")

print(" ")
print("============================================================================")
print("[0] RUN SAMBA Code                                                          ")
print("[1] Install/Update the SAMBA python module                                  ")
print("[2] Exit                                                                    ")
print("============================================================================")
modulo = input(" "); modulo = int(modulo)
print(" ")

if (modulo == 0):
   subprocess.run(["python3", "-m", "samba_ilum", dir_files])

if (modulo == 1):
   subprocess.run(["pip", "install", "--upgrade", "samba_ilum"])

#=====================================================================
# User option to perform another calculation or end the code =========
#=====================================================================
execute_python_file(filename = '_loop.py')