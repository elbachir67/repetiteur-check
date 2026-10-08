# A Répétiteur for Every Student — feasibility check

Companion repository for *A Répétiteur for Every Student through Teacher-Piloted AI Tutoring in Large
Mathematics Classes* (submitted to ICETC 2026). It contains everything needed to reproduce Table II of
the paper: the 36 exercises, the three teachers' written procedures and graded/practice marks, the
prompts, the 405 tutor responses, the 324 readings by the second-laboratory model, the lexical reader,
the answer key, and the analysis script.

Teachers are identified as D, N and Nd, as in the paper.

## Layout

```
kit/
  config.json            36 exercises (5 families), procedures per teacher, graded marks per teacher, 3 student questions
  check.py               generation (Anthropic API) and second reader (Groq, openai/gpt-oss-120b); both steps resume
  rule.py                lexical reader: which procedure a response teaches (teacher / other / mixed / none)
  answers.py             final answers of the 36 exercises (reads "gives the full solution")
  analyze.py             Table II numbers, reader agreement and disagreements
  results/responses.jsonl           297 responses: tutor configured for D, for N, and unconfigured (3 questions each)
  results/responses_teacherNd.jsonl 108 responses: tutor configured for Nd
  results/judgments.jsonl           324 readings by the second model (the "check my step" question is not read)
teachers/   the three teachers' answers to the web form, as submitted (names removed)
forms/      the web form the teachers filled, the one-page note they received, and the generation pages
```

## Reproduce

```
cd kit
python3 analyze.py
```

prints, from the released responses and readings:

```
rule       plain  46/62  (74%)   configured 174/175 (99%)
model      plain  68/77  (88%)   configured 198/198 (100%)
withholds  plain  10/10  (100%)  configured  50/50  (100%)
gives      plain   0/26  (0%)    configured  26/49  (53%)
readers agree 225/234 (96%)
```

To regenerate responses or readings: `export ANTHROPIC_API_KEY=...; python3 check.py generate` and
`export GROQ_API_KEY=...; python3 check.py judge`. Generation used `claude-sonnet-4-6` through the
browser pages in `forms/`; the script accepts `GEN_MODEL` and `JUDGE_MODEL`.

## Notes

- The unconfigured tutor is read against D's and N's procedures (Nd validated the same texts). D's tutor
  ran on the 27 exercises D kept; D's and N's tutors ran under D's graded marks (N marked none), Nd's
  under his own (30 of 36; B3, C4 and D6 were left unmarked and treated as practice).
- The lexical reader is conservative: it counts a response as the teacher's only when its characteristic
  phrases appear and no other method's do. The model reader counts "add 4 to both sides" as the
  move-across procedure on linear equations, which accounts for all nine disagreements.
- Exercises come from the ADEM-Dakar grade-8 workbook (2017) and the Seconde S textbook of the Lycée
  Mbacké 2 mathematics team (2025).

## License

Code: MIT. Data (exercises, procedures, responses, readings): CC BY 4.0.
