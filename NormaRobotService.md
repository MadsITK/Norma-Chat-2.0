Refaktorer Norma_Output.py (Python 2.7) til en service-baseret arkitektur med følgende krav:

1. **Ekstraher NAOqi funktionalitet til en NormaRobotService klasse** med metoderne:
   - `say(text, gesture=None)` - TTS med optional gesture
   - `play_gesture(gesture_name)` - Afspil specifik gesture
   - `show_tablet_image(image_path)` - Vis billede på tablet
   - `show_tablet_html(html_content)` - Vis HTML på tablet
   - `hide_tablet()` - Skjul tablet
   - `get_status()` - Returner robot status (IP, port, interaction_count)

2. **Implementer command processor** der:
   - Læser JSON kommandofil: `commands/pending_command.json`
   - Eksekuterer tilsvarende service metode
   - Skriver resultat til: `commands/command_result.json`
   - Format:
     ```json
     Input:  {"command": "say", "params": {"text": "Hej", "gesture": "hello"}}
     Output: {"status": "success", "data": {...}} eller {"status": "error", "message": "..."}
     ```

3. **Erstat while-loop** med command polling:
   - Tjek for ny `pending_command.json` (via modification time)
   - Eksekver kommando
   - Slet pending efter eksekution
   - Behold error handling

4. **Bevar al eksisterende funktionalitet**:
   - Tablet intro med billede
   - Gesture cycling logik
   - UTF-8 encoding håndtering
   - Samme ROBOT_IP/PORT konfiguration

5. **Opret commands/ mappe** automatisk ved opstart

Resultatet skal stadig kunne køre i Python 2.7 med NAOqi, men være klar til at modtage kommandoer fra et Python 3.11 API via filsystemet.
