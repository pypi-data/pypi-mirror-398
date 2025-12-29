import numpy as np
import pandas as pd
from scipy.optimize import fsolve
from scipy import interpolate
import matplotlib.pyplot as plt
from io import StringIO
data=StringIO("""name,aT1,aT2,aT6,aP1,aP2,aP3
isobutane, -1166846,     0,       7.72668,-0.92213, 0,       0
n-butane,  -1280557,     0,       7.94986,-0.93159, 0,       0
isopentane,-1481583,     0,       7.58071,-0.93159, 0,       0
n-pentane, -1524891,     0,       7.33129,-0.89143, 0,       0
n-hexane,  -1778901,     0,       6.96783,-0.84634, 0,       0
n-heptane, -2013803,     0,       6.52914,-0.79543, 0,       0
n-octane,   0,       -7646.81641,12.48457,-0.73152, 0,       0""")
# data=StringIO("""name,aT1,aT2,aT6,aP1,aP2,aP3
# methane,    -292860,     0,       8.2445, -0.8951, 59.8465,  0
# ethylene,   -600076.875, 0,       7.90595,-0.84677,42.94594, 0
# ethane,     -687248.25,  0,       7.90694,-0.88600,49.02654, 0
# propylene,  -923484.6875,0,       7.71725,-0.87871,47.67624, 0
# propane,    -970688.5625,0,       7.15059,-0.76984, 0,       6.90224
# isobutane, -1166846,     0,       7.72668,-0.92213, 0,       0
# n-butane,  -1280557,     0,       7.94986,-0.93159, 0,       0
# isopentane,-1481583,     0,       7.58071,-0.93159, 0,       0
# n-pentane, -1524891,     0,       7.33129,-0.89143, 0,       0
# n-hexane,  -1778901,     0,       6.96783,-0.84634, 0,       0
# n-heptane, -2013803,     0,       6.52914,-0.79543, 0,       0
# n-octane,   0,       -7646.81641,12.48457,-0.73152, 0,       0
# n-nonane,  -2551040,     0,       5.69313,-0.67818, 0,       0
# n-decane,   0,       -9760.45703,13.80354,-0.71470, 0,       0""")
dpdf=pd.read_csv(data,header=0,index_col=0)
C=dpdf.shape[0]

kPa_per_psia=6.89476
K_per_R=5./9.
def DePriesterK(compound,T_R,p_psia):
    p=dpdf.loc[compound]
    lnK=p['aT1']/T_R**2+p['aT2']/T_R+p['aT6']+p['aP1']*np.log(p_psia)+p['aP2']/p_psia**2+p['aP3']/p_psia
    return np.exp(lnK)

def get_Pxy(components,T_K,npts=101):
    X=np.linspace(0,1,npts)
    def get_P(x,components,T):
        def zero_me(P,x,components,T):
            K1=DePriesterK(components[0],T/K_per_R,P/kPa_per_psia)
            K2=DePriesterK(components[1],T/K_per_R,P/kPa_per_psia)
            return 1-(x*K1+(1-x)*K2)
        Pinit=100 # kPa
        P=fsolve(zero_me,Pinit,args=(x,components,T))[0]
        return P
    P=[]
    y=[]
    for x in X:
        P.append(get_P(x,components,T_K))
        K1=DePriesterK(components[0],T_K/K_per_R,P[-1]/kPa_per_psia)
        y.append(x*K1)
    return np.array(P),X,np.array(y)

def get_Txy(components,P_kPa,npts=101):
    X=np.linspace(0,1,npts)
    def get_T(x,components,P_kPa,Tinit=350):
        def zero_me(T,x,components,P):
            K1=DePriesterK(components[0],T/K_per_R,P/kPa_per_psia)
            K2=DePriesterK(components[1],T/K_per_R,P/kPa_per_psia)
            return 1-(x*K1+(1-x)*K2)
        T=fsolve(zero_me,Tinit,args=(x,components,P_kPa))[0]
        return T
    T=[]
    y=[]
    for x in X[::-1]:
        if len(T)>0:
            Tinit=T[-1]
        else:
            Tinit=300
        T.append(get_T(x,components,P_kPa,Tinit=Tinit))
        K1=DePriesterK(components[0],T[-1]/K_per_R,P_kPa/kPa_per_psia)
        y.append(x*K1)
    T=T[::-1]
    y=y[::-1]
    return np.array(T),X,np.array(y)

