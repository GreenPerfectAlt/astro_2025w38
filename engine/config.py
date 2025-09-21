# engine/config.py

# --- Настройки окна ---
SCR_WIDTH, SCR_HEIGHT = 1200, 800

# --- Настройки мира ---
CHUNK_SIZE = 16
WORLD_HEIGHT_LIMIT = 120
VIEW_DISTANCE_IN_CHUNKS = 8

# --- Параметры генерации шума ---
SCALE = 30.0
OCTAVES = 4
PERSISTENCE = 0.5
LACUNARITY = 2.0
SEED = 0
HEIGHT_MULTIPLIER = 15