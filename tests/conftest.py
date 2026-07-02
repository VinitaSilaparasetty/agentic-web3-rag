import os
import sys
from pathlib import Path

# Ensure the repo root is on sys.path so package imports resolve correctly
# when pytest is run from any working directory.
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Run tests from the repo root so relative data paths (data/consents.yaml etc.) resolve.
os.chdir(ROOT)
