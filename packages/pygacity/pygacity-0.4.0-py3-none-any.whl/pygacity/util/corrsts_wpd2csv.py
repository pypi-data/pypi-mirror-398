"""
convert data extracted from webplot digitizer to csv for corresponding states
"""

import pandas as pd
from importlib.resources import files

def wbd2csv(args):
    stem = args.stem
    resources_dir = files('pygplates') / "resources"
    data_dir = resources_dir / "corresponding-states-data"
    with open(data_dir / f'{stem}.raw','r') as f:
        lines=f.read().split('\n')
        blocks=[]
        for l in lines:
            if l.startswith('#'):
                tok=l.split()
                tr=float(tok[2])
                if tr>1:
                    d=dict(Tr=tr,Pr=[0.0],Dr=[0.0])
                else:
                    d=dict(Tr=tr,Pr=[],Dr=[])
                blocks.append(d)
            else:
                tok=l.split(',')
                x=float(tok[0])
                y=float(tok[1])
                d['Pr'].append(x)
                d['Dr'].append(y)

        dp=pd.DataFrame(columns=['Tr','Pr','Dr'])
        for b in blocks:
            tmp=pd.DataFrame.from_dict(b)
            # print(tmp.head())
            dp=pd.concat((dp,tmp))
        dp.to_csv(data_dir / f'{stem}.csv',index=False,header=True)
        print(f'wrote {data_dir / f"{stem}.csv"}')
