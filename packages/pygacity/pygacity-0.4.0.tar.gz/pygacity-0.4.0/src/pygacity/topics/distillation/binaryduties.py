import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve
from scipy.interpolate import interp1d
import pandas as pd
from matplotlib.ticker import AutoMinorLocator, MultipleLocator
from pygacity.pick import *

def Antoine(T,pardict):
    A,B,C=pardict['A'],pardict['B'],pardict['C']
    return np.exp(A-B/(T+C))

def BUBT(P,x,par):
    ap1,ap2=par
    def zerome(T,x,P,ap1,ap2):
        pv1=Antoine(T,ap1)
        pv2=Antoine(T,ap2)
        Papp=x*pv1+(1-x)*pv2
        return (P-Papp)**2
    T=fsolve(zerome,300,args=(x,P,ap1,ap2))[0]
    return T

def compute_Txy_Raoults(specs):
    P=specs['Column']['Pressure']
    ap1=specs['Components']['A']['Antoine']
    ap2=specs['Components']['B']['Antoine']
    xdomain=np.linspace(0,1,21)
    T,y=[],[]
    for x in xdomain:
        thisT=BUBT(P,x,[ap1,ap2])
        thisy=x*Antoine(thisT,ap1)/P
        T.append(thisT)
        y.append(thisy)
    T_of_x=interp1d(xdomain,np.array(T))
    T_of_y=interp1d(np.array(y),np.array(T))
    y_of_x=interp1d(xdomain,np.array(y))
    x_of_y=interp1d(np.array(y),xdomain)
    specs["Components"]["A"]["NormalBoilingPoint"]=T[-1]
    specs["Components"]["B"]["NormalBoilingPoint"]=T[0]
    specs["Thermodynamics"]["Interpolators"]={'T_of_x':T_of_x,'T_of_y':T_of_y,'y_of_x':y_of_x,'x_of_y':x_of_y}
    if 'Txy_xy_graphic' in specs["Thermodynamics"]:
        plot_Txy(xdomain,y,T,filename=specs["Thermodynamics"]["Txy_xy_graphic"])
    return specs

def plot_Txy(X,Y,T,**kwargs):
    fig,ax=plt.subplots(1,2,figsize=kwargs.get('figsize',(12,6)))
    filename=kwargs.get('filename','Txy-xy.png')
    T_major_inc=kwargs.get('T_major_inc',5)
    minT,maxT=min(T),max(T)
    Tlow=int(np.round(minT,0))-int(np.round(minT,0))%T_major_inc
    Thi=int(np.round(maxT,0))+(T_major_inc-int(np.round(maxT,0))%T_major_inc)
    ax1,ax2=ax
    ax1.set_xlim([0,1])
    ax1.xaxis.set_minor_locator(MultipleLocator(0.02))
    ax1.yaxis.set_minor_locator(MultipleLocator(1))
    ax1.set_ylim(kwargs.get('ylim',[Tlow,Thi]))
    ax1.grid(visible=True,which='major',axis='both',color='k',linestyle='-',linewidth=0.8,alpha=0.6)
    ax1.grid(visible=True,which='minor',axis='both',color='k',linestyle='-',linewidth=0.5,alpha=0.4)    
    ax2.grid(visible=True,which='major',axis='both',color='k',linestyle='-',linewidth=0.8,alpha=0.6)
    ax2.grid(visible=True,which='minor',axis='both',color='k',linestyle='-',linewidth=0.5,alpha=0.4)

    ax1.set_yticks(kwargs.get('yticks',np.arange(Tlow,Thi+1,T_major_inc)))
    ax1.set_xlabel('x')
    ax1.set_ylabel('T (K)')
    ax1.plot(X,T,label='Bubble points')
    ax1.plot(Y,T,label='Dew points')
    ax1.set_xticks(np.linspace(0,1,11))
    ax2.set_xticks(np.linspace(0,1,11))
    ax2.set_yticks(np.linspace(0,1,11))
    ax1.legend()
    ax2.xaxis.set_minor_locator(MultipleLocator(0.02))
    ax2.yaxis.set_minor_locator(MultipleLocator(0.02))
    ax2.set_xlim([0,1])
    ax2.set_ylim([0,1])
    ax2.set_xlabel('x')
    ax2.set_ylabel('y')
    ax2.plot(X,X,'k--')
    ax2.plot(X,Y,'b-')
    plt.savefig(filename,bbox_inches='tight')
    plt.clf()

