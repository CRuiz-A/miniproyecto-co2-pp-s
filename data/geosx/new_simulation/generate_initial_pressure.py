#!/usr/bin/env python3
"""Generate noisy initial pressure include file for PFLOTRAN."""
import numpy as np

NX, NY, NZ = 64, 28, 25
MEAN_PRESSURE = 100.0  # Bar
NOISE_STD = 5.0        # Bar (1-sigma)
LOWER_BOUND = 50.0
UPPER_BOUND = 150.0
OUTPUT_FILE = "initial_pressure.inc"
SEED = 42

rng = np.random.default_rng(SEED)
pressure = MEAN_PRESSURE + rng.normal(loc=0.0, scale=NOISE_STD, size=(NX, NY, NZ))
pressure = np.clip(pressure, LOWER_BOUND, UPPER_BOUND)

flattened = pressure.transpose(2, 1, 0).flatten(order='F')
with open(OUTPUT_FILE, 'w') as f:
    f.write("PRESSURE\n")
    for val in flattened:
        f.write(f" {val:.6e}\n")

print(f"Wrote {OUTPUT_FILE} with {flattened.size} values (mean={flattened.mean():.2f} Bar)")
