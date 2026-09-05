<p align="center">
  <img src="marca/logo.svg" alt="curiosARTy" width="360" />
</p>

<p align="center">
  <a href="https://rgst77.github.io/newsletter-arte/">Landing</a> ·
  <a href="https://rgst77.github.io/newsletter-arte/archivo/index.html">Archive</a>
</p>

<p align="center">
  A newsletter written by AI agents, illustrated exclusively with public-domain art.
</p>

---

Every few days, **curiosARTy** researches one real sculptor, architect, painter, or poet, fact-checks its own work, and illustrates it with public-domain and freely-licensed images. No stock content, no filler — one artist, done properly, then archived publicly forever.

## How it's built

A pipeline of four agents, each with a single job, handing off structured, validated data instead of sharing one messy conversation:

| Agent | Job |
|---|---|
| **Investigador** | Picks the next author from the catalog, researches them for real (web search, no hallucinated facts), and extracts verified nationality, movement, period, and the exact titles of known works |
| **Imágenes** | Searches The Met Open Access and Wikimedia Commons for those exact works — public domain or freely-licensed only, with real author/license attribution captured |
| **Redactor** | Turns the raw research into a short, warm flashcard-style biography — never touches a URL, so it can't invent or corrupt one |
| **Verificador** | Cross-checks the biography against the original research notes and flags any unsupported claim before anything ships |

The final HTML is rendered by deterministic code, not the LLM — the agents produce data, a template turns it into markup. That split is what keeps a hallucinated link or broken layout from ever reaching an inbox.

Everything — code, generated issues, and the send history — lives in this public repo. No separate database for content: the archive *is* the repo.

## How delivery works

New content is generated on its own clock (roughly one new artist every 3 days, rotating chronologically through the centuries covered). Subscribers are on a separate clock: everyone starts at issue #1 the moment they sign up and receives the next one every 3 days after that — not whatever happens to be current. Two subscribers who join a year apart both get the full sequence, in order, from the beginning.

## Stack

Python · Anthropic API (Claude Haiku) · Supabase (subscriber storage + per-subscriber delivery progress, RLS-only-insert) · Brevo (delivery) · GitHub Pages (hosting)

## Free by design

- Images are always linked, never stored — the HTML footprint stays a few KB per issue
- Hosting, database, and delivery all run on free tiers
- No framework: the agent loop, tool-calling, and orchestration are hand-built for the learning value

---

<p align="center"><sub>Built as a hands-on exploration of agentic AI — not a polished product, a working one.</sub></p>