def Txy(specs):
    # if Antoine parameters are given, compute
    # Txy data using Raoult's law
    if 'Components' in specs:
        comp=specs['Components']
        has_params=np.all(['Antoine' in x for x in comp.values()])
        if has_params:
            specs=compute_Txy_Raoults(specs)
    elif 'EquilibriumData' in specs:
        pass
    return specs

def plot_pvap(specs,**kwargs):
    ap1=specs['Components']['A']['Antoine']
    ap2=specs['Components']['B']['Antoine']
    Tdomain=kwargs.get('Tdomain',np.linspace(250,500,26))
    pv1,pv2=[],[]
    for T in Tdomain:
        pv1.append(Antoine(T,ap1))
        pv2.append(Antoine(T,ap2))
    fig,ax=plt.subplots(1,1,figsize=(6,6))
    ax.set_xlabel('T (K)')
    ax.set_ylabel('Pvap (bar)')
    ax.set_ylim(kwargs.get('ylim',[0,30]))
    ax.plot(Tdomain,pv1,label='Comp1')
    ax.plot(Tdomain,pv2,label='Comp2')
    ax.legend()
    plt.show()

def AllFlows(specs):
    sumFz=0.0
    sumF=0.0
    zlist=[]
    qlist=[]
    llist=[]
    nlist=[]
    for name,feed in specs['Streams']['Feeds'].items():
        F=feed['Ndot']
        z=feed['Components']['A']['MoleFraction']
        q=feed['q']
        sumFz+=F*z
        sumF+=F
        llist.append(name)
        zlist.append(z)
        qlist.append(q)
        nlist.append(F)
    feeddf=pd.DataFrame({'Feed':llist,'N':nlist,'z':zlist,'q':qlist})
    feeddf.set_index('Feed',inplace=True)
    xB=specs['Streams']['B']['Components']['A']['MoleFraction']
    xD=specs['Streams']['D']['Components']['A']['MoleFraction']
    if 'Thermodynamics' in specs:
        try:
            y_of_x=specs['Thermodynamics']['Interpolators']['y_of_x']
            T_of_x=specs['Thermodynamics']['Interpolators']['T_of_x']
            T_of_y=specs['Thermodynamics']['Interpolators']['T_of_y']
        except:
            raise Exception('No binary equilibrium interpolators found')
        specs['Reboiler']['T']=T_of_x(xB)
        # temperature of condenser producing saturated liquid
        specs['Condenser']['T']=T_of_x(xD)
        if specs['Reboiler']['Type']=='Partial':
        # composition of boilup vapor
            ybar=y_of_x(xB)
        else:
            ybar=xB
        specs['Column']['ybar']=ybar
    # sumFz = D xD + B xB = (sumF-B) xD + B xB
    # sumFz = sumF xD + B (xB - xD)
    # (sumFz - sumF xD)/(xB - xD) = B = (sumF xD - sumFz)/(xD - xB)
    B=(sumF*xD-sumFz)/(xD-xB)
    # what={'sumF':sumF,'sumFz':sumFz,'xD':xD,'sumFz*xD':sumFz*xD,'numerator':(sumF*xD-sumFz),'denominator':(xD-xB),'B':B}
    # print(what)
    D=sumF-B
    specs['Streams']['B']['Ndot']=B
    specs['Streams']['D']['Ndot']=D
    if 'boilup_ratio' in specs['Column']:
        # sort feed keys along decreasing z and tiebreak with increasing q
        feeddf.sort_values(by=['z','q'],ascending=[True,False],inplace=True)
        # print(feeddf.to_string())
        specs['Column']['FeedOrder']=feeddf.index.to_list()
        br=specs['Column']['boilup_ratio']
        Vbar=B*br
        Lbar=Vbar+B
        if 'Thermodynamics' in specs:
            xbar=(xB*B+ybar*Vbar)/Lbar
            specs['Column']['xbar']=xbar
        specs['Column']['Vbar']=Vbar
        specs['Column']['Lbar']=Lbar
        # feed tray phase balances under CMO
        vin,vout,lin,lout=[],[],[],[]
        for f in specs['Column']['FeedOrder']:
            feed=specs['Streams']['Feeds'][f]
            F=feed['Ndot']
            q=feed['q']
            feed['V_in']=Vbar
            feed['L_out']=Lbar
            feed['V_out']=feed['V_in']+(1-q)*F
            feed['L_in']=feed['L_out']-q*F
            vin.append(feed['V_in'])
            vout.append(feed['V_out'])
            lin.append(feed['L_in'])
            lout.append(feed['L_out'])
            Vbar=feed['V_out']
            Lbar=feed['L_in']
        feeddf['V_in']=vin
        feeddf['V_out']=vout
        feeddf['L_in']=lin
        feeddf['L_out']=lout
        # print(feeddf.to_string())
        V=Vbar
        L=Lbar
        specs['Column']['V_calc']=V
        specs['Column']['L_calc']=L
        specs['Column']['reflux_ratio_calc']=L/D
    elif 'reflux_ratio' in specs['Column']:
        # apply CMO down the column; feed with highest z topmost
        feeddf.sort_values(by=['z','q'],ascending=[False,False],inplace=True)
        specs['Column']['FeedOrder']=feeddf.index.to_list()
        rr=specs['Column']['reflux_ratio']
        L=rr*D
        V=D+L
        specs['Column']['V']=V
        specs['Column']['L']=L
        specs['Column']['y']=specs['Streams']['D']['Components']['A']['MoleFraction']
        # feed tray phase balances under CMO
        vin,vout,lin,lout=[],[],[],[]
        for f in specs['Column']['FeedOrder']:
            feed=specs['Streams']['Feeds'][f]
            # print(f'feed {f}')
            F=feed['Ndot']
            q=feed['q']
            feed['V_out']=V
            feed['L_in']=L
            feed['V_in']=V-(1-q)*F
            feed['L_out']=L+q*F
            vin.append(feed['V_in'])
            vout.append(feed['V_out'])
            lin.append(feed['L_in'])
            lout.append(feed['L_out'])
            V=feed['V_in']
            L=feed['L_out']
        Vbar=V
        Lbar=L
        feeddf['V_in']=vin
        feeddf['V_out']=vout
        feeddf['L_in']=lin
        feeddf['L_out']=lout
        specs['Column']['Vbar_calc']=Vbar
        specs['Column']['Lbar_calc']=Lbar
        specs['Column']['boilup_ratio_calc']=Vbar/B
        if 'Thermodynamics' in specs:
            xbar=(ybar*Vbar+xB*B)/Lbar
            specs['Column']['ybar']=ybar
            specs['Column']['xbar']=xbar
    else:
        raise Exception('Must specify either boilup ratio or reflux ratio')
    specs['Column']['FeedsSummaryDataFrame']=feeddf
    return specs

