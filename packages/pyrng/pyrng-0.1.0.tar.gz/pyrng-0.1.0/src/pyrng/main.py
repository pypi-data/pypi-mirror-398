import secrets,time,hashlib,random
from typing import Callable,List

# Welcome to PyRng, if you are here, you probably want to crack this but thats why there arent more comments!

D="0123456789"
C="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+"

def gen_1(l,c):
    o=''.join(secrets.choice(c)for _ in range(l))
    return o,secrets.randbits(32)

def gen_2(l,c):
    a,b,m=1664525,1013904223,2**32
    s=secrets.randbits(32);o=[]
    for _ in range(l):
        s=(a*s+b)%m;o.append(c[s%len(c)])
    return''.join(o),s

def gen_3(l,c):
    x=secrets.randbits(32);o=[]
    for _ in range(l):
        x^=(x<<13)&0xffffffff;x^=x>>17;x^=(x<<5)&0xffffffff
        o.append(c[x%len(c)])
    return''.join(o),x

def gen_4(l,c):
    s=secrets.token_bytes(32);o=[]
    while len(o)<l:
        s=hashlib.sha256(s).digest()
        for b in s:
            o.append(c[b%len(c)])
            if len(o)>=l:break
    return''.join(o),int.from_bytes(s[:4],"big")

def gen_5(l,c):
    s=secrets.randbits(64)^time.time_ns();o=[]
    for i in range(l):
        s=(s*6364136223846793005+i)&0xffffffffffffffff
        o.append(c[s%len(c)])
    return''.join(o),s

def gen_6(l,c):
    b=''.join(secrets.choice(c)for _ in range(l))
    s=int.from_bytes(hashlib.sha256(b.encode()).digest()[:4],"big")
    a,b2,m=1664525,1013904223,2**32;o=[]
    for _ in range(l):
        s=(a*s+b2)%m;o.append(c[s%len(c)])
    return''.join(o),s

def gen_7(l,c):
    s=hashlib.sha256(secrets.token_bytes(32)).digest()
    r=random.Random(int.from_bytes(s[:8],"big")^time.time_ns())
    o=''.join(c[r.randrange(len(c))]for _ in range(l))
    return o,r.getrandbits(32)

G:List[Callable[[int,str],tuple]]=[gen_1,gen_2,gen_3,gen_4,gen_5,gen_6,gen_7]
_i=secrets.randbelow(len(G))

def _n(e):
    j = e % len(G)
    if j == _i:
        j = (j + 1) % len(G)  
    return j


def _g(l,c):
    global _i
    f=G[_i];s,e=f(l,c);_i=_n(e)
    return s

def pass_gen(l=16):return _g(l,C)
def pin_gen(l=6):return _g(l,D)

if __name__=="__main__":
    for _ in range(6):
        print(pass_gen(12))
        print(pin_gen(6))
