import dearpygui.dearpygui as dpg
import numpy as np
import noise

# --- Параметры нашей карты ---
MAP_WIDTH = 1820
MAP_HEIGHT = 300
# Масштаб шума. Попробуй поменять это значение, чтобы увидеть разницу
SCALE = 100.0

# --- Функция для генерации данных текстуры ---
def generate_world_texture_data():
    # Создаем пустой 3D-массив (ширина, высота, 4 канала RGBA) с помощью NumPy
    texture_data = np.zeros((MAP_HEIGHT, MAP_WIDTH, 4), dtype=np.float32)

    # Проходим по каждому пикселю будущего изображения
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            # Генерируем значение шума для каждой точки
            # pnoise2 - 2D шум. Мы делим на SCALE для масштабирования.
            value = noise.pnoise2(x / SCALE, y / SCALE, octaves=6, persistence=0.5, lacunarity=2.0, base=0)

            # Приводим значение из диапазона [-1, 1] к [0, 1]
            value_normalized = (value + 1) / 2

            # Выбираем цвет в зависимости от "высоты" (значения шума)
            if value_normalized < 0.2:
                # Глубокая вода (синий)
                color = [0.0, 0.0, 0.5, 1.0]
            elif value_normalized < 0.3:
                # Мелководье (голубой)
                color = [0.0, 0.5, 1.0, 1.0]
            elif value_normalized < 0.5:
                # Равнина (зеленый)
                color = [0.0, 0.8, 0.0, 1.0]
            elif value_normalized < 0.7:
                # Горы (коричневый)
                color = [0.6, 0.4, 0.2, 1.0]
            else:
                # Снег (белый)
                color = [1.0, 1.0, 1.0, 1.0]
            
            # Записываем цвет пикселя в наш массив
            texture_data[y, x] = color
    
    # Dear PyGui требует плоский массив, поэтому "выравниваем" его
    return texture_data.flatten()

# --- Настройка Dear PyGui ---
dpg.create_context()

# Сгенерированные данные нужно где-то хранить. Для этого есть реестр текстур.
with dpg.texture_registry(show=False):
    texture_data = generate_world_texture_data()
    # Добавляем нашу "сырую" текстуру в реестр.
    # tag - это ID, по которому мы будем ее вызывать.
    dpg.add_raw_texture(width=MAP_WIDTH, height=MAP_HEIGHT, default_value=texture_data, format=dpg.mvFormat_Float_rgba, tag="world_texture")

# Создаем главное окно
with dpg.window(label="Генератор процедурных миров", tag="Primary Window"):
    # Добавляем в окно виджет Image, который показывает нашу текстуру
    dpg.add_image("world_texture")

# Стандартный код для запуска
dpg.create_viewport(title='Астро-генератор v0.1', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)
dpg.start_dearpygui()
dpg.destroy_context()