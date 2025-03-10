# with open(r'D:\Desktop\temp\CONTCAR (1)', 'r') as f1:
#     pos_file = f1.read()
# from itertools import product

atno2element={1:"H",2:"He",3:"Li",4:"Be",5:"B",6:"C",7:"N",8:"O",9:"F",10:"Ne",11:"Na",12:"Mg",13:"Al",14:"Si", \
                 15:"P",16:"S",17:"Cl",18:"Ar",19:"K",20:"Ca",21:"Sc",22:"Ti",23:"V",24:"Cr",25:"Mn",26:"Fe",27:"Co", \
                 28:"Ni",29:"Cu",30:"Zn",31:"Ga",32:"Ge",33:"As",34:"Se",35:"Br",36:"Kr",37:"Rb",38:"Sr",39:"Y", \
                 40:"Zr",41:"Nb",42:"Mo",43:"Tc",44:"Ru",45:"Rh",46:"Pd",47:"Ag",48:"Cd",49:"In",50:"Sn",51:"Sb", \
                 52:"Te",53:"I",54:"Xe",55:"Cs",56:"Ba",57:"La",58:"Ce",59:"Pr",60:"Nd",61:"Pm",62:"Sm",63:"Eu", \
                 64:"Gd",65:"Tb",66:"Dy",67:"Ho",68:"Er",69:"Tm",70:"Yb",71:"Lu",72:"Hf",73:"Ta",74:"W",75:"Re", \
                 77:"Ir",78:"Pt",79:"Au",82:"Pb",179:"Au",100:"XX"
                 }
elem2mass = {
        "H": 1.00794, "He": 4.002602, "Li": 6.938, "Be": 9.012182, "B": 10.81, "C": 12.011, "N": 14.007, "O": 15.999, "F": 18.9984032, "Ne": 20.1797, \
        "Na": 22.98976928, "Mg": 24.305, "Al": 26.9815386, "Si": 28.085, "P": 30.973762, "S": 32.06, "Cl": 35.45, "Ar": 39.948, \
        "K": 39.0983, "Ca": 40.078, "Sc": 44.955912, "Ti": 47.867, "V": 50.9415, "Cr": 51.9961, "Mn": 54.938045, "Fe": 55.845, "Co": 58.933195, "Ni": 58.6934, "Cu": 63.546, "Zn": 65.38, "Ga": 69.723, "Ge": 72.63, "As": 74.92160, "Se": 78.96, "Br":79.904, "Kr":\
}
class ReadPOS:
    def __init__(self, path) -> None:
        with open(path, 'r') as f:
            self.lines = f.readlines()
        self.comment = self.lines[0].strip()
        self.CoodSsys = self.lines[8]
        self.scale = float(self.lines[1].strip())
        self.symbol = self.lines[5].split()
        self.atom_num = sum(int(i) for i in self.lines[6].split())
        # self.constrain = self.atom_pos_con

    def element_line(self):
        element_line = 5
        try:
            # 尝试将第六行转换为整数，如果成功，则没有元素种类行
            element_counts = list(map(int, self.lines[element_line].split()))
            elements = None
        except ValueError:
            # 第六行不是纯数字，所以它包含元素种类
            elements = self.lines[element_line].split()
            element_counts = list(map(int, self.lines[element_line + 1].split()))
            element_line += 1

    @property
    def lattice(self):
        return [list(map(float, v.split())) for v in self.lines[2:5]]

    @property
    def atom_pos_con(self):
        cons = []
        for i in range(9, 9 + self.atom_num):
            cons.append(self.lines[i].split()[3:6])
        return cons

    @property
    def atom_pos(self):
        pos = []
        for i, line in enumerate(self.lines):
            if i < 9:
                continue
            if line.strip() == '':
                break
            pos.append([float(p) for p in line.strip('\n').split()[:3]])
        if len(pos) != self.atom_num:
            raise Exception('pos num not match')
        return pos

    def set_constrain(self, atom_order, relax: int | bool = True, direct='xyz'):

        con = ['T', 'T', 'T']

        if len(list(direct)) != 3:  #
            print(direct.split())
            raise Exception("direction must be xyz")
        if not bool(relax):
            con = ['F', 'F', 'F']
        if len(self.atom_pos_con) == 0:
            self.constrain = [con for _ in range(self.atom_num)]
        self.constrain[atom_order] = con

    def __str__(self):
        pos_con = []
        for i, j in zip(self.atom_pos, self.constrain):
            pos_con.append(str('{:.17f}  ' * 3).format(*i) + '   ' + '  '.join(j))
        return '\n'.join(pos_con)

    def __repr__(self) -> str:
        return self.__str__()


pos = ReadPOS(r'D:\Desktop\temp\POSCAR')
print(pos.scale)
