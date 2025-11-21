import numpy as np

def convert_npy_to_inc_correct_order(npy_file_path, inc_file_path, convert_perm_to_mD=False):
    """Genera archivo .inc con orden X-Y-Z (Fortran column-major)"""
    data = np.load(npy_file_path)
    
    if data.ndim == 4:
        data_3d = data[:, :, :, 0]
    else:
        data_3d = data

    # INVERTIR EL EJE Z 
    data_3d = data_3d[::-1, :, :]  # Shape: (nz, ny, nx)
    print(f"  ✓ Eje Z invertido: capa 1 <-> capa {data_3d.shape[0]}")

    # TRANSPONER para orden X-Y-Z (PFLOTRAN espera Fortran column-major)
    # De (nz, ny, nx) a (nx, ny, nz) y luego flatten
    data_3d_transposed = data_3d.transpose(2, 1, 0)  # (nx, ny, nz)
    print(f"  ✓ Transpuesto: (nz,ny,nx) -> (nx,ny,nz) para orden X-Y-Z")
    
    # Flatten en orden Fortran (column-major): x más lento, y medio, z más rápido
    flattened_data = data_3d_transposed.flatten(order='F')  # X-Y-Z order
    print(f"  ✓ Aplanado en orden Fortran (X-Y-Z)")

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
    print(f"  Shape original: {data_3d.shape}, Shape transpuesto: {data_3d_transposed.shape}")

print("\n=== Regenerando archivos .inc con orden X-Y-Z correcto ===\n")
print("1. Permeabilidad (Z invertido, orden X-Y-Z, PERMX/Y/Z):")
convert_npy_to_inc_correct_order('/home/spell/Desktop/reservorio_forzado/geosx/permeability.npy', 
                                  'permeability.inc', convert_perm_to_mD=True)

print("\n2. Porosidad (Z invertido, orden X-Y-Z):")
convert_npy_to_inc_correct_order('/home/spell/Desktop/reservorio_forzado/geosx/porosity.npy', 
                                  'porosity.inc', convert_perm_to_mD=False)

print("\n✓ Archivos regenerados con orden X-Y-Z correcto!")


