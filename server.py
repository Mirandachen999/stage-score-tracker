"""Learning stage tracker: standard-library web server with JSON-in-TXT persistence.
Run: python3 server.py   → http://localhost:8000
"""
import json
import os
import re
import tempfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / 'data'
DATA_FILE = DATA_DIR / 'records.txt'
LOCK = Lock()
DEFAULT = {'version': 1, 'sectionCount': 8, 'records': {}}
MAX_BODY = 1024 * 1024


def validate(value):
    if not isinstance(value, dict):
        raise ValueError('必須是 JSON 物件')
    count = value.get('sectionCount', 8)
    if type(count) is not int or count < 1:
        raise ValueError('階段數必須是正整數')
    raw = value.get('records', {})
    if not isinstance(raw, dict):
        raise ValueError('records 必須是物件')
    records = {}
    for key, rec in raw.items():
        if not re.fullmatch(r'[1-9]\d*-[1-5]', key) or not isinstance(rec, dict):
            raise ValueError('關卡 ID 格式錯誤')
        if not isinstance(rec.get('subject'), str) or not rec['subject'].strip() or len(rec['subject']) > 80:
            raise ValueError('科目名稱格式錯誤')
        score = rec.get('score')
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 100:
            raise ValueError('分數需介於 0～100')
        note = rec.get('notes', '')
        date = rec.get('updatedAt', '')
        if not isinstance(note, str) or len(note) > 1000 or not isinstance(date, str) or len(date) > 100:
            raise ValueError('備註或時間格式錯誤')
        records[key] = {'subject': rec['subject'].strip(), 'score': score, 'notes': note, 'updatedAt': date}
    return {'version': 1, 'sectionCount': count, 'records': records}


def read_data():
    DATA_DIR.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps(DEFAULT, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return validate(json.loads(DATA_FILE.read_text(encoding='utf-8')))


def write_data(value):
    DATA_DIR.mkdir(exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='records-', suffix='.tmp', dir=DATA_DIR)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            json.dump(value, out, ensure_ascii=False, indent=2)
            out.write('\n')
        os.replace(tmp, DATA_FILE)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def json_response(self, code, value):
        payload = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/data':
            try:
                with LOCK:
                    self.json_response(200, read_data())
            except Exception as e:
                self.json_response(500, {'error': str(e)})
            return
        # Keep the writable data file private; users can export from the UI.
        if path.startswith('/data/') or path == '/data':
            self.send_error(403, 'Forbidden')
            return
        super().do_GET()

    def do_PUT(self):
        if urlsplit(self.path).path != '/api/data':
            self.json_response(404, {'error': 'Not Found'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length <= 0 or length > MAX_BODY:
                self.json_response(413, {'error': '資料大小不合法或超過 1MB'})
                return
            body = self.rfile.read(length)
            content = validate(json.loads(body.decode('utf-8')))
            with LOCK:
                write_data(content)
            self.json_response(200, content)
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as e:
            self.json_response(400, {'error': str(e)})
        except Exception as e:
            self.json_response(500, {'error': str(e)})


if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '8000'))
    with ThreadingHTTPServer((host, port), Handler) as server:
        print(f'網站已啟動：http://{host}:{port}')
        print(f'JSON TXT 位置：{DATA_FILE}')
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('\n已停止')
