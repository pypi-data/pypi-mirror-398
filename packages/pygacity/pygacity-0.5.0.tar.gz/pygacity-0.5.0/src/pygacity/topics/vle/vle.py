
# # Low-P VLE Calculations and Diagrams
# 
# BUBP, DEWP, BUBT, DEWT, and Isothermal flash calculations with activity coefficients
# 
# Cameron F Abrams
# 
# Department of Chemical and Biological Engineering
# 
# Drexel University
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

R=8.314 # J/mol-K

# Antoine equation defintion. 
# 
# $$
# \ln P_i^{\rm vap} = A + \frac{B}{T+C}
# $$
# 
# You can compute $P_i^{\rm vap}$ at any $T$ by
# ```
# pv=pvap(T,ant_parms)
# ```
# 
# where `ant_params` is with keys 'A', 'B', and 'C', each of whose value is either a scalar or a list of values (for computing vapor pressure for two or more compounds at once).

def pvap(T,ant_parms):
    a,b,c=ant_parms['A'],ant_parms['B'],ant_parms['C']
    base=ant_parms.get('base','exp')
    if base=='exp':
        return np.exp(a+b/(T+c))
    else:
        return pow(base,a+b/(T+c))

# Two-constant activity coefficient models.  You can compute $\gamma_A$ and $\gamma_B$ at any $x_A$ by 
# ```
# gA,gB=acm(x,T,acm_parms)
# ```
# where `acm_parms` is a dictionary where the value of the key 'TYPE' is one of `RAOULT`, `VANLAAR` or `TWO-CONSTANT MARGULES`.  Other entries hold required parameters:
#    - RAOULT:  No parameters
#    - VANLAAR: 'ALPHA' and 'BETA'
#    - TWO-CONSTANT MARGULES: 'A' and 'B'.

def acm(x,T,acm_parms,ep=1.e-6):
    model_type=acm_parms['TYPE']
    if model_type=='RAOULT':
        return 1,1
    elif model_type=='VANLAAR':
        a,b=acm_parms['ALPHA'],acm_parms['BETA']
        return np.exp(a/(1+a/b*x/(1-x+ep))**2),np.exp(b/(1+b/a*(1-x)/(x+ep))**2)
    elif model_type=='TWO-CONSTANT MARGULES':
        RT=R*T
        a,b=acm_parms['A'],acm_parms['B']
        return np.exp((a+3*b)*(1-x)**2/RT+(-4*b)*(1-x)**3/RT),np.exp((a-3*b)*x**2/RT+4*b*x**3/RT)
    else:
        return 1,1

# BUBP, DEWP, BUBT, DEWP, and isothermal flash calculations using an activity coefficient model.  Examples:
# 
# ```
# P,y=bubp(x,T,ant_parms,acm_parms)
# P,x=dewp(y,T,ant_parms,acm_parms)
# T,y=bubt(x,P,ant_parms,acm_parms)
# T,x=dewt(y,P,ant_parms,acm_parms)
# L,x,y=isothermal_flash(z,T,P,ant_parms,acm_parms)
# ```
# 
# All of `bubp()`, `dewp()`, `bubt()` and `dewt()` can handle array-like arguments at the first position.  `isothermal_flash()` can handled *one* array-like argument at any one of the first three positions.

def bubp(x,T,ant_parms,acm_parms):
    pv=pvap(T,ant_parms)
    gA,gB=acm(x,T,acm_parms)
    P=x*gA*pv[0]+(1-x)*gB*pv[1]
    y=x*gA*pv[0]/P
    return P,y

def dewp(y,T,ant_parms,acm_parms,xinit=0.1):
    def f_dewp(x,y,T,ant_parms,acm_parms):
        P,ycomp=bubp(x,T,ant_parms,acm_parms)
        return y-ycomp
    if hasattr(y,'__len__'): # requested DEWP curve along y
        x=np.zeros(len(y))
        P=np.zeros(len(y))
        for i in range(len(y)):
            x[i]=fsolve(f_dewp,xinit,args=(y[i],T,ant_parms,acm_parms))
            gA,gB=acm(x[i],T,acm_parms)
            pv=pvap(T,ant_parms)
            P[i]=x[i]*gA*pv[0]+(1-x[i])*gB*pv[1]
        return P,x
    else: # requested DEWP at one value of y only
        x=fsolve(f_dewp,xinit,args=(y,T,ant_parms,acm_parms))
        gA,gB=acm(x,T,acm_parms)
        pv=pvap(T,ant_parms)
        P=x*gA*pv[0]+(1-x)*gB*pv[1]
        return P.item(),x.item()