def pick_state(specs):
    num=specs['tag']
    if num<1e7:
        raise Exception(f'{num} is too small')
    idx=[]
    while num>0:
        idx.append(num%100)
        num//=10
    c1_idx=int(idx[0]/100*C)
    c2_idx=int(idx[1]/100*C)
    if c1_idx==c2_idx:
        c2_idx=(c1_idx+1)%C
    if c1_idx>c2_idx:
        tmp=c1_idx;c1_idx=c2_idx;c2_idx=tmp
    while c2_idx-c1_idx > C//2:
        c1_idx+=1
    all_components=dpdf.index.to_list()
    span=0
    c1=all_components[c1_idx]
    c2=all_components[c2_idx]
    P_kPa_lim=np.array([400,1000.0])
    log_lim=np.log(P_kPa_lim)
    fac=idx[2]/100
    logP=log_lim[0]+fac*(log_lim[1]-log_lim[0])
    P_kPa=np.exp(logP)
    z=np.around(0.4+0.2*(idx[3]/100),2)
    while span<30:
        T,x,y=get_Txy([c1,c2],P_kPa,npts=501)
        T_of_x=interpolate.interp1d(x,T)
        T_of_y=interpolate.interp1d(y,T)
        x_of_T=interpolate.interp1d(T,x)
        y_of_T=interpolate.interp1d(T,y)
        Tdew=T_of_y(z)
        Tbub=T_of_x(z)
        span=Tdew-Tbub
        if span<30:
            # print(f'{c1} {c2} at {P_kPa} kPa; less than 20 deg separates Tbub {Tbub} and Tdew {Tdew}')
            if c1_idx>0:
                c1_idx-=1
            elif c2_idx<(C-2):
                c2_idx+=1
            c1=all_components[c1_idx]
            c2=all_components[c2_idx]
    T_drum_K=Tdew-10-idx[3]/100*(span-20)
    T_drum_C=T_drum_K-273.15
    T_drum_C=np.around(T_drum_C,-1)
    # print(Tdew,Tbub,T_drum_K,T_drum_C)
    if T_drum_C>200:
        raise Exception(f'You picked a T {Tbub-273.15} < {T_drum_C} < {Tdew-273.15}C at {P_kPa} kPa off the chart for {c1}/{c2} -- too high')
    if T_drum_C<-70:
        raise Exception('You picked a T off the chart -- too low')
    # T_drum_K=T_drum_C+273.15
    if T_drum_K<Tbub:
        raise Exception('whoops -- you rounded Tdrum outside the 2-phase envelope (too low)')
    if T_drum_K>Tdew:
        raise Exception('whoops -- you rounded Tdrum outside the 2-phase envelope (too high)')
    specs.update(dict(z=z,T_drum_C=(T_drum_K-273.15),P_drum_kPa=P_kPa,components=[c1,c2],
    Thermodynamics={'x_of_T':x_of_T,'y_of_T':y_of_T,'T_of_x':T_of_x,'T_of_y':T_of_y},Tdew=Tdew,Tbub=Tbub,Txy=[T,x,y]))
    return specs

def solve(specs):
    c1,c2=specs['components']
    T_drum_K=specs['T_drum_C']+273.15
    P_drum_kPa=specs['P_drum_kPa']
    x_of_T=specs['Thermodynamics']['x_of_T']
    y_of_T=specs['Thermodynamics']['y_of_T']
    z=specs['z']
    K=[DePriesterK(c1,T_drum_K/K_per_R,P_drum_kPa/kPa_per_psia),DePriesterK(c2,T_drum_K/K_per_R,P_drum_kPa/kPa_per_psia)]
    xlr=x_of_T(T_drum_K)
    ylr=y_of_T(T_drum_K)
    L_F=(ylr-z)/(ylr-xlr)
    specs.update(dict(x=xlr,y=ylr,L_F=L_F,K=K))
    plot_Txy(specs)
    return specs

def plot_Txy(specs):
    T,x,y=specs['Txy']
    plotfile=specs['plotfile']
    Tdew=specs['Tdew']
    Tbub=specs['Tbub']
    z=specs['z']
    xlr,ylr=specs['x'],specs['y']
    T_drum_K=specs['T_drum_C']+273.15
    P_drum_kPa=specs['P_drum_kPa']
    c1,c2=specs['components']
    fig,ax=plt.subplots(1,1)
    ax.plot(x,T)
    ax.plot(y,T)
    ax.plot([z,z],[Tdew,Tbub],marker='o')
    ax.plot([xlr,ylr],[T_drum_K,T_drum_K])
    ax.set_title(f'{c1}/{c2} at {P_drum_kPa} kPa')
    ax.set_xlabel('x,y')
    ax.set_ylabel('T [K]')
    plt.savefig(plotfile,bbox_inches='tight')
    plt.clf()

if __name__=='__main__':
    num=[113344556677]
    Z=[]
    X=[]
    Y=[]
    K1=[]
    K2=[]
    T=[]
    P=[]
    LF=[]
    LITE=[]
    HEAVY=[]
    for tag in num:
        specs={'tag':tag,'plotfile':'tmp.png'}
        specs=pick_state(specs)
        res=solve(specs)
        components=res['components']
        K=res['K']
        LITE.append(components[0])
        HEAVY.append(components[1])
        K1.append(K[0])
        K2.append(K[1])
        T.append(res['T_drum_C'])
        P.append(res['P_drum_kPa'])
        LF.append(res['L_F'])
        Z.append(res['z'])
        Y.append(res['y'])
        X.append(res['x'])
    sumdat=pd.DataFrame({'tag':num,'T':T,'P':P,'LF':LF,'Z':Z,'Y':Y,'X':X,'C1':LITE,'C2':HEAVY,'K1':K1,'K2':K2})
    # sumdat.to_csv('results.csv',sep=' ',header=True,index=False)