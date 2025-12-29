import numpy as np
import fractions as fr
from scipy.linalg import null_space
class Reaction:
    ''' simple class for describing and balancing chemical reactions
    
        a Reaction() instance must be initialized with a list of reactant Compound()'s 
        and a list of product Compound()'s.  scipy.linalg.null_space is used on the
        matrix of elements by compounds (with negative counts for reactants) to determine
        the balancing list of stoichiometric coefficients, stored in nu.

        Cameron F. Abrams cfa22@drexel.edu
     '''
    def __init__(self,R=[],P=[],nosums=False):
        self.R=R
        self.nReactants=len(self.R)
        self.P=P
        self.Compounds=R+P
        self.nProducts=len(self.P)
        self.nCompounds=len(self.Compounds)
        self.nu=[]
        self.stoProps={}
        if len(R)>0 and len(P)>0:
            self._balance()
            if not nosums:
                self._computeStoSums()
        else:
            print('Empty Reaction created.')
    def __str__(self):
        ''' spoof nu if reaction is not yet balanced '''
        nuR=['*']*self.nReactants if len(self.nu)==0 else self.nu[:self.nReactants]
        nuP=['*']*self.nProducts  if len(self.nu)==0 else self.nu[self.nReactants:]
        return '  +  '.join([f'{n:.0f} {str(s)}' for n,s in zip(-nuR,self.R)])+'   ->   '+'  +  '.join([f'{n:.0f} {str(s)}' for n,s in zip(nuP,self.P)])
    def show(self):
        retstr=str(self)+'\n'
        infolist=[]
        for p,v in self.stoProps.items():
            if hasattr(v, '__iter__'):
                infolist.append(f'Δ{p} = ['+', '.join([f'{vv:.4e}' for vv in v])+']')
            else:
                infolist.append(f'Δ{p} = {v:.2f}')
        return retstr+' '.join(infolist)
    def as_tex(self):
        reactants,products,nureactants,nuproducts=self._split_reactants_products()
        rxnstr=r'\ce{'+' + '.join(['{:s} {:s}'.format(n,e) for n,e in zip(nureactants,reactants)])+r' <=> '+' + '.join(['{:s} {:s}'.format(n,e) for n,e in zip(nuproducts,products)])+r'}'
        return rxnstr
    def _split_reactants_products(self):
        reactants=[]
        products=[]
        nureactants=[]
        nuproducts=[]
        emps=[c.ef for c in self.Compounds]
        for e,n in zip(emps,self.nu):
            if n<0:
                reactants.append(e)
                f=fr.Fraction(-n).limit_denominator(1000)
                nureactants.append(self._frac_or_int_as_str(f))
            elif n>0:
                products.append(e)
                f=fr.Fraction(n).limit_denominator(1000)
                nuproducts.append(self._frac_or_int_as_str(f))
        return (reactants,products,nureactants,nuproducts)
    def _frac_or_int_as_str(self,f):
        if f.denominator>1:
            return r'\frac{'+'{:d}'.format(f.numerator)+r'}{'+'{:d}'.format(f.denominator)+r'}'
        else:
            if f.numerator==1:
                return ''
            else:
                return '{:d}'.format(f.numerator)

    def _balance(self):
        ''' Uses nullspace of (element)x(count-in-molecule) matrix to balance reaction '''
        self.Ratoms=set()
        for r in self.R:
            self.Ratoms.update(r.atomset)
        self.Patoms=set()
        for p in self.P:
            self.Patoms.update(p.atomset)
        self.atomList=list(self.Ratoms)
        #print(self.atomList)
        self.nAtoms=len(self.atomList)
        #print(f'{self.nReactants} reactants and {self.nProducts} products')
        if len(self.Ratoms.symmetric_difference(self.Patoms))>0:
            print('Error: all atoms not represented on both sides of reaction')
            print('R:',self.Ratoms)
            print('P:',self.Patoms)
        else:
            # make element x count-in-compound matrix
            mat=np.zeros((self.nCompounds,self.nAtoms))
            for i in range(self.nCompounds):
                for j in range(self.nAtoms):
                    if i<self.nReactants:
                        mat[i][j]=self.R[i].countAtoms(self.atomList[j])
                    else:
                        mat[i][j]=self.P[i-self.nReactants].countAtoms(self.atomList[j])
            # find its nullspace vector
            ns=null_space(mat.T)
            ns*=np.sign(ns[0,0])
            # set nu; scale so lowest value is 1 making all integers
            self.nu=np.array([a[0] for a in ns/min([np.abs(x) for x in ns])])*-1
    def _computeStoSums(self):
        propNames=list(self.R[0].thermoChemicalData.keys())
#        print(propNames)
        for p in propNames:
            self.stoProps[p]=0
            if p=='Cp':
                self.stoProps[p]=np.zeros(4)
            for i,c in enumerate(self.R+self.P):
                self.stoProps[p]+=c.thermoChemicalData[p]*self.nu[i]
if __name__=='__main__':
    from .compound import Compound
    rxn=Reaction(R=[Compound('AgNO3'),Compound('CoCl2')],P=[Compound('AgCl'),Compound('Co(NO3)2')])
    print(str(rxn))
    rxn=Reaction(R=[Compound('AgCl'),Compound('NH3')],P=[Compound('Ag(NH3)2^{+1}'),Compound('Cl^{-1}')])
    print(str(rxn))
    rxn=Reaction(R=[Compound('AgCl'),Compound('Na3AsO4')],P=[Compound('Ag3AsO4'),Compound('NaCl')])
    print(str(rxn))
    rxn=Reaction(R=[Compound('H2'),Compound('O2')],P=[Compound('H2O')])
    print(str(rxn))
    rxn=Reaction(R=[Compound('H2'),Compound('N2')],P=[Compound('NH3')])
    print(str(rxn))
    rxn=Reaction(R=[Compound('H2'),Compound('N2'),Compound('O2')],P=[Compound('HNO3')])
    print(str(rxn))
    rxn=Reaction(R=[Compound('Ca^{+2}'),Compound('H2PO4^{-1}'),Compound('H2O')],P=[Compound('Ca3(PO4)2'),Compound('H3O^{+1}')])
    print(rxn.show())
    
    rxn=Reaction(R=[
                    Compound('Ca(HCO3)2',G=1000,H=2112,Cp=np.array([34,0.4,0.05,0.004])),
                    Compound('Ca(OH)2',G=1200,H=938,Cp=np.array([32,0.3,0.02,0.009]))
                    ],
                 P=[
                    Compound('CaCO3',G=-700,H=739,Cp=np.array([31,0.7,0.01,0.0004])),
                    Compound('H2O',G=-900,H=-923,Cp=np.array([30,0.9,0.03,0.003]))
                    ]
                )
    print(rxn.as_tex())

