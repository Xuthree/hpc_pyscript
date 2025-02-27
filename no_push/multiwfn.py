import subprocess
from subprocess import Popen
from pathlib import Path
import re
import os
import argparse
from enum import Enum
import shutil
import sys

MULTIWFN_PATH = Path('D:/Portable Program Files/Multiwfn')
SETTINGS = MULTIWFN_PATH / 'settings.ini'
VMD_SCRIPT = MULTIWFN_PATH / 'examples/scripts'
GRID_QUALITY = 2


class MultiwfnArgv(Enum):
    # GRID_QUALITY = set_grid()
    HOMO_LUMO_EXC = [200, 3, 'HOMO, LUMO', 2, 1]
    NCI_CAL = [20, 1, 2, 9, '0,0,0', '', '0.2']
    NCI_LOCAL = [13, 14, 1.3, 100, '{PART1}', '{PART2}', '0', '']
    ESP_PT = ['12', '3', '0.15', '0', '5', '{fname}.pdb', '6']
    IRI_CAL = [20, 4, 2]


class MultiwfnWrap:

    def __init__(self, file: str | Path, nthreads: int = -1, mode=None) -> None:
        self.file = Path(file)
        self.multiwfn = MULTIWFN_PATH / 'Multiwfn'

        self.nthreads = ['-nt', nthreads] if nthreads > 0 else []  # 默认使用settings中的nthreads数
        self.mode = ['-m', mode] if mode else []

        self.process = self._create
        self.stdin = self.process.stdin

    def __enter__(self):
        return self

    @property
    def _create(self) -> subprocess.Popen:
        os.chdir(self.file.parent)
        command_list = [self.multiwfn, self.file] + self.nthreads + ['-set', SETTINGS] + self.mode
        return Popen(command_list,
                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, text=True)

    def run(self, args=None):
        if args:
            for arg in args:
                self.stdin.write(str(arg) + '\n')
                # 添加进度条

            self.stdin.write('0\n')  # 命令执行完成回到主界面
        else:
            raise Exception('args not set or occurred error')

    def push(self, arg):
        self.process.stdin.write(arg + '\n')

    @staticmethod
    def unkown_err(log):
        if re.search('Unknown', log):
            return True
        else:
            return False

    def turnoff(self):
        self.stdin.write('q\n')
        # self.stdin.close()
        stdout, stderr = self.process.communicate()
        os.chdir(self.file.parent)
        with open(Path.cwd() / 'stdout.txt', 'w') as out:
            out.write(stdout)
        if self.unkown_err(stderr):
            print("Please check the stdout.txt and stderr.txt for more information")
            with open(Path.cwd() / 'stdout.txt', 'w') as out, open(Path.cwd() / 'stderr.txt', 'w') as err:
                out.write(stdout)
                err.write(stderr)
            print("Please check errors")
            print(stderr)
            raise Exception('Unkown Error in Multiwfn')

    def __exit__(self, exc_type, exc_value, traceback):
        if self.process and not self.process.poll():
            self.turnoff()


def get_orb(file, orb, grid=2):
    with MultiwfnWrap(file) as p:
        p.run([200, 3, f'{orb}', 2 ,1])
    shutil.copy(VMD_SCRIPT / 'showorb.vmd', Path.cwd() / 'orb.vmd')
# def to_gjf(mol_f):
#     mol_f = Path(mol_f)
#     with MultiwfnWrap(mol_f) as p:
#         p.run(['100', '2', '10', ''])

def to_file(in_f, out_f_t):

    infile = Path(in_f)
    with MultiwfnWrap(in_f) as p:
        p.run(['100', '2', '10', '\n', 'q\n'])
    # for out_f in out_f_t:
        # shutil.copy(Path.cwd() / 'output.fch', out_f)


if __name__ == '__main__':
    test()
