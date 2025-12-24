# VASProcar Copyright (C) 2023
# GNU GPL-3.0 license

inputs_types = ['dos','locpot','chgcar','spin','orbitals','location','bands', 'spin_video', 'fermi_surface']
inputs = []

# ------------------------------------------------------------------------------
# Checking if the "inputs" folder exists ---------------------------------------
# ------------------------------------------------------------------------------
if os.path.isdir(dir_files + '/inputs'):
    folder_input = 'yes'
else:
    folder_input = 'not'
# ----------------------

#------------------------------------------------ ------------------------------
# reading input files: ---------------------------------------------------------
#------------------------------------------------ ------------------------------

if (folder_input == 'yes'):
   for i in range(len(inputs_types)):
       try:
           f = open(dir_files + '/inputs/' + 'input.vasprocar.' + inputs_types[i])
           f.close()
           inputs.append(inputs_types[i])
       except:
           0 == 0
