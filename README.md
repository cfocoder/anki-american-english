# American English Anki pronunciation deck

Source repo for an Anki deck focused on American English pronunciation practice. It is designed to work well with [Hermes AI Agent](https://hermes-agent.nousresearch.com/): a user can ask Hermes to add new words, regenerate audio, rebuild the Anki package, and commit the updated artifacts.

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

On a machine with Anki Desktop:

1. Open Anki.
2. `File` → `Import`.
3. Choose `decks/american_english_pronunciation.apkg`.
4. Sync from Anki Desktop to AnkiWeb.

## Hermes AI Agent workflow

When a user asks Hermes AI Agent to add a new word through Slack, Telegram, or another connected chat surface:

1. Add it to `words.yaml`.
2. Run `python3 scripts/build_deck.py`.
3. Commit `words.yaml`, new `media/*.mp3`, and updated `decks/*.apkg`.
4. Push to GitHub.
5. Deliver the updated `.apkg` file to the user, or copy it to the user's target machine when a reachable destination has been configured.
