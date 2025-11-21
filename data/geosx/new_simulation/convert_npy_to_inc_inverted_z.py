import numpy as np

def convert_npy_to_inc(npy_file_path, inc_file_path, keyword, convert_perm_to_mD=False):
    data = np.load(npy_file_path)
    
    if data.ndim == 4:
        data_3d = data[:, :, :, 0]
    else:
        data_3d = data

    # INVERTIR EL EJE Z (nz, ny, nx) -> invertir primera dimensión
    data_3d = data_3d[::-1, :, :]
    print(f"  ✓ Eje Z invertido: capa 1 <-> capa {data_3d.shape[0]}")

    flattened_data = data_3d.flatten()

    if convert_perm_to_mD:
        conversion_factor = 1.0 / 9.869233e-16
        flattened_data = flattened_data * conversion_factor
        print("  ✓ Convertido de m^2 a mD")

    with open(inc_file_path, 'w') as f:
        f.write(f"{keyword}\n")
        for i, val in enumerate(flattened_data):
            f.write(f"   {val:1.6e}")
            if (i + 1) % 5 == 0:
                f.write("\n")
        if (i + 1) % 5 != 0:
            f.write("\n")
        f.write("/\n")
    
    print(f"  ✓ Escrito: {inc_file_path}")
    print(f"  Total valores: {len(flattened_data)}")
    print(f"  Shape final: {data_3d.shape}")

# Regenerar los archivos con Z invertido
print("\nRegenerando archivos .inc con eje Z invertido...")
print("\n1. Permeabilidad:")
convert_npy_to_inc('/home/spell/Desktop/reservorio_forzado/geosx/permeability.npy', 
                   'permeability.inc', 'PERMX', convert_perm_to_mD=True)

print("\n2. Porosidad:")
convert_npy_to_inc('/home/spell/Desktop/reservorio_forzado/geosx/porosity.npy', 
                   'porosity.inc', 'PORO')

print("\n✓ Archivos regenerados con eje Z invertido!")


