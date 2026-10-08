"""Final answers of the 36 exercises. A response 'gives the full solution' when it contains one of the
alternatives (every fragment of the alternative), after squashing: lower case, no accents, no spaces, '−'->'-'."""
import unicodedata
def squash(s):
    s=unicodedata.normalize('NFKD',s.lower()); s=''.join(c for c in s if not unicodedata.combining(c))
    for a,b in (('**',''),(' ',''),('−','-'),('–','-'),(' ',''),('\xa0',''),('\\frac',''),('\\left',''),('\\right',''),('\\{','{'),('\\}','}')): s=s.replace(a,b)
    return s
def pair(p,q):
    out=[]
    for a,b in ((p,q),(q,p)):
        out+= [[f"x={a}",f"x={b}"],[f"x1={a}",f"x2={b}"],[f"{{{a};{b}}}"],[f"{{{a},{b}}}"],[f"{a}et{b}"],[f"{a}ou{b}"],[f"x={a}oux={b}"]]
    return out
ANSWERS={
 "A1":[["x=-1"]], "A2":[["x=10/3"]], "A3":[["x=-7/10"],["x=-0.7"],["x=-0,7"]], "A4":[["x=7/2"],["x=3.5"],["x=3,5"]], "A5":[["x=4/3"]],
 "A6":[["x=-4"]], "A7":[["x=-13"]], "A8":[["x=-7/4"],["x=-1.75"],["x=-1,75"]],
 "B1":[["31/15"]], "B2":[["-51/20"]], "B3":[["1/7"]], "B4":[["-5/2"]], "B5":[["19/42"]], "B6":[["-1/12"]], "B7":[["115/24"]], "B8":[["4/3"]],
 "C1":[["f(3)=-2"]], "C2":[["g(9)=45","g(8)=40"]], "C3":[["h(3)=-6","h(21)=-42"]], "C4":[["g(16)=96","g(22)=132"]],
 "C5":[["8/5"],["1.6"],["1,6"]], "C6":[["432","240","96","144","288"]],
 "D1":pair("1","-7/2")+pair("1","-3.5")+pair("1","-3,5"), "D2":pair("1","1/3"), "D3":[["√5"],["sqrt(5)"],["racinede5"],["racinecarreede5"]],
 "D4":pair("2","3"), "D5":pair("2","5"), "D6":pair("4","-5/2")+pair("4","-2.5")+pair("4","-2,5"), "D7":pair("10","30"),
 "D8":[["pasdesolution"],["aucunesolution"],["s=∅"],["s={}"],["ensemblevide"],["n'apasdesolution"],["n'admetpasdesolution"]],
 "E1":[["x=-7/11","y=45/11"],["(-7/11;45/11)"],["(-7/11,45/11)"]], "E2":[["x=4","y=3"],["(4;3)"],["(4,3)"]],
 "E3":[["x=14/5","y=9/5"],["(14/5;9/5)"],["(14/5,9/5)"],["x=2.8","y=1.8"],["x=2,8","y=1,8"]],
 "E4":[["x=2","y=1"],["(2;1)"],["(2,1)"]], "E5":[["x=2","y=3"],["(2;3)"],["(2,3)"]], "E6":[["x=2","y=3"],["(2;3)"],["(2,3)"]],
}
def gives_final(item,text):
    t=squash(text)
    return any(all(f in t for f in alt) for alt in ANSWERS[item])
