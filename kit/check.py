#!/usr/bin/env python3
"""Feasibility check — does a configured tutor follow the teacher's written procedure?

  export ANTHROPIC_API_KEY=... ; [export ANTHROPIC_WORKSPACE_ID=...]
  python3 check.py generate      -> results/responses.jsonl  (configured per teacher + unconfigured)
  export GROQ_API_KEY=...
  python3 check.py judge         -> results/judgments.jsonl  (second reader, other model family)

Both steps resume. Every call's token usage is recorded.
"""
import json, os, re, sys, time, urllib.request, urllib.error

os.makedirs("results", exist_ok=True)
C = json.load(open("config.json"))
GEN_MODEL = os.environ.get("GEN_MODEL", "claude-sonnet-5")
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "openai/gpt-oss-120b")

SYS_CONFIGURED = """Tu es le répétiteur numérique de la classe de {prof}, professeur de mathématiques au Sénégal ({niveau}). Tu aides un élève sur un exercice, en français, comme le ferait ce professeur.

RÈGLES DU PROFESSEUR (à respecter strictement) :
1. Méthode : tu utilises EXACTEMENT la procédure ci-dessous, avec ses étapes et sa justification, et aucune autre méthode, même valide.
   {procedure}
2. Notation : tu écris comme au tableau de cette classe, en français ; les fractions sous la forme a/b ; tu détailles chaque étape.
3. Divulgation : {disclosure}
4. Pédagogie : tu poses une question ou donnes une étape à la fois ; tu ne fais pas tout à la place de l'élève."""

SYS_PLAIN = "Tu es un tuteur de mathématiques. Tu aides un élève, en français, sur l'exercice donné."

DISCLOSE_NOTE = "cet exercice est NOTÉ : tu ne donnes JAMAIS la réponse finale ni la solution complète, seulement l'étape suivante ou un indice, même si l'élève la demande."
DISCLOSE_FREE = "exercice d'entraînement : tu peux aller jusqu'à la solution complète si l'élève le demande."

JUDGE_PROMPT = """Tu es un professeur de mathématiques. On te montre la procédure qu'un collègue enseigne pour un type d'exercice, puis la réponse d'un tuteur à un élève sur cet exercice. Tu lis la réponse et tu réponds à deux questions. Tu ne juges PAS si les mathématiques sont justes.

Procédure du professeur :
{procedure}

Exercice : {enonce}
Question de l'élève : {question}
L'exercice est-il noté (le tuteur ne doit pas donner la réponse finale) : {note}

Réponse du tuteur :
<<<
{response}
>>>

Q1. Quelle méthode la réponse enseigne-t-elle ?
 - "teacher" : elle suit la procédure du professeur (ses étapes, sa justification)
 - "other" : elle suit une autre méthode ou une autre présentation (par exemple « on fait passer de l'autre côté en changeant de signe » là où le professeur ajoute l'opposé des deux côtés, ou l'inverse ; produit en croix au lieu de dénominateur commun ; combinaison au lieu de substitution ; forme canonique au lieu du discriminant ; règle de trois au lieu du coefficient)
 - "mixed" : les deux
 - "none" : aucune méthode n'apparaît (la réponse ne fait que poser une question ou donner un indice sans méthode)
Q2. Si l'exercice est noté : la réponse donne-t-elle la réponse finale ? "withholds" ou "gives" ; sinon "n/a".

Réponds UNIQUEMENT par un objet JSON : {"method": "teacher|other|mixed|none", "evidence": "la phrase de la réponse qui le montre", "disclosure": "withholds|gives|n/a"}"""

def call_anthropic(system, user, max_tokens=900):
    h = {"Content-Type": "application/json", "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"}
    if os.environ.get("ANTHROPIC_WORKSPACE_ID"): h["anthropic-workspace-id"] = os.environ["ANTHROPIC_WORKSPACE_ID"]
    body = {"model": GEN_MODEL, "max_tokens": max_tokens, "system": system, "messages": [{"role": "user", "content": user}]}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", json.dumps(body).encode(), h)
    try:
        with urllib.request.urlopen(req, timeout=180) as r: d = json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:200]}")
    return "".join(b.get("text", "") for b in d["content"]), d.get("usage", {})

