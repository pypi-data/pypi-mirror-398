from .core import *
from .ops import *
from subprocess import Popen, PIPE
from pathlib import Path


def run(cmd, **env):
    cmd = cmd.split(" ") if isinstance(cmd, str) else cmd
    p = Popen(cmd, cwd=str(Path(__file__).parent), env={**os.environ, **env})
    p.communicate()
    return p.returncode

def replace_in_file(file, old, new):
    with open(file, "r") as f:
        content = f.read()
    content = content.replace(old, new)
    with open(file, "w") as f:
        f.write(content)

def replace_var_in_file(filename, var, new, from_line=0, to_line=-1):
    with open(filename, 'r') as fr:
        init_list = fr.readlines()
    for idx, line in enumerate(init_list[from_line:to_line]):
        if "__version__" in line:
            new_line = f"""{var} = {new}\n"""
            init_list[idx] = new_line
            break
    with open(filename, 'w') as fw:
        fw.writelines(init_list)
