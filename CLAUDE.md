# CLAUDE.md — Workspace-niveau (Norma-Chat-2.0)

Dette er **workspace-meta-repoet** for Norma-Chat-2.0. Det versionerer kun limet — top-niveau dokumentation, dev-scripts, agent-konfiguration og en arkivkopi af den gamle kode. Den faktiske implementering bor i sub-repos der ligger i søstermapper (gitignored fra dette repo, hvert med sit eget `.git/`).

## Repo-oversigt

| Mappe | Status | Python | Indhold |
|---|---|---|---|
| `Norma-Chat-2.0/` (her) | Workspace meta-repo (git-tracked) | n/a | Docs, scripts, `.claude/`, `norma-archive/` |
| `Norma-Chat-2.0/norma-robot-bridge/` | Sub-repo (gitignored, eget `.git/`) | **2.7** | NAOqi HTTP-bridge — taler direkte med Pepper/NAO |
| `Norma-Chat-2.0/norma-input/` | Sub-repo (gitignored, eget `.git/`) | **3.11+** | Mikrofon → STT → Emo Engine → bridge over HTTP |
| `Norma-Chat-2.0/norma-ui/` | Sub-repo (gitignored, eget `.git/`) | **3.11+** | FastAPI + HTML/JS — control-panel og tablet-side |
| `Norma-Chat-2.0/norma-archive/` | Læsbar reference | 2.7 + 3.11 | Den gamle monolitiske kode (`Norma_Output.py`, `Norma Input.py`) |

Sub-repos er **ikke** git submodules. De klones manuelt via `scripts/clone-all.ps1`. Hvert sub-repo lever sit eget liv med egne branches og remotes.

## Hvor skal jeg redigere?

**Før du redigerer kode i et sub-repo, læs sub-repoets egen `CLAUDE.md`** — den indeholder Python-version-specifikke regler, threading-mønstre osv. Workspace-niveauet ved kun "hvor tingene bor", ikke "hvordan koden skal skrives".

| Vil du... | Gå til |
|---|---|
| Tilføje en HTTP-kommando til robotten | `norma-robot-bridge/` |
| Ændre hvordan robot-laget kalder NAOqi | `norma-robot-bridge/` |
| Ændre intro-flow / velkomst | `norma-robot-bridge/config/` |
| Tilføje en LLM-provider | `norma-input/src/norma_input/llm/` |
| Justere emotionel respons / gesture-mapping | `norma-input/src/norma_input/emo/` |
| Ændre hvordan brugerinput optages | `norma-input/src/norma_input/audio/` |
| Ændre system-prompten | `norma-input/prompts/` |
| Ændre hvad der vises på Norma's tablet | `norma-ui/` |
| Tilføje en knap/kommando til operatør-UI | `norma-ui/` |
| Læse den gamle kode for kontekst | `norma-archive/` (read-only) |

## Python-versioner — vigtigt

`norma-robot-bridge` er **låst til Python 2.7** fordi NAOqi-SDK'et kræver det. Det betyder ingen f-strings, ingen `pathlib`, ingen `typing`-annotationer, ingen `dataclasses`. Sub-repoets `CLAUDE.md` har detaljerne. Bekræft kompatibilitet før commit:
```bash
python2 -m py_compile norma-robot-bridge/src/norma_bridge/**/*.py
```

`norma-input` er **Python 3.11+**. Type hints er forventet, f-strings velkomne.

Når Claude Code arbejder fra workspace-roden er der **ingen** aktiv Python-runtime — opgaver der involverer kørsel skal udføres i den relevante sub-repos venv.

## Kommunikation mellem komponenter

```
┌──────────┐  HTTP   ┌────────────┐  HTTP /api/command  ┌──────────────────────┐
│ norma-ui │────────►│ norma-input│───────────────────────►│ norma-robot-bridge   │
│ (Py3.11) │         │  (Py3.11)  │                        │ (Py 2.7 + NAOqi)     │
│ FastAPI  │◄────────│ Emo Engine │◄───────────────────────│ ALProxy → Pepper/NAO │
│ + HTML/JS│         │ Pipeline   │   JSON-svar            └──────────────────────┘
└──────────┘         └────────────┘                                  ▲
      ▲                                                              │
      │  Norma-tabletten åbner UI-URL via show_tablet_url-kommando   │
      └──────────────────────────────────────────────────────────────┘
```

API-kontrakten ejes af bridge'en. Spec'en ligger på `norma-robot-bridge/api-spec/openapi.yaml`. Klient-siden i `norma-input` skal holde sig synkroniseret med den. `norma-ui` taler primært med `norma-input` (start/stop loop, send tekst), og kun indirekte med bridge'en.

## Workspace-indhold

- `README.md` — onboarding for nye udviklere (klon alle repos, sæt venvs op)
- `CLAUDE.md` — denne fil
- `.claude/settings.json` — tilladelser så Claude Code kan læse på tværs af sub-mapper
- `.claude/pointers.md` — hurtig agent-orientering
- `docs/architecture.md` — tværgående arkitektur og sekvensdiagrammer
- `scripts/clone-all.ps1` — kloner alle sub-repos
- `scripts/dev-up.ps1` — starter fake-bridge + input lokalt
- `norma-archive/` — den gamle monolitiske kode bevaret som reference

## Plan-filen

Den oprindelige refaktoreringsplan ligger på `C:\Users\az77820\.claude\plans\vi-er-i-gang-clever-thunder.md`. Den beskriver målarkitekturen og migrationsfaserne.

## Vigtige principper når du arbejder her

- **Aldrig redigér i `norma-archive/`** — det er en frosset reference.
- **Ingen Py 2.7-kode i `norma-input/` eller `norma-ui/`, ingen Py 3-kode i `norma-robot-bridge/`** — to runtimes, to verdener.
- **API-kontraktændringer kræver opdatering af `openapi.yaml` i samme PR**.
- **Bridge må ikke afhænge af noget i input- eller ui-repoet og omvendt** — de kommunikerer kun over HTTP.
- **Hukommelse er bevidst ikke designet endnu** — den defineres efter et grundlæggende LLM-flow er oppe at køre. Implementér ikke spekulativt persistens.
