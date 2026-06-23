import base64
from pathlib import Path
p = Path(__file__).parent
for f in ['.dk', '.bt']:
    path = p / f
    if path.exists():
        d = base64.b64decode(path.read_text().strip()).decode()
        print(f"✅ {f}: {d[:12]}...")
    else:
        print(f"❌ {f}: NOT FOUND")
