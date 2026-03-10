"""
Copy 2035 network to validation tool expected location.
"""

import shutil
from pathlib import Path

BASE = Path(__file__).parent.parent
SOURCE = BASE / 'data' / 'networks' / '2035' / 'baseline'
TARGET = Path(r"C:\Users\Public\Documents\Thesis\analysis\dispatch_data\cases\reference\2035\jul_2035")

print("="*80)
print("PREPARING 2035 NETWORK FOR VALIDATION")
print("="*80)

print(f"\nSource: {SOURCE}")
print(f"Target: {TARGET}")

TARGET.parent.mkdir(parents=True, exist_ok=True)

if TARGET.exists():
    print("\nRemoving existing 2035 network...")
    shutil.rmtree(TARGET)

print("\nCopying network...")
shutil.copytree(SOURCE, TARGET)

print("\nOK - Network copied and ready for validation")
print("="*80)