#!/usr/bin/env python3
"""Detailed timing test including module imports."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Time module imports
print("=" * 60)
print("DETAILED TIMING TEST")
print("=" * 60)

t0 = time.time()
print("Importing panel.serve...")
from panel.serve import process_lxf_upload
t_import = time.time() - t0
print(f"✓ Panel.serve imported in {t_import:.2f}s\n")

# Clear database
from database import clear_fed_tables
clear_fed_tables()

# Test upload via process_lxf_upload
test_file = "data/antalya_millitakim_secme_sonuc.lxf"

print(f"Processing {test_file}...")
t0 = time.time()
result = process_lxf_upload(test_file, race_leg='antalya')
t_total = time.time() - t0

print(f"\nResult: {result['message']}")
print(f"\n✓ Total process_lxf_upload: {t_total:.2f}s")
print("=" * 60)
