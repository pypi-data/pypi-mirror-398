import ase
from ase.build import surface
from ase.io import read

file_path = 'POSCAR_SiO2_Bulk'
n_layers = 2
direction = [-1, 0, -1]
vacuum = 15

def build_nlayer(poscar_file, n_layers, direction, vacuum):
    str_dir = ''
    for i in direction: str_dir += str(i)
    formula = poscar_file.get_chemical_formula()    
    ### Generate the surfaces

    surface = ase.build.surface(poscar_file,direction,n_layers,vacuum=vacuum)
    ase.io.vasp.write_vasp(f'POSCAR_{formula}_{str_dir}_{n_layers}layers.vasp',surface,direct=False,sort=True)

poscar = read(file_path)

build_nlayer(poscar, n_layers, direction, vacuum)

