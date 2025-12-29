import numpy as np
from iapws import IAPWS97
from pygacity.util.texutils import *

def st_report(R):
    r=f'{R.T:.2f} {R.P:.2f} {R.x:.2f} {R.v:.4f} {R.h:.4f} {R.s:.4f} {R.u:.4f}'
    # for k,v in R.__dict__.items():
    #     if k in ['Liquid','Vapor']:
    #         print(k)
    #         for kk,vv in v.__dict__.items():
    #             print('    ',kk,vv)
    #     else:
    #         print(k,v)
    return r

def steam_tank(V=40,VL0=0.005,T0=393.15,P1=0.5,Ti=373.15,xi=0.9,quiet=True):
    """ Solves the steam tank problem:  Given a tank of volume V (m^3) in which VL0 (m^3) of liquid water
        is in equilibrium with water vapor at T0 (K), suppose an inlet steam line at Ti (K) and quality
        xi is allowed to inject steam into tank until pressure in tank reaches P1 (MPa).  Compute
        the mass of steam injected (kg) and the quality of the tank contents. """
    VV0=V-VL0
    initial_contents=IAPWS97(T=T0,x=0.5)
    init_V=initial_contents.Vapor
    init_L=initial_contents.Liquid
    P0=initial_contents.P
    if not quiet:
        print(f'P0 = {P0*1000:.4f} kPa')
        print(f'VhatL0 = {init_L.v:.6f} m3/kg, UhatL0 = {init_L.u:.4f} kJ/kg')
        print(f'VhatV0 = {init_V.v:.4f} m3/kg, UhatV0 = {init_V.u:.4f} kJ/kg')
    mL0=VL0/init_L.v
    mV0=VV0/init_V.v
    m0=mL0+mV0
    U0=mL0*init_L.u+mV0*init_V.u
    if not quiet:
        print(f'mL0 = {mL0:.2f} kg, mV0 = {mV0:.2f} kg => m0 = {m0:.2f} kg')
        print(f'U0 = {U0:.1f} kJ')

    final_contents=IAPWS97(P=P1,x=0.5)
    T1=final_contents.T
    fin_L=final_contents.Liquid
    fin_V=final_contents.Vapor
    if not quiet:
        print(f'T1 = {T1:.2f} K')
        print(f'VhatL1 = {fin_L.v:.6f} m3/kg, UhatL0 = {fin_L.u:.4f} kJ/kg')
        print(f'VhatV1 = {fin_V.v:.4f} m3/kg, UhatV0 = {fin_V.u:.4f} kJ/kg')

    in_stream=IAPWS97(T=Ti,x=xi)
    in_L=in_stream.Liquid
    in_V=in_stream.Vapor
    if not quiet:
        print(f'HhatiL = {in_L.h:.2f} kJ/kg, HhatiV = {in_V.h:.2f} kJ/kg')

    A=np.array([[fin_V.v,fin_L.v,0],[1,1,-1],[fin_V.u,fin_L.u,-(xi*in_V.h+(1-xi)*in_L.h)]])
    B=np.array([V,m0,U0])
    x=np.linalg.solve(A,B)
    if not quiet:
        print(f'm1V = {x[0]:.4f}, m1L = {x[1]:.4f}, m = {x[2]:0.4f}, all in kg')

    kg_added=x[2]
    quality_in_tank=x[0]/(x[0]+x[1])
    if not quiet:
        print(f'ANSWER: {kg_added:.2f} kg steam added; quality in tank is {quality_in_tank:.2f}')
    return kg_added,quality_in_tank

if __name__=='__main__':
    DeltaM,x=steam_tank()
    print(f'DeltaM = {DeltaM:0.2f} kg inlet steam added, final quality in tank is {x:.2f}')
