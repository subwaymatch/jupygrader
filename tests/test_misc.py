import os
from pathlib import Path

def test_get_cwd():
    print(f'os.getcwd={os.getcwd()}')

    print(f'Path.cwd()={Path.cwd()}')
