import json, sys, io
src, out = sys.argv[1], sys.argv[2]
W,S,E,N = 119.0, 21.0, 151.0, 48.0
TOL = 0.004
def clip(ring):
    def inside(p,edge):
        x,y=p
        return {'W':x>=W,'E':x<=E,'S':y>=S,'N':y<=N}[edge]
    def inter(a,b,edge):
        (x1,y1),(x2,y2)=a,b
        if edge in 'WE':
            x=W if edge=='W' else E; t=(x-x1)/(x2-x1); return (x,y1+t*(y2-y1))
        y=S if edge=='S' else N; t=(y-y1)/(y2-y1); return (x1+t*(x2-x1),y)
    poly=ring
    for edge in 'WESN':
        if not poly: return []
        outp=[]; prev=poly[-1]
        for cur in poly:
            if inside(cur,edge):
                if not inside(prev,edge): outp.append(inter(prev,cur,edge))
                outp.append(cur)
            elif inside(prev,edge): outp.append(inter(prev,cur,edge))
            prev=cur
        poly=outp
    return poly
def dp(pts,tol):
    if len(pts)<3: return pts
    import math
    def dist(p,a,b):
        (x,y),(x1,y1),(x2,y2)=p,a,b
        dx,dy=x2-x1,y2-y1
        if dx==0 and dy==0: return math.hypot(x-x1,y-y1)
        t=max(0,min(1,((x-x1)*dx+(y-y1)*dy)/(dx*dx+dy*dy)))
        return math.hypot(x-(x1+t*dx),y-(y1+t*dy))
    stack=[(0,len(pts)-1)]; keep=[False]*len(pts); keep[0]=keep[-1]=True
    while stack:
        i,j=stack.pop(); md=0; mi=-1
        for k in range(i+1,j):
            d=dist(pts[k],pts[i],pts[j])
            if d>md: md,mi=d,k
        if md>tol and mi>0:
            keep[mi]=True; stack.append((i,mi)); stack.append((mi,j))
    return [p for p,k in zip(pts,keep) if k]
data=json.load(io.open(src,encoding='utf-8'))
rings=[]
for f in data['features']:
    g=f['geometry']; polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
    for poly in polys:
        ext=[(float(x),float(y)) for x,y in poly[0]]
        xs=[p[0] for p in ext]; ys=[p[1] for p in ext]
        if max(xs)<W or min(xs)>E or max(ys)<S or min(ys)>N: continue
        c=clip(ext)
        if len(c)<4: continue
        c=dp(c,TOL)
        if len(c)<4: continue
        flat=[]
        for x,y in c: flat.append(round(x,3)); flat.append(round(y,3))
        rings.append(flat)
s=json.dumps(rings,separators=(',',':'))
io.open(out,'w',encoding='utf-8').write(s)
print('rings',len(rings),'points',sum(len(r)//2 for r in rings),'bytes',len(s))
