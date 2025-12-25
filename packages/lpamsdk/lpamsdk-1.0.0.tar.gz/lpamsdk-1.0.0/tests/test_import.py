import os
import sys

# Change to the project directory to ensure proper path resolution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Attempting to import lpamsdk...")

try:
    import lpamsdk
    print("✓ Successfully imported lpamsdk")
except Exception as e:
    print(f"✗ Failed to import lpamsdk: {e}")
    import traceback
    traceback.print_exc()