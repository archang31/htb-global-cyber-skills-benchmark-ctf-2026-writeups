import sys, os, subprocess

def main():
    c = r"""
#include <stdio.h>
#define MAXN 524288
typedef long long ll;
static ll t[MAXN*2], d[MAXN*2];
static int n, h;
static inline void ap(int p,ll v){t[p]+=v;d[p]+=v;}
static inline void build(int p){for(p>>=1;p;p>>=1)t[p]=(t[2*p]>t[2*p+1]?t[2*p]:t[2*p+1])+d[p];}
static inline void push(int p){int s;ll di;for(s=h;s>0;s--){int i=p>>s;if((di=d[i])){ap(2*i,di);ap(2*i+1,di);d[i]=0;}}}
static inline void upd(int l,int r,ll v){int l0=l,r0=r;for(;l<=r;l>>=1,r>>=1){if(l&1)ap(l++,v);if(!(r&1))ap(r--,v);}build(l0);build(r0);}
static inline ll qry(int l,int r){push(l);push(r);ll res=0;for(;l<=r;l>>=1,r>>=1){if(l&1){if(t[l]>res)res=t[l];l++;}if(!(r&1)){if(t[r]>res)res=t[r];r--;}}return res;}
int main(){
    int N,Q,i;scanf("%d %d",&N,&Q);
    n=1;h=0;while(n<N){n<<=1;h++;}
    for(i=0;i<N;i++){int x;scanf("%d",&x);t[n+i]=x;}
    for(i=n-1;i>=1;i--)t[i]=t[2*i]>t[2*i+1]?t[2*i]:t[2*i+1];
    ll tot=0;char op[4];int l,r,v;
    for(i=0;i<Q;i++){
        scanf("%s",op);
        if(op[0]=='U'){scanf("%d %d %d",&l,&r,&v);upd(l+n,r+n,v);}
        else{scanf("%d %d",&l,&r);tot+=qry(l+n,r+n);}
    }
    printf("%lld\n",tot);return 0;
}
"""
    with open('/tmp/_sg.c', 'w') as f:
        f.write(c)
    os.system('gcc -O2 -o /tmp/_sg /tmp/_sg.c')
    data = sys.stdin.buffer.read()
    r = subprocess.run(['/tmp/_sg'], input=data, capture_output=True)
    sys.stdout.buffer.write(r.stdout)

main()
