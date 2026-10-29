"""
Santali TTS - Complete System
==============================
/       → Recording Studio
/tts    → TTS Web App
Supports: Latin script + Ol Chiki script
"""

from flask import Flask, request, jsonify, send_from_directory, send_file
import os
import io
from gtts import gTTS

app = Flask(__name__, static_folder='static')

BASE_DIR       = r'G:\My Drive\SantaliTTS'
RECORDINGS_DIR = os.path.join(BASE_DIR, 'recordings')
METADATA_FILE  = os.path.join(BASE_DIR, 'dataset', 'metadata.csv')

SCRIPTS = {
    'latin':   'sentences_latin.txt',
    'olchiki': 'sentences_olchiki.txt',
}

SPEAKERS = [
    {'id': 'male',   'label': 'Male Voice',   'icon': '👨'},
    {'id': 'female', 'label': 'Female Voice', 'icon': '👩'},
    {'id': 'elder',  'label': 'Elder Voice',  'icon': '🧓'},
]

os.makedirs(RECORDINGS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)


def load_sentences(script='latin'):
    fname = SCRIPTS.get(script, SCRIPTS['latin'])
    with open(fname, 'r', encoding='utf-8') as f:
        return [l.strip() for l in f if l.strip()]


def get_recorded(speaker_id, script='latin'):
    sentences = load_sentences(script)
    done = []
    for i in range(len(sentences)):
        fname = f"{script}_{speaker_id}_sentence_{i+1:04d}.webm"
        if os.path.exists(os.path.join(RECORDINGS_DIR, fname)):
            done.append(i)
    return done


# ─── Pages ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/tts')
def tts_page():
    return send_from_directory('static', 'tts.html')


# ─── API ──────────────────────────────────────────────────────────────────────

@app.route('/api/sentences')
def get_sentences():
    speaker_id = request.args.get('speaker', 'male')
    script     = request.args.get('script',  'latin')
    sentences  = load_sentences(script)
    recorded   = get_recorded(speaker_id, script)
    return jsonify({
        'sentences':        sentences,
        'total':            len(sentences),
        'recorded':         len(recorded),
        'recorded_indices': recorded,
        'speakers':         SPEAKERS,
        'script':           script,
    })


@app.route('/api/save', methods=['POST'])
def save_recording():
    speaker_id     = request.form.get('speaker', 'male')
    script         = request.form.get('script',  'latin')
    sentence_index = int(request.form.get('index', 0))
    audio_file     = request.files.get('audio')

    if not audio_file:
        return jsonify({'error': 'No audio'}), 400

    sentences = load_sentences(script)
    filename  = f"{script}_{speaker_id}_sentence_{sentence_index+1:04d}.webm"
    filepath  = os.path.join(RECORDINGS_DIR, filename)
    audio_file.save(filepath)

    with open(METADATA_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{filename}|{sentences[sentence_index]}|{speaker_id}|{script}\n")

    recorded = get_recorded(speaker_id, script)
    print(f"✅ {filename} saved ({len(recorded)}/{len(sentences)})")

    return jsonify({
        'success':  True,
        'filename': filename,
        'progress': f"{len(recorded)}/{len(sentences)}",
    })


@app.route('/api/speakers')
def get_speakers():
    script    = request.args.get('script', 'latin')
    sentences = load_sentences(script)
    result    = []
    for sp in SPEAKERS:
        recorded = get_recorded(sp['id'], script)
        result.append({
            **sp,
            'recorded': len(recorded),
            'total':    len(sentences),
            'ready':    len(recorded) >= 10,
        })
    return jsonify(result)


@app.route('/api/generate', methods=['POST'])
def generate_tts():
    """Generate audio from text using gTTS and return as MP3."""
    data   = request.get_json()
    text   = data.get('text', '').strip()
    slow   = data.get('slow', False)
    script = data.get('script', 'latin')

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    # Ol Chiki script — transliterate to Latin for gTTS
    if script == 'olchiki':
        text = transliterate_olchiki(text)

    try:
        tts = gTTS(text=text, lang='en', slow=slow)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        audio_bytes = buf.read()
        return send_file(
            io.BytesIO(audio_bytes),
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name='santali.mp3',
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def transliterate_olchiki(text):
    """Simple Ol Chiki → Latin transliteration for gTTS pronunciation."""
    mapping = {
        'ᱚ':'o','ᱛ':'t','ᱜ':'g','ᱝ':'ng','ᱞ':'l','ᱟ':'a','ᱠ':'k','ᱡ':'j',
        'ᱢ':'m','ᱣ':'w','ᱤ':'i','ᱥ':'s','ᱦ':'h','ᱧ':'ny','ᱨ':'r','ᱩ':'u',
        'ᱪ':'ch','ᱫ':'d','ᱬ':'nd','ᱭ':'y','ᱮ':'e','ᱯ':'p','ᱰ':'dr','ᱱ':'n',
        'ᱲ':'rr','ᱳ':'o','ᱴ':'tt','ᱵ':'b','ᱶ':'v','ᱷ':'h','ᱸ':'n','ᱹ':'',
        'ᱺ':'','ᱻ':' ','ᱼ':'','ᱽ':'','।':'.','?':'?',
    }
    result = ''
    for ch in text:
        result += mapping.get(ch, ch if ch.isascii() else ' ')
    return result


@app.route('/api/delete/<speaker>/<script>/<int:index>', methods=['DELETE'])
def delete_recording(speaker, script, index):
    filename = f"{script}_{speaker}_sentence_{index+1:04d}.webm"
    filepath = os.path.join(RECORDINGS_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'success': True})
    return jsonify({'error': 'Not found'}), 404


if __name__ == '__main__':
    latin_count   = len(load_sentences('latin'))
    olchiki_count = len(load_sentences('olchiki'))
    print("=" * 50)
    print("  Santali TTS System")
    print("=" * 50)
    print(f"  Latin sentences   : {latin_count}")
    print(f"  Ol Chiki sentences: {olchiki_count}")
    print(f"  Speakers          : {len(SPEAKERS)}")
    print("=" * 50)
    print("  🎤 Recording : http://localhost:5000")
    print("  🔊 TTS App   : http://localhost:5000/tts")
    print("=" * 50)
    app.run(debug=False, port=5000)