def cpdt(poly,T2,T1):
    p=1
    ltrs='abcdefghij'
    idx=0
    dh=0
    while ltrs[idx] in poly:
        dh+=1/p*poly[ltrs[idx]]*(T2**p-T1**p)
        p+=1
        idx+=1
    return dh

def hcalc(T,Tref,Cpl_poly):
    return cpdt(Cpl_poly,T,Tref)

def Hcalc(T,Tref,Tboil,Hvap,Cpv_poly,Cpl_poly):
    return cpdt(Cpl_poly,Tboil,Tref)+Hvap+cpdt(Cpv_poly,T,Tboil)

def AllDuties(specs):
    if not 'Thermodynamics' in specs:
        return specs
    Tref=specs['Thermodynamics']['Tref']
    TR=specs['Reboiler']['T']
    TC=specs['Condenser']['T']
    streams=specs["Streams"]
    B=streams['B']['Ndot']
    D=streams['D']['Ndot']
    xB=streams["B"]["Components"]["A"]["MoleFraction"]
    xD=streams["D"]["Components"]["A"]["MoleFraction"]
    comp=specs["Components"]
    Hvap1=comp["A"]["Hvap"]
    Hvap2=comp["B"]["Hvap"]
    try:
        Tboil1=comp["A"]['NormalBoilingPoint']
        Tboil2=comp["B"]['NormalBoilingPoint']
    except:
        raise Exception('Error: Normal boiling points not specified/calculated')
    Cpv_poly1=comp["A"]['Cpv']
    Cpv_poly2=comp["B"]['Cpv']
    Cpl_poly1=comp["A"]['Cpl']
    Cpl_poly2=comp["B"]['Cpl']

    if 'boilup_ratio' in specs['Column']:
        L=specs['Column']['L_calc']
        V=specs['Column']['V_calc']
        Vbar=specs['Column']['Vbar']
        Lbar=specs['Column']['Lbar']
    elif 'reflux_ratio' in specs['Column']:
        L=specs['Column']['L']
        V=specs['Column']['V']
        Vbar=specs['Column']['Vbar_calc']
        Lbar=specs['Column']['Lbar_calc']
    ybar=specs['Column']['ybar']
    xbar=specs['Column']['xbar']
    # temperature of stage N feeding reboiler
    Tbar=specs['Thermodynamics']['Interpolators']['T_of_x'](xbar)
    specs['Column']['Tbar']=Tbar
    # print(specs["Streams"]["Feeds"])
    for feed in specs["Streams"]["Feeds"].values():
        # print(','.join(feed.keys()))
        F=feed["Ndot"]
        z=feed["Components"]["A"]["MoleFraction"]
        q=feed["q"]
        if q==1.0:
            # temperature of saturated liquid feed
            TF=specs['Thermodynamics']['Interpolators']['T_of_x'](z)
            feed['T']=TF
            # enthalpy per mole of feed
            hFA=hcalc(TF,Tref,Cpl_poly1)
            hFB=hcalc(TF,Tref,Cpl_poly2)
            hF=z*hFA+(1-z)*hFB
            feed["Components"]["A"]["MolarEnthalpy"]=hFA
            feed["Components"]["B"]["MolarEnthalpy"]=hFB
            feed["MolarEnthalpy"]=hF
        else:
            raise Exception('Cannot handle feeds other than saturated liquids for now')
    # enthalpy per mole of entering liquid Lbar
    hbarA=hcalc(Tbar,Tref,Cpl_poly1)
    hbarB=hcalc(Tbar,Tref,Cpl_poly2)
    hbar=xbar*hbarA+(1-xbar)*hbarB
    # bottoms product B
    hBA=hcalc(TR,Tref,Cpl_poly1)
    hBB=hcalc(TR,Tref,Cpl_poly2)
    hB=xB*hBA+(1-xB)*hBB
    # vapor boilup Vbar
    HbarA=Hcalc(TR,Tref,Tboil1,Hvap1,Cpv_poly1,Cpl_poly1)
    HbarB=Hcalc(TR,Tref,Tboil2,Hvap2,Cpv_poly2,Cpl_poly2)
    Hbar=ybar*HbarA+(1-ybar)*HbarB
    specs['Reboiler']['hbar']=hbar
    specs['Reboiler']['hbarA']=hbarA
    specs['Reboiler']['hbarB']=hbarB
    specs['Reboiler']['Hbar']=Hbar
    specs['Reboiler']['HbarA']=HbarA
    specs['Reboiler']['HbarB']=HbarB
    streams["B"]["MolarEnthalpy"]=hB
    streams["B"]["Components"]["A"]["MolarEnthalpy"]=hBA
    streams["B"]["Components"]["B"]["MolarEnthalpy"]=hBB
    # Need enthalpy of vapor stream leaving tray 1, so need temperature of tray 1
    # this must be the temperature at which a vapor with composition xD=y1 is in VLE
    T1=specs['Thermodynamics']['Interpolators']['T_of_y'](xD)
    # if the condenser outlet is saturated liquid, this will also be the temperature of the condenser
    # vapor inlet V
    HVA=Hcalc(T1,Tref,Tboil1,Hvap1,Cpv_poly1,Cpl_poly1)
    HVB=Hcalc(T1,Tref,Tboil2,Hvap2,Cpv_poly2,Cpl_poly2)
    HV=xD*HVA+(1-xD)*HVB
    # distillate product D(+L)
    hDA=hcalc(TC,Tref,Cpl_poly1)
    hDB=hcalc(TC,Tref,Cpl_poly2)
    hD=xD*hDA+(1-xD)*hDB
    specs['Column']['T1']=T1
    specs['Condenser']['HVA']=HVA
    specs['Condenser']['HVB']=HVB
    specs['Condenser']['HV']=HV
    streams["D"]["MolarEnthalpy"]=hD
    streams["D"]["Components"]["A"]["MolarEnthalpy"]=hDA
    streams["D"]["Components"]["B"]["MolarEnthalpy"]=hDB
    if 'boilup_ratio' in specs['Column']:
        # energy balance around reboiler
        # Lbar hbar + Q_R = B hB + Vbar Hbar
        specs['Reboiler']['Duty']=B*hB+Vbar*Hbar-Lbar*hbar
        # energy balance around total condenser
        specs['Condenser']['CMO-Duty']=V*(hD-HV) #(D+L)*hD-V*HV
        specs['Column']['Condenser-Duty']=B*hB+D*hD-F*hF-specs['Reboiler']['Duty']
    elif 'reflux_ratio' in specs['Column']:
        specs['Condenser']['Duty']=V*(hD-HV)
        specs['Column']['Reboiler-Duty']=B*hB+D*hD-F*hF-specs['Condenser']['Duty']
        specs['Reboiler']['CMO-Duty']=B*hB+Vbar*Hbar-Lbar*hbar
    return specs

