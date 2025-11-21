import numpy as np

def convert_npy_to_inc_full(npy_file_path, inc_file_path, convert_perm_to_mD=False):
    """Genera archivo .inc con PERMX, PERMY, PERMZ (o solo PORO)"""
    data = np.load(npy_file_path)
    
    if data.ndim == 4:
        data_3d = data[:, :, :, 0]
    else:
        data_3d = data

    # INVERTIR EL EJE Z 
    data_3d = data_3d[::-1, :, :]
    print(f"  ✓ Eje Z invertido: capa 1 <-> capa {data_3d.shape[0]}")

    flattened_data = data_3d.flatten()

    if convert_perm_to_mD:
        conversion_factor = 1.0 / 9.869233e-16
        flattened_data = flattened_data * conversion_factor
        print("  ✓ Convertido de m^2 a mD")

    with open(inc_file_path, 'w') as f:
        if convert_perm_to_mD:
            # Escribir PERMX, PERMY, PERMZ con los mismos valores (isotrópico)
            for keyword in ['PERMX', 'PERMY', 'PERMZ']:
                f.write(f"{keyword}\n")
                for i, val in enumerate(flattened_data):
                    f.write(f"   {val:1.6e}")
                    if (i + 1) % 5 == 0:
                        f.write("\n")
                if (i + 1) % 5 != 0:
                    f.write("\n")
                f.write("/\n")
                if keyword != 'PERMZ':
                    f.write("\n")
        else:
            # Solo PORO
            f.write("PORO\n")
            for i, val in enumerate(flattened_data):
                f.write(f"   {val:1.6e}")
                if (i + 1) % 5 == 0:
                    f.write("\n")
            if (i + 1) % 5 != 0:
                f.write("\n")
            f.write("/\n")
    
    print(f"  ✓ Escrito: {inc_file_path}")
    print(f"  Total valores: {len(flattened_data)}")
    print(f"  Shape: {data_3d.shape}")

print("\n=== Regenerando archivos .inc con PERMX, PERMY, PERMZ ===\n")
print("1. Permeabilidad (con Z invertido y PERMX/Y/Z):")
convert_npy_to_inc_full('/home/spell/Desktop/reservorio_forzado/geosx/permeability.npy', 
                        'permeability.inc', convert_perm_to_mD=True)

print("\n2. Porosidad (con Z invertido):")
convert_npy_to_inc_full('/home/spell/Desktop/reservorio_forzado/geosx/porosity.npy', 
                        'porosity.inc', convert_perm_to_mD=False)

print("\n✓ Archivos regenerados correctamente!")


