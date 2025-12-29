"""

Generate xy and Txy diagrams using input data

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse as ap
from scipy.optimize import curve_fit

def getdat(fn):
    dat=pd.read_csv(fn,index_col=False,header=0)
    return dat

def y_of_x(x,*a):
    """ My custom regression of y(x) data """
    s=0.0
    for i,c in enumerate(a):
        s+=c*(1-x)**(i+1)
    return x/(x+s)

def xy(dat,fn='xy.png',comp1_name='Comp. 1',comp2_name='Comp. 2',P_label='1 bar',x_label='x',y_label='y',t_label='T(C)',do_fit={}):
    fig,ax=plt.subplots(1,1,figsize=(9,9))
    plt.grid(visible=True,which='major',axis='both')
    ax.set_xlim([0,1])
    ax.set_title(f'{comp1_name}-{comp2_name} binary, $P$ = {P_label}')
    ax.set_xlabel(r'$x_{\rm '+f'{comp1_name}'+r'}$')
    ax.set_ylabel(r'$y_{\rm '+f'{comp1_name}'+r'}$')
    ax.set_xlim([0,1])
    ax.set_ylim([0,1])
    ax.set_xticks(np.linspace(0,1,11))
    ax.set_yticks(np.linspace(0,1,11))
    ax.tick_params(labelright=True)
    ax.plot(dat[x_label],dat[y_label])
    ax.plot(dat[x_label],dat[x_label],'k--')
    if do_fit:
        Nterms=do_fit.get('N',2)
        coeff,stat=curve_fit(y_of_x,dat[x_label],dat['y'],p0=np.ones(Nterms))
        ax.plot(dat[x_label],y_of_x(dat[x_label],*coeff),'r--')
        print(coeff)
    plt.savefig(fn)
    fig.clf()

def T_of_x(x,*a):
    """ My custom regression of T(x) data; a[0] and a[1] are boiling point temperatures """
    s=0
    for i,c in enumerate(a[2:]):
        s+=c*(2*x-1)**i
    l=(1-x)*a[0]+x*a[1]
    return l+s*x*(1-x)

def Txy(dat,fn='Txy.png',comp1_name='Comp. 1',comp2_name='Comp. 2',P_label='1 bar',x_label='x',y_label='y',t_label='T(C)',do_fit={}):
    fig,ax=plt.subplots(1,1,figsize=(9,9))
    plt.grid(visible=True,which='major',axis='both')
    ax.set_xlim([0,1])
    ax.set_title(f'{comp1_name}-{comp2_name} binary, $P$ = {P_label}')
    ax.set_xlabel(r'$x_{\rm '+f'{comp1_name}'+r'}$')
    ax.set_ylabel(r'$T$ (C)')
    ax.set_xlim([0,1])
    ax.spines['top'].set_visible(False)
    ax.set_xticks(np.linspace(0,1,11))
    ax.tick_params(labelright=True)
    ax.plot(dat[x_label],dat[t_label])
    ax.plot(dat[y_label],dat[t_label])
    if do_fit:
        ep=do_fit.get('epsilon',1.e-10)
        Nterms=do_fit.get('N',5)
        p0=np.concatenate(([dat[t_label][0],dat[t_label][dat.shape[0]-1]],np.ones(Nterms)))
        lower=np.concatenate(([dat[t_label][0],dat[t_label][dat.shape[0]-1]],-np.inf*np.ones(Nterms)))
        upper=np.concatenate(([dat[t_label][0]+ep,dat[t_label][dat.shape[0]-1]+ep],np.inf*np.ones(Nterms)))
        coeffx,stat=curve_fit(T_of_x,dat[x_label],dat[t_label],p0=p0,bounds=(lower,upper))
        ax.plot(dat[x_label],T_of_x(dat[x_label],*coeffx),'r--')
        print(coeffx)
        coeffy,stat=curve_fit(T_of_x,dat[y_label],dat[t_label],p0=p0,bounds=(lower,upper))
        ax.plot(dat[y_label],T_of_x(dat[y_label],*coeffy),'g--')
        print(coeffy)
    plt.savefig(fn)
    fig.clf()

if __name__=='__main__':
    parser=ap.ArgumentParser()
    parser.add_argument('-c',type=str,nargs=2,default=['',''],help='names of components')
    parser.add_argument('f',type=str,default='',help='name of input csv file')
    parser.add_argument('-p',type=str,default='1 bar',help='pressure label')
    parser.add_argument('-xyfn',type=str,default='xy.png',help='xy diagram file name')
    parser.add_argument('-Txyfn',type=str,default='Txy.png',help='Txy diagram file name')
    parser.add_argument('--fits', action=ap.BooleanOptionalAction,help='Do curve-fits')
    args=parser.parse_args()
    comp1_name,comp2_name=args.c 
    fn=args.f 
    plab=args.p 
    dat=getdat(fn)
    xy(dat,fn=args.xyfn,comp1_name=comp1_name,comp2_name=comp2_name,P_label=plab,do_fit=args.fits)
    Txy(dat,fn=args.Txyfn,comp1_name=comp1_name,comp2_name=comp2_name,P_label=plab,do_fit=args.fits)


