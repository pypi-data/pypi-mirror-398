# Author: Cameron F. Abrams, <cfa22@drexel.edu>
#
# Methods for pure-component Peng-Robinson real-gas calculations: 
#
# - compressibilities
# - departure functions
# - fugacity coefficients
# - vapor pressure 

import numpy as np

R=8.314 # J/mol-K

def CalcZ_PR(A,B):
    """ Computes the compressibility factor of a Peng-Robinson fluid 
    
    Parameters
    ----------
    - A (float): non-dimensionalized *a* P-R parameter
    - B (float): non-dimensionalized *b* P-R parameter
    
    Returns
    -------
    - (numpy array): array of real roots of cubic compressibility factor equation
    """
    coeff=np.array([1,-1+B,A-3*B**2-2*B,-A*B+B**2+B**3])
    complx_roots=np.roots(coeff)
    real_roots_idx=np.where(complx_roots.imag==0)[0]
    real_roots=complx_roots[real_roots_idx].real
    return real_roots # always returns a list

def CalcConstants_PR(T,Tc,Pc,omega):
    """ Computes various constants used in the Peng-Robinson equation
    
    Parameters
    ----------
    - T (float): Temperature in K
    - Tc (float): Critical temperature in K
    - Pc (float): Critical pressure in any pressure unit
    - omega (float): Acentricity factor

    Globals
    -------
    - R (float): gas constant in J/mol-K

    Returns
    -------
    *Dictionary* with the following entries (all in SI units):
    - a: *a* in units of (J/mol)<sup>2</sup>/[Pressure units]
    - b: *b* in units of J/mol/[Pressure units]
    - alpha: *&alpha;* (dimensionless)
    - kappa: *&kappa;* (dimensionless)
    - da_dT: *da/dT* in units of (J/mol)<sup>2</sup>/[Pressure units]/K

    Notes
    -----
    If pressure units are Pa,
    - units of *a* are J-m<sup>3</sup>/mol<sup>2</sup>
    - units of *b* are m<sup>3</sup>/mol
    - units of *da/dT* are J-m<sup>3</sup>/mol<sup>2</sup>-K
    """
    kappa=0.37464+1.54226*omega-0.26992*omega**2
    alpha=(1+kappa*(1-np.sqrt(T/Tc)))**2
    a=0.45724*R**2*Tc**2/Pc*alpha
    b=0.07780*R*Tc/Pc
    da_dT=-a*kappa/np.sqrt(alpha*T*Tc)
    return dict(a=a,b=b,alpha=alpha,kappa=kappa,da_dT=da_dT)

def CalcAB_PR(T,P,a,b):
    """ Computes non-dimensionalized *a* and *b* P-R parameters *A* and *B* 
    
    Parameters
    ----------
    - T (float): Temperature in K
    - P (float): Pressure in any pressure units
    - a (float): Peng-Robinson *a* parameter in units of (J/mol)<sup>2</sup>/[Pressure units]
    - b (float): Peng-Robisson *b* parameter in units of J/mol/[Pressure units]

    Globals
    -------
    - R (float): gas constant in J/mol-K

    Returns
    -------
    *Tuple* with the following elements:
    - (float) *A* (dimensionless)
    - (float) *B* (dimensionless)
    """
    A=a*P/(R*T)**2
    B=b*P/(R*T)
    return A,B

def CalcDepartures_PR(T,P,Tc,Pc,omega):
    """ Computes enthalpy and entropy depatures
    for a Peng-Robinson fluid 
    
    Parameters
    ----------
    - T (float): Temperature in K
    - P (float): Pressure in any pressure units
    - Cp (dict): Ideal-gas heat capacity coefficients with keys *a*, *b*, *c*, and *d*
    - Tc (float): Critical temperature in K
    - Pc (float): Critical pressure in same pressure units as P
    - omega (float): Acentricity factor

    Globals
    -------
    - R (float): gas constant in J/mol-K

    Returns
    -------
    *Tuple* with the following elements:
    - (float): Enthalpy depature in J/mol
    - (float): Entropy depature in J/mol-K
    """
    C=CalcConstants_PR(T,Tc,Pc,omega)
    a=C['a'] # units of (J/mol)<sup>2</sup>/[Pressure units]
    b=C['b'] # units of J/mol/[Pressure units]
    A,B=CalcAB_PR(T,P,a,b)
    Zlist=CalcZ_PR(A,B)
    Z=Zlist[0]
    da_dT=C['da_dT'] # (J/mol)<sup>2</sup>/[Pressure units]/K
    lrfac=np.log((Z+(1+np.sqrt(2))*B)/(Z+(1-np.sqrt(2))*B))
    Hdep=R*T*(Z-1)+(T*da_dT-a)/(2*np.sqrt(2)*b)*lrfac
    Sdep=R*np.log(Z-B)+da_dT/(2*np.sqrt(2)*b)*lrfac
    return dict(Hdep=Hdep,Sdep=Sdep,lrfac=lrfac)

