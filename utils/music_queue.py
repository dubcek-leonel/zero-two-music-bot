"""
Sistema de cola de música
"""

import random
from collections import deque
from typing import Optional, List


class Song:
    """Representa una canción en la cola"""

    def __init__(self, data: dict):
        self.url = data.get("url")
        self.title = data.get("title", "Desconocido")
        self.duration = data.get("duration", 0)
        self.thumbnail = data.get("thumbnail")
        self.requester = data.get("requester")
        self.webpage_url = data.get("webpage_url")

    def format_duration(self) -> str:
        """Formatea la duración como HH:MM:SS o MM:SS"""
        if not self.duration:
            return "Desconocido"
        minutes, seconds = divmod(int(self.duration), 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"


class MusicQueue:
    """Cola de reproducción por servidor"""

    def __init__(self):
        self._queue: deque = deque()
        self.current: Optional[Song] = None
        self.loop: bool = False  # loop de la canción actual
        self.loop_queue: bool = False  # loop de toda la cola

    # ── Consultas ─────────────────────────────

    def is_empty(self) -> bool:
        return len(self._queue) == 0

    def __len__(self) -> int:
        return len(self._queue)

    def get_queue(self) -> List[Song]:
        return list(self._queue)

    # ── Escritura ─────────────────────────────

    def add(self, song: Song) -> int:
        """Agrega una canción al final de la cola. Devuelve la posición."""
        self._queue.append(song)
        return len(self._queue)

    def next(self) -> Optional[Song]:
        """
        Avanza al siguiente elemento según el modo activo:
        - loop=True  → repite la canción actual
        - loop_queue → mueve la canción actual al final antes de avanzar
        - normal     → simplemente avanza
        """
        if self.loop and self.current:
            return self.current

        if self.loop_queue and self.current:
            self._queue.append(self.current)

        if not self._queue:
            self.current = None
            return None

        self.current = self._queue.popleft()
        return self.current

    def skip(self) -> Optional[Song]:
        """
        Avanza siempre al siguiente elemento, ignorando el modo loop.
        Se usa cuando el usuario pide saltar explícitamente.
        """
        if not self._queue:
            self.current = None
            return None
        self.current = self._queue.popleft()
        return self.current

    def remove(self, index: int) -> bool:
        """Elimina la canción en la posición index (0-based)."""
        try:
            del self._queue[index]
            return True
        except (IndexError, TypeError):
            return False

    def shuffle(self) -> int:
        """Mezcla aleatoriamente la cola. Devuelve el número de canciones."""
        lst = list(self._queue)
        random.shuffle(lst)
        self._queue = deque(lst)
        return len(lst)

    def clear_queue_only(self) -> int:
        """
        Limpia las canciones pendientes sin detener la reproducción actual
        ni modificar los modos de loop.
        """
        count = len(self._queue)
        self._queue.clear()
        return count

    def clear(self):
        """Limpia todo: cola, canción actual y modos de loop."""
        self._queue.clear()
        self.current = None
        self.loop = False
        self.loop_queue = False
