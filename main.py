from pathlib import Path
import shutil
import subprocess
from subprocess import CompletedProcess
from typing import Any, Union
import time
import sys
from gen_input import GenIncar
from enum import Enum
from read_outcar import ReadOutcar


class StrNumVdw(Enum):
    w_v = 1
    n_v = 0
    w_v_d = 2


def mk_floders(path) -> None:
    if path.exists():
        print(f"{path} floder is existed, skip it")
    else:
        path.mkdir(parents=True, exist_ok=True)
        print(f"{path} floder is created")


def copy_file(ph: Path, fl_name: Union[str, Path]) -> None:
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
        # return exc_com(ph, command_str)

    elif fl_name == "POTCAR":
        command_str = "vaspkit -task 103"
    else:
        raise Exception("尚未进行支持的输入文件")

    return exc_com(ph, command_str)


def file_is(file_path: Path) -> bool:
    return file_path.exists() and file_path.stat().st_size != 0


def check_input_files(fld):
    files = ("INCAR", "POTCAR", "KPOINTS", "POSCAR", "vasp_dcu.job")
    input_files = (Path(fld / i) for i in files)
    miss_meg = []

    for file in input_files:
        file_ph = Path("./") / file
        if not file_is(file_ph):
            miss_meg.append(f"{file} 不存在或为空")

    if miss_meg:
        raise Exception("文件存在或为空：\n ".join(miss_meg))

    return True


def mk_vdw_fld(gen_num: Union[int, list[int]]) -> list[str]:
    if isinstance(gen_num, list):
        fld_list = ""
        for i in gen_num:
            fld_list += StrNumVdw(i).name + " "
        return fld_list.strip().split(' ')

    return StrNumVdw(gen_num).name.split()


def parse_num(task_num):
    length = len(task_num)
    if length > 1:
        return [int(i) for i in task_num[-1:0:-1]]
    return int(task_num)


incar = Genincar()


def gen4txt(path: Path):
    """
    目录下存在txt格式的结构文件，创建同名文件夹，
    在同名目录下创建w_v文件夹，
    在w_v目录下创建vasp输入文件，并提交任务
    """
    fld_list: list[Path] = []
    for f in path.iterdir():
        if f.is_file() and f.suffix == ".txt":
            fld = Path(path / f.stem)
            mk_floders(fld)
            fld_list.append(fld)
            copy_file(fld / "POSCAR", f)
            fld_list += gen4pos(fld)
    return fld_list


def gen4pos(fld: Path, gen_num: Union[int, list[int]] = 1, job_fld=Path.home()):
    subflds = []
    for i in mk_vdw_fld(gen_num):
        subfld = Path(fld / i)
        vdw_name = StrNumVdw[str(subfld.as_posix()).split('/')[-1]].value
        if vdw_name == 1:
            incar.add_pa(ivdw=12)
        elif vdw_name == 3:
            incar.add_pa(ivdw=12, idipol=3, ldipol=True)
        else:
            pass

        mk_floders(subfld)
        with open(subfld / "INCAR", "w") as f_in:
            f_in.write(str(incar))

        copy_file(subfld, fld / Path("POSCAR"))
        shutil.copy(job_fld / "vasp_dcu.job", subfld)
        for kp_pot in ('KPOINTS', 'POTCAR'):
            create_file(subfld, kp_pot)
        print(f'input flies generate success in {subfld}')
        subflds.append(subfld)
    return subflds


def gen_scf(fld: Path = Path.cwd()) -> Path:
    scf_fld = Path(fld / 'scf')
    mk_floders(scf_fld)

    input_file = [Path(fld / i) for i in ['INCAR', 'KPOINTS', 'POTCAR', 'vasp_dcu.job']]
    for f in input_file:
        if not f.is_file():
            raise Exception(f"{f} 不存在")
        copy_file(scf_fld, f)

    if not (scf_fld / 'POSCAR').is_file():
        raise Exception("POSCAR 不存在")
    shutil.copy(fld / 'CONTCAR', scf_fld / 'POSCAR')

    scf_incar = Genincar(scf_fld / 'INCAR')
    scf_incar.add_pa(nsw=0)
    scf_incar.write2(scf_fld / 'INCAR')
    return scf_fld


# def plot_
def print_guides():
    print(
        """
            # 1. 运行脚本:python3 t.py cal_path task_type
            # 2. 三个参数,cal_path为计算路径,task_type为任务类型
            # 3. 任务类型:
            # # 1. gen4pos, 默认为11
            ### 10. gen4pos,n_v, 11. gen4pos,w_v, 12. gen4pos,w_v_d, 
            ### 101. gen4pos,w_v,n_v, 112. gen4pos,w_v_d, w_v, 102. gen4pos,w_v_d, n_v,
            ### 1012. gen4pos,w_v_d, w_v, n_v,
            # # 2. gen4txt, 
            # # 3. gen_scf
            # # 4. get_scf_energy, 
            ### 41. converge and eneger
        """
    )


def get_converge_and_energy(fld: Path):
    outcar = ReadOutcar(fld / 'OUTCAR')
    converge = outcar.is_converge
    energy = outcar.ionic_energy
    return converge, energy


def main() -> None:
    t1 = time.time()
    if len(sys.argv) > 3:
        print_guides()
    _, path, task = sys.argv  # [0], sys.argv[1], sys.argv

    path = Path(path)
    task = parse_num(task)
    fld = None
    if isinstance(task, list) or task == 1:
        fld = gen4pos(Path(path), task)
    elif task == 2:
        fld = gen4txt(Path(path))
    elif task == 3:
        fld = [gen_scf(Path(path))]
    elif task == 4:
        converge, energy = get_converge_and_energy(Path(path))
        print(f'task converge: {converge}, energy: {energy}')
    elif task == 41:
        cou = 1
        for fl in path.glob('**/OUTCAR'):
            if fl.exists() and fl.stat().st_size > 0:
                try:
                    converge, energy = get_converge_and_energy(fl.parent)
                except Exception as e:
                    print(f'>>>{e}<<< is loomed, maybe outcar have somethings wrong')
                    continue

                if converge:
                    print(cou)
                    print(f'>{fl.parent}<')
                    print(f'--->Get Converged: {converge}  |  Energy: {energy}')
                else:
                    print(f'{fl.parent} --->Get Converged: {converge} ')
                cou += 1

    if fld is not None:
        for fl in fld:
            try:
                if check_input_files(fl):
                    result = exc_com(fl, "sbatch vasp_dcu.job")
                    print_guides()
                    print(result.stderr, '\n', result.stdout)
            except Exception as e:
                print(e)
                continue
        t2 = time.time()
        print(f"总共花费{(t2 - t1):.9f}ns")


if __name__ == '__main__':
    main()
