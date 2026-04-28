# Norma Robot HTTP Service (Python 2.7 / NAOqi)

Denne repository indeholder en lille HTTP‑service, der kører direkte på Norma (Pepper/NAO) eller på en maskine med adgang til robotten via NAOqi. Servicen omslutter robotfunktioner (TTS, animationer/gestures, tablet‑visning) og eksponerer dem via et enkelt JSON‑baseret API på port 8080. Den kan dermed kaldes fra moderne Python 3.11 apps (f.eks. FastAPI) eller fra ethvert system, der kan lave HTTP‑kald.

## Indhold
- Hvad du får
- Forudsætninger
- Installation og konfiguration
- Kørsel (Windows/Linux)
- API reference og eksempler
- Hurtig integration fra Python 3 (FastAPI/requests)
- Fejlfinding og tips

## Hvad du får
- `Norma Output/Norma_Output.py` — Python 2.7 HTTP‑service med:
  - Thread‑safe `NormaRobotService` klasse
    - `say(text, gesture=None)`
    - `play_gesture(gesture_name)`
    - `show_tablet_image(image_path)`
    - `show_tablet_html(html_content)`
    - `hide_tablet()`
    - `get_status()`
  - Trådet HTTP‑server på port 8080 med endpoints:
    - `POST /api/command` (udfører en af ovenstående metoder)
    - `GET  /api/status` (returnerer status)
- `NormaRobotService.md` — designnoter (tidligere krav/overblik)

## Forudsætninger
- Python 2.7 miljø på den maskine, der skal tale med robotten.
- NAOqi SDK og runtime tilgængelig (så `from naoqi import ALProxy` virker).
- Netværksforbindelse til robotten (IP og port 9559 som standard).
- Adgang til port 8080 på værtsmaskinen (firewall skal tillade indgående trafik, hvis du kalder fra en anden maskine).

## Installation og konfiguration
1. Klon eller kopier projektet til den maskine, der skal køre servicen.
2. Åbn filen `Norma Output/Norma_Output.py` og sæt følgende konstanter i toppen:
   - `ROBOT_IP` — robotens IP (tryk på Norma’s maveknap for at høre IP’en).
   - `ROBOT_PORT` — typisk `9559`.
   - `LOCAL_IMAGE_PATH` — valgfrit. Sti til et lokalt PNG/JPG intro‑billede der vises på tablet ved opstart. Tom streng betyder “ingen intro”.
3. (Valgfrit) Verificér NAOqi virker ved at køre en simpel Python 2.7 REPL og importere `naoqi`:
   ```python
   >>> from naoqi import ALProxy
   ```

## Kørsel
Kør altid med Python 2.7.

- Windows (PowerShell eller cmd):
  ```bat
  cd "C:\dev\Norma-Chat-2.0"
  python "Norma Output\Norma_Output.py"
  ```

- Linux/macOS:
  ```bash
  cd /path/to/Norma-Chat-2.0
  python2 "Norma Output/Norma_Output.py"
  ```

Hvis alt er korrekt, ser du en besked á la:
```
Norma HTTP service lytter på port 8080 ...
```
Samtidig kører en kort animation, og (hvis sat) vises intro‑billedet på tablet. Norma siger en velkomstsætning.

Servicen kører i forgrunden. Brug Ctrl+C for at stoppe den. Ønsker du at køre den som service/daemon, anvend dit OS’ standardmekanismer (systemd, NSSM, Task Scheduler el.lign.).

## API reference
Base‑URL: `http://<host>:8080`

- GET `/api/status`
  - Response:
    ```json
    {"status":"success","data":{"ip":"<ROBOT_IP>","port":9559,"interaction_count":N}}
    ```

