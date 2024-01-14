from pathlib import Path
import re


class Outcarinfo:
    def __init__(self, path: Path | str):
        with open(Path(path), 'r') as f:
            self.outcar = f.read()

    @property
    def get_input(self):
        incar_lines = {}
        incar_pattern = re.compile(r'INCAR:(.*?)POTCAR', re.DOTALL)
        if ma := incar_pattern.search(self.outcar):
            for line in ma.group(1).strip().split('\n'):
                incar_lines[line.strip().split('=')[0].strip()] = line.strip().split('=')[1].split()[0]
        return incar_lines

    @property
    def energy_fermi(self):
        if ma := re.findall(r'E-fermi\s*:\s*[-+]?[0-9]*\.?[0-9]+', self.outcar):
            return float(ma[-1].split(':')[1])
        return None

    @property
    def energy_free_list(self):
        free_energy = r'free  energy   TOTEN  =\s+[-+]?\d*\.?\d+'
        energy_free = []
        if ma := re.findall(free_energy, self.outcar):
            for ml in ma:
                energy_free.append(float(ml.split('=')[1].strip()))
        # else: print('0')
        return energy_free

    @property
    def energy_no_list(self):
        free_energy = r'energy  without entropy=\s+[-+]?\d*\.?\d+'
        energy_free = []
        if ma := re.findall(free_energy, self.outcar):
            for ml in ma:
                energy_free.append(float(ml.split('=')[1].strip()))
        # else: print('0')
        return energy_free

    @property
    def ionic_energy(self):
        return self.energy_no_list[-1]

    @property
    def ionic_energy_free(self):
        return self.energy_free_list[-1]

    @property
    def stest(self):
        pattern = re.compile(r'total energy-change \(2\. order\) :(-?\d+\.\d+E[+-]\d+).*?(-?\d+\.\d+E[+-]\d+)',
                             re.DOTALL)
        matches = re.search(pattern, self.outcar)
        if matches:
            print(matches.groups())
            return float(matches.group(1)), float(matches.group(2))

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
        ediff = float(self.get_input.get('EDIFF'))
        ibv = int(self.get_input.get('IBRION'))
        nsw = int(self.get_input.get('NSW'))

        # Optimization is converged , and some in other tasks
        if self.is_relaxed and ibv in [1, 2, 3] and nsw > 1:
            return True

        pattern = re.compile(r'total energy-change \(2\. order\) :(-?\d+\.\d+E[+-]\d+).*?(-?\d+\.\d+E[+-]\d+)',
                             re.DOTALL)
        matches = re.findall(pattern, self.outcar)[-1]

        # SCF is converged if the energy change is less than EDIFF
        if any(abs(float(m)) < ediff for m in matches):
            return True

        return False

    def get_force_rms(self):

        return

    @property
    def total_drift(self):

        return [sum(i) for i in zip(*self.forces())]


def main():
    outcar_file_path = Path(r'D:\Documents\Code\vscode\python\小脚本\chem\multiwfn\OUTCAR')
    outcar = Outcarinfo(outcar_file_path)
    print(outcar.forces()[-1])
    print(outcar.total_drift)


if __name__ == "__main__":
    main()
