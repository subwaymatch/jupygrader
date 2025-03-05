import os
from pathlib import Path

def test_get_cwd():
    print(os.getcwd())

    print(Path.cwd())
