import os
import sys
from pathlib import Path

path = Path(os.path.dirname(os.path.realpath(__file__)))

sys.path.append(os.path.abspath(path.parent.absolute()))
sys.path.append(os.path.abspath(path.parent.absolute().joinpath("src")))