def process_input(specs):
    if "Column" in specs:
        if "reflux_ratio" in specs["Column"] and "boilup_ratio" in specs["Column"] and len(specs["Components"])==2:
            raise Exception('You cannot specify both a reflux ratio and a boilup ratio in binary distillation')
    streams=specs['Streams']
    for sname,sdict in streams.items():
        if sname=='Feeds':
            for fname,fdict in sdict.items():
                fdict['Components']=mf_restraints(fdict['Components'])
        else:
            sdict['Components']=mf_restraints(sdict['Components'])
    return specs

def mf_restraints(component_dict):
    unsets=[]
    smf=0.0
    for cname,cdict in component_dict.items():
        smf+=cdict.get('MoleFraction',0.0)
        if not 'MoleFraction' in cdict:
            unsets.append(cname)
    if len(unsets)==1:
        component_dict[unsets[0]]['MoleFraction']=1.0-smf
    return component_dict


def solve(specs,duties=True):
    specs=process_input(specs)
    specs=Txy(specs)
    specs=AllFlows(specs)
    if duties:
        specs=AllDuties(specs)
    return specs

if __name__=='__main__':
    specs={
        'tag':13424726,
        'Streams':{
            'Feeds':{
                'F1':{
                    'Ndot':{'pick':{'pickfrom':[90,100,110]}},'q':{'pick':{'pickfrom':[0,1]}},
                    'Components':{
                        'A':{'MoleFraction':{'pick':{'between':[0.6,0.7],'round':2}}},
                        'B':{}
                        }
                    },
                'F2':{
                    'Ndot':{'pick':{'pickfrom':[90,100,110]}},'q':{'pick':{'pickfrom':[0.25,0.75]}},
                    'Components':{
                        'A':{'MoleFraction':{'pick':{'between':[0.35,0.55],'round':2}}},
                        'B':{}
                        }
                    }
                },
            'B':{'Components':{
                'A':{},
                'B':{'MoleFraction':{'pick':{'between':[0.85,0.95],'round':2}}}
                }
            },
            'D':{'Components':{
                'A':{'MoleFraction':{'pick':{'between':[0.85,0.99],'round':2}}},
                'B':{}
                }}
        }, 
        'Column':{'reflux_ratio':{'pick':{'between':[1.3,2.7]}},'Pressure':1},
        'Components':{
            'A':{'name':'1','Hvap':{'pick':{'pickfrom':[990,1000,1100]}},'Cpv':{'a':{'pick':{'pickfrom':[34,35,36]}},'b':{'pick':{'pickfrom':[0.15,0.20,0.25]}}},'Cpl':{'a':{'pick':{'pickfrom':[34,35,36]}}},
            'Antoine':{'A':{'pick':{'pickfrom':[11.9,12,12.1]}},'B':{'pick':{'pickfrom':[3975,4000,4025]}},'C':{'pick':{'pickfrom':[44,45,46]}}}},
            'B':{'name':'2','Hvap':{'pick':{'pickfrom':[1175,1200,1225]}},'Cpv':{'a':{'pick':{'pickfrom':[26,27,28]}},'b':{'pick':{'pickfrom':[0.05,0.1,0.15]}}},'Cpl':{'a':{'pick':{'pickfrom':[31,32,33]}}},
            'Antoine':{'A':{'pick':{'pickfrom':[9.9,10,10.1]}},'B':{'pick':{'pickfrom':[3775,3800,3825]}},'C':{'pick':{'pickfrom':[49,50,51]}}}}
        },
        'Thermodynamics':{'Tref':200},
        'Condenser':{'Type':'Total'},
        'Reboiler':{'Type':'Partial'},
    }
    specs=pick_state(specs)
    specs=process_input(specs)
    specs=Txy(specs)
    specs=AllFlows(specs)
    # specs=AllDuties(specs)
    # print(specs['Streams'])
    # print(specs['Column'])
    # print(specs['Reboiler'])
    # print(specs['Condenser'])
    feeddf=specs['Column']['FeedsSummaryDataFrame']
    print(feeddf.to_string())
    # F1=feeddf.loc['F','N']
    # print(F1)
#    res=pick_state(0,specs)
    #print(res)