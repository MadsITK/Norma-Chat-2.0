# Arkitektur — Norma-Chat-2.0

Tværgående arkitekturdokumentation for projektet. Sub-repo-specifikke detaljer (Python 2.7-mønstre, NAOqi-kald, Whisper-konfiguration osv.) hører til i de respektive sub-repos egen `docs/`.

## Komponenter

```
┌──────────┐ HTTP  ┌────────────┐ HTTP  ┌──────────────────┐
│ norma-ui │──────►│ norma-input│──────►│ norma-robot-bridge│──► NAOqi → Pepper/NAO
│ (Py3.11) │       │  (Py3.11)  │       │   (Py 2.7)       │
│ FastAPI  │◄──────│ Emo Engine │       └──────────────────┘
│ + HTML/JS│       │ Pipeline   │                ▲
└──────────┘       └────────────┘                │
      ▲                                          │ POST /api/command
      │  Tablet WebView peget på UI-URL          │ {"command":"show_tablet_url",
      │  via show_tablet_url-kommando            │  "params":{"url":"..."}}
      │                                          │
      └──────────────────────────────────────────┘
```

### `norma-robot-bridge` — robot-bridge (Python 2.7)

Eksponerer NAOqi-funktionalitet via en JSON-API på TCP 8080. Kører på en maskine med NAOqi SDK installeret (på robotten selv eller på en dedikeret host med netværksforbindelse til den).

**Ansvar:**
- Indkapsle NAOqi-proxies (`ALTextToSpeech`, `ALAnimationPlayer`, `ALTabletService`)
- Trådsikker dispatch af robot-kommandoer (RLock på service-niveau)
- Stateful intro/welcome-flow ved opstart (data-drevet via config)
- HTTP-API på `/api/...` (uversioneret indtil videre — se afsnit "API-kontrakt" nedenfor)

**Ikke ansvar:**
- Audio capture, STT, LLM-orkestrering, emotionel vurdering — alt det hører til input-laget
- Hosting af web-UI — det hører til ui-laget; bridge peger blot tabletten på en URL
- Persistent state (interaction_count nulstilles ved restart — det er fint)

### `norma-input` — pipeline + Emo Engine (Python 3.11+)

Kører på en operatør-maskine med mikrofon. Optager input, transkriberer med Whisper, og lader **Emo Engine** generere et emotionelt afstemt svar (tekst + gesture) via en pluggable LLM-adapter.

**Ansvar:**
- Audio capture (PyAudio + push-to-talk eller VAD)
- Speech-to-text (Whisper, lokal)
- LLM-adapter med pluggable providers (Ollama, Claude, OpenAI) — `LLMClient`-interface
- **Emo Engine** — laget oven på LLM'en der returnerer `EmoResponse{text, gesture, emotion}`
- HTTP-klient til bridge
- Eksponerer en intern HTTP/WebSocket-flade som `norma-ui` taler med (start/stop loop, send statisk tekst)

**Ikke ansvar:**
- Direkte NAOqi-kald — al robot-interaktion går via bridge'ens HTTP-API
- Hosting af tablet-UI — det er ui-lagets opgave

### `norma-ui` — web-UI (Python 3.11+)

Kører på samme maskine som `norma-input`. Hoster en lokal FastAPI-server med to formål:

1. **Operatør-kontrolpanel** — knapper og samtalevindue til den menneskelige operatør (start/stop loop, send statisk tekst, debug-visning)
2. **Tablet-side** — den side Norma's egen tablet viser, peget på via bridge'ens `show_tablet_url`-kommando

**Ansvar:**
- HTML/JS-frontend
- REST/WebSocket-proxy mod `norma-input`
- Konfigurerbar URL-routing så tablet og operatør kan ramme forskellige sider (eller samme — bestemmes ved implementering)

**Ikke ansvar:**
- Direkte mic/STT/LLM-kald — proxer via input
- Direkte bridge-kald (foreløbig). UI sender kommandoer til input, der dispatcher videre til bridge. Hvis det viser sig at give for meget overhead, kan UI få lov at kalde bridge direkte for "neutrale" kommandoer (fx `play_gesture`).

## Sekvens: en samtaletur

