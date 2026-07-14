<p align="center">
  <img src="docs/assets/triage-logo.png" width="96" alt="Triage logo">
</p>

<h1 align="center">Triage</h1>
<p align="center"><b>Right model, every request.</b><br>
Free open-source models answer first. Your paid model is called only when
the answer's own signals prove it's needed. Unanswerable requests are refused,
not hallucinated.</p>

---

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/mtbench_curve_dark.svg">
  <img src="docs/assets/mtbench_curve_light.svg" alt="MT-Bench cost-quality curve: 95.3% cost reduction at 100.3% of the paid model's quality.">
</picture>

**Measured, not estimated** — real API bills, raw per-query receipts in `data/`:

| Result | Number | Where |
|---|---|---|
| MT-Bench, free Ministral-8B → GPT-4o | **95.3% saved** at **100.3%** of GPT-4o quality (5% escalated) | `data/mtbench_gpt4o.json` |
| MT-Bench, free Nemotron-Nano-9B → GPT-4o | **78.6% saved** at **103.8%** of GPT-4o quality (16% escalated) | `data/mtbench_nemotron.json` |
| 30-query mixed live bill | **69.5% saved** ($0.0637 → $0.0195) | `data/showtime.json` |
| Answers that cost exactly $0 | **24 / 30** | same run |

---

## Quick start

```bash
git clone <this-repo> && cd triage
cp .env.example .env        # add the keys you have
./run.sh                    # venv + deps + server on :8000
```

Open **http://localhost:8000**. A one-time setup asks two questions:

1. **Small tasks** → pick a free open-source model (default: Llama 3.1 8B on NVIDIA NIM)
2. **Hard tasks** → pick your paid model (e.g. GPT-4o) and paste your API key
   — the key lives in your browser only, attached per request, never stored server-side

Every answer shows which model ran, why, the tokens, the exact cost, and your
running savings. A **Live demo** page (`/ui/demo.html`) tells the cost story
with the measured numbers.

**Keys** (any subset; missing providers fall back to an offline mock):

| Provider | `.env` line | Role |
|---|---|---|
| NVIDIA NIM — [free key](https://build.nvidia.com) | `nvidia=nvapi-…` | the **free lane**: Llama, Nemotron, Gemma, Phi (with logprobs) |
| OpenAI | `OPENAI_API_KEY=sk-…` | the **paid lane**: gpt-4o-mini / gpt-4o / gpt-5-mini / gpt-5 |

---

## How it works

```
request ─► calculator tool ── exact arithmetic → exact answer, $0, no LLM
        └► FREE small model ── one pass + free logprob uncertainty
              │ confident → ship it            (the 80–95% case, $0)
              │ suspicious → deeper signals: resample agreement · self-check · evidence
              │ risky → retrieve → verify (can revise) → escalate to YOUR paid model
              └ unanswerable → PENDING_REVIEW  (refuse, never confabulate)
```

The decision is made **after observing the free model's actual answer** — not by
guessing from the prompt. No router training, no preference data, no calibration
per model pair: pick any two models in the UI and it works.

Extras that keep it cheap and honest: expensive signals only fire when the free
uncertainty signal is already elevated; a semantic memory skips probes on
known-safe prompt clusters; an online learner keeps the escalation rate on
target; `/anomalies` flags cost spikes; every decision is logged to SQLite with
its full signal vector.

---

## Benchmarks — reproduce everything

```bash
PYTHONPATH=. python scripts/mtbench.py llama-3.1-8b gpt-4o     # cost-quality curve, any pair
PYTHONPATH=. python scripts/showtime.py                        # 30-query live bill
PYTHONPATH=. python -m app.benchmark.rigor --dataset gsm8k --n 200   # GSM8K/MMLU/traps + 95% CIs
```

The MT-Bench script makes **one paid pass per question**, then sweeps the
escalation threshold offline — the whole curve costs one run. The rigor harness
adds bootstrap confidence intervals and an unanswerable-traps set for the
abstain axis.

*Fine print (all truth):* single runs; the judge is gpt-4o-mini scoring 1–10;
first turns only; free-lane models run on provider free tiers. At "never
escalate" the free model alone held 96.7% of GPT-4o quality on MT-Bench — the
benchmark is partly saturated for modern small models, so the headline is the
≥95%-quality operating point, and the raw per-question scores are all in the
JSON for you to check.

---

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Chat UI (setup wizard on first visit) |
| `GET` | `/ui/demo.html` | Live demo — the measured cost story |
| `POST` | `/chat` | Route + answer one message |
| `GET` | `/models` | Model catalog + live provider status |
| `GET` | `/health` | Providers, retrieval backend, mock flag |
| `GET` | `/telemetry?limit=N` | Per-request tier/signals/cost log |
| `GET` | `/anomalies` | Cost-anomaly detection |
| `POST` | `/ingest` | Add documents to the retrieval store |
| `POST` | `/benchmark` | 3-config eval harness |

```bash
curl -s localhost:8000/chat -H 'content-type: application/json' -d '{
  "message": "Prove sqrt 2 is irrational",
  "model": "llama-3.1-8b",
  "escalate_to": "gpt-4o",
  "api_key": "sk-optional-byo-key"
}'
```

---

## Make it yours (modular by design)

- **Add a model** — one YAML block in [`config/models.yaml`](config/models.yaml):
  set `provider`, `provider_model`, `role: small` (everyday picker) or
  `role: big` (hard-task picker). Done — it appears in the UI.
- **Add a provider** — subclass the adapter in `app/providers/` (anything
  OpenAI-compatible is ~10 lines) and register it in `registry.py`.
- **Retune routing** — every threshold lives in
  [`config/router.yaml`](config/router.yaml): signal gate, escalation risk,
  verify caps, pre-filter cuts, online-learning bounds, tools. No code edits.
- **Swap retrieval** — local numpy store by default; set
  `RETRIEVAL_BACKEND=pgvector` + `docker compose up -d` for Postgres.

```
app/
  main.py             FastAPI endpoints
  router/             tiers · abstain · prefilter · memory · online learning
  signals/proxy.py    black-box reliability signals
  tools/calculator.py exact math, $0
  providers/          openai_compat · mock · registry (add yours here)
  verify/             grounding pass (can revise answers)
  telemetry/          SQLite log + anomaly detection
  benchmark/          harness + rigor (GSM8K/MMLU/traps, CIs)
scripts/              mtbench.py · showtime.py · make_curve_svg.py
config/               models.yaml · router.yaml
ui/                   index.html (chat + wizard) · demo.html (cost story)
```

## Deploy

`uvicorn app.main:app` runs on any Python host (Render, Railway, Fly.io, a VPS).
Vercel/Netlify are static-only — they can serve the UI, not the router. Set
provider keys as env vars on the host; visitors bring their own OpenAI key
through the UI.

## Principles

- **Black-box only** — logprobs + resampling; no weights, no attention hooks.
- **Mock-first** — runs end-to-end with zero keys.
- **All truth** — published numbers are measured bills with raw receipts
  committed; negative results get reported, not buried.
