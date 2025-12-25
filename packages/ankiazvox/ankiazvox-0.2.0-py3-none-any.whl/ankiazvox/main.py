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

    def __init__(self, key: str, region: str, voice: Optional[str] = None):
        self.speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
        if voice:
            self.speech_config.speech_synthesis_voice_name = voice
        # Set output format to MP3
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

    def list_voices(self, locale: Optional[str] = None):
        """Fetch and display available voices from Azure."""
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=None)
        result = synthesizer.get_voices_async(locale if locale else "").get()
        
        if result.reason == speechsdk.ResultReason.VoicesListRetrieved:
            voices = sorted(result.voices, key=lambda x: x.short_name)
            click.echo(f"{'Voice Name':<40} | {'Gender':<10} | {'Locale':<10}")
            click.echo("-" * 65)
            for v in voices:
                gender = "Female" if v.gender == speechsdk.SynthesisVoiceGender.Female else "Male"
                click.echo(f"{v.short_name:<40} | {gender:<10} | {v.locale:<10}")
        else:
            click.secho("Error: Failed to retrieve voices list.", fg="red")


# --- CLI Command Group ---

@click.group()
def cli():
    """AnkiVox CLI: Professional Anki TTS Synchronization Tool."""
    pass

@cli.command()
@click.option("--env", type=click.Path(exists=True), help="Path to your .env file")
@click.option("--locale", "-l", help="Filter voices by locale (e.g., en-US, zh-CN)")
def list_voices(env, locale):
    """List all available Azure TTS voices."""
    # Load configuration
    env_path = Path(env) if env else Path.cwd() / ".env"
    load_dotenv(dotenv_path=env_path)

    tts_key = os.getenv("AZURE_SPEECH_KEY")
    tts_region = os.getenv("AZURE_SPEECH_REGION")

    if not tts_key or not tts_region:
        click.secho("Error: Please configure AZURE_SPEECH_KEY and AZURE_SPEECH_REGION.", fg="red")
        return

    tts = AzureTTSManager(tts_key, tts_region)
    tts.list_voices(locale)


@cli.command()
@click.option("--env", type=click.Path(exists=True), help="Path to your .env file")
@click.option("--query", "-q", required=True, help='Anki query string, e.g., "deck:Default"')
@click.option("--source", "-s", required=True, help="Source text field name")
@click.option("--target", "-t", required=True, help="Target audio field name")
@click.option("--voice", "-v", help="Azure voice name (overrides .env)")
@click.option("--temp-dir", default="temp_audios", help="Directory for temporary audio files")
@click.option("--limit", type=int, help="Limit the number of notes to process")
def sync(env, query, source, target, voice, temp_dir, limit):
    """Sync Anki notes with generated Azure TTS audio."""
    # 1. Load configuration
    env_path = Path(env) if env else Path.cwd() / ".env"
    load_dotenv(dotenv_path=env_path)

    anki_url = os.getenv("ANKI_CONNECT_URL", "http://127.0.0.1:8765")
    tts_key = os.getenv("AZURE_SPEECH_KEY")
    tts_region = os.getenv("AZURE_SPEECH_REGION")
    default_voice = voice or os.getenv("DEFAULT_VOICE")

    if not tts_key or not tts_region:
        click.secho("Error: Missing Azure credentials in configuration.", fg="red")
        return

    # 2. Initialize
    anki = AnkiClient(anki_url)
    tts = AzureTTSManager(tts_key, tts_region, default_voice)
    audio_path = Path(temp_dir)
    audio_path.mkdir(exist_ok=True)

    # 3. Process
    click.echo(f"Searching notes: {query}...")
    note_ids = anki.invoke("findNotes", query=query)
    if not note_ids:
        click.echo("No notes found.")
        return

    if limit:
        note_ids = note_ids[:limit]

    notes_data = anki.invoke("notesInfo", notes=note_ids)
    success_count = 0
    for note in tqdm(notes_data, desc="Syncing Progress"):
        note_id = note["noteId"]
        text = note["fields"].get(source, {}).get("value", "").strip()
        if not text:
            continue

        file_name = f"tts_{note_id}.mp3"
        local_file = audio_path / file_name

        if tts.text_to_mp3(text, local_file):
            with open(local_file, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")
            anki.invoke("storeMediaFile", filename=file_name, data=b64_data)
            anki.invoke(
                "updateNoteFields",
                note={"id": note_id, "fields": {target: f"[sound:{file_name}]"}},
            )
            success_count += 1
            time.sleep(0.05)

    click.secho(f"\nCompleted! Successfully updated {success_count} notes.", fg="green")


if __name__ == "__main__":
    cli()