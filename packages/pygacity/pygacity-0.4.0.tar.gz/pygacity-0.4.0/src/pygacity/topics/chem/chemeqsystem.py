import numpy as np
from scipy.optimize import fsolve
import roman
from ...util.texutils import *
from .reaction import Reaction

class ChemEqSystem:
    R = 8.314 # J/mol.K
    Pstdst = 1.0 # bar
    T0 = 298.15 # K
    def __init__(self, N0: dict[str, float] = {}, T: float = 298.15, P: float = 1.0, Reactions: list[Reaction]=[]):
        self.T = T
        self.P = P
        self.RT = self.R * self.T
        self.compounds = []
        self.N0 = np.array([])
        for c, n0 in N0.items():
            self.compounds.append(c)
            self.N0 = np.append(self.N0, n0)
        self.C = len(self.compounds)
        self.N = np.zeros(self.C)
        self.y = np.zeros(self.C)

        self.Reactions = Reactions
        self.M = len(Reactions)
        if self.M > 0:
            ''' Explicit reactions are specified; will use equilibrium constants
                and extents of reaction to solve '''
            self.nu = []
            self.dGr = np.array([])
            self.dHr = np.array([])
            self.dCp = np.array([])
            self.nu = np.zeros((self.M, self.C))
            for i, r in enumerate(Reactions):
                self.dGr = np.append(self.dGr, r.stoProps['G'])
                self.dHr = np.append(self.dHr, r.stoProps['H'])
                self.dCp = np.append(self.dCp, r.stoProps['Cp'])
                for c in self.compounds:
                    if c in r.Compounds:
                        ci = self.compounds.index(c)
                        nu = r.nu[r.Compounds.index(c)]
                        self.nu[i][ci] = nu
            self.Ka0 = np.exp(-self.dGr/(self.R*self.T0))
            self.KaT = self.Ka0 * np.exp(-self.dHr/self.R*(1/T-1/self.T0))
            # to do -- full van't hoff
            self.Xeq = np.zeros(self.M)
    
    def texgen_kacalculations(self, simplified=True, sig=5) -> str:
        ka_calcslines = []
        for i in range(self.M):
            rxn_super = ''
            if self.M > 1:
                ka_calcslines.append(rf'\underline{{Reaction {roman.toRoman(i+1)}}}\\')
                rxn_super = f'^{{{roman.toRoman(i+1)}}}'
            ka_calcslines.append(r'\begin{align*}')
            ka_calcslines.append(r'K_a'+rxn_super+r'(T_0) & = \exp\left[\frac{-\gr'+rxn_super+r'}{RT_0}\right] ')
            ka_calcslines.append(r' = \exp\left[\frac{' + f'-({self.dGr[i]:.0f})' + r'}{' + f'({self.R})({self.T0})' + r'}\right]')
            ka_calcslines.append(r' = ' + f'{format_sig(self.Ka0[i],sig)}' + r'\\')
            if simplified:
                ka_calcslines.append(r'K_a'+rxn_super+r'(T) & = K_a'+rxn_super+r'(T_0) \exp\left[\frac{-\hr'+rxn_super+r'}{R}\left(\frac{1}{T} - \frac{1}{T_0}\right)\right]\\')
                ka_calcslines.append((r'& = ' + f'({format_sig(self.Ka0[i],sig)})' + r'\exp\left[\frac{' + f'-({self.dHr[i]:.0f})' + r'}{'
                                    f'({self.R})' + r'}\left(\frac{1}{' + f'{self.T}' + r'} - \frac{1}{' + f'{self.T0}' + r'}\right)\right]\\'))
            ka_calcslines.append(r'& = ' + f'{format_sig(self.KaT[i],sig)}')
            ka_calcslines.append(r'\end{align*}')
        return '\n'.join(ka_calcslines)

    def report(self) -> str:
        result = ''
        if len(self.Reactions)>0:
            for i,(r,k,x) in enumerate(zip(self.Reactions,self.KaT,self.Xeq)):
                result += f'Reaction {roman.toRoman(i+1):>4s}:'
                result += str(r)
                result += f' Ka({self.T:.2f} K)={k:.5e} => Xeq={x:.5e}' 
                result += '\n'
        for i,(c,y) in enumerate(zip(self.compounds,self.ys)):
            result += f'y_{{{str(c)}}}={y:.4f}' 
            result += '\n'
        return result
    
    def stoichiometrictable_as_tex(self, float_format='{:.3f}'):
        total_row = ['Totals:']
        col1 = [c.as_tex() for c in self.compounds]
        fstr = float_format
        col2 = ['\('+fstr.format(n)+'\)' for n in self.N0] 
        total_row += ['\('+fstr.format(self.N0.sum())+'\)']
        tabledict = {'Species': col1, r'$N_{0,i}$': col2}
        tabledict[f'$N_{{i}}$'] = []
        Nus = [self.nu[j].sum() for j in range(self.M)]
        Nis = []
        for i,c in enumerate(self.compounds):
            Ni = fstr.format(self.N0[i])
            for j,r in enumerate(self.Reactions):
                nu_sign = [' + ' if self.nu[j][i]>=0 else ' - ' for i in range(self.C)]
                Xj = f'X_{{{roman.toRoman(j+1)}}}' if self.M>1 else 'X'
                Ni += f'{nu_sign[i]}\\left({np.fabs(self.nu[j][i]):.2f}\\right){Xj}'
            Nis.append(Ni)
            tabledict[f'$N_{{i}}$'].append('\('+Ni+'\)')
        Ni_total = fstr.format(self.N0.sum())
        for j in range(self.M):
            nu_sign = ' + ' if Nus[j]>=0 else ' - '
            Xj = f'X_{{{roman.toRoman(j+1)}}}' if self.M>1 else 'X'
            Ni_total += f'{nu_sign}\\left({np.fabs(Nus[j]):.2f}\\right){Xj}'
        total_row += ['\('+Ni_total+'\)']
        tabledict[f'$y_{{i}} = N_{{i}} / \sum_{{i}} N_{{i}}$'] = []
        for i in range(self.C):
            yi = r'\left[' + Nis[i] + r'\right] / \left[' + Ni_total + r'\right]'
            tabledict[f'$y_{{i}} = N_{{i}} / \sum_{{i}} N_{{i}}$'].append('\('+yi+'\)')
        total_row += ['\(1.0\)']
        return table_as_tex(tabledict, float_format=float_format, total_row=total_row, index=False)
    
    def thermochemicaltable_as_tex(self, float_format='\({:,.0f}\)'):
        return table_as_tex({
            'Species':[c.as_tex() for c in self.compounds],
            r'$\hf$ (J/mol)':[c.thermoChemicalData['H'] for c in self.compounds],
            r'$\gf$ (J/mol)':[c.thermoChemicalData['G'] for c in self.compounds]},
            drop_zeros=[False,True,True], float_format=float_format.format)
    
    def solve_implicit(self, Xinit=[], ideal=True):
        ''' Implicit solution of M equations using equilibrium constants '''
        def _NX(X):
            ''' Numbers of moles from extent of reaction '''
            return self.N0 + np.dot(X, self.nu)
        def _YX(X):
            ''' Mole fractions from numbers of moles '''
            n = _NX(X)
            return n / sum(n)
        def f_func(X):
            ''' equality of given and apparent equilibrium constants '''
            y = _YX(X)
            phi = np.ones(self.C)
            if not ideal:
                pass
                # to do -- fugacity coefficient calculation
            Ka_app = [np.prod(y**nu_j)*np.prod(phi**nu_j)*(self.P/self.Pstdst)**sum(nu_j) for nu_j in self.nu]
            # print(y,Ka_app)
            return np.array([(kk-ka)/(kk+ka) for kk,ka in zip(Ka_app,self.KaT)])
        self.Xeq = fsolve(f_func, Xinit)
        self.N = _NX(self.Xeq)
        self.ys = _YX(self.Xeq)

    def solve_lagrange(self, ideal=True, zInit=[]):
        atomset = set()
        for c in self.compounds:
            atomset.update(c.atomset)
            c.computeGoT(self.T)
        self.atomlist = list(atomset)
        self.E = len(self.atomlist)
        self.A = np.zeros(self.E)
        for i in range(self.C):
            # compute total moles N by summing over mole numbers; 
            for k in range(self.E):
                # compute constant number of atom-moles, A[]
                self.A[k] += self.N0[i] * self.compounds[i].countAtoms(self.atomlist[k])
        def f_func(z):
            F = np.zeros(self.C + self.E)
            N = 0.0
            for i in range(self.C):
                # compute total moles N by summing over mole numbers; 
                N += z[i]
            # stub:  phi values are all ones
            phi = np.ones(self.C)
            for i in range(self.C):
                # Computed Gibbs energy for each molecular species...
                dGfoT = self.compounds[i].thermoChemicalData['GoT']
                F[i] = dGfoT/self.RT + np.log(z[i]/N * phi[i] * self.P/self.Pstdst)
                for k in range(self.E):
                    # sum up Lagrange multiplier terms from each atom-balance
                    F[i] += z[self.C+k]/self.RT * self.compounds[i].countAtoms(self.atomlist[k])
                    # sum up each atom balance
                    F[k+self.C] += z[i] * self.compounds[i].countAtoms(self.atomlist[k])
            for k in range(self.E):
                # close each atom balance
                F[k+self.C] -= self.A[k]
            return F
        zGuess = zInit
        if len(zGuess) == 0:
            zGuess = np.array([0.1]*self.C + [1000.]*self.E)
            z = fsolve(f_func, zGuess)
        self.N = z[:self.C]
        self.ys = self.N / sum(self.N)

if __name__=='__main__':
    from .properties import PureProperties
    from .reaction import Reaction
    Prop = PureProperties()
    my_compounds =  {
        'A':Prop.get_compound('hydrogen (equilib)'),
        'B':Prop.get_compound('oxygen'),
        'C':Prop.get_compound('water'),
        'D':Prop.get_compound('nitrogen'),
        'E':Prop.get_compound('ammonia'),
        'F':Prop.get_compound('argon')
    }
    # solving a chemical equilibrium problem, no reactions specified
    N0 = {my_compounds['A']:4., my_compounds['D']:1., my_compounds['E']:0.}
    Eq = ChemEqSystem(N0=N0, T=500, P=15)
    Eq.solve_lagrange()

    # specifying reactions, just for output
    R = Reaction(R=[my_compounds['A'], my_compounds['D']], P=[my_compounds['E']], nosums=True)
    print(R.as_tex())