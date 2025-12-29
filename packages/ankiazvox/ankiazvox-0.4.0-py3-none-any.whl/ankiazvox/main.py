import os
import base64
import time
import shutil
import yaml
import subprocess
from typing import Any, Optional, Dict, List
from pathlib import Path
from dotenv import load_dotenv

import requests
import azure.cognitiveservices.speech as speechsdk
from tqdm import tqdm
import click
from bs4 import BeautifulSoup

# --- Constants ---
DEFAULT_CONFIG_FILENAME = "azv_config.yaml"

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
        """Synthesize text and save it as an MP3 file."""
        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(save_path))
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, audio_config=audio_config
        )
        result = synthesizer.speak_text_async(text).get()
        return result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted

    def get_voice_list(self, locale: Optional[str] = None) -> List[Any]:
        """Fetch list of available voices from Azure."""
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=None)
        result = synthesizer.get_voices_async(locale if locale else "").get()
        if result.reason == speechsdk.ResultReason.VoicesListRetrieved:
            return sorted(result.voices, key=lambda x: x.short_name)
        return []

    def list_voices(self, locale: Optional[str] = None):
        """Display available voices in terminal."""
        voices = self.get_voice_list(locale)
        if voices:
            click.echo(f"{'Voice Name':<40} | {'Gender':<10} | {'Locale':<10}")
            click.echo("-" * 65)
            for v in voices:
                gender = "Female" if v.gender == speechsdk.SynthesisVoiceGender.Female else "Male"
                click.echo(f"{v.short_name:<40} | {gender:<10} | {v.locale:<10}")
        else:
            click.secho("Error: Failed to retrieve voices list.", fg="red")


