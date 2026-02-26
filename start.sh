#!/bin/bash
apt-get update -qq && apt-get install -y ffmpeg libopus0 2>/dev/null || true
python bot.py
```

Y actualiza el `Procfile`:
```
worker: bash start.sh