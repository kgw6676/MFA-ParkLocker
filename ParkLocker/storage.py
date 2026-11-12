import json
from pathlib import Path

class Storage:
    def __init__(self, path='parking_state.json'):
        self.path = Path(path)

    def save(self, parking):
        data = {str(n): {'status': b.status.value, 'occupied': b.occupied} for n, b in parking.bays.items()}
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def load(self):
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding='utf-8'))
