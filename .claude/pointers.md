# Agent-pointers

Hurtig orientering til Claude Code når den arbejder i dette workspace.

## Det vigtigste først

1. **Læs `CLAUDE.md` i workspace-roden** for arkitekturoverblik.
2. **Hvis du redigerer kode i et sub-repo, læs det sub-repos egen `CLAUDE.md` først** — Python-version, konventioner og threading-regler er specifikke pr. sub-repo.
3. **`norma-archive/` er read-only** — det er et frosset snapshot af den gamle monolit. Brug det som reference, men redigér ikke i det.

## Mapping: opgave → repo

| Opgave | Repo |
|---|---|
| Robot-kommando, NAOqi-kald, intro, tablet | `norma-robot-bridge/` (Py 2.7) |
| LLM-adapter, Whisper, mikrofon, pipeline | `norma-input/` (Py 3.11) |
| API-kontrakt (OpenAPI), prompt-skabeloner | bor i `norma-robot-bridge/` |
| Tværgående arkitektur, dev-scripts | her i workspace-roden |

## Python-version-faldgruber

- `norma-robot-bridge` er **Python 2.7**. Ingen f-strings, ingen `pathlib`, ingen `typing`-annotationer, ingen `dataclasses`. Brug `from __future__ import print_function` og `% (...)`-formatering. Verificér med `python2 -m py_compile`.
- `norma-input` er **Python 3.11+**. Type hints og f-strings er standarden.

## Hvorfor er sub-repos gitignored fra workspace?

De er separate git-repos med egne `.git/`-mapper, klonet ind som søsterklones. Workspace-repoet versionerer kun limet (docs, scripts, agent-konfig). Se `README.md` for begrundelse.

## Plan-fil

Den oprindelige refaktoreringsplan ligger på `C:\Users\az77820\.claude\plans\vi-er-i-gang-clever-thunder.md`.
