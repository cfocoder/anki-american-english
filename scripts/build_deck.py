#!/usr/bin/env python3
"""Build an Anki .apkg deck from words.yaml.

The YAML file is the source of truth. Generated artifacts go to:
- media/*.mp3
- decks/*.apkg
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sqlite3
import zipfile
from pathlib import Path
from typing import Any

import edge_tts
import genanki
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORDS_FILE = ROOT / "words.yaml"
MEDIA_DIR = ROOT / "media"
DECKS_DIR = ROOT / "decks"
APKG = DECKS_DIR / "american_english_pronunciation.apkg"

MODEL_ID = 1907202605
DECK_ID = 1907202606
SLOW_RATE = "-40%"
NORMAL_RATE = "+0%"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


async def synthesize(text: str, path: Path, voice: str, rate: str, force: bool) -> None:
    if path.exists() and path.stat().st_size > 1000 and not force:
        return
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(str(path))


async def make_audio(words: list[dict[str, Any]], voice: str, force: bool) -> None:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    for item in words:
        slug = slugify(item["word"])
        normal = MEDIA_DIR / f"{slug}_normal.mp3"
        slow = MEDIA_DIR / f"{slug}_slow.mp3"
        # Slow audio intentionally repeats only the complete word at a slower rate.
        # No spelling and no syllable-by-syllable spoken decomposition.
        await synthesize(item["word"], normal, voice, NORMAL_RATE, force)
        await synthesize(item["word"], slow, voice, SLOW_RATE, force)
        item["normal_file"] = normal.name
        item["slow_file"] = slow.name


def build_model() -> genanki.Model:
    return genanki.Model(
        MODEL_ID,
        "American Pronunciation With Normal And Slower Audio",
        fields=[
            {"name": "Word"},
            {"name": "IPA"},
            {"name": "Meaning_ES"},
            {"name": "Example_EN"},
            {"name": "Example_ES"},
            {"name": "Audio_Normal"},
            {"name": "Audio_Slow"},
            {"name": "Notes"},
        ],
        templates=[
            {
                "name": "Pronunciation Card",
                "qfmt": """
<div class="front">
  <div class="word">{{Word}}</div>
  <div class="hint">Pronounce it first, then flip.</div>
</div>
""",
                "afmt": """
{{FrontSide}}
<hr id="answer">
<div class="back">
  <div class="section"><b>Normal pronunciation</b><br>{{Audio_Normal}}</div>
  <div class="section"><b>Slower pronunciation</b><br>{{Audio_Slow}}</div>
  <div class="ipa">{{IPA}}</div>
  <div><b>Meaning:</b> {{Meaning_ES}}</div>
  <div class="example"><b>Example:</b><br>{{Example_EN}}</div>
  <div class="example es"><b>ES:</b><br>{{Example_ES}}</div>
  {{#Notes}}<div class="notes"><b>Note:</b> {{Notes}}</div>{{/Notes}}
</div>
""",
            }
        ],
        css="""
.card { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; font-size: 22px; text-align: center; color: #1f2937; background: #fafafa; }
.word { font-size: 44px; font-weight: 750; margin: 24px 0 8px; }
.hint { color: #6b7280; font-size: 16px; }
.section { margin: 18px 0; padding: 12px; background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; }
.ipa { font-size: 24px; color: #2563eb; margin: 18px 0; }
.example { margin-top: 14px; line-height: 1.35; }
.es { color: #4b5563; }
.notes { margin-top: 16px; font-size: 16px; color: #92400e; }
""",
    )


def build_deck(config: dict[str, Any]) -> tuple[Path, int, int]:
    DECKS_DIR.mkdir(parents=True, exist_ok=True)
    deck_name = config["deck"]["name"]
    words = config["words"]
    model = build_model()
    deck = genanki.Deck(DECK_ID, deck_name)

    for item in words:
        note = genanki.Note(
            model=model,
            fields=[
                item["word"],
                item.get("ipa", ""),
                item.get("meaning_es", ""),
                item.get("example_en", ""),
                item.get("example_es", ""),
                f"[sound:{item['normal_file']}]",
                f"[sound:{item['slow_file']}]",
                item.get("note", ""),
            ],
            guid=genanki.guid_for("american-pronunciation", item["word"].lower()),
        )
        deck.add_note(note)

    media_files = []
    for item in words:
        media_files.append(str(MEDIA_DIR / item["normal_file"]))
        media_files.append(str(MEDIA_DIR / item["slow_file"]))

    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(str(APKG))
    return APKG, len(words), len(media_files)


def verify_apkg(path: Path, expected_notes: int, expected_media: int) -> None:
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if "collection.anki2" not in names:
            raise RuntimeError("APKG missing collection.anki2")
        # genanki stores media as numbered files plus a media manifest.
        if len(names) < expected_media + 2:
            raise RuntimeError(f"APKG has too few members: {len(names)}")
        temp_collection = DECKS_DIR / ".collection_check.anki2"
        temp_collection.write_bytes(z.read("collection.anki2"))

    try:
        conn = sqlite3.connect(temp_collection)
        notes = conn.execute("select count(*) from notes").fetchone()[0]
        cards = conn.execute("select count(*) from cards").fetchone()[0]
        conn.close()
    finally:
        temp_collection.unlink(missing_ok=True)

    if notes != expected_notes or cards != expected_notes:
        raise RuntimeError(f"Expected {expected_notes} notes/cards, got notes={notes}, cards={cards}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-audio", action="store_true", help="Regenerate audio even if MP3s already exist")
    args = parser.parse_args()

    config = load_config(WORDS_FILE)
    voice = config.get("deck", {}).get("voice", "en-US-JennyNeural")
    words = config["words"]

    asyncio.run(make_audio(words, voice, force=args.force_audio))
    apkg, note_count, media_count = build_deck(config)
    verify_apkg(apkg, note_count, media_count)

    small = [p.name for p in MEDIA_DIR.glob("*.mp3") if p.stat().st_size < 1000]
    if small:
        raise RuntimeError(f"Suspiciously small audio files: {small}")

    print(f"Wrote: {apkg}")
    print(f"Notes/cards: {note_count}")
    print(f"Media files: {media_count}")
    print(f"Size: {apkg.stat().st_size} bytes")


if __name__ == "__main__":
    main()
