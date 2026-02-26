# Zero Two — Bot de Música para Discord

Bot de música modular construido con discord.py que reproduce audio de YouTube directamente en canales de voz.

---

## Requisitos

| Dependencia | Versión |
|---|---|
| Python | 3.11+ |
| discord.py[voice] | 2.3.2 |
| yt-dlp | 2024.8.6+ |
| PyNaCl | 1.5.0 |
| python-dotenv | 1.0.0 |
| aiohttp | 3.9.0+ |

**Binarios requeridos (Windows):**
- `ffmpeg.exe` y `ffprobe.exe` en la raíz del proyecto (o en PATH)
- `opus.dll` en la raíz del proyecto

En Linux/Mac, instala ffmpeg con el gestor de paquetes del sistema (`apt`, `brew`, etc.) y el bot lo detectará automáticamente.

---

## Instalación

```bash
# 1. Clonar o descargar el proyecto
cd BOT_DISCORD

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt
```

---

## Configuración

Crea un archivo `.env` en la raíz con las siguientes variables:

```env
DISCORD_TOKEN=tu_token_aqui
PREFIX=!
OWNER_ID=tu_id_de_discord

# Opcional: rutas personalizadas
FFMPEG_PATH=./ffmpeg.exe
COOKIES_PATH=./cookies.txt
```

Obtén tu token en el Discord Developer Portal.

### cookies.txt (opcional)

Si YouTube bloquea las búsquedas, exporta las cookies de tu navegador a `cookies.txt` usando la extensión "Get cookies.txt LOCALLY" disponible para Chrome/Firefox.

---

## Ejecución

```bash
python bot.py
```

Los logs se escriben en `logs/bot.log` y también se muestran en consola.

---

## Comandos

### General

| Comando | Descripción |
|---|---|
| `!ping` | Muestra la latencia del bot |
| `!info` | Estadísticas del bot (servidores, uptime, versión) |
| `!help` | Lista todos los comandos disponibles |

### Conexión

| Comando | Aliases | Descripción |
|---|---|---|
| `!join` | `connect` | Conecta el bot a tu canal de voz |
| `!leave` | `disconnect`, `dc` | Desconecta el bot del canal de voz |

### Reproducción

| Comando | Aliases | Descripción |
|---|---|---|
| `!play <búsqueda>` | `p` | Busca en YouTube y reproduce / agrega a la cola |
| `!pause` | — | Pausa la reproducción |
| `!resume` | — | Reanuda la reproducción |
| `!skip` | `s` | Salta la canción actual (funciona aunque loop esté activo) |
| `!stop` | — | Detiene la reproducción, limpia la cola y desconecta |

### Cola

| Comando | Aliases | Descripción |
|---|---|---|
| `!queue` | `q` | Muestra la cola (hasta 10 canciones) |
| `!nowplaying` | `np` | Muestra la canción en reproducción |
| `!shuffle` | — | Mezcla aleatoriamente la cola |
| `!remove <pos>` | `rm` | Elimina la canción en la posición indicada |
| `!clear` | `clean` | Limpia canciones pendientes sin detener la actual |

### Ajustes

| Comando | Aliases | Descripción |
|---|---|---|
| `!volume [0-100]` | `vol`, `v` | Ajusta o consulta el volumen |
| `!loop` | `repeat` | Activa/desactiva el loop de la canción actual |
| `!loopqueue` | `lq` | Activa/desactiva el loop de la cola completa |

### Administración (solo owner)

| Comando | Descripción |
|---|---|
| `!reload <cog>` | Recarga un cog sin reiniciar el bot |
| `!shutdown` | Apaga el bot |

---

## Arquitectura

```
BOT_DISCORD/
├── bot.py              # Entry point: FlaviBot, carga de cogs, logging
├── config.py           # Configuración centralizada (env vars + constantes)
├── requirements.txt
├── .env                # Variables de entorno (no commitear)
├── cookies.txt         # Cookies de YouTube (opcional)
├── ffmpeg.exe          # Binario FFmpeg (Windows)
├── opus.dll            # Codec Opus (Windows)
├── cogs/
│   ├── admin.py        # Comandos de administración (owner only)
│   ├── general.py      # Comandos generales (ping, info, help)
│   └── music.py        # Comandos de música + gestión de colas por servidor
├── utils/
│   ├── music_queue.py  # Clases Song y MusicQueue
│   └── youtube.py      # YTDLSource: búsqueda y streaming con yt-dlp
├── data/
│   └── playlists/      # Reservado para futuras playlists persistentes
└── logs/
    └── bot.log         # Log de la sesión actual
```

### Flujo de reproducción

```
!play "nombre canción"
  └─ YTDLSource.search()       → búsqueda en YouTube con yt-dlp
       └─ Song(data)           → objeto con título, URL, duración, etc.
            └─ MusicQueue.add()
                 └─ play_next()
                      └─ YTDLSource.from_url()   → extrae URL de audio
                           └─ FFmpegPCMAudio      → stream al canal de voz
                                └─ after_playing  → llama play_next() recursivo
```

### Aislamiento por servidor

Cada servidor tiene su propia instancia de `MusicQueue` en `Music.queues[guild_id]`.
Las colas se limpian automáticamente cuando:
- El bot se desconecta del canal (`on_voice_state_update`)
- El bot es expulsado del servidor (`on_guild_remove`)

---

## Variables de entorno

| Variable | Obligatoria | Default | Descripción |
|---|---|---|---|
| `DISCORD_TOKEN` | Sí | — | Token del bot |
| `PREFIX` | No | `!` | Prefijo de comandos |
| `OWNER_ID` | No | `0` | ID del dueño del bot |
| `FFMPEG_PATH` | No | `./ffmpeg.exe` (Win) / `ffmpeg` (otros) | Ruta al ejecutable FFmpeg |
| `COOKIES_PATH` | No | `./cookies.txt` | Ruta al archivo de cookies |

---

## Notas de seguridad

- **Nunca commitees `.env`** — está en `.gitignore` por defecto.
- Si el token queda expuesto, regenerarlo inmediatamente en el Discord Developer Portal.
- El `OWNER_ID` determina quién puede usar `!reload` y `!shutdown`.
