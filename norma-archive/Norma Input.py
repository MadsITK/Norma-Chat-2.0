# -*- coding: utf-8 -*-
# ------------------------------------------------------------------
#K1 del 1: Encoding: Husk Encoding for at programmet kan forstå ÆØÅ. 
# ------------------------------------------------------------------
# Norma Chat 2.0 - Python 3.11
# Facilitere kommunikation mellem besøgende ved Dokk1 og Aarhus AI
# Aarhus AI er ikke klar til API implementation til Norma endnu, derfor kører vi med en lokal LLM model i form af Ollama indtil da. 
# Kode struktureret modulært i Kapitel 1-3 (Python 3.11) og Kapitel 4 (Python 2.7)
# Hele proceduren kører sekventielt. 

# -----------------------------
# K1 Del 2: Importer nødvendige biblioteker
# -----------------------------
#pyaudio lader os optage lyd via mikrofon
import pyaudio
#wave lader os gemme lydoptagelser i wav format
import wave
#os er til filsystem operationer. 
import os
#tilføjer whisper-bibliotekets sti så Python kan finde det. 
import sys
#OpenAI's tale til tekst model (whisper) 
import whisper
#subprocess til køring af eksterne programmer i dette tilfælde ollama og hente output
import subprocess
#keyboard læser tastaturinput
import keyboard
#time til forsinkelser og tidshåndtering
import time
#Subprocess for at lade flere aspekter køre på samme tid
import subprocess

# -----------------------------
# K1 Del 3: Konstanter
# -----------------------------
#BASE_DIR finder den mappe hvor scriptet kører
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#Angiv en undermappe til at gemme optagelser MIDLERTIGDIGT
AUDIO_FOLDER = os.path.join(BASE_DIR, "audio")
#L1_FILENAME navnet på den lydfil der gemmes
L1_FILENAME = "L1.wav"
#Kombinering af mappe og filnavn til en komplet sti
L1_PATH = os.path.join(AUDIO_FOLDER, L1_FILENAME)
#Angiver lydformatet som 16-bit PCM
FORMAT = pyaudio.paInt16
#Angiver om hvilken slags optagelse det skal være, here mono optagelse. 
CHANNELS = 1
#Rate er sample raten 16 kHz, standarden for talegenkendelsen
RATE = 16000
#Bufferstørrelse for PyAudio - antallet af frames der læses ad gangen. 
CHUNK = 2048

#Model som bruges ved Ollama
#Muligt at tage andre modeller i brug men en balance skal vedligeholdes mellem hastighed og præcision ift output. 
OLLAMA_MODEL = "llama3.2:3b"

print(f"Lydfil vil blive gemt her: {L1_PATH}")

# -----------------------------
# K1 Del 4: Mappeoprettelse
# -----------------------------

#Først tjekkes om mappen "AUDIO_FOLDER" eksisterer
#Hvis den ikke eksisterer laves den 
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)
    print(f"Mappen 'audio' blev oprettet her: {AUDIO_FOLDER}")
else:
    print("Mappen 'audio' findes allerede din dingus")

if os.path.exists(L1_PATH):
    os.remove(L1_PATH)
    print(f" Eksisterende L1.wav blev slettet: {L1_PATH}")

# -----------------------------
# K1 Del 5: Start PyAudio
# -----------------------------

#Initialisering af PyAudio som bruges til at åbne mikrofon streamen og optage lyd bidder
audio = pyaudio.PyAudio()

# -----------------------------
# K1 Del 6: Funktion til at åbne mikrofon-stream
# -----------------------------
def open_stream():
    return audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

# -----------------------------
# K1 Del 7: Funktion til optagelse af lyd
# -----------------------------
def record_audio():
    """
    Optager lyd så længe mellemrum holdes nede.
    Returnerer stream og frames.
    """
    frames = []
    recording = False
    stream = open_stream()  # K1 Del 6

    print("Hold mellemrum nede på tastaturet for at tale")

    try:
        while True:
            if keyboard.is_pressed("space"):
                if not recording:
                    print("Nu optages der, så snak dog!")
                    recording = True

                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)

            else:
                if recording:
                    print("Nu optages der ikke")
                    recording = False
                    break  # stop optagelsen når space slippes

    except KeyboardInterrupt:
        print("Optagelse afbrudt manuelt")
        stream.stop_stream()
        stream.close()
        return None

    return stream, frames

# -----------------------------
# K1 Del 8: Funktion til at lukke stream
# -----------------------------
def close_stream(stream):
    stream.stop_stream()
    stream.close()

# -----------------------------
# K1 Del 9: Funktion til at gemme lyd
# -----------------------------
def save_audio(frames, path=L1_PATH):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))
    print(f"L1 gemt som: {path}")

# -----------------------------
# K2: Indlæs Whisper-model (small)
# -----------------------------
print("Indlæser Whisper-model...")
model = whisper.load_model("small")
print("Whisper klar")

# -----------------------------
# K1-K3: Hovedloop
# -----------------------------
try:
    while True:
        # --- K1 Del 7: Optag lyd ---
        result = record_audio()
        if result is None:
            continue  # Hvis optagelsen blev afbrudt

        stream, frames = result

        # --- K1 Del 8: Luk stream ---
        close_stream(stream)
        print("Optagelse færdig")

        # --- K1 Del 9: Gem lydfil ---
        save_audio(frames)

        # --- K2: Whisper transkribering ---
        result = model.transcribe(L1_PATH, language="da")
        TL1 = result["text"]
        print(f"Transkriberet L1 til TL1: {TL1}")

        if not TL1.strip():
            print("Ingen tale opfanget - pr                                                                                                   n                                                                                   øv igen. Snak højt og tydeligt til Norma!")
            continue

        # --- K3: Send til Ollama ---
        prompt = f"""Du er Norma, en venlig biblioteksrobot i Dokk1.
Hvis brugerens spørgsmål er uklart eller lyder forkert, så stil ét kort opklarende spørgsmål.
Svar ellers kort og præcist (1-2 sætninger).

Brugerens input: {TL1}"""


        print("Sender TL1 til Ollama med bibliotekar-prompt...")

        process = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=prompt,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=True
        )

        ATF1 = process.stdout.strip()
        print("Svar fra Ollama(ATF1):")
        print(ATF1)

        OUTPUT_FILE = os.path.join(BASE_DIR, "latest_response.txt")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(ATF1)
        print(f"ATF1 gemt i filen: {OUTPUT_FILE}")

finally:
    # Luk PyAudio først, når hele programmet stopper
    audio.terminate()
