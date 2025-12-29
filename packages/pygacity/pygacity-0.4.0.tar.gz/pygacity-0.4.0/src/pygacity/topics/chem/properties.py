import numpy as np
from .compound import Compound
from sandlerprops.properties import PropertiesDatabase

class PureProperties:

    def __init__(self):
        self.Properties = PropertiesDatabase()
    
    def report(self):
        self.Properties.show_properties()
    
    def get_crits(self, compound_name: str = ''):
        cmpd = self.Properties.get_compound(compound_name)
        if cmpd:
            return cmpd.Tc, cmpd.Pc, cmpd.Omega
        return None, None, None
    
    def get_compound(self, compound_name=''):
        cmpd = self.Properties.get_compound(compound_name)
        ''' Returns a fully loaded Compound instance '''
        if cmpd:
            cp = np.array([cmpd.CpA, cmpd.CpB, cmpd.CpC, cmpd.CpD])
            C = Compound(
                empirical_formula=cmpd.Formula,
                name=compound_name,
                Tc=cmpd.Tc,
                Pc=cmpd.Pc,
                omega=cmpd.Omega,
                Cp=cp,
                H=cmpd.dHf,
                G=cmpd.dGf
                )
            return C
        else:
            return None
        
if __name__=='__main__':
    Prop=PureProperties()
    Prop.report()
    M=Prop.get_compound('cyclopentane')
    for p,v in M.thermoChemicalData.items():
        print(f'{p}: {v}')