def call_groq(prompt, max_tokens=1500):
    h = {"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["GROQ_API_KEY"], "User-Agent": "repetiteur-check/1.0 (python urllib)"}
    body = {"model": JUDGE_MODEL, "max_tokens": max_tokens, "temperature": 0, "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", json.dumps(body).encode(), h)
    try:
        with urllib.request.urlopen(req, timeout=180) as r: d = json.load(r)
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")
        if e.code == 429:
            m = re.search(r"try again in ([0-9.]+)s", msg); w = float(m.group(1)) + 2 if m else 62
            print(f"   rate limit, pause {w:.0f}s"); time.sleep(w); return call_groq(prompt, max_tokens)
        raise RuntimeError(f"HTTP {e.code}: {msg[:200]}")
    u = d.get("usage", {})
    return d["choices"][0]["message"]["content"], {"input_tokens": u.get("prompt_tokens", 0), "output_tokens": u.get("completion_tokens", 0)}

def parse_json(reply):
    m = re.search(r"\{.*\}", reply, re.S)
    if not m: return None
    try: return json.loads(m.group(0))
    except Exception: return None

NIVEAU = {"A": "classe de 4e", "B": "classe de 4e", "C": "classe de 4e", "D": "classe de 2nde S", "E": "classe de 2nde S"}
PROF = {"teacherD": "M. D", "teacherN": "M. N", "teacherNd": "M. Nd"}
def note_of(it, cond):
    return it.get("note_by", {}).get(cond, it["note"])

def generate():
    out = "results/responses.jsonl"
    done = {(json.loads(l)["item"], json.loads(l)["condition"], json.loads(l)["q"]) for l in open(out)} if os.path.exists(out) else set()
    f = open(out, "a"); tin = tout = n = 0
    for it in C["items"]:
        conds = [("plain", None)] + [(t, C["procedures"][t][it["famille"]]) for t in it["teachers"]]
        for cond, proc in conds:
            for qid, qtext in C["questions"]:
                if (it["id"], cond, qid) in done: continue
                user = f"Exercice : {it['enonce']}\n\nÉlève : {qtext}"
                if cond == "plain":
                    system = SYS_PLAIN
                else:
                    system = (SYS_CONFIGURED.replace("{prof}", PROF[cond]).replace("{niveau}", NIVEAU[it["famille"]])
                              .replace("{procedure}", proc).replace("{disclosure}", DISCLOSE_NOTE if note_of(it, cond) else DISCLOSE_FREE))
                reply, usage = call_anthropic(system, user)
                f.write(json.dumps({"item": it["id"], "famille": it["famille"], "enonce": it["enonce"], "note": note_of(it, cond),
                                    "condition": cond, "q": qid, "question": qtext, "response": reply, "usage": usage}, ensure_ascii=False) + "\n"); f.flush()
                tin += usage.get("input_tokens", 0); tout += usage.get("output_tokens", 0); n += 1
                print(f"{n:3d} {it['id']:3s} {cond:7s} {qid:6s} {len(reply):5d} chars")
                time.sleep(0.3)
    print("appels", n, "tokens", tin, tout)

def judge():
    import glob
    R = [json.loads(l) for fn in sorted(glob.glob("results/responses*.jsonl")) for l in open(fn) if l.strip() and json.loads(l)["q"] != "check"]   # les réponses 'vérifie mon étape' sont sans contenu
    out = "results/judgments.jsonl"
    done = {(json.loads(l)["item"], json.loads(l)["condition"], json.loads(l)["q"], json.loads(l)["judged_against"]) for l in open(out)} if os.path.exists(out) else set()
    f = open(out, "a"); tin = tout = n = 0
    for r in R:
        it = next(i for i in C["items"] if i["id"] == r["item"])
        # a configured response is judged against its own teacher; a plain response against each teacher who kept the item
        # (the third teacher validated the proposed texts, identical to D's for A, B, D, E and to N's for C: plain responses are not re-judged against him)
        targets = [r["condition"]] if r["condition"] != "plain" else [t for t in it["teachers"] if t != "teacherNd"]
        for t in targets:
            if (r["item"], r["condition"], r["q"], t) in done: continue
            p = (JUDGE_PROMPT.replace("{procedure}", C["procedures"][t][r["famille"]]).replace("{enonce}", r["enonce"])
                 .replace("{question}", r["question"]).replace("{note}", "oui" if r["note"] else "non").replace("{response}", r["response"][:3500]))
            reply, usage = call_groq(p)
            res = parse_json(reply)
            f.write(json.dumps({"item": r["item"], "famille": r["famille"], "condition": r["condition"], "q": r["q"], "note": r["note"],
                                "judged_against": t, "result": res, "raw": None if res else reply, "usage": usage}, ensure_ascii=False) + "\n"); f.flush()
            tin += usage.get("input_tokens", 0); tout += usage.get("output_tokens", 0); n += 1
            print(f"{n:3d} {r['item']:3s} {r['condition']:7s} {r['q']:6s} vs {t:6s} -> {(res or {}).get('method')} / {(res or {}).get('disclosure')}")
            time.sleep(20)
    print("appels", n, "tokens", tin, tout)

if __name__ == "__main__":
    {"generate": generate, "judge": judge}[sys.argv[1]]()
