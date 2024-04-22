from pathlib import Path
import re
import numpy as np


class ReadOutcar:
    def __init__(self, path: Path | str):
        with open(Path(path), 'r') as f:
            self.outcar = f.read()
        self.incar_pattern = re.compile(r'INCAR:(.*?)POTCAR', re.DOTALL)
        self.e_fermi_p = re.compile(r'E-fermi\s*:\s*[-+]?[0-9]*\.?[0-9]+')
        self.energy_p = re.compile(r'energy\(sigma->0\) =\s+[-+]?\d*\.?\d+')
        self.free_energy_p = re.compile(r'free {2}energy {3}TOTEN {2}=\s+[-+]?\d*\.?\d+')
        self.NIONS = int(re.compile(r'NIONS\s+=\s+\d+').search(self.outcar).group().split('=')[1])
    @property
    def get_input(self) -> dict:
        """
        获取INCAR中的参数
        :return:
        """
        incar_lines = {}
        if ma := self.incar_pattern.search(self.outcar):
            for line in ma.group(1).strip().split('\n'):
                incar_lines[line.strip().split('=')[0].strip()] = line.strip().split('=')[1].split()[0]
        return incar_lines

    @property
    def energy_fermi(self):
        if ma := re.findall(self.e_fermi_p, self.outcar):
            return float(ma[-1].split(':')[1])
        return None

    @property
    def energy_free_list(self):

        energy_free = []
        if ma := re.findall(self.free_energy_p, self.outcar):
            for ml in ma:
                energy_free.append(float(ml.split('=')[1].strip()))
        # else: print('0')
        return energy_free

    @property
    def energy_list(self):
        energy_free = []
        if ma := re.findall(self.energy_p, self.outcar):

            for ml in ma:
                energy_free.append(float(ml.split('=')[1].strip()))
        # else: print('0')
        return energy_free

    @property
    def ionic_energy(self):
        return self.energy_list[-1]

    @property
    def ionic_energy_free(self):
        return self.energy_free_list[-1]

    def forces(self, all_f: bool | int = False, gpos: bool | int = False):
        pos = []
        all_forces = []
        pattern = re.compile(r'POSITION(.*?)total drift', re.DOTALL)
        for chuck in re.findall(pattern, self.outcar):
            lines = chuck.split('\n')[2:-2]
            scf_forces = []
            scf_pos = []
            for line in lines:
                scf_forces.append([float(x) for x in line.split()[3:]])
                scf_pos.append([float(x) for x in line.split()[0:3]])
            all_forces.append(scf_forces)
            pos.append(scf_pos)
        # return scf_forces
        if all_f:
            if gpos:
                return pos, all_forces
            else:
                return all_forces
        return all_forces[-1]

    @property
    def is_relaxed(self):
        return 'reached required accuracy' in self.outcar

    @property
    def is_converge(self):
        ediff = float(self.get_input.get('EDIFF', 1e-4))
        ibv = int(self.get_input.get('IBRION', 0))
        nsw = int(self.get_input.get('NSW', 0))

        # Optimization is converged , and some in other tasks
        if self.is_relaxed and ibv in [1, 2, 3] and nsw > 1:
            return True

        pattern = re.compile(r'total energy-change \(2\. order\) :(-?\d+\.\d+E[+-]\d+).*?(-?\d+\.\d+E[+-]\d+)',
                             re.DOTALL)
        matches = re.findall(pattern, self.outcar)

        # SCF is converged if the energy change is less than EDIFF
        if any(abs(float(m)) < ediff for m in matches[-1]):
            return True

        return False

    def get_force_rms(self):

        return

    @property
    def total_drift(self):

        return [sum(i) for i in zip(*self.forces())]

    @property
    def lattice_vec(self):
        la = re.compile(r'Lattice vectors:(.*?)Analysis', re.DOTALL).search(self.outcar)
        return {i.split('=')[0].strip(): list(map(float, i.split('=')[1].strip().strip('()').split(','))) for i
                in la.group(1).strip().split('\n')}


def get_sefA(path):
    outcar = ReadOutcar(path)
    lv = [v for _, v in outcar.lattice_vec.items()]
    return np.cross(lv[0], lv[1])

def sur_enrgy(slab_n, bulk_n, E_slab, E_bulk, A):
    return (E_slab - E_bulk * slab_n / bulk_n) / 2 / A


def main():
    # _, path = sys.argv
    # for ph in Path(path).glob('**/OUTCAR'):
        # oc = ReadOutcar(ph / 's')

    outcar = ReadOutcar(Path(r'D:\Documents\Code\vscode\python\小脚本\chem\multiwfn\OUTCAR'))
    # # print(outcar.forces()[-1])
    # lv = [v for _, v in outcar.lattice_vec.items()]
    # # print(np.cross(lv[0], lv[1]))
    # print(np.linalg.norm(np.cross(lv[0], lv[1])))
    print(outcar.NIONS)

#

if __name__ == "__main__":
    main()
