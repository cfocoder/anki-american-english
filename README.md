# American English Anki pronunciation deck

Source repo for an Anki deck focused on American English pronunciation practice.

The source of truth is [`words.yaml`](./words.yaml). The generated deck is:

```text
decks/american_english_pronunciation.apkg
```

Each card currently has:

- front: the English word only;
- back: normal pronunciation audio;
- back: slower pronunciation audio;
- IPA;
- Spanish meaning;
- English example;
- Spanish translation;
- optional note.

## Add a word

Edit `words.yaml` and add an entry:

```yaml
  - word: thorough
    ipa: /ˈθɜːroʊ/
    meaning_es: minucioso; completo
    example_en: The team performed a thorough review.
    example_es: El equipo hizo una revisión minuciosa.
```

Then rebuild:

```bash
python3 -m pip install --user --break-system-packages -r requirements.txt
python3 scripts/build_deck.py
```

The build script creates or reuses:

```text
media/<word>_normal.mp3
media/<word>_slow.mp3
decks/american_english_pronunciation.apkg
```

The slower audio is intentionally just the same word at a slower speed. It does **not** spell the word or pronounce syllables separately.

## Import into Anki

On the laptop with Anki Desktop:

1. Open Anki.
2. `File` → `Import`.
3. Choose `decks/american_english_pronunciation.apkg`.
4. Sync from Anki Desktop to AnkiWeb.

## Notes for Hermes

When Héctor requests a new word through Slack or Telegram:

1. Add it to `words.yaml`.
2. Run `python3 scripts/build_deck.py`.
3. Commit `words.yaml`, new `media/*.mp3`, and updated `decks/*.apkg`.
4. Push to GitHub.
5. If the Dell Vostro is reachable, copy the `.apkg` to `~/Downloads/`.
