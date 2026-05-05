# API-kontrakt

## Single source of truth

API-kontrakten ejes af **`norma-robot-bridge`**. Spec'en lever på:

```
norma-robot-bridge/api-spec/openapi.yaml
```

Hver ændring til API'et skal opdatere spec'en i samme commit/PR som ændrer `norma_bridge/api/commands.py`.

## Versionering

API'et er **uversioneret** lige nu — endpoints lever på `/api/command` og `/api/status`. Hvis breaking changes en dag bliver nødvendige, introducerer vi `/api/v2/...` parallelt med de uversionerede endpoints så klienter kan migrere kontrolleret. Indtil da gælder: én klient, én kontrakt — ingen grund til at versionere.

## Kontrakttests

Bridge har eksekverbare kontrakttests i `norma-robot-bridge/tests/test_contract.py`. De kører kommando-dispatcheren mod en `FakeRobotService` og asserter at hver kommando returnerer det forventede skema.

`norma-input` har klient-side kontrakttests der starter en local fake-bridge og kører forventede request/response-par igennem.

## Synkroniseringsstrategi

Indtil videre er aftalen: når bridge ændrer kontrakten, opdaterer udvikleren også `norma-input` i samme arbejdsblok. Når projektet vokser, kan vi tilføje:

- En CI-job i `norma-input` der downloader bridge's nuværende `openapi.yaml` (fra GitHub raw URL eller via lokal sti i workspace) og fejler hvis input's antagelser om API'et er forældede.
- En genereret klient-pakke fra OpenAPI-spec'en, vendor-kopieret ind i `norma-input/src/norma_input/contracts/`.
