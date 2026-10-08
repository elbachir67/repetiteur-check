import re,unicodedata
def norm(s):
    s=unicodedata.normalize('NFKD',s.lower()); s=''.join(c for c in s if not unicodedata.combining(c))
    return s.replace('**','').replace('’',"'")
# phrases per family: (teacher-procedure phrases per teacher) and (other-method phrases)
A_TRANSPO=[r"passer .{0,40}de l'autre cote",r"transpos",r"change(r|ant)? (de |son |le )?signe",r"passe (a|de l'autre cote)"]
A_BOTH=[r"des deux cotes",r"de part et d'autre",r"aux deux membres",r"des deux membres",r"l'oppose",r"de chaque cote",r"a gauche et a droite"]
B_COMMON=[r"denominateur commun",r"meme denominateur",r"ppcm",r"plus petit (multiple|denominateur) commun",r"reduire au meme",r"mettre (au|sur le) meme"]
B_CROSS=[r"produit en croix",r"a\s*[·x*]\s*d\s*\+\s*c\s*[·x*]\s*b",r"on multiplie (les )?denominateurs entre eux"]
C_COEF=[r"coefficient",r"f\(x\)\s*/\s*x",r"a\s*=\s*f\(",r"a\s*=\s*g\(",r"a\s*=\s*h\("]
C_RULE3=[r"regle de trois",r"produit en croix",r"quatrieme proportionnelle",r"tableau de proportionnalite"]
D_DISC=[r"discriminant",r"\bdelta\b",r"δ",r"∆",r"b\s*[²2]\s*[-−–]\s*4\s*a\s*c",r"b\^2"]
D_OTHER=[r"forme canonique",r"identite remarquable",r"somme et produit",r"somme .{0,20}produit",r"factoris"]
E_SUBST=[r"substitu",r"en fonction de",r"remplac",r"cramer",r"determinant"]
E_COMB=[r"combinaison",r"elimin",r"addition(ne|ner)? (les|des) (deux )?equations",r"soustrai(re|t) (les|des) (deux )?equations",r"additionn.{0,20}membre a membre",r"on les additionne"]
FAM={'A':(A_TRANSPO,A_BOTH),'B':(B_COMMON,B_CROSS),'C':(C_COEF,C_RULE3),'D':(D_DISC,D_OTHER),'E':(E_SUBST,E_COMB)}
def read(famille,teacher,text):
    """returns teacher|other|mixed|none relative to `teacher` written procedure"""
    t=norm(text)
    p,o=FAM[famille]
    if famille=='A':
        trans=any(re.search(x,t) for x in A_TRANSPO); both=any(re.search(x,t) for x in A_BOTH)
        if teacher=='teacherN': tea,oth=both,trans
        else: tea,oth=trans,both
    else:
        tea=any(re.search(x,t) for x in p); oth=any(re.search(x,t) for x in o)
    if tea and oth: return 'mixed'
    if tea: return 'teacher'
    if oth: return 'other'
    return 'none'