def clean_html(raw_html: str) -> str:
    """Remove HTML tags and convert entities to plain text for TTS."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def load_config(config_path: Optional[str] = None) -> Dict[str, str]:
    """Load configuration from YAML or .env file."""
    config = {
        "ANKI_CONNECT_URL": "http://127.0.0.1:8765",
        "AZURE_SPEECH_KEY": "",
        "AZURE_SPEECH_REGION": "",
        "DEFAULT_VOICE": ""
    }

    if config_path:
        target_path = Path(config_path)
    else:
        target_path = Path.cwd() / DEFAULT_CONFIG_FILENAME
        if not target_path.exists():
            alt_yml = Path.cwd() / "azv_config.yml"
            if alt_yml.exists():
                target_path = alt_yml
            else:
                target_path = Path.cwd() / ".env"

    if target_path.exists():
        if target_path.suffix.lower() in [".yaml", ".yml"]:
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    yaml_data = yaml.safe_load(f)
                    if isinstance(yaml_data, dict):
                        config.update(yaml_data)
                    return config
            except Exception as e:
                click.secho(f"Warning: Failed to parse YAML at {target_path}: {e}", fg="yellow")
        
        elif target_path.name == ".env" or target_path.suffix == "":
            load_dotenv(dotenv_path=target_path)
            config["ANKI_CONNECT_URL"] = os.getenv("ANKI_CONNECT_URL", config["ANKI_CONNECT_URL"])
            config["AZURE_SPEECH_KEY"] = os.getenv("AZURE_SPEECH_KEY", "")
            config["AZURE_SPEECH_REGION"] = os.getenv("AZURE_SPEECH_REGION", "")
            config["DEFAULT_VOICE"] = os.getenv("DEFAULT_VOICE", "")
            return config

    return config

def play_audio(file_path: Path):
    """Attempt to play the audio file using system players."""
    try:
        if os.name == 'nt':  # Windows
            os.startfile(file_path)
        elif os.uname().sysname == 'Darwin':  # macOS
            subprocess.run(['afplay', str(file_path)], check=True)
        else:  # Linux/others
            subprocess.run(['ffplay', '-nodisp', '-autoexit', str(file_path)], check=True)
    except Exception:
        pass

# --- CLI Command Group ---

@click.group()
def cli():
    """AnkiVox CLI: Professional Anki TTS Synchronization Tool."""
    pass

@cli.command()
@click.option("--config", type=click.Path(exists=True), help="Path to config file")
@click.option("--voice", "-v", help="Specific Azure voice name to sample")
@click.option("--locale", "-l", help="Sample all voices in a specific locale (e.g., en-US)")
@click.option("--text", "-t", default="Hello, this is a sample of the selected voice.", help="Text to synthesize")
@click.option("--out-dir", "-o", default="samples", help="Directory to save samples")
@click.option("--play", is_flag=True, default=False, help="Play audio (only works for single voice mode)")
def sample(config, voice, locale, text, out_dir, play):
    """Generate sample audio files for specific voices or entire locales."""
    if not voice and not locale:
        click.secho("Error: You must provide either --voice or --locale.", fg="red")
        return

    cfg = load_config(config)
    tts_key = cfg.get("AZURE_SPEECH_KEY")
    tts_region = cfg.get("AZURE_SPEECH_REGION")

    if not tts_key or not tts_region:
        click.secho("Error: Missing Azure credentials.", fg="red")
        return

    out_path = Path(out_dir)
    out_path.mkdir(exist_ok=True)
    
    tts_manager = AzureTTSManager(tts_key, tts_region)

    voices_to_sample = []
    if voice:
        voices_to_sample.append(voice)
    else:
        click.echo(f"Fetching voice list for locale '{locale}'...")
        list_res = tts_manager.get_voice_list(locale)
        voices_to_sample = [v.short_name for v in list_res]

    if not voices_to_sample:
        click.secho("No voices found to sample.", fg="yellow")
        return

    click.echo(f"Generating {len(voices_to_sample)} samples in '{out_dir}'...")
    
    for v_name in tqdm(voices_to_sample, desc="Generating Samples"):
        file_path = out_path / f"{v_name}.mp3"
        tts_manager.speech_config.speech_synthesis_voice_name = v_name
        if tts_manager.text_to_mp3(text, file_path):
            if play and len(voices_to_sample) == 1:
                play_audio(file_path)
        else:
            click.secho(f"Failed to generate for {v_name}", fg="yellow")

    click.secho(f"\nDone! Samples are available in the '{out_dir}/' folder.", fg="green")


@cli.command()
@click.option("--config", type=click.Path(exists=True), help="Path to azv_config.yaml or .env file")
@click.option("--locale", "-l", help="Filter voices by locale (e.g., en-US, zh-CN)")
def list_voices(config, locale):
    """List all available Azure TTS voices."""
    cfg = load_config(config)
    tts_key = cfg.get("AZURE_SPEECH_KEY")
    tts_region = cfg.get("AZURE_SPEECH_REGION")

    if not tts_key or not tts_region:
        click.secho(f"Error: Credentials missing.", fg="red")
        return

    tts = AzureTTSManager(tts_key, tts_region)
    tts.list_voices(locale)


@cli.command()
@click.option("--config", type=click.Path(exists=True), help="Path to config file")
@click.option("--query", "-q", required=True, help='Anki query string, e.g., "deck:Default"')
@click.option("--source", "-s", required=True, help="Source text field name")
@click.option("--target", "-t", required=True, help="Target audio field name")
@click.option("--voice", "-v", help="Azure voice name (overrides config)")
@click.option("--temp-dir", default="temp_audios", help="Directory for temporary audio files")
@click.option("--limit", type=int, help="Limit the number of notes to process")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite target field if not empty")
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation prompt")
def sync(config, query, source, target, voice, temp_dir, limit, overwrite, yes):
    """Sync Anki notes and generate Azure TTS audio."""
    cfg = load_config(config)

    anki_url = cfg.get("ANKI_CONNECT_URL")
    tts_key = cfg.get("AZURE_SPEECH_KEY")
    tts_region = cfg.get("AZURE_SPEECH_REGION")
    default_voice = voice or cfg.get("DEFAULT_VOICE")

    if not tts_key or not tts_region:
        click.secho(f"Error: Missing Azure credentials.", fg="red")
        return

    anki = AnkiClient(anki_url)
    tts = AzureTTSManager(tts_key, tts_region, default_voice)
    audio_path = Path(temp_dir)

    try:
        click.echo(f"Searching notes: {query}...")
        note_ids = anki.invoke("findNotes", query=query)
        if not note_ids:
            click.echo("No matching notes found.")
            return

        if limit: note_ids = note_ids[:limit]
        notes_data = anki.invoke("notesInfo", notes=note_ids)
        
        eligible_notes = []
        for note in notes_data:
            fields = note.get("fields", {})
            if source not in fields or target not in fields: continue
            if fields.get(target, {}).get("value", "").strip() and not overwrite: continue
            
            clean_text = clean_html(fields.get(source, {}).get("value", ""))
            if clean_text: eligible_notes.append((note["noteId"], clean_text))

        if not eligible_notes:
            click.secho("No notes require synchronization.", fg="yellow")
            return

        if not yes:
            if not click.confirm(f"Proceed syncing {len(eligible_notes)} notes?"): return

        audio_path.mkdir(exist_ok=True)
        for note_id, clean_text in tqdm(eligible_notes, desc="Syncing"):
            file_name = f"azv_{source}_{note_id}.mp3"
            local_file = audio_path / file_name
            if tts.text_to_mp3(clean_text, local_file):
                with open(local_file, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode("utf-8")
                anki.invoke("storeMediaFile", filename=file_name, data=b64_data)
                anki.invoke("updateNoteFields", note={"id": note_id, "fields": {target: f"[sound:{file_name}]"}})
                time.sleep(0.05)

        click.secho(f"\nCompleted!", fg="green")
    
    finally:
        if audio_path.exists(): shutil.rmtree(audio_path)


if __name__ == "__main__":
    cli()