# CLAUDE.md — Projektoversigt og retningslinjer for agenter

Dette dokument giver en kort, operationel introduktion til projektet, så både mennesker og AI‑agenter hurtigt kan forstå formål, arkitektur, drift, og vigtige hensyn ved videreudvikling.

## 1) Formål
- Eksponere NAOqi‑funktionalitet (Pepper/NAO) via en lille HTTP‑service, så moderne apps (fx Python 3/FastAPI) kan interagere med robotten via et enkelt JSON‑API.
- Bevare eksisterende funktionalitet fra tidligere script: TTS, gestures/animationer, tablet‑visning, intro‑billede ved opstart, og simpel gesture‑cykling.

## 2) Teknisk overblik
- Sprog/runtime: Python 2.7 (krav fra NAOqi‑miljøet)
- NAOqi: `ALProxy` til TTS (`ALTextToSpeech`), animationer (`ALAnimationPlayer`), og tablet (`ALTabletService`).
- HTTP‑server: Python 2.7 `BaseHTTPServer` + `SocketServer.ThreadingMixIn` (threaded, port 8080).
- Tråd‑sikkerhed: Alle robotkald går gennem en delt `NormaRobotService` beskyttet med `threading.RLock`.
- API: 
  - `GET /api/status`
  - `POST /api/command` med JSON: `{ "command": "...", "params": { ... } }`

## 3) Repo‑struktur (essentielt)
- `Norma Output/Norma_Output.py` — Hovedservice (HTTP + `NormaRobotService`).
- `README.md` — Kørevejledning, API‑eksempler, fejlfinding.
- `NormaRobotService.md` — Tidligere designkrav/overblik (arkiv/koncept).

Bemærk mellemrummet i mappenavnet “Norma Output”. Bevar sti‑formateringen i scripts og dokumenter.

## 4) Servicearkitektur og flow
- Ved opstart initialiseres NAOqi‑proxies og et intro‑flow kører:
  - Valgfri tablet‑intro (lokalt billede som data‑URI) + kort animation + velkomst‑TTS.
- HTTP‑serveren starter på port 8080 og deler én `NormaRobotService` mellem tråde.
- Indkomne kommandoer dispatches sikkert via lås, returnerer JSON `{status, data|message}`.

## 5) API (kort)
- GET `/api/status`
  - Response: `{"status":"success","data":{"ip":"<ROBOT_IP>","port":9559,"interaction_count":N}}`
- POST `/api/command`
  - Body: `{"command":"<navn>","params":{...}}`
  - Kommandoer:
    - `say` — `{ "text": "Hej", "gesture": "hello" }` (gesture er valgfri)
    - `play_gesture` — `{ "gesture_name": "bow" }` (eller `gesture`)
    - `show_tablet_image` — `{ "image_path": "C:\\path\\to\\image.png" }`
    - `show_tablet_html` — `{ "html": "<h1>Hej</h1>" }` (eller `html_content`)
    - `hide_tablet` — `{}`
    - `get_status` — `{}`

## 6) Konfiguration
- Redigér i toppen af `Norma Output/Norma_Output.py`:
  - `ROBOT_IP` (robot‑IP; kan læses op på robotten)
  - `ROBOT_PORT` (typisk 9559)
  - `LOCAL_IMAGE_PATH` (valgfri sti til introbillede vist på tablet)
- Server binder til `('', 8080)` → alle interfaces.

## 7) Kørsel
- Kør i Python 2.7‑miljø med NAOqi tilgængelig.
- Windows:
  ```bat
  python "Norma Output\Norma_Output.py"
  ```
- Linux/macOS:
  ```bash
  python2 "Norma Output/Norma_Output.py"
  ```
- Forventet log: `Norma HTTP service lytter på port 8080 ...`

## 8) Vigtige hensyn (for fremtidige ændringer)
- Python 2.7‑kompatibilitet: Brug `from __future__ import print_function`, undgå Python 3‑only features. Unicode‑håndtering er eksplicit i koden (`_ensure_unicode`, UTF‑8 bytes til TTS).
- Tråd‑sikkerhed: Bevar/lås al robot‑I/O via `RLock`. Nye metoder i `NormaRobotService` skal følge samme mønster.
- NAOqi‑afhængighed: Import af `ALProxy` kan fejle udenfor robotmiljø. Koden udsætter fejl til runtime; bevar denne adfærd for bedre DX.
- Tablet‑visning: Bruger data‑URI (base64). Store billeder/HTML kan blive tunge; overvej størrelser/komprimering.
- Gestures: `_cycle_gesture_name()` kører hver anden interaktion. Hvis du ændrer logik eller `GESTURES`, dokumentér ændringen.
- Port og binding: Standard 8080. Hvis du ændrer port, opdater `README.md` og alle integrationseksempler.
- Publik API‑stabilitet: Undgå breaking changes i `POST /api/command` format. Tilføj hellere nye kommandoer fremfor at ændre eksisterende parametre.

## 9) Sikkerhed og netværk
- Default er ingen auth/SSL (lokalt/lukket net). Hvis eksponeret bredt, tilføj mindst IP‑whitelisting eller en simpel token.
- Sørg for firewall‑regel for indgående TCP 8080 på værtsmaskinen, hvis klienter er på andre maskiner.
- Kode binder til alle interfaces; drift i delt miljø bør overveje binding til specifik IP eller reverse proxy.

## 10) Fejlfinding (kort)
- Virker lokalt men ikke eksternt: sandsynligvis firewall. Åbn 8080/tcp (se README “Fejlfinding”).
- NAOqi importfejl: Installer/aktiver NAOqi i Python 2.7‑miljø.
- Tablet viser intet: Tjek sti/fil og at webview ikke blokeres.
- Encoding: Send altid JSON som UTF‑8; vær opmærksom på æ/ø/å.

## 11) Udvidelse (vejledning til agenter)
- Tilføj ny robotfunktion:
  1. Implementér ny metode i `NormaRobotService` med `with self._lock:` og robust fejlbehandling.
  2. Tilføj tilsvarende gren i `ApiHandler._dispatch()` for `command`‑navnet.
  3. Opdater `README.md` (API‑reference + eksempler).
  4. Overvej tidsouts og fejlmeddelelser der er konsistente med eksisterende `{status:"error", message}`.
- Bevar Python 2.7‑kompatibilitet (ingen f‑strings, ingen `pathlib`, osv.).
- Logning holdes enkel (stdout). Støj må ikke blokere I/O.

## 12) Kendte begrænsninger
- Ingen persistens/metrics; kun simpel status (`interaction_count`).
- Ingen auth/SSL; forudsætter kontrolleret netværksmiljø.
- Ingen officielle tests pga. NAOqi runtime‑afhængighed.

## 13) “Før PR merge”‑tjekliste
- [ ] Koden kører i Python 2.7 uden syntaksfejl.
- [ ] NAOqi‑kald er beskyttet af lås og har fejlhåndtering.
- [ ] API‑ændringer dokumenteret i `README.md`.
- [ ] Port/konfiguration i kode og docs stemmer overens.
- [ ] Hurtig manuelle tests: `GET /api/status`, `POST /api/command` (mindst `say`).

## 14) Changelog (kort format)
- v1: HTTP‑service på port 8080, `NormaRobotService`, trådet server, intro‑billede/velkomst, grundlæggende API.
