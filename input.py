from pathlib import Path
import shutil
import subprocess
from subprocess import CompletedProcess
from typing import Any
import time


class Genincar:
    p = {  # dictionary to hold the routine parameters of incar file
        'str_keys': {
            'system',  # name
            'algo',  # algorithm: Normal (Davidson) | Fast | Very_Fast (RMM-DIIS)},
            'prec',  # Precission grid of calculation (Low, Normal, Accurate)},
        },
        'float_keys': {
            'encut',  # Planewave cutoff
            'sigma',  # Broadening for SCF
        },

        'int_keys': {
            'ispin',  # Spin polarization
            'ibrion',  # ionic relaxation: 0-MD 1-quasi-New 2-CG
            'icharge',  # charge: 0-WAVECAR 1-CHGCAR 2-atom 10-const
            'isif',  # calculate stress and what to relax
            'ivdw',  # Choose which dispersion correction method to use
            'ismear',  # part. occupancies: -5 Blochl -4-tet -1-fermi 0-gaus >0 MP
            'ispin',  # spin-polarized calculation
            'istart',  # startjob: 0-new 1-cont 2-samecut
            'nsw',  # number of steps for ionic relaxation
            'nelm',  # Maximum number of electronic steps
        },

        'bool_keys': {
            'lcharg',  # .true. to calculate charge density
            'lwave',  # .true. to write WAVECAR
        },

        'exp_keys': {
            'ediff',  # stopping-criterion for electronic upd.
            'ediffg',  # stopping-criterion for ionic upd.
        },
        'special_keys': {
            'lreal',  # non-local projectors in real space
        }
    }

    default_incar_params = {
        'istart': 0,
        'ispin': 1,
        'icharge': 2,
        'lreal': 'Auto',
        'encut': 400,
        'prec': 'Normal',
        'algo': 'Fast',
        'lcharg': False,
        'lwave': False,
        'ismear': 0,  # Gaussian smearing
        'sigma': 0.05,
        'ediff': 1e-5,
        'ediffg': -2e-2,
        'nsw': 400,
        'isif': 2,
        'ibrion': 2,
    }

    def __init__(self, param_dict: dict = None, **kwargs):
        if param_dict is None:
            self.params = self.default_incar_params
        else:
            self.params = param_dict

        for key, value in kwargs.items():
            self.params[key] = value

    def _convert(self, key, value):
        if key in self.p['float_keys']:
            val = f'{float(value)}'
        elif key in self.p['int_keys']:
            val = f'{int(value)}'
        elif key in self.p['bool_keys']:
            val = f'.{bool(value)}.'
        elif key in self.p['str_keys']:
            val = str(value)
        elif key in self.p['exp_keys']:
            val = f'{value:5.2e}'
        elif key in self.p['special_keys']:
            if isinstance(value, bool):
                val = f'.{value}.'
            else:
                val = str(value)
        else:
            raise Exception(f'{key} is not a valid key')
        return val

    def add_pa(self, **kwargs):
        all_pa = [i for value in self.p.values() for i in value]
        for key in kwargs:
            if key in all_pa:
                self.params[key] = kwargs[key]
            else:
                raise Exception(f'{key} parameter is not defined')

    def _get_params(self):
        params = {key.upper(): self._convert(key, self.params[key])
                  for key, value in self.params.items()}
        return params

    def __str__(self) -> str:
        incar_dict = self._get_params()
        key_value = [f'{k} = {v}' for k, v in incar_dict.items()]
        return 'Globle Parameters\n' + '\n'.join(key_value)


def mk_floders(path) -> None:
    if path.exists():
        print(f"{path} floder is existed, skip it")
    else:
        path.mkdir(parents=True, exist_ok=True)
        print(f"{path} floder is created")


def copy_file(ph: Path, fl_name: str) -> None:
    if Path(ph, fl_name).is_file():  # 说明覆写已存在文件
        print(f"{fl_name} is existed, it would be overwrite")
    shutil.copy(fl_name, ph)


def exc_com(ph: Path, command_s: str) -> CompletedProcess[str]:
    command = [i for i in command_s.split()]
    execute_result = subprocess.run(command,
                                   cwd=ph,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   text=True)
    return execute_result


def create_file(ph: Path, fl_name: str) -> Any:  # 利用vaspkit生成文件
    if fl_name == "KPOINTS":
        command_str = "vaspkit -task 102 -kps M 0.03"
        return exc_com(ph, command_str)

    if fl_name == "POTCAR":
        command_str = "vaspkit -task 103"
        return exc_com(ph, command_str)


def file_is(file_path: Path) -> bool:
    return file_path.exists() and file_path.stat().st_size != 0


def check_input_files(ph: Path = Path('./')):
    input_files = ("INCAR", "POTCAR", "KPOINTS", "POSCAR", "vasp_dcu.job")
    for f in input_files:
        if not file_is(ph / f):
            raise Exception(f"{f} is not found in {ph}")


# def cal_config():


def task1():
    pass


def task2():
    pass


def main() -> None:
    vaspkit_gen = ("KPOINTS", "POTCAR")
    flod_names = ("n_v", "w_v")  # , "w_v_d")
    cwp = Path.cwd() ## 当前目录
    home = Path.home() ## vasp_dcu.job 所在目录

    incar = Genincar() # 根据默认参数生成 INCAR 文件

    # 根据当前目录下的txt（other）文件创建目录生成器
    txt_fld = (txt_f.stem for txt_f in cwp.iterdir() if txt_f.is_file() and txt_f.suffix =='.py')

    folders = (Path(cwp, tf, tpf) for tpf in flod_names for tf in txt_fld)

    for fld in folders:
        mk_floders(fld)

        incar.add_pa(ivdw=12)
        time.sleep(0.1)
        with open(fld / "INCAR", "w") as incar_f:
            incar_f.write(str(incar))

        copy_file(fld / "POSCAR", f.name)
        shutil.copy(home / "vasp_dcu.job", fld)

        time.sleep(0.1)
        for gen_fl in vaspkit_gen:
            create_file(fld, gen_fl)

        time.sleep(1)
        check_input_files(fld)
        result = exc_com(fld, 'sbatch vasp_dcu.job')
        print(result.stderr, '\n', result.stdout)


if __name__ == '__main__':
    main()
