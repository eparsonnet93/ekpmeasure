from ._install import install
import argparse

def install_interface():
    """ Installs Seeq Add-on Tool """
    parser = argparse.ArgumentParser(description='Install Relaxation')
    parser.add_argument('--name', type=str,
                        help='Name of notebook to create', default='Relaxation.ipynb')
    return parser.parse_args()


if __name__ == "__main__":

	args = install_interface()

	install(name=args.name)