```
Operatør holder mellemrum nede og taler (eller klikker en knap i norma-ui)
    │
    ▼
norma-input.audio.recorder        ── PyAudio capture ──►  L1.wav
    │
    ▼
norma-input.audio.stt             ── Whisper transcribe ──►  bruger_input: str
    │
    ▼
norma-input.emo.engine            ── LLM-kald + emotionel vurdering ──►
                                  EmoResponse{text, gesture, emotion}
    │
    ▼
norma-input.robot_client          ── HTTP POST /api/command {say} ──►
                                                                       │
                                                                       ▼
                                                  norma-robot-bridge.api.handlers
                                                                       │
                                                                       ▼
                                                  norma-bridge.robot.service.say()
                                                                       │
                                                                       ▼
                                                                  ALTextToSpeech
                                                                       │
                                                                       ▼
                                                              Pepper/NAO taler
```

Parallelt med dette opdaterer `norma-input` `norma-ui` over WebSocket, så samtalevinduet på operatørens skærm (og evt. på Norma's tablet) viser den nye replik.

## API-kontrakt (bridge)

Bridge'en ejer kontrakten. Spec'en bor på `norma-robot-bridge/api-spec/openapi.yaml` og er autoritativ.

API'et er uversioneret lige nu — endpoints lever på `/api/...`. Hvis vi en dag har en breaking change, indfører vi `/api/v2/...` parallelt med de uversionerede endpoints, så klienter kan migrere kontrolleret.

Endpoints (planlagt):
- `GET /api/status` — server- og robot-status
- `POST /api/command` med `command` ∈ {`say`, `play_gesture`, `show_tablet_image`, `show_tablet_html`, `show_tablet_url`, `hide_tablet`, `get_status`}

Se [api-contract.md](api-contract.md) for kontrakt-tests og synkroniseringsstrategi.

## Emo Engine — kontrakt

Lever i `norma-input/src/norma_input/emo/`. Sidder oven på `LLMClient`-adapteren og returnerer både tekst og en passende gesture baseret på emotionel vurdering af input + svar.

```python
@dataclass
class EmoResponse:
    text: str           # det Norma skal sige
    gesture: str | None # NAOqi animation-tag, fx "animations/Stand/Gestures/Yes_1"
    emotion: str        # fx "joy" / "neutral" / "concern" — til UI/logging

class EmoEngine:
    def __init__(self, llm: LLMClient, gesture_map: dict[str, list[str]]): ...
    def respond(self, user_input: str, history: list[Turn]) -> EmoResponse: ...
```

Pipeline kalder `engine.respond(...)` (ikke `llm.complete(...)` direkte). Bridge'ens fallback-cycling i `gestures.py` aktiveres kun når `gesture=None` (fx UI-knapper der bare sender statisk tekst).

## Fejlhåndtering

- **Kommandofejl** (klient sender ugyldigt input): bridge returnerer HTTP 400 med `{"status":"error","message":"..."}`.
- **Robot-fejl** (NAOqi-kald fejler): bridge returnerer HTTP 500 med samme format. Klient skal være forberedt på timeout/retry.
- **LLM-fejl** (provider nede, rate limit): Emo Engine fanger det og returnerer en fallback `EmoResponse` med en neutral undskyldning + `emotion="error"`. Pipeline fortsætter.
- **Netværksfejl mellem ui og input**: UI viser disconnected state og prøver at reconnecte (eksponentiel backoff).

## Trådsikkerhed (bridge)

Bridge serveren er threaded (`SocketServer.ThreadingMixIn`). Alle robotkald går gennem en delt `NormaRobotService`-instans beskyttet af en `threading.RLock`. Nye metoder i service'en skal følge samme `with self._lock:`-mønster — se `norma-robot-bridge/CLAUDE.md` for detaljer.

## Hukommelse — bevidst udskudt

Konversations-/topik-hukommelse er **ikke** designet endnu. Den defineres efter et grundlæggende LLM-flow er oppe at køre. Indtil da:

- Implementér ikke spekulativ persistens i nogen komponent
- Hold Emo Engine stateless: `respond()` tager `history` som parameter, returnerer ny respons — ingen globale buffers
- Når hukommelse skal designes, bliver det formentlig en ny komponent (egen klasse i input, evt. eget sub-repo hvis det vokser)

## Fremtidige udvidelser (ikke aktive)

- **Pepper-on-board ASR** — alternativ input-implementering der bruger NAOqi `ALSpeechRecognition` i stedet for Whisper. Vil være en ny implementering af samme `AudioInput`-interface i `norma-input`.
- **Tredje klient** — hvis fx en analytics-pipeline også skal kalde bridge'en, så er det det punkt hvor en publiceret API-klient-pakke (genereret fra OpenAPI-spec'en) bliver berettiget.
- **Hukommelse** — se ovenstående afsnit.
