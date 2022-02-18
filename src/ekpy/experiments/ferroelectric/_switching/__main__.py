from .._install import install
import argparse
from pathlib import Path

def install_interface():
    """ Installs Notebook """
    parser = argparse.ArgumentParser(description='Install Switching')
    parser.add_argument('--name', type=str,
                        help='Name of notebook to create', default='Switching.ipynb')
    return parser.parse_args()


if __name__ == "__main__":
	_dir = Path(__file__).resolve().parent # get location of this file after wheel installation

	args = install_interface()

	install(_dir=_dir,name=args.name)