- POST `/api/command`
  - Body (JSON):
    ```json
    {"command":"<navn>","params":{...}}
    ```
  - Mulige kommandoer:
    - `say` — sig noget (valgfrit gesture)
      - Params: `{ "text": "Hej", "gesture": "hello" }`
    - `play_gesture` — afspil specifik gesture
      - Params: `{ "gesture_name": "bow" }` (eller `gesture`)
    - `show_tablet_image` — vis lokalt billede på tablet
      - Params: `{ "image_path": "C:\\path\\to\\image.png" }`
    - `show_tablet_html` — vis HTML på tablet
      - Params: `{ "html": "<h1>Hej</h1>" }` (eller `html_content`)
    - `hide_tablet` — skjul tablet
      - Params: `{}`
    - `get_status` — returnér status (samme som GET /api/status)
      - Params: `{}`
  - Generel respons:
    ```json
    {"status":"success","data":{...}}
    ```
    eller ved fejl
    ```json
    {"status":"error","message":"..."}
    ```

## Eksempler (curl)
- Say med gesture:
  ```bash
  curl -X POST http://<host>:8080/api/command \
       -H "Content-Type: application/json" \
       -d '{"command":"say","params":{"text":"Hej","gesture":"hello"}}'
  ```
- Afspil gesture:
  ```bash
  curl -X POST http://<host>:8080/api/command \
       -H "Content-Type: application/json" \
       -d '{"command":"play_gesture","params":{"gesture_name":"bow"}}'
  ```
- Vis billede på tablet:
  ```bash
  curl -X POST http://<host>:8080/api/command \
       -H "Content-Type: application/json" \
       -d '{"command":"show_tablet_image","params":{"image_path":"C:\\path\\to\\image.png"}}'
  ```
- Vis HTML på tablet:
  ```bash
  curl -X POST http://<host>:8080/api/command \
       -H "Content-Type: application/json" \
       -d '{"command":"show_tablet_html","params":{"html":"<h1>Hej</h1>"}}'
  ```
- Skjul tablet:
  ```bash
  curl -X POST http://<host>:8080/api/command \
       -H "Content-Type: application/json" \
       -d '{"command":"hide_tablet"}'
  ```
- Status:
  ```bash
  curl http://<host>:8080/api/status
  ```

## Hurtig integration fra Python 3
Eksempel på at kalde servicen fra Python 3.11 (f.eks. i en FastAPI‑app), via `requests`:
```python
import requests

BASE = "http://<host>:8080"

# Sig noget
r = requests.post(f"{BASE}/api/command", json={
    "command": "say",
    "params": {"text": "Hej fra FastAPI", "gesture": "hello"}
})
print(r.json())

# Vis HTML
requests.post(f"{BASE}/api/command", json={
    "command": "show_tablet_html",
    "params": {"html": "<h2>Hej Norma</h2>"}
})

# Hent status
print(requests.get(f"{BASE}/api/status").json())
```

Hvis du vil indkapsle dette i en FastAPI‑route, så lav en endpoint der videresender JSON uændret til servicen.

## Fejlfinding og tips
- Importfejl: "NAOqi ALProxy ikke tilgængelig" — Sørg for at NAOqi SDK er installeret og tilgængeligt i Python 2.7‑miljøet.
- Forbindelse nægtes til robot: Tjek `ROBOT_IP`/`ROBOT_PORT`, samt at du kan ping’e robotten fra værtsmaskinen.
- Port 8080 utilgængelig: Luk anden service på porten, eller skift port i `Norma_Output.py` (server_address i `run_server`). Husk firewall‑regler.
- Tablet viser intet billede: Tjek sti i `LOCAL_IMAGE_PATH` eller i `show_tablet_image`‑kaldet. Filen skal eksistere på værtsmaskinen hvor servicen kører.
- Encoding/æøå: Koden håndterer UTF‑8; send JSON som UTF‑8. I Python 3 sender `requests` korrekt UTF‑8 som standard.
- Samtidige kald: Serveren er trådet og alle robotkald er beskyttet med en re‑entrant lock.

## Licens
Internt projekt. Del eller licensér efter organisationens retningslinjer.
