import os
import base64
import time
from typing import Any, Optional
from pathlib import Path
from dotenv import load_dotenv

import requests
import azure.cognitiveservices.speech as speechsdk
from tqdm import tqdm
import click

# --- Core Logic Classes ---

class AnkiClient:
    """Wrapper for AnkiConnect API interactions."""
    
    def __init__(self, url: str):
        self.url = url
        self.version = 6

    def invoke(self, action: str, **params) -> Any:
        """Standard method to invoke AnkiConnect actions."""
        payload = {"action": action, "version": self.version, "params": params}
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            data = response.json()
            if data.get("error"):
                raise Exception(f"AnkiConnect Error: {data['error']}")
            return data.get("result")
        except Exception as e:
            click.secho(
                f"Error: Unable to connect to Anki. Please ensure Anki is running "
                f"and the AnkiConnect plugin is installed. ({e})",
                fg="red",
            )
            return None


class AzureTTSManager:
    """Wrapper for Azure Cognitive Services Speech Synthesis."""

    def __init__(self, key: str, region: str, voice: str):
        self.speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
        self.speech_config.speech_synthesis_voice_name = voice
        # Set output format to MP3 (16khz, 32kbitrate, mono)
        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )

    def text_to_mp3(self, text: str, save_path: Path) -> bool:
        """Synthesize text to an MP3 file."""
        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(save_path))
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, audio_config=audio_config
        )
        result = synthesizer.speak_text_async(text).get()
        return result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted


# --- CLI Wrapper ---


@click.command()
@click.option(
    "--query",
    "-q",
    required=True,
    help='Anki query string, e.g., "deck:Default" or "nid:123456"',
)
@click.option(
    "--source", 
    "-s", 
    required=True, 
    help="Source text field name (used for speech generation)"
)
@click.option(
    "--target", 
    "-t", 
    required=True, 
    help="Target audio field name (for storing [sound:...] tags)"
)
@click.option(
    "--voice", 
    "-v", 
    help="Azure voice name (falls back to DEFAULT_VOICE in .env if not provided)"
)
@click.option(
    "--temp-dir", 
    default="temp_audios", 
    help="Directory for temporary audio files"
)
@click.option(
    "--limit", 
    type=int, 
    help="Limit the number of notes to process"
)
def main(query, source, target, voice, temp_dir, limit):
    """
    AnkiVox CLI: Sync Anki notes with high-quality Azure TTS audio.
    """
    # 1. Load configurations
    load_dotenv()

    anki_url = os.getenv("ANKI_CONNECT_URL", "http://127.0.0.1:8765")
    tts_key = os.getenv("AZURE_SPEECH_KEY")
    tts_region = os.getenv("AZURE_SPEECH_REGION")
    default_voice = voice or os.getenv("DEFAULT_VOICE")

    if not tts_key or not tts_region:
        click.secho(
            "Error: Please configure AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in your .env file.",
            fg="red",
        )
        return

    # 2. Initialize clients
    anki = AnkiClient(anki_url)
    tts = AzureTTSManager(tts_key, tts_region, default_voice)
    audio_path = Path(temp_dir)
    audio_path.mkdir(exist_ok=True)

    # 3. Fetch notes
    click.echo(f"Searching notes with query: {query}...")
    note_ids = anki.invoke("findNotes", query=query)

    if not note_ids:
        click.echo("No matching notes found.")
        return

    if limit:
        note_ids = note_ids[:limit]

    notes_data = anki.invoke("notesInfo", notes=note_ids)

    # 4. Process notes
    success_count = 0
    for note in tqdm(notes_data, desc="Syncing Progress"):
        note_id = note["noteId"]
        text = note["fields"].get(source, {}).get("value", "").strip()

        if not text:
            continue

        file_name = f"tts_{note_id}.mp3"
        local_file = audio_path / file_name

        # --- Step A: Generate Audio ---
        if tts.text_to_mp3(text, local_file):
            with open(local_file, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")

            # --- Step B: Store Media File in Anki ---
            anki.invoke("storeMediaFile", filename=file_name, data=b64_data)
            
            # --- Step C: Update Note Fields ---
            anki.invoke(
                "updateNoteFields",
                note={"id": note_id, "fields": {target: f"[sound:{file_name}]"}},
            )
            success_count += 1
            time.sleep(0.1)  # Brief pause to avoid overwhelming the APIs

    click.secho(f"\nTask completed! Successfully updated {success_count} notes.", fg="green")


if __name__ == "__main__":
    main()