import numpy as np
from ...util.texutils import *

class Compound:
    ''' simple class for describing chemical compounds by empirical formula 
    
        e.g., 

        my_compound = Compound('A2B')

        creates a Compound instance my_compound for which my_compound.A is the
        following dictionary

        {'A':2, 'B':1}

        Empirical formulas can have nested parentheses, integer subscripts (1-implied if missing), and charges (indicated by a terminal '^{#}', where # is a string
        interpretable as a signed integer).  Element names can be either a single capital letter or a capital-lowercase dyad.  Another example:

        another_compound = Compound('H(OCH3CH2)10H')

        gives for another_compound.A:

        {'H':52, 'O':10, 'C':20}

        By parsing empirical formulas into element:count dictionaries, Compounds
        can be incorporated into Reactions and those Reactions can be balanced. 

        Any keyword arguments passed to __init__ that are not 'empirical_formula'
        or 'name' are stored in the attribute dictionary 'thermoChemicalData'

        Cameron F. Abrams cfa22@drexel.edu 

    '''
    compound_properties=['H','G','Cp']
    system_properties=['T','Tref','P']
    def __init__(self,empirical_formula='',name='',**kwargs):
        if len(empirical_formula)>0:
            self.name=name # optional namestring
            efc=empirical_formula.split('^')
            self.ef=efc[0]
            if len(self.name)==0:
                self.name=self.ef
            self.charge=0
            if len(efc)>1:
                expo=efc[1]
                if expo[0]=='{' and expo[-1]=='}':
                    self.charge=int(expo[1:-1])
                else:
                    print('Error: malformed charge:',efc[1])
            ''' dictionary of atomname:count items representing empirical formula '''
            self.A=parse_empirical_formula(self.ef)
            self._reorder_elements()
            self.atomset=set(self.A.keys())
            self.thermoChemicalData={}
            self.systemData={}
            self._parseKeywords(kwargs)
            if 'Tref' not in self.systemData:
                self.systemData['Tref']=298.15 # assumed by default
    def _parseKeywords(self,words):
        for n,v in words.items():
            if n in self.compound_properties:
                self.thermoChemicalData[n]=v
            elif n in self.system_properties:
                self.systemData[n]=v
        for reqScal in ['H','G']:
            if reqScal not in self.thermoChemicalData:
                self.thermoChemicalData[reqScal]=0.
        for reqArr in ['Cp']:
            if reqArr not in self.thermoChemicalData:
                self.thermoChemicalData[reqArr]=np.array([0.]*4)
        
    def setThermochemicalData(self,**kwargs):
        for k,v in kwargs.items():
            self.thermoChemicalData[k]=v
    def report(self,indent=''):
        print(f'{self.name}({self.ef})\n{indent}Thermochemical Data:')
        for k,v in self.thermoChemicalData.items():
            print(f'{indent}    {k}: {str(v)}')
        print(f'{indent}System Data:')
        for k,v in self.systemData.items():
            print(f'{indent}    {k}: {str(v)}')
    def report_as_tex(self):
        retstr=f'{self.name} ({self.as_tex()})\\\\'
        retstr+=r'$\Delta_f H^\circ$ = '+f"{self.thermoChemicalData['H']:,.0f} J/mol\\\\\n"
        retstr+=r'$\Delta_f G^\circ$ = '+f"{self.thermoChemicalData['G']:,.0f} J/mol\\\\\n"
        retstr+=r'$C_p^\circ$ = '+f"{self.thermoChemicalData['Cp'][0]:.3f} + "
        retstr+=r'('+sci_notation_as_tex(self.thermoChemicalData['Cp'][1],mantissa_fmt='{:.4e}')+r') $T$ + '
        retstr+=r'('+sci_notation_as_tex(self.thermoChemicalData['Cp'][2],mantissa_fmt='{:.4e}')+r') $T^2$ + '
        retstr+=r'('+sci_notation_as_tex(self.thermoChemicalData['Cp'][3],mantissa_fmt='{:.4e}')+r') $T^3$'
        return(retstr)
    def Cp_as_tex(self):
        Cp=self.thermoChemicalData['Cp']
        return Cp_as_tex(Cp)

    def CpInt_as_tex(self):
        Cp=self.thermoChemicalData['Cp']
        retstr=f"{Cp[0]:.3f}($T_2-T_1$) + "
        retstr+=r'$\frac{1}{2}$('+sci_notation_as_tex(Cp[1],mantissa_fmt='{:.4e}')+r') ($T_2^2-T_1^2$) + '
        retstr+=r'$\frac{1}{3}$('+sci_notation_as_tex(Cp[2],mantissa_fmt='{:.4e}')+r') ($T_2^3-T_1^3$) + '
        retstr+=r'$\frac{1}{4}$('+sci_notation_as_tex(Cp[3],mantissa_fmt='{:.4e}')+r') ($T_2^4-T_1^4$)'
        return(retstr)
    def computeGoT(self,T):
        ''' Computes the standard state Gibbs energy of formation at arbitrary temperature T '''
        go=self.thermoChemicalData['G']
        ho=self.thermoChemicalData['H']
        cpo=self.thermoChemicalData['Cp']
        Tref=self.systemData['Tref']
        self.systemData['T']=T
        gT=go*T/Tref+ho*(1-T/Tref)+self._cpI(cpo,(Tref,T))-T*self._cpTI(cpo,(Tref,T))
        self.thermoChemicalData['GoT']=gT
    def _cpI(self,cp,TL):
        return sum([cp[i]/(i+1)*(TL[1]**(i+1)-TL[0]**(i+1)) for i in range(len(cp))])
    def _cpTI(self,cp,TL):
        return cp[0]*np.log(TL[1]/TL[0])+sum([cp[i]/i*(TL[1]**i-TL[0]**i) for i in range(1,len(cp))])
    def _reorder_elements(self):
        my_order_preference=['C','O','N','H','Na','K','Ca','F','Cl','Br','I']
        A=self.A.copy()
        ef=''
        for a in my_order_preference:
            if a in A:
                c='' if A[a]==1 else str(A[a])
                ef+=f'{a}{c}'
                del A[a]
        for e,c in A.items():
            c='' if c==1 else str(c)
            ef+=f'{e}{c}'
        self.ef=ef
    def __eq__(self,other):
        return self.A==other.A
    def __hash__(self):
        ''' provided to make instances of Compounds hashable (i.e., so they can
            be dictionary keys) '''
        return id(self)
    def __str__(self):
        return self.ef+('' if self.charge==0 else r'^{'+f'{self.charge:+}'+r'}')
    def as_tex(self):
        return r'\ce{'+str(self)+r'}'
    def countAtoms(self,a):
        if a in self.A:
            return self.A[a]
        else:
            return 0