def Calc_DeltaH_IG(T1,T2,Cp):
    """ Computes change in enthalpy of an ideal gas 

    Parameters
    ----------
    - T1 (float): Temperature of state 1 in K
    - T2 (float): Temperature of state 2 in K
    - Cp (dict): Ideal-gas heat capacity coefficients with keys *a*, *b*, *c*, and *d*

    Returns
    -------
    (float) Delta H in J/mol
     
    """
    a,b,c,d=Cp['a'],Cp['b'],Cp['c'],Cp['d']
    dt1=T2-T1
    dt2=T2**2-T1**2
    dt3=T2**3-T1**3
    dt4=T2**4-T1**4
    return a*dt1 + b/2*dt2 + c/3*dt3 + d/4*dt4

def Calc_DeltaS_IG(T1,T2,P1,P2,Cp):
    """ Computes change in entropy of an ideal gas 

    Parameters
    ----------
    - T1 (float): Temperature of state 1 in K
    - P1 (float): Pressure of state 1 in any pressure units
    - T2 (float): Temperature of state 2 in K
    - P2 (float): Pressure of state 2 in same units as P1
    - Cp (dict): Ideal-gas heat capacity coefficients with keys *a*, *b*, *c*, and *d*

    Globals
    -------
    - R (float): gas constant in J/mol-K

    Returns
    -------
    (float) Delta S in J/mol-K
     
    """
    a,b,c,d=Cp['a'],Cp['b'],Cp['c'],Cp['d']
    lrt=np.log(T2/T1)
    dt1=T2-T1
    dt2=T2**2-T1**2
    dt3=T2**3-T1**3
    return a*lrt+b*dt1+c/2*dt2+d/3*dt3-R*np.log(P2/P1)

def Calc_Delta_HUS(T1,P1,T2,P2,Cp,Tc,Pc,omega):
    """ Computes changes in enthalpy, internal energy, and entropy
    for a Peng-Robinson fluid 
    
    Parameters
    ----------
    - T1 (float): Temperature of state 1 in K
    - P1 (float): Pressure of state 1 in anu pressure units
    - T2 (float): Temperature of state 2 in K
    - P2 (float): Pressure of state 2 in same pressure units as P1
    - Cp (dict): Ideal-gas heat capacity coefficients with keys *a*, *b*, *c*, and *d*
    - Tc (float): Critical temperature in K
    - Pc (float): Critical pressure in same pressure units as P1
    - omega (float): Acentricity factor

    Globals
    -------
    - R (float): gas constant in J/mol-K

    Returns
    -------
    Dictionary with the following entries:
    - H (float): Delta H in J/mol
    - U (float): Delta U in J/mol
    - S (float): Delta S in J/mol-K
    """
    dHIG=Calc_DeltaH_IG(T1,T2,Cp)
    dSIG=Calc_DeltaS_IG(T1,T2,P1,P2,Cp)
    r=CalcDepartures_PR(T1,P1,Tc,Pc,omega)
    Hdep1,Sdep1=r['Hdep'],r['Sdep']
    r=CalcDepartures_PR(T2,P2,Tc,Pc,omega)
    Hdep2,Sdep2=r['Hdep'],r['Sdep']
    dH=dHIG+Hdep2-Hdep1
    dS=dSIG+Sdep2-Sdep1
    C1,C2=CalcConstants_PR(T1,Tc,Pc,omega),CalcConstants_PR(T2,Tc,Pc,omega)
    a1,b1=C1['a'],C1['b']
    a2,b2=C2['a'],C2['b']
    A1,B1=CalcAB_PR(T1,P1,a1,b1)
    A2,B2=CalcAB_PR(T2,P2,a2,b2)
    Z1,Z2=CalcZ_PR(A1,B1)[0],CalcZ_PR(A2,B2)[0]
    dPV=R*(Z2*T2-Z1*T1)
    dU=dH-dPV
    return dict(H=dH,U=dU,S=dS)