def bubt (x,P,ant_parms,acm_parms,Tinit=400):
    def f_bubt(T,P,x,ant_parms,acm_parms):
        Pcomp,y=bubp(x,T,ant_parms,acm_parms)
        return Pcomp-P
    if hasattr(x, "__len__"):  # BUBT curve along x
        T=np.zeros(len(x))
        y=np.zeros(len(x))
        for i in range(len(x)):
            T[i]=fsolve(f_bubt,Tinit,args=(P,x[i],ant_parms,acm_parms))
            pv=pvap(T[i],ant_parms)
            gA,gB=acm(x[i],T[i],acm_parms)
            y[i]=x[i]*gA*pv[0]/P
        return T,y
    else: # scalar calculation only
        T=fsolve(f_bubt,Tinit,args=(P,x,ant_parms,acm_parms))
        pv=pvap(T,ant_parms)
        gA,gB=acm(x,T,acm_parms)
        y=x*gA*pv[0]/P
        return T.item(),y.item()

def dewt(y,P,ant_parms,acm_parms,Tinit=400,xinit=0.1):
    def f_dewt(Tx,P,y,ant_parms,acm_parms):
        T,x=Tx
        Pcomp,ycomp=bubp(x,T,ant_parms,acm_parms)
        return ((Pcomp-P)**2,(ycomp-y)**2)
    if hasattr(y,'__len__'): # DEWT along y
        T=np.zeros(len(y))
        x=np.zeros(len(y))
        for i in range(len(y)):
            Tx=fsolve(f_dewt,(Tinit,xinit),args=(P,y[i],ant_parms,acm_parms))
            T[i],x[i]=Tx
            pv=pvap(T[i],ant_parms)
            gA,gB=acm(x[i],T[i],acm_parms)
            y[i]=x[i]*gA*pv[0]/P
        return T,x
    else:
        Tx=fsolve(f_dewt,(Tinit,xinit),args=(P,y,ant_parms,acm_parms))
        T,x=Tx
        return T.item(),x.item()

def isothermal_flash_scalar(z,T,P,ant_parms,acm_parms,Linit=0.5,xinit=0.1):
    def f_isoflash(Lx,z,T,P,ant_parms,acm_parms):
        pv=pvap(T,ant_parms)
        L,tx=Lx
        gA,gB=acm(tx,T,acm_parms)
        KA=gA*pv[0]/P
        KB=gB*pv[1]/P
        xA=z/(L+KA*(1-L))
        xB=(1-z)/(L+KB*(1-L))
        yA=KA*xA
        yB=KB*xB
        e1=(xA-tx)**2+(xB-(1-tx))**2
        e2=(yA+yB-1)**2
        return (e1,e2)
    L,x=fsolve(f_isoflash,(Linit,xinit),args=(z,T,P,ant_parms,acm_parms))
    pv=pvap(T,ant_parms)
    gA,gB=acm(x,T,acm_parms)
    KA=gA*pv[0]/P
    y=KA*x
    return L.item(),x.item(),y.item()   

