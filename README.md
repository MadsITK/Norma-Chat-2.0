# Norma-Chat-2.0 — Workspace

Dette repo er **workspace-meta-repoet** for Norma-projektet. Det versionerer kun limet (top-niveau dokumentation, dev-scripts, agent-konfiguration). Den faktiske implementering bor i tre selvstændige sub-repos der lever side om side i denne mappe.

## Arkitektur i én figur

```
┌──────────┐ HTTP  ┌────────────────────────┐ HTTP  ┌────────────────────────┐
│ norma-ui │──────►│ norma-input            │──────►│ norma-robot-bridge     │
│ (Py3.11) │       │ (Py3.11)               │       │ (Py 2.7 + NAOqi)       │
│ FastAPI  │◄──────│ mic ─► STT ─► Emo ─────┘       │ ALProxy ─► Pepper/NAO  │
│ + HTML/JS│       │       Engine                   └────────────────────────┘
└──────────┘       └────────────────────────┘                  ▲
      ▲                                                        │
      │  Norma's tablet åbner UI-URL via show_tablet_url       │
      └────────────────────────────────────────────────────────┘
```

- **`norma-robot-bridge`** kører tæt på robotten (Py 2.7 fordi NAOqi kræver det) og eksponerer en JSON-API på port 8080.
- **`norma-input`** kører på en operatør-maskine med mikrofon, optager tale, transkriberer den, lader Emo Engine generere et emotionelt afstemt svar (tekst + gesture), og taler med robotten over HTTP.
- **`norma-ui`** kører på samme maskine som input. Det er dels operatørens kontrolpanel, dels den side Norma's tablet selv åbner. Det starter/stopper lytteloop, sender statisk tekst, og viser samtalevindue.
- Alle tre har **separate git-historier** og adskilte release-cyklusser.

Den oprindelige monolit (`Norma_Output.py` + `Norma Input.py`) ligger frosset i `norma-archive/` som læsbar reference.

## Mappestruktur

```
Norma-Chat-2.0/                          ← du er her (git-tracked workspace)
├── README.md                             ← denne fil
├── CLAUDE.md                             ← agent-kontekst på workspace-niveau
├── .claude/                              ← Claude Code-konfig (cross-repo læseadgang)
├── docs/                                 ← arkitektur, API-kontrakt, sekvensdiagrammer
├── scripts/                              ← clone-all, dev-up
├── norma-archive/                        ← gammel kode, frosset reference
├── norma-robot-bridge/  (gitignored)     ← klones via scripts/clone-all.ps1
├── norma-input/         (gitignored)     ← klones via scripts/clone-all.ps1
└── norma-ui/            (gitignored)     ← klones via scripts/clone-all.ps1
```

## Kom i gang

### 1. Klon workspace
```powershell
git clone <workspace-remote> Norma-Chat-2.0
cd Norma-Chat-2.0
```

### 2. Klon sub-repos ind ved siden af
```powershell
.\scripts\clone-all.ps1
```

Når sub-repos er publiceret, kloner scriptet dem ind i `norma-robot-bridge/` og `norma-input/`. Indtil da skal de oprettes manuelt — se de migrations-noter der følger med planfilen i `.claude/plans/`.

### 3. Sæt venvs op (én pr. sub-repo)

**Bridge (Python 2.7):**

Bridge'en har sit eget setup-script der håndterer venv, `pip install -e ".[test]"`, NAOqi-SDK-stien og en `activate-with-naoqi.{sh,bat}`-helper. Se [norma-robot-bridge/scripts/README.md](norma-robot-bridge/scripts/README.md) for forudsætninger (Python 2.7-install, NAOqi-SDK-download) og fuldt kald.

```bash
# Linux
cd norma-robot-bridge
./scripts/setup-linux.sh --naoqi-sdk /opt/aldebaran/pynaoqi-python2.7-2.5.5.5-linux64
```

```cmd
REM Windows cmd
cd norma-robot-bridge
scripts\setup-windows.bat C:\tools\pynaoqi
```

**Input (Python 3.11+):**
```powershell
cd norma-input
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

**UI (Python 3.11+):**
```powershell
cd norma-ui
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

### 4. Kør lokalt
```powershell
.\scripts\dev-up.ps1
```
Starter bridge i `--fake`-mode (ingen ægte robot påkrævet), en input-process, og UI-serveren — alle som separate vinduer der kan stoppes individuelt.

## Hvilket repo skal jeg åbne?

| Hvis du vil... | Åbn |
|---|---|
| Tilføje en HTTP-kommando til robotten | `norma-robot-bridge/` |
| Refaktorere robot-laget eller intro-flow | `norma-robot-bridge/` |
| Tilføje en LLM-provider (Claude, OpenAI) | `norma-input/` |
| Justere emotionel respons / gesture-mapping | `norma-input/` (Emo Engine) |
| Ændre hvordan brugerinput optages | `norma-input/` |
| Ændre system-prompten til samtaler | `norma-input/prompts/` |
| Ændre hvad der vises på Norma's tablet | `norma-ui/` |
| Tilføje en knap eller kommando til operatør-UI'et | `norma-ui/` |
| Læse hvordan tingene plejede at være | `norma-archive/` (read-only) |

Hvert sub-repo har sin egen `README.md` og `CLAUDE.md` med detaljer der er specifikke for dets Python-version og scope.

## API-kontrakt

Bridge'en ejer API-spec'en. Den ligger på `norma-robot-bridge/api-spec/openapi.yaml`. `norma-input` er forbruger og skal holdes synkroniseret. Se `docs/api-contract.md` for detaljer om versionering og kontrakttests.

## Hvorfor multi-repo?

To grunde:

1. **Inkompatible Python-runtimes**. Bridge er låst til 2.7 (NAOqi). Input og UI bruger 3.11 (moderne LLM-SDK'er, FastAPI, type hints). Et monorepo ville tvinge koordineret dependency-management på tværs af to runtimes der ikke deler en pakkemanager — ren smerte.
2. **Forskelligt deployment-mål**. Bridge kører på/ved robotten. Input + UI kører på en operatør-maskine med mikrofon. Forskellige hardware, forskellige opdateringscyklusser.

Hvorfor input og UI så ikke er ét repo: forskellig teknologistak (audio + LLM vs. FastAPI + HTML/JS) og forskellige iterationsrytmer. Begge bor på samme maskine, men leves uafhængigt.

Vi bruger **ikke** git submodules — sub-repos klones som løse søsterklones via `scripts/clone-all.ps1`. Det er nemmere at arbejde med dagligt, og workspace-repoet behøver ikke at "pinne" sub-repo-versioner.

## Licens

Internt projekt. Del eller licensér efter organisationens retningslinjer.