''' a bunch of functions that permit conversion of an empirical formula into
    an element:count dictionary '''
# per https://stackoverflow.com/users/5079316/olivier-melan%c3%a7on
def _push(obj,l,depth):
    while depth:
        l = l[-1]
        depth -= 1
    l.append(obj)

def _parse_parentheses(s):
    ''' byte-wise de-nestify a string with parenthesis '''
    groups = []
    depth = 0
    try:
        i=0
        while i<len(s):
            char=s[i]
            if char == '(':
                _push([], groups, depth)
                depth += 1
            elif char == ')':
                depth -= 1
            else:
                _push(char, groups, depth)
            i+=1
    except IndexError:
        raise ValueError('Parentheses mismatch')
    if depth != 0:
        raise ValueError('Parentheses mismatch')
    else:
        return groups

def bankblock(B,b):
    if len(b[0])>0: # bank this block
        if not any(isinstance(i, list) for i in b[0]):
            b[0]=''.join(b[0])
        nstr=''.join(b[1])
        b[1]=1 if len(nstr)==0 else int(nstr)
        B.append(b)

def blockify(bl):
    ''' parse the byte_levels returned from the byte-wise de-nester into blocks, where
        a block is a two-element list, where first element is a block and second is 
        an integer subscript >= 1.  A "primitive" block is one in which the first
        element is not a list, but instead a string that indentifies a chemical element. '''
    blocks=[]
    curr_block=[[],[]]
    for b in bl:
        if len(b)==1:
            if b.isalpha():
                if b.isupper(): # new block
                    bankblock(blocks,curr_block)
                    curr_block=[[b],[]]
                else: # still building this block's elem name
                    curr_block[0].append(b)
            elif b.isdigit():
                curr_block[1].append(b)
        else:
            bankblock(blocks,curr_block)
            curr_block=[blockify(b),[]]
    bankblock(blocks,curr_block)
    return blocks

def flattify(B):
    ''' distribute the block counts inward '''
    for b in B:
        if isinstance(b[0],str) or b[1]==1: # already flat
            pass
        else:
            m=b[1]
            b[1]=1
            for bb in b[0]:
                bb[1]*=m
                flattify(b[0])

def my_flatten(L,size=(2)):
    ''' flatten '''
    flatlist=[]
    for i in L:
        if not isinstance(i[0],list):
            flatlist.append(i)
        else:
            newlist=my_flatten(i[0])
            flatlist.extend(newlist)
    return flatlist

def reduce(L):
    ''' produce a dictionary of element:number '''
    result_dict={}
    for i in L:
        if i[0] in result_dict:
            result_dict[i[0]]+=i[1]
        else:
            result_dict[i[0]]=i[1]
    return result_dict

def parse_empirical_formula(ef):
    block_levels=blockify(_parse_parentheses(ef))
    flattify(block_levels)
    return reduce(my_flatten(block_levels))

if __name__ == '__main__':
    A=Compound(empirical_formula='A2B')
    B=Compound(empirical_formula='BA2')
    print(A==B) # test for equality by reduced empirical formula; should be true
    my_dict={A:0.5,B:1.2} # should be possible to use Compound instances as dictionary keys
    print(my_dict)

