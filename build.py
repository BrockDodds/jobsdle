import json,glob,sys
d={}
for f in glob.glob(sys.argv[1]+'/d_*.json'):
    for s in json.load(open(f))['Results']['series']:
        for p in s['data']:
            if p['period']=='M13' or p['value'] in ('-',''): continue
            d.setdefault(s['seriesID'],{})[(int(p['year']),int(p['period'][1:]))]=float(p['value'])
N,U,C,L,W,M=[d[k] for k in ["CES0000000001","LNS14000000","CUSR0000SA0","LNS11300000","CES0500000008","CES3000000001"]]
def prev(k,n=1):
    y,m=k; m-=n
    while m<1: m+=12;y-=1
    return (y,m)
rows=[]
for k in sorted(N):
    if k<(1980,1): continue
    def g(f):
        try: return f()
        except KeyError: return None
    if prev(k) not in N: continue
    r=[k[0],k[1],round(N[k]-N[prev(k)])]+[g(f) for f in (lambda:U[k],lambda:round((C[k]/C[prev(k,12)]-1)*100,1),lambda:round((C[k]/C[prev(k)]-1)*100,1),lambda:L[k],lambda:round((W[k]/W[prev(k,12)]-1)*100,1),lambda:round(M[k]-M[prev(k)]),lambda:round(N[prev(k)]-N[prev(k,2)]),lambda:round(U[k]-U[prev(k)],1))]
    if False: r=[k[0],k[1],round(N[k]-N[prev(k)]),U[k],round((C[k]/C[prev(k,12)]-1)*100,1),round((C[k]/C[prev(k)]-1)*100,1),L[k],round((W[k]/W[prev(k,12)]-1)*100,1),round(M[k]-M[prev(k)]),round(N[prev(k)]-N[prev(k,2)]),round(U[k]-U[prev(k)],1)]
    rows.append(r)
print(len(rows),rows[0],rows[-3:],file=sys.stderr)
json.dump(rows,open(sys.argv[2],'w'),separators=(',',':'))
