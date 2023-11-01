from pathlib import Path
import shutil
import subprocess
from subprocess import CompletedProcess
from typing import Any
import time
from gen_input import Genincar
from enum import Enum
class Glnum(Enum):
    w_v

def mk_floders(path) -> None:
    if path.exists():
        print(f"{path} floder is existed, skip it")
    else:
        path.mkdir(parents=True, exist_ok=True)
        print(f"{path} floder is created")


def copy_file(ph: Path, fl_name: str) -> None:
    if a := Path(ph, fl_name).is_file():  # 说明覆写已存在文件
        print(f"{a} is existed, it would be overwrite")
    shutil.copy(fl_name, ph)


def exc_com(ph: Path, command_s: str) -> CompletedProcess[str]:
    comand = [i for i in command_s.split()]
    excute_result = subprocess.run(comand,
                                   cwd=ph,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   text=True)
    return excute_result


def create_file(ph: Path, fl_name: str) -> Any:  # 利用vaspkit生成文件
    if fl_name == "KPOINTS":
        command_str = "vaspkit -task 102 -kps M 0.03"
        return exc_com(ph, command_str)

    if fl_name == "POTCAR":
        command_str = "vaspkit -task 103"
        return exc_com(ph, command_str)


def file_is(file_path: Path) -> bool:
    return file_path.exists() and file_path.stat().st_size != 0


def check_input_files():
    input_files = ("INCAR", "POTCAR", "KPOINTS", "POSCAR", "vasp_dcu.job")
    miss_meg = []

    for file in  input_files:
        file_ph = Path("./") / file
        if not file_is(file_ph):
            miss_meg.append(f"{file} 不存在或为空")

    if miss_meg:
        raise Exception("文件存在或为空：\n ".join(miss_meg))
    else:
        return True

incar = Genincar()
def gen_input_file(fld:Path, job_fld, ph:str='w_v') -> None:
    if ph == 'w_v':
        incar.add_pa(ivdw=12)
    with open("INCAR", "w") as f_in:
        f_in.write(str(incar))

    copy_file(fld / "POSCAR", f.name)
    shutil.copy(job_fld / "vasp_dcu.job", fld)

    for kp_pot in ('KPOINTS', 'POTCAR'):
        create_file(fld, kp_pot)

def from_txt_fld(ph: Path, fl_name: str, gen_num=1) -> None:
    for f in Path.cwd().iterdir():
        if f.is_file() and f.suffix == ".txt":
            mk_floders(Path('.' / f.stem / 'w_v'))



def main() -> None:
    vaspkit_gen = ("KPOINTS", "POTCAR")

    flod_names = ("n_v", "w_v")  # , "w_v_d")
    cwp = Path.cwd()
    home = Path.home()
    # 在当前目录里创建子路径
    incar = Genincar()
    for f in cwp.iterdir():
        if f.is_file() and f.suffix == ".txt":
            fld = Path(cwp / f.stem / "w_v")
            mk_floders(fld)

            incar.add_pa(ivdw=12)
            time.sleep(0.1)
            with open(fld / "INCAR", "w") as fin:
                fin.write(str(incar))

            copy_file(fld / "POSCAR", f.name)
            shutil.copy(home / "vasp_dcu.job", fld)

            time.sleep(0.1)
            for gen_fl in vaspkit_gen:
                create_file(fld, gen_fl)

            time.sleep(1)
            check_input_files(fld)
            result = exc_com(fld, "sbatch vasp_dcu.job")
            print(result.stderr, '\n', result.stdout)
            # try:
            #     in_fl = ("INCAR", "POTCAR", "KPOINTS", "POSCAR", "vasp_dcu.job"):
            #     if all(all(Path(file).is_file() and Path(file).stat().st_size > 0 for file in in_fl)):
            #         result = exc_com(fld, "sbatch vasp_dcu.job")
            #         print(result.stderr, '\n', result.stdout)
            # except:
            #     raise Exception()


if __name__ == '__main__':
    main()


