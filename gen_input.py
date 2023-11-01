# from collections import defaultdict
from typing import Optional


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

    def __init__(self, param_dict: Optional[dict] = None, **kwargs):
        # param_dict = dict(param_dict)
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
            val = f'{(value):5.2e}'
        elif key in self.p['special_keys']:
            if isinstance(value, bool):
                val = f'.{value}.'
            else:
                val = str(value)
        else:
            raise Exception(f'{key} is not a valid key')
        return val

    def add_pa(self, **kwargs):
        all_pa = (i for value in self.p.values() for i in value)
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