def isothermal_flash(z,T,P,ant_parms,acm_parms,Linit=0.5,xinit=0.1):
    if hasattr(T,'__len__') and not hasattr(P,'__len__') and not hasattr(z,'__len__'):
        L=np.zeros(len(T))
        x=np.zeros(len(T))
        y=np.zeros(len(T))
        for i in range(len(T)):
            L[i],x[i],y[i]=isothermal_flash_scalar(z,T[i],P,ant_parms,acm_parms,Linit=Linit,xinit=xinit)
            Linit=L[i]
            xinit=x[i]
    elif hasattr(P,'__len__') and not hasattr(T,'__len__') and not hasattr(z,'__len__'):
        L=np.zeros(len(P))
        x=np.zeros(len(P))
        y=np.zeros(len(P))
        for i in range(len(P)):
            L[i],x[i],y[i]=isothermal_flash_scalar(z,T,P[i],ant_parms,acm_parms,Linit=Linit,xinit=xinit)
            Linit=L[i]
            xinit=x[i]
    elif hasattr(z,'__len__') and not hasattr(P,'__len__') and not hasattr(T,'__len__'):
        L=np.zeros(len(z))
        x=np.zeros(len(z))
        y=np.zeros(len(z))
        for i in range(len(z)):
            L[i],x[i],y[i]=isothermal_flash_scalar(z[i],T,P,ant_parms,acm_parms,Linit=Linit,xinit=xinit)
            Linit=L[i]
            xinit=x[i]
    elif hasattr(P,'__len__') and  hasattr(T,'__len__'):
        print('Error: isothermal_flash() cannot handle array comprehension on both T[] and P[].')
    elif hasattr(T,'__len__') and  hasattr(z,'__len__'):
        print('Error: isothermal_flash() cannot handle array comprehension on both T[] and z[].')
    elif hasattr(z,'__len__') and  hasattr(P,'__len__'):
        print('Error: isothermal_flash() cannot handle array comprehension on both z[] and P[].')
    else: # scalar
        L,x,y=isothermal_flash_scalar(z, T, P, ant_parms, acm_parms, Linit=Linit, xinit=xinit)
    return L,x,y