def CalcLogPhi_PR(Z,A,B):
    """ Computes the fugacity coefficient of a Peng-Robinson fluid 
    
    Parameters
    ----------
    - Z (float): compressibility factor
    - A (float): non-dimensionalized *a* P-R parameter
    - B (float): non-dimensionalized *b* P-R parameter
    
    Returns
    -------
    - (float) *natural log* of fugacity coefficient
    """
    lnf_P=Z-1-np.log(Z-B)-A/(2*np.sqrt(2)*B)*np.log((Z+(1+np.sqrt(2))*B)/(Z+(1-np.sqrt(2))*B))
    return lnf_P

def Calc_fL_fV_PR(P,T,Tc,Pc,omega):
    """ Computes liquid-phase and vapor-phase fugacities of a Peng-Robinson fluid
    
    Parameters
    ----------
    - P (float): Pressure in any pressure unit
    - T (float): Temperature in K
    - Tc (float): Critical temperature in K
    - Pc (float): Critical pressure in same units as P
    - omega (float): Acentricity factor

    Returns
    -------
    - A *tuple* whose first element is the liquid-phase fugacity and whose
    second element is the vapor-phase fugacity, in units of P

    Exceptions
    ----------
    - If there are not three real roots to the cubic EOS, raises an
    exception.

    """
    C=CalcConstants_PR(T,Tc,Pc,omega)
    A,B=CalcAB_PR(T,P,C['a'],C['b'])
    Zlist=CalcZ_PR(A,B)
    if len(Zlist)!=3:
        raise Exception(f'Error: {len(Zlist)} root(s) found ({Zlist}).  No VLE.')
    Zlist=np.array([min(Zlist),max(Zlist)]) # throw away middle root
    lnPhi=CalcLogPhi_PR(Zlist,A,B)
    fL=np.exp(lnPhi[0])*P
    fV=np.exp(lnPhi[1])*P
    return fL,fV

def Z_PR(T,P,Tc,Pc,omega):
    """ Computes compressibilities
    for a Peng-Robinson fluid 
    
    Parameters
    ----------
    - T (float): Temperature in K
    - P (float): Pressure in any pressure units
    - Cp (dict): Ideal-gas heat capacity coefficients with keys *a*, *b*, *c*, and *d*
    - Tc (float): Critical temperature in K
    - Pc (float): Critical pressure in same pressure units as P
    - omega (float): Acentricity factor

    Globals
    -------
    - R (float): gas constant in J/mol-K

    Returns
    -------
    List of one or three compressibilities
    """
    C=CalcConstants_PR(T,Tc,Pc,omega)
    A,B=CalcAB_PR(T,P,C['a'],C['b'])
    Zlist=CalcZ_PR(A,B)
    return Zlist

def CalcPvap_PR(T,Tc,Pc,omega,Pinit=None,epsilon=1.e-6,maxiter=1000,showiter=False):
    """ Computes vapor pressure of a Peng-Robinson fluid.

    Positional Parameters
    ---------------------
    - T (float): Temperature in K
    - Tc (float): Critical temperature in K
    - Pc (float): Critical pressure in any pressure unit
    - omega (float): Acentricity factor

    Keyword Parameters
    ------------------
    - Pinit (float): initial guess for vapor pressure, in same units as Pc.  Default: None
    - epsilon (float): tolerance for iterations. Default: 1.e-6
    - maxiter (int): maximum number of iterations to perform. Default: 1000
    - showiter (bool): show result of each iteration. Default: False

    Returns
    -------
    If *successful*, returns a dictionary with the following key:value pairs:
    - Pvap (float): Vapor pressure in same units as Pc
    - ZL (float): Liquid-phase compressibility factor
    - ZV (float): Vapor-phase compressibility factor

    If *not successful*, returns *None*.

    """
    P=Pc*(T/Tc)**8 if not Pinit else Pinit
    keepgoing=True
    iter=0
    while keepgoing:
        iter+=1
        try:
            fL,fV=Calc_fL_fV_PR(P,T,Tc,Pc,omega)
        except:
            print(f'Error computing pvap at {T} K')
            return None
        err=np.abs(fL/fV-1)
        if showiter: print(f'Iter {iter}: P {P:.6f}, fV {fV:.6f}, fL {fL:.6f}; error {err:.4e}')
        P=P*fL/fV
        if err<epsilon or iter==maxiter:
            keepgoing=False
    if iter>=maxiter:
        print(f'Reached {iter} iterations without convergence; error {np.abs(fL/fV-1):.4e}')
        return None
    C=CalcConstants_PR(T,Tc,Pc,omega)
    A,B=CalcAB_PR(T,P,C['a'],C['b'])
    Zlist=CalcZ_PR(A,B)
    return dict(Pvap=P,ZL=min(Zlist),ZV=max(Zlist),fL=fL,fV=fV)