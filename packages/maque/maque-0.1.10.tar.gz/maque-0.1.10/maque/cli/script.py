import os
from rich import print
import subprocess
from pathlib import Path


def source_and_run(filename):
    command = f'source {filename}; env'
    pipe = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable="/bin/bash")
    output = pipe.communicate()[0]
    env = dict((line.decode().split('=', 1) for line in output.splitlines()))
    os.environ.update(env)

def install_node_with_nvm(version='16'):
    args = (f"curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash &&"
            f"source ~/.nvm/nvm.sh &&"
            f"nvm install {version}")
    os.system(args)
    print("Install Node.js success, please exec command `nvm use {version}` to use Node.js v{version}")


def install_nvim(version="0.9.2"):
    nvim_dir = Path("~/software/nvim/")
    if not nvim_dir.exists():
        nvim_dir.mkdir(parents=True)

    args = (
            f"wget https://github.com/neovim/neovim/releases/download/v{version}/nvim.appimage &&"
            f"sudo mv nvim.appimage ~/software/nvim/ &&"
            f"chmod u+x ~/software/nvim/nvim.appimage &&"
            f"sudo ln -s ~/software/nvim/nvim.appimage /usr/local/bin/nvim &&"
            f"sudo ln -s ~/software/nvim/nvim.appimage /usr/bin/nvim" # If your system does not have FUSE you can extract the appimage: https://github.com/AppImage/AppImageKit/wiki/FUSE#install-fuse
            )
    os.system(args)
    print(f"Install neovim {version} success.")

def uninstall_nvim():
    args = (
        f"sudo rm -f /user/local/bin/nvim &&"
        f"sudo rm -f /user/bin/nvim &&"
        f"rm -f ~/software/nvim/nvim.appimage"
    )
    os.system(args)
    print("Uninstall neovim success.")


def install_make():
    os.system("sudo apt install build-essential")


def install_cargo():
    os.system("curl https://sh.rustup.rs -sSf | sh")
