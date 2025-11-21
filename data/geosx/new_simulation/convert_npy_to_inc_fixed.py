#!/usr/bin/env python3
"""
Script to convert numpy arrays (.npy) to PFLOTRAN-compatible .inc files
WITH CORRECT UNIT CONVERSION
"""

import numpy as np
import sys
import os

def convert_npy_to_inc(npy_file, inc_file, property_name, nx, ny, nz, component_idx=0):
    """
    Convert a numpy array to PFLOTRAN .inc format
    
    Parameters:
    -----------
    npy_file : str
        Path to input .npy file
    inc_file : str
        Path to output .inc file
    property_name : str
        Name of the property (e.g., 'PERMX', 'PORO')
    nx, ny, nz : int
        Grid dimensions
    component_idx : int
        Index of component to use if array is 4D (default: 0)
    """
    # Load the numpy array
    data = np.load(npy_file)
    
    print(f"Loaded {npy_file}")
    print(f"  Original shape: {data.shape}")
    print(f"  Data type: {data.dtype}")
    print(f"  Min value: {data.min():.6e}")
    print(f"  Max value: {data.max():.6e}")
    
    # Handle 4D arrays - take the specified component
    if len(data.shape) == 4:
        print(f"  4D array detected, using component {component_idx}")
        data = data[:, :, :, component_idx]
    
    # Reshape if necessary
    if data.shape != (nz, ny, nx):
        print(f"  Reshaping from {data.shape} to ({nz}, {ny}, {nx})")
        if data.size == nx * ny * nz:
            data = data.reshape(nz, ny, nx)
        else:
            raise ValueError(f"Cannot reshape {data.shape} to ({nz}, {ny}, {nx})")
    
    # Write to .inc file
    with open(inc_file, 'w') as f:
        # Write property name header
        f.write(f"{property_name}\n")
        
        # Write data in Fortran order (z, y, x)
        values_per_line = 5  # Standard format: 5 values per line
        count = 0
        
        for z in range(nz):
            for y in range(ny):
                for x in range(nx):
                    value = data[z, y, x]
                    
                    # Format based on property type
                    if property_name.startswith('PERM'):
                        # Permeability: convert from m^2 to mD
                        # 1 mD = 9.869233e-16 m^2
                        value_mD = value / 9.869233e-16
                        f.write(f"   {value_mD:.6f}")
                    else:
                        # Porosity (dimensionless)
                        f.write(f"   {value:.6f}")
                    
                    count += 1
                    
                    # New line every 5 values
                    if count % values_per_line == 0:
                        f.write("\n")
        
        # Add final newline if needed
        if count % values_per_line != 0:
            f.write("\n")
    
    print(f"  Written {inc_file}")
    print(f"  Total values written: {count}")
    if property_name.startswith('PERM'):
        print(f"  Converted from m^2 to mD")
    print(f"  Final shape: ({nz}, {ny}, {nx})")
    print()

if __name__ == "__main__":
    # Grid dimensions
    nx = 64
    ny = 28
    nz = 25
    
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    npy_dir = os.path.join(base_dir, 'geosx')
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    perm_npy = os.path.join(npy_dir, 'permeability.npy')
    poro_npy = os.path.join(npy_dir, 'porosity.npy')
    
    perm_inc = os.path.join(output_dir, 'permeability.inc')
    poro_inc = os.path.join(output_dir, 'porosity.inc')
    
    # Convert permeability
    print("Converting permeability (m^2 to mD)...")
    convert_npy_to_inc(perm_npy, perm_inc, 'PERMX', nx, ny, nz, component_idx=0)
    
    # Convert porosity
    print("Converting porosity...")
    convert_npy_to_inc(poro_npy, poro_inc, 'PORO', nx, ny, nz, component_idx=0)
    
    print("Conversion complete!")
    print(f"\nGrid dimensions: nx={nx}, ny={ny}, nz={nz}")
    print(f"Total grid cells: {nx * ny * nz}")


