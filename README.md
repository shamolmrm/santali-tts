# Santali TTS — recording studio & text-to-speech web app

A Flask app for building a **Santali speech dataset** and testing text-to-speech. Supports both **Latin** and **Ol Chiki** scripts.

## Pages
| Route | What it does |
|---|---|
| `/` | **Recording Studio** — shows sentences one by one; speakers (male / female / elder voice) record them; audio is saved and listed in `dataset/metadata.csv`. |
| `/tts` | **TTS web app** — type text and hear it spoken. |

## Files
- `app.py` — Flask server (routes, saving recordings, metadata)
- `sentences_latin.txt`, `sentences_olchiki.txt`, `sentences.txt` — prompt sentences for recording
- `static/index.html`, `static/tts.html` — front end

> Sentence lists and recordings must be checked by native Santali speakers before they are used to train any model.

## Run
```bash
pip install -r requirements.txt gtts
python app.py
```
`BASE_DIR` in `app.py` points to the folder where recordings and `metadata.csv` are stored — change it for your machine.

Related: the full Santali platform lives in the [SANTALIQ](https://github.com/shamolbro/SANTALIQ) repo.