if __name__=='__main__':
    # ## Examples
    # 
    # BUBP calculation at a specific $x_A$ and $T$:
    x_A=0.295
    T=385 # K
    acmp=dict(TYPE='TWO-CONSTANT MARGULES',A=2200,B=800)
    a=np.array([9.9,9.7])
    b=np.array([-2700,-2800])
    c=np.array([-55,-57])
    antp=dict(A=a,B=b,C=c)
    Pbub,y=bubp(x_A,T,antp,acmp)
    print('Bubble point at x = %.3f and %.1f K is %.3f bar, y = %.3f.'%(x_A,T,Pbub,y))

    # BUBT calculation at a specific $x_A$ and $P$:
    x_A = 0.4
    P = 3.0
    Tbub,y = bubt(x_A,P,antp,acmp)
    print('Bubble point at x = %.3f and %.3f bar is %.2f K, y = %.3f.'%(x_A,P,Tbub,y))

    # DEWP calculation at a specific $y_A$ and $T$:
    y_A = 0.4
    T = 373
    Pdew,x = dewp(y_A,T,antp,acmp)
    print('Dew point at y = %.3f and %.1f K is %.2f bar, x = %.3f.'%(y_A,T,Pdew,x))

    # DEWT calculation at a specific $y_A$ and $P$:
    y_A = 0.68
    P = 2.9764
    Tdew,x = dewt(y_A,P,antp,acmp)
    print('Dew point at y = %.3f and %.2f bar is %.2f K, x = %.3f.'%(y_A,P,Tdew,x))

    # P-x-y diagram construction using a series of BUBP calculations at a specific $T$:
    num_points=100
    x=np.linspace(0,1,num_points)
    #acmp=dict(TYPE='VANLAAR',ALPHA=1.117,BETA=2.02)
    acmp=dict(TYPE='TWO-CONSTANT MARGULES',A=5000,B=1000)
    a=np.array([9.9,9.7])
    b=np.array([-2700,-2800])
    c=np.array([-55,-57])
    antp=dict(A=a,B=b,C=c)

    T=385 # K
    P,y=bubp(x,T,antp,acmp)

    plt.rcParams.update({'font.size': 16})
    plt.figure(figsize=(7,7))
    plt.xlabel('$x_1$, $y_1$')
    plt.ylabel('P [bar]')
    plt.title('P-x-y at T = %.1f K'%T)
    plt.xlim([0,1])
    plt.plot(x,P,'b-',label='Bubble point')
    plt.plot(y,P,'r-',label='Dew point')
    plt.legend()
    plt.savefig('myPxy1.pdf')
    plt.show()

    # P-x-y diagram construction using a series of DEWP calculations at a specific $T$:
    num_points=100
    y=np.linspace(0,1,num_points)
    T=373
    P,x=dewp(y,T,antp,acmp)
    plt.rcParams.update({'font.size': 16})
    plt.figure(figsize=(7,7))
    plt.xlabel('$x_1$, $y_1$')
    plt.ylabel('P (bar)')
    plt.title('P-x-y at T = %.1f K'%T)
    plt.xlim([0,1])
    plt.plot(x,P,'b-',label='Bubble point')
    plt.plot(y,P,'r-',label='Dew point')
    plt.legend()
    plt.savefig('myPxy2.pdf')
    plt.show()

    # T-x-y diagram construction using a series of BUBT calculations at a specific $P$:
    num_points=100
    x=np.linspace(0,1,num_points)
    P=3.75
    T,y=bubt(x,P,antp,acmp)

    plt.rcParams.update({'font.size': 16})
    plt.figure(figsize=(7,7))
    plt.xlabel('$x_1$, $y_1$')
    plt.ylabel('T (K)')
    plt.title('T-x-y at P = %.1f bar'%P)
    plt.xlim([0,1])
    plt.plot(x,T,'b-',label='Bubble point')
    plt.plot(y,T,'r-',label='Dew point')
    plt.legend()
    plt.savefig('myTxy1.pdf')
    plt.show()

    # T-x-y diagram construction using a series of DEWT calculations at a specific $P$:
    num_points=100
    y=np.linspace(0,1,num_points)
    P=3.75
    T,x=dewt(y,P,antp,acmp)

    plt.rcParams.update({'font.size': 16})
    plt.figure(figsize=(7,7))
    plt.xlabel('$x_1$, $y_1$')
    plt.ylabel('T (K)')
    plt.title('T-x-y at P = %.1f bar'%P)
    plt.xlim([0,1])
    plt.plot(x,T,'b-',label='Bubble point')
    plt.plot(y,T,'r-',label='Dew point')
    plt.savefig('myTxy2.pdf')
    plt.show()

    # Single isothermal flash at specific $z$, $P$, and $T$:
    z=0.4
    P=3.8
    T=375
    L,x,y=isothermal_flash(z,T,P,antp,acmp,Linit=0.2)
    print('Isothermal flash of z = %.2f at %.1f bar and %.1f K gives L = %.2f, x = %.3f, and y = %.3f.'%(z,P,T,L,x,y))

    # Series of isothermal flashes of at specific $z$ and $T$ for $P_{\rm dew} \le P \le P_{\rm bub}$:
    T=375
    z=0.4
    Pdew,xdum=dewp(z,T,antp,acmp)
    Pbub,xdum=bubp(z,T,antp,acmp)
    P=np.linspace(Pdew,Pbub,100)

    L,x,y=isothermal_flash(z,T,P,antp,acmp,Linit=0.1,xinit=0.1)

    plt.rcParams.update({'font.size': 16})
    plt.figure(figsize=(7,7))
    plt.xlabel('$P$ (bar)')
    plt.ylabel('$L$, $x$, $y$')
    plt.title('Isothermal flashes of $z$ = %.2f and $T$ = %.1f K'%(z,T))
    plt.ylim([0,1])
    plt.xlim([Pdew,Pbub])
    plt.plot(P,L,'b-',label='$L$')
    plt.plot(P,x,'r-',label='$x$')
    plt.plot(P,y,'g-',label='$y$')
    plt.legend()
    plt.savefig('myFlashP.pdf')
    plt.show()

    # Series of isothermal flashes of at specific $z$ and $P$ for $T_{\rm bub} \le T \le T_{\rm dew}$:
    P=4.2
    z=0.4
    Tdew,xdum=dewt(z,P,antp,acmp)
    Tbub,xdum=bubt(z,P,antp,acmp)
    T=np.linspace(Tbub,Tdew,100)

    L,x,y=isothermal_flash(z,T,P,antp,acmp,Linit=0.1,xinit=0.1)

    plt.rcParams.update({'font.size': 16})
    plt.figure(figsize=(7,7))
    plt.xlabel('$T$ (K)')
    plt.ylabel('$L$, $x$, $y$')
    plt.title('Isothermal flashes of $z$ = %.2f and $P$ = %.1f bar'%(z,P))
    plt.ylim([0,1])
    plt.xlim([Tbub,Tdew])
    plt.plot(T,L,'b-',label='$L$')
    plt.plot(T,x,'r-',label='$x$')
    plt.plot(T,y,'g-',label='$y$')
    plt.legend()
    plt.savefig('myFlashT.pdf')
    plt.show()
