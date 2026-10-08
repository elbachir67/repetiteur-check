#!/usr/bin/env python3
"""Table II numbers from results/responses*.jsonl, results/judgments.jsonl and rule.py (lexical reader)."""
import json, glob, re, sys, collections
sys.path.insert(0, ".")
from rule import read, norm
from answers import gives_final
C = json.load(open("config.json"))
R = [json.loads(l) for fn in sorted(glob.glob("results/responses*.jsonl")) for l in open(fn) if l.strip() and json.loads(l)["q"] != "check"]
J = {(j["item"], j["condition"], j["q"], j["judged_against"]): j for j in (json.loads(l) for l in open("results/judgments.jsonl"))}
items = {i["id"]: i for i in C["items"]}
def conds(r):
    return [r["condition"]] if r["condition"] != "plain" else [t for t in items[r["item"]]["teachers"] if t != "teacherNd"]
rows = collections.defaultdict(lambda: [0, 0])
agree = both = 0; dis = []
for r in R:
    grp = "plain" if r["condition"] == "plain" else "configured"
    for t in conds(r):
        rr = read(r["famille"], t, r["response"]); mm = J[(r["item"], r["condition"], r["q"], t)]["result"]["method"]
        if rr != "none": rows[(grp, "rule")][1] += 1; rows[(grp, "rule")][0] += rr == "teacher"
        if mm != "none": rows[(grp, "model")][1] += 1; rows[(grp, "model")][0] += mm == "teacher"
        if rr != "none" and mm != "none":
            both += 1; agree += rr == mm
            if rr != mm: dis.append((r["item"], r["condition"], r["q"], t, rr, mm))
    if r["q"] == "answer":
        if r["note"]:   # graded: withholding as read by the model reader (Q2), and by the answer key
            jj = [J[(r["item"], r["condition"], r["q"], t)]["result"]["disclosure"] for t in conds(r)]
            rows[(grp, "withholds")][1] += 1; rows[(grp, "withholds")][0] += all(d == "withholds" for d in jj)
            rows[(grp, "withholds_key")][1] += 1; rows[(grp, "withholds_key")][0] += not gives_final(r["item"], r["response"])
        else:           # practice: states the exercise's final answer (answer key)
            rows[(grp, "gives")][1] += 1; rows[(grp, "gives")][0] += gives_final(r["item"], r["response"])
print("responses read:", len(R))
for k in ["rule", "model", "withholds", "withholds_key", "gives"]:
    p, c = rows[("plain", k)], rows[("configured", k)]
    print(f"{k:10s} plain {p[0]:3d}/{p[1]:<3d} ({100*p[0]/max(1,p[1]):.0f}%)   configured {c[0]:3d}/{c[1]:<3d} ({100*c[0]/max(1,c[1]):.0f}%)")
print(f"readers agree {agree}/{both} ({100*agree/both:.0f}%); disagreements:")
for d in dis: print("  ", d)
# per-condition detail
per = collections.defaultdict(lambda: [0, 0])
for r in R:
    for t in conds(r):
        rr = read(r["famille"], t, r["response"])
        if rr != "none": per[(r["condition"], t, r["famille"])][1] += 1; per[(r["condition"], t, r["famille"])][0] += rr == "teacher"
print("rule, per condition/target/family:", {f"{k[0]}>{k[1]}/{k[2]}": f"{v[0]}/{v[1]}" for k, v in sorted(per.items())})
