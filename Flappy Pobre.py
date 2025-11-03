import pygame
import random
import sys
import os
import math
import json
from itertools import cycle
from pygame.locals import *  # Importación necesaria para las constantes como QUIT, KEYDOWN, etc.

# Configuración del juego
FPS = 30
SCREENWIDTH = 576  # Duplicado de 288 a 576
SCREENHEIGHT = 768  # Incrementado de 512 a 768
PIPEGAPSIZE = 150  # Incrementado de 100 a 150 para más espacio entre tuberías
BASEY = SCREENHEIGHT * 0.79

# Configuración de pantalla
FULLSCREEN = False  # Cambiar a True para pantalla completa

# Diccionarios para almacenar imágenes, sonidos y máscaras de colisión
IMAGES, SOUNDS, HITMASKS = {}, {}, {}

# Colores para las imágenes generadas
COLORS = {
    'day_sky': (135, 206, 235),  # Azul cielo diurno
    'night_sky': (25, 25, 112),  # Azul cielo nocturno
    'ground': (222, 184, 135),   # Marrón arena
    'pipe_green': (0, 128, 0),   # Verde
    'pipe_red': (220, 20, 60),   # Rojo
    'red_box': (220, 20, 60),    # Rojo
    'blue_box': (30, 144, 255),  # Azul
    'yellow_box': (255, 215, 0), # Amarillo
    'white': (255, 255, 255),    # Blanco
    'black': (0, 0, 0),          # Negro
    'text': (255, 255, 255),     # Blanco para texto
    'button': (100, 100, 200),   # Azul para botones
    'clear_button': (200, 50, 50), # Rojizo para botón de borrar
}

# Lista de jugadores (cada uno con 3 posiciones de aleteo)
PLAYERS_LIST = (
    # caja roja
    ('redbox-upflap', 'redbox-midflap', 'redbox-downflap'),
    # caja azul
    ('bluebox-upflap', 'bluebox-midflap', 'bluebox-downflap'),
    # caja amarilla
    ('yellowbox-upflap', 'yellowbox-midflap', 'yellowbox-downflap'),
)

# Lista de fondos
BACKGROUNDS_LIST = (
    'background-day',
    'background-night',
)

# Lista de tuberías
PIPES_LIST = (
    'pipe-green',
    'pipe-red',
)

# Archivos para guardar puntuaciones
SCORES_FILE = "flappy_pobre_scores.json"  # Cambiado de flappy_box a flappy_pobre
CURRENT_SCORE_FILE = "flappy_pobre_current_score.json"  # Cambiado de flappy_box a flappy_pobre

try:
    xrange
except NameError:
    xrange = range

def load_high_scores():
    """Carga las puntuaciones más altas desde un archivo"""
    try:
        if os.path.exists(SCORES_FILE):
            with open(SCORES_FILE, 'r') as f:
                scores = json.load(f)
                # Verificar si los datos están en formato antiguo (solo números)
                if scores and isinstance(scores[0], int):
                    # Convertir formato antiguo a nuevo
                    return [{'name': 'Jugador', 'score': score} for score in scores]
                return scores
        return []
    except:
        return []

def save_high_scores(scores):
    """Guarda las puntuaciones más altas en un archivo"""
    try:
        with open(SCORES_FILE, 'w') as f:
            json.dump(scores, f)
        return True
    except:
        return False

def clear_high_scores():
    """Borra todas las puntuaciones guardadas"""
    try:
        # Borrar archivo de puntuaciones altas
        if os.path.exists(SCORES_FILE):
            os.remove(SCORES_FILE)
        
        # Limpiar archivo de puntuación actual
        save_current_score(0, "")
        
        return True
    except:
        return False

def load_current_score():
    """Carga la puntuación actual desde un archivo"""
    try:
        if os.path.exists(CURRENT_SCORE_FILE):
            with open(CURRENT_SCORE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('score', 0), data.get('name', '')
        return 0, ''
    except:
        return 0, ''

def save_current_score(score, name):
    """Guarda la puntuación actual en un archivo"""
    try:
        with open(CURRENT_SCORE_FILE, 'w') as f:
            json.dump({'score': score, 'name': name}, f)
        return True
    except:
        return False

def update_high_scores(new_score, name):
    """Actualiza la tabla de puntuaciones con una nueva puntuación"""
    scores = load_high_scores()
    
    # Buscar si el nombre ya existe
    found = False
    for i, score_data in enumerate(scores):
        # Verificar si score_data es un diccionario (formato nuevo)
        if isinstance(score_data, dict):
            if score_data['name'] == name:
                # Si el nombre ya existe, actualizar solo si la nueva puntuación es mayor
                if new_score > score_data['score']:
                    scores[i]['score'] = new_score
                found = True
                break
    
    # Si el nombre no existe, añadirlo
    if not found:
        scores.append({'name': name, 'score': new_score})
    
    # Ordenar de mayor a menor
    scores.sort(key=lambda x: x['score'], reverse=True)
    scores = scores[:10]  # Mantener solo las 10 mejores puntuaciones
    save_high_scores(scores)
    return scores

def get_player_name():
    """Pide al jugador que ingrese su nombre"""
    input_active = True
    player_name = ""
    input_box = pygame.Rect(SCREENWIDTH//2 - 150, SCREENHEIGHT//2, 300, 50)
    
    # Generar imagen para el fondo de entrada de nombre
    name_bg = pygame.Surface((400, 300), pygame.SRCALPHA)
    pygame.draw.rect(name_bg, (0, 0, 0, 200), (0, 0, 400, 300))
    pygame.draw.rect(name_bg, COLORS['white'], (0, 0, 400, 300), 3)
    
    # Crear un fondo simple para la pantalla de entrada de nombre
    temp_bg = pygame.Surface((SCREENWIDTH, SCREENHEIGHT))
    temp_bg.fill(COLORS['day_sky'])  # Usar color del cielo diurno
    
    while input_active:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == K_RETURN:
                    if player_name.strip():  # Solo continuar si hay texto
                        input_active = False
                elif event.key == K_BACKSPACE:
                    player_name = player_name[:-1]
                else:
                    # Limitar la longitud del nombre
                    if len(player_name) < 15:
                        player_name += event.unicode
        
        # Dibujar fondo temporal
        SCREEN.blit(temp_bg, (0, 0))
        
        # Dibujar caja de entrada de nombre
        name_x = (SCREENWIDTH - name_bg.get_width()) // 2
        name_y = (SCREENHEIGHT - name_bg.get_height()) // 2
        SCREEN.blit(name_bg, (name_x, name_y))
        
        # Dibujar texto
        title_font = pygame.font.SysFont('Arial', 30, bold=True)
        title_text = title_font.render("Ingresa tu nombre", True, COLORS['white'])
        title_rect = title_text.get_rect(center=(SCREENWIDTH//2, name_y + 50))
        SCREEN.blit(title_text, title_rect)
        
        # Dibujar campo de entrada
        pygame.draw.rect(SCREEN, COLORS['white'], input_box, 2)
        
        # Dibujar texto ingresado
        font = pygame.font.SysFont('Arial', 24)
        text_surface = font.render(player_name, True, COLORS['white'])
        SCREEN.blit(text_surface, (input_box.x + 10, input_box.y + 10))
        
        # Instrucciones
        inst_font = pygame.font.SysFont('Arial', 18)
        inst_text = inst_font.render("Presiona ENTER para continuar", True, COLORS['white'])
        inst_rect = inst_text.get_rect(center=(SCREENWIDTH//2, name_y + 230))
        SCREEN.blit(inst_text, inst_rect)
        
        pygame.display.update()
        FPSCLOCK.tick(FPS)
    
    return player_name.strip()

def generate_images():
    """Genera todas las imágenes necesarias para el juego"""
    
    # Generar fondos
    # Fondo diurno
    day_bg = pygame.Surface((SCREENWIDTH, SCREENHEIGHT))
    day_bg.fill(COLORS['day_sky'])
    # Añadir nubes
    for _ in range(10):  # Más nubes para pantalla más grande
        x = random.randint(0, SCREENWIDTH)
        y = random.randint(50, SCREENHEIGHT // 2)
        radius = random.randint(20, 40)
        pygame.draw.circle(day_bg, COLORS['white'], (x, y), radius)
        pygame.draw.circle(day_bg, COLORS['white'], (x + radius, y), radius)
        pygame.draw.circle(day_bg, COLORS['white'], (x - radius, y), radius)
    IMAGES['background-day'] = day_bg
    
    # Fondo nocturno
    night_bg = pygame.Surface((SCREENWIDTH, SCREENHEIGHT))
    night_bg.fill(COLORS['night_sky'])
    # Añadir estrellas
    for _ in range(100):  # Más estrellas para pantalla más grande
        x = random.randint(0, SCREENWIDTH)
        y = random.randint(0, SCREENHEIGHT // 2)
        pygame.draw.circle(night_bg, COLORS['white'], (x, y), 1)
    IMAGES['background-night'] = night_bg
    
    # Generar base (suelo)
    base_height = SCREENHEIGHT - BASEY
    base = pygame.Surface((SCREENWIDTH * 2, base_height))
    base.fill(COLORS['ground'])
    # Añadir textura al suelo
    for x in range(0, SCREENWIDTH * 2, 20):
        pygame.draw.line(base, (200, 164, 115), (x, 0), (x, base_height), 2)
    IMAGES['base'] = base
    
    # Generar tuberías (más grandes para pantalla más grande)
    pipe_width = 104  # Duplicado de 52 a 104
    pipe_height = 640  # Duplicado de 320 a 640
    
    # Tubería verde
    pipe_green = pygame.Surface((pipe_width, pipe_height), pygame.SRCALPHA)
    pygame.draw.rect(pipe_green, COLORS['pipe_green'], (0, 0, pipe_width, pipe_height))
    pygame.draw.rect(pipe_green, (0, 100, 0), (0, 0, pipe_width, pipe_height), 3)
    # Añadir borde superior
    pygame.draw.rect(pipe_green, (0, 100, 0), (0, 0, pipe_width, 60))  # Duplicado de 30 a 60
    pygame.draw.rect(pipe_green, (0, 100, 0), (0, 0, pipe_width, 60), 3)
    IMAGES['pipe-green'] = pipe_green
    
    # Tubería roja
    pipe_red = pygame.Surface((pipe_width, pipe_height), pygame.SRCALPHA)
    pygame.draw.rect(pipe_red, COLORS['pipe_red'], (0, 0, pipe_width, pipe_height))
    pygame.draw.rect(pipe_red, (139, 0, 0), (0, 0, pipe_width, pipe_height), 3)
    # Añadir borde superior
    pygame.draw.rect(pipe_red, (139, 0, 0), (0, 0, pipe_width, 60))  # Duplicado de 30 a 60
    pygame.draw.rect(pipe_red, (139, 0, 0), (0, 0, pipe_width, 60), 3)
    IMAGES['pipe-red'] = pipe_red
    
    # Generar cajas (jugadores)
    # Caja roja - más pequeña que las otras
    redbox_size = 40  # Tamaño más pequeño para la caja roja
    redbox_collision_size = 25  # Tamaño de colisión más pequeño
    
    for flap, offset in [('upflap', -6), ('midflap', 0), ('downflap', 6)]:  # Ajustado para tamaño más pequeño
        redbox = pygame.Surface((redbox_size, redbox_size), pygame.SRCALPHA)
        pygame.draw.rect(redbox, COLORS['red_box'], (0, 0, redbox_size, redbox_size))
        pygame.draw.rect(redbox, (139, 0, 0), (0, 0, redbox_size, redbox_size), 2)
        # Añadir ala
        wing_y = redbox_size // 2 + offset
        pygame.draw.ellipse(redbox, (180, 0, 0), (redbox_size-12, wing_y-6, 18, 12))  # Ajustado para tamaño más pequeño
        IMAGES[f'redbox-{flap}'] = redbox
    
    # Caja azul - tamaño normal
    bluebox_size = 68  # Tamaño normal
    
    for flap, offset in [('upflap', -10), ('midflap', 0), ('downflap', 10)]:
        bluebox = pygame.Surface((bluebox_size, bluebox_size), pygame.SRCALPHA)
        pygame.draw.rect(bluebox, COLORS['blue_box'], (0, 0, bluebox_size, bluebox_size))
        pygame.draw.rect(bluebox, (0, 0, 139), (0, 0, bluebox_size, bluebox_size), 2)
        # Añadir ala
        wing_y = bluebox_size // 2 + offset
        pygame.draw.ellipse(bluebox, (0, 0, 180), (bluebox_size-20, wing_y-10, 30, 20))
        IMAGES[f'bluebox-{flap}'] = bluebox
    
    # Caja amarilla - tamaño normal
    yellowbox_size = 68  # Tamaño normal
    
    for flap, offset in [('upflap', -10), ('midflap', 0), ('downflap', 10)]:
        yellowbox = pygame.Surface((yellowbox_size, yellowbox_size), pygame.SRCALPHA)
        pygame.draw.rect(yellowbox, COLORS['yellow_box'], (0, 0, yellowbox_size, yellowbox_size))
        pygame.draw.rect(yellowbox, (184, 134, 0), (0, 0, yellowbox_size, yellowbox_size), 2)
        # Añadir ala
        wing_y = yellowbox_size // 2 + offset
        pygame.draw.ellipse(yellowbox, (218, 165, 32), (yellowbox_size-20, wing_y-10, 30, 20))
        IMAGES[f'yellowbox-{flap}'] = yellowbox
    
    # Generar números para el marcador (más grandes)
    font = pygame.font.SysFont('Arial', 60, bold=True)  # Duplicado de 30 a 60
    for i in range(10):
        num_surface = font.render(str(i), True, COLORS['white'])
        IMAGES[str(i)] = num_surface
    
    # Generar mensaje de bienvenida (más grande)
    message = pygame.Surface((368, 534), pygame.SRCALPHA)  # Duplicado de 184,267 a 368,534
    pygame.draw.rect(message, (0, 0, 0, 128), (0, 0, 368, 534))
    pygame.draw.rect(message, COLORS['white'], (0, 0, 368, 534), 2)
    
    # Título "Flappy Pobre" - Cambiado de "Flappy Box"
    title_font = pygame.font.SysFont('Arial', 60, bold=True)  # Duplicado de 30 a 60
    title_text = title_font.render("Flappy Pobre", True, COLORS['text'])  # Cambiado de "Flappy Box" a "Flappy Pobre"
    title_rect = title_text.get_rect(center=(184, 100))  # Duplicado de 92,50 a 184,100
    message.blit(title_text, title_rect)
    
    # Instrucciones
    inst_font = pygame.font.SysFont('Arial', 30)  # Duplicado de 15 a 30
    inst_text = inst_font.render("Presiona ESPACIO", True, COLORS['text'])
    inst_rect = inst_text.get_rect(center=(184, 300))  # Duplicado de 92,150 a 184,300
    message.blit(inst_text, inst_rect)
    
    inst_text2 = inst_font.render("para empezar", True, COLORS['text'])
    inst_rect2 = inst_text2.get_rect(center=(184, 340))  # Duplicado de 92,170 a 184,340
    message.blit(inst_text2, inst_rect2)
    
    IMAGES['message'] = message
    
    # Generar pantalla de Game Over (más grande)
    gameover = pygame.Surface((376, 120), pygame.SRCALPHA)  # Duplicado de 188,60 a 376,120
    pygame.draw.rect(gameover, (0, 0, 0, 128), (0, 0, 376, 120))
    pygame.draw.rect(gameover, COLORS['white'], (0, 0, 376, 120), 2)
    
    go_font = pygame.font.SysFont('Arial', 80, bold=True)  # Duplicado de 40 a 80
    go_text = go_font.render("Game Over", True, COLORS['text'])
    go_rect = go_text.get_rect(center=(188, 60))  # Duplicado de 94,30 a 188,60
    gameover.blit(go_text, go_rect)
    
    IMAGES['gameover'] = gameover
    
    # Generar botón de tabla de puntuaciones
    button_width, button_height = 150, 50
    button = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
    pygame.draw.rect(button, COLORS['button'], (0, 0, button_width, button_height))
    pygame.draw.rect(button, COLORS['white'], (0, 0, button_width, button_height), 2)
    
    button_font = pygame.font.SysFont('Arial', 30, bold=True)
    button_text = button_font.render("Tabla", True, COLORS['white'])
    button_text_rect = button_text.get_rect(center=(button_width//2, button_height//2))
    button.blit(button_text, button_text_rect)
    
    IMAGES['button'] = button
    
    # Generar botón de borrar puntuaciones - más pequeño
    clear_button_width, clear_button_height = 100, 35  # Reducido de 120,40 a 100,35
    clear_button = pygame.Surface((clear_button_width, clear_button_height), pygame.SRCALPHA)
    pygame.draw.rect(clear_button, COLORS['clear_button'], (0, 0, clear_button_width, clear_button_height))
    pygame.draw.rect(clear_button, COLORS['white'], (0, 0, clear_button_width, clear_button_height), 2)
    
    clear_button_font = pygame.font.SysFont('Arial', 20, bold=True)  # Reducido de 24 a 20
    clear_button_text = clear_button_font.render("Borrar", True, COLORS['white'])
    clear_button_text_rect = clear_button_text.get_rect(center=(clear_button_width//2, clear_button_height//2))
    clear_button.blit(clear_button_text, clear_button_text_rect)
    
    IMAGES['clear_button'] = clear_button
    
    # Generar pantalla de tabla de puntuaciones
    scores_bg = pygame.Surface((400, 500), pygame.SRCALPHA)
    pygame.draw.rect(scores_bg, (0, 0, 0, 200), (0, 0, 400, 500))
    pygame.draw.rect(scores_bg, COLORS['white'], (0, 0, 400, 500), 3)
    
    # Título "Tabla de Puntuaciones" - Tamaño más pequeño
    title_font = pygame.font.SysFont('Arial', 28, bold=True)  # Reducido de 40 a 28
    title_text = title_font.render("Tabla de Puntuaciones", True, COLORS['white'])
    title_rect = title_text.get_rect(center=(200, 40))
    scores_bg.blit(title_text, title_rect)
    
    IMAGES['scores_bg'] = scores_bg

def generate_sounds():
    """Genera sonidos simples para el juego"""
    try:
        # Sonido de aleteo
        SOUNDS['wing'] = pygame.mixer.Sound(buffer=create_sine_wave(440, 100))
        
        # Sonido de punto
        SOUNDS['point'] = pygame.mixer.Sound(buffer=create_sine_wave(880, 150))
        
        # Sonido de golpe
        SOUNDS['hit'] = pygame.mixer.Sound(buffer=create_noise(200))
        
        # Sonido de muerte
        SOUNDS['die'] = pygame.mixer.Sound(buffer=create_noise(500))
    except:
        print("No se pudieron generar los sonidos. El juego continuará sin sonido.")

def create_sine_wave(frequency, duration):
    """Crea una onda sinusoidal para generar sonidos simples"""
    sample_rate = 22050
    samples = int(sample_rate * duration / 1000)
    waves = [int(32767.0 * math.sin(2.0 * math.pi * frequency * i / sample_rate)) for i in range(samples)]
    
    # Convertir a bytes
    sound_data = bytearray()
    for sample in waves:
        sound_data.extend([sample & 0xFF, (sample >> 8) & 0xFF])
    
    return bytes(sound_data)

def create_noise(duration):
    """Crea ruido para sonidos de impacto"""
    sample_rate = 22050
    samples = int(sample_rate * duration / 1000)
    noise = [random.randint(-32767, 32767) for _ in range(samples)]
    
    # Convertir a bytes
    sound_data = bytearray()
    for sample in noise:
        sound_data.extend([sample & 0xFF, (sample >> 8) & 0xFF])
    
    return bytes(sound_data)

def main():
    global SCREEN, FPSCLOCK
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    
    # Configuración de pantalla (ahora opcional pantalla completa)
    if FULLSCREEN:
        SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT), pygame.SCALED | pygame.FULLSCREEN)
    else:
        SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT), pygame.SCALED)
    pygame.display.set_caption('Flappy Pobre')  # Cambiado de 'Flappy Box' a 'Flappy Pobre'
    
    # Generar imágenes y sonidos
    generate_images()
    generate_sounds()
    
    # Pedir nombre del jugador al inicio
    player_name = get_player_name()
    
    while True:
        # Seleccionar fondo aleatorio
        randBg = random.randint(0, len(BACKGROUNDS_LIST) - 1)
        IMAGES['background'] = IMAGES[BACKGROUNDS_LIST[randBg]]
        
        # Seleccionar jugador aleatorio
        randPlayer = random.randint(0, len(PLAYERS_LIST) - 1)
        IMAGES['player'] = (
            IMAGES[PLAYERS_LIST[randPlayer][0]],
            IMAGES[PLAYERS_LIST[randPlayer][1]],
            IMAGES[PLAYERS_LIST[randPlayer][2]],
        )
        
        # Seleccionar tuberías aleatorias
        pipeindex = random.randint(0, len(PIPES_LIST) - 1)
        pipe_key = PIPES_LIST[pipeindex]
        IMAGES['pipe'] = (
            pygame.transform.flip(IMAGES[pipe_key], False, True),
            IMAGES[pipe_key],
        )
        
        # Máscaras de colisión para tuberías
        HITMASKS['pipe'] = (
            getHitmask(IMAGES['pipe'][0]),
            getHitmask(IMAGES['pipe'][1]),
        )
        
        # Máscaras de colisión para jugador (con área de colisión más pequeña)
        HITMASKS['player'] = (
            getReducedHitmask(IMAGES['player'][0]),  # Usar función de máscara reducida
            getReducedHitmask(IMAGES['player'][1]),
            getReducedHitmask(IMAGES['player'][2]),
        )
        
        movementInfo = showWelcomeAnimation(player_name)
        crashInfo = mainGame(movementInfo, player_name)
        showGameOverScreen(crashInfo, player_name)

def showWelcomeAnimation(player_name):
    """Muestra la animación de bienvenida"""
    # Índice del jugador para mostrar en pantalla
    playerIndex = 0
    playerIndexGen = cycle([0, 1, 2, 1])
    # Iterador usado para cambiar playerIndex después de cada 5ª iteración
    loopIter = 0
    
    playerx = int(SCREENWIDTH * 0.2)
    playery = int((SCREENHEIGHT - IMAGES['player'][0].get_height()) / 2)
    
    messagex = int((SCREENWIDTH - IMAGES['message'].get_width()) / 2)
    messagey = int(SCREENHEIGHT * 0.12)
    
    # Posición del botón de tabla
    buttonx = int((SCREENWIDTH - IMAGES['button'].get_width()) / 2)
    buttony = int(SCREENHEIGHT * 0.7)
    
    basex = 0
    # Cantidad máxima que la base puede desplazarse a la izquierda
    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()
    
    # Movimiento del jugador para el movimiento arriba-abajo en la pantalla de bienvenida
    playerShmVals = {'val': 0, 'dir': 1}
    
    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP) or event.type == MOUSEBUTTONDOWN:
                # Verificar si se hizo clic en el botón de tabla
                if event.type == MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    button_rect = pygame.Rect(buttonx, buttony, IMAGES['button'].get_width(), IMAGES['button'].get_height())
                    if button_rect.collidepoint(mouse_pos):
                        showScoresTable()  # Mostrar tabla de puntuaciones
                    else:
                        # Reproducir primer sonido de aleteo y devolver valores para mainGame
                        if 'wing' in SOUNDS:
                            SOUNDS['wing'].play()
                        return {
                            'playery': playery + playerShmVals['val'],
                            'basex': basex,
                            'playerIndexGen': playerIndexGen,
                        }
                else:  # Si es un evento de teclado
                    # Reproducir primer sonido de aleteo y devolver valores para mainGame
                    if 'wing' in SOUNDS:
                        SOUNDS['wing'].play()
                    return {
                        'playery': playery + playerShmVals['val'],
                        'basex': basex,
                        'playerIndexGen': playerIndexGen,
                    }
        
        # Ajustar playery, playerIndex, basex
        if (loopIter + 1) % 5 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 4) % baseShift)
        playerShm(playerShmVals)
        
        # Dibujar sprites
        SCREEN.blit(IMAGES['background'], (0, 0))
        SCREEN.blit(IMAGES['player'][playerIndex], (playerx, playery + playerShmVals['val']))
        SCREEN.blit(IMAGES['message'], (messagex, messagey))
        SCREEN.blit(IMAGES['base'], (basex, BASEY))
        
        # Mostrar botón de tabla
        SCREEN.blit(IMAGES['button'], (buttonx, buttony))
        
        # Mostrar nombre del jugador
        font = pygame.font.SysFont(None, 32)
        name_text = font.render(f"Jugador: {player_name}", True, (255, 255, 255))
        name_rect = name_text.get_rect(center=(SCREENWIDTH/2, 30))
        SCREEN.blit(name_text, name_rect)
        
        # Instrucciones en pantalla (texto más pequeño)
        text = font.render("Presiona ESPACIO o haz clic para jugar", True, (255, 255, 255))
        text_rect = text.get_rect(center=(SCREENWIDTH/2, SCREENHEIGHT - 80))  # Ajustado de 100 a 80
        SCREEN.blit(text, text_rect)
        
        text_quit = font.render("Presiona ESC para salir", True, (255, 255, 255))
        text_quit_rect = text_quit.get_rect(center=(SCREENWIDTH/2, SCREENHEIGHT - 50))  # Ajustado de 50 a 50
        SCREEN.blit(text_quit, text_quit_rect)
        
        pygame.display.update()
        FPSCLOCK.tick(FPS)

def showScoresTable():
    """Muestra la tabla de puntuaciones con su propio bucle de eventos"""
    # Posición de la tabla en la pantalla
    scores_x = (SCREENWIDTH - IMAGES['scores_bg'].get_width()) // 2
    scores_y = (SCREENHEIGHT - IMAGES['scores_bg'].get_height()) // 2
    
    # Posición del botón de borrar - Centrado sobre el texto "haz clic fuera para cerrar"
    clear_button_x = scores_x + 150  # Centrado en la tabla (400/2 - 100/2 = 150)
    clear_button_y = scores_y + 410  # Posición sobre el texto
    
    # Área para cerrar (fuera de la tabla)
    close_area = pygame.Rect(scores_x - 10, scores_y - 10, 
                           IMAGES['scores_bg'].get_width() + 20, 
                           IMAGES['scores_bg'].get_height() + 20)
    
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                return  # Cerrar la tabla con ESC
            
            if event.type == MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Verificar si se hizo clic en el botón de borrar
                clear_button_rect = pygame.Rect(clear_button_x, clear_button_y, 
                                             IMAGES['clear_button'].get_width(), 
                                             IMAGES['clear_button'].get_height())
                if clear_button_rect.collidepoint(mouse_pos):
                    clear_high_scores()  # Borrar puntuaciones
                
                # Verificar si se hizo clic fuera de la tabla para cerrar
                if not close_area.collidepoint(mouse_pos):
                    return  # Cerrar la tabla
        
        # Dibujar la tabla de puntuaciones
        scores_surface = IMAGES['scores_bg'].copy()
        
        # Cargar puntuaciones
        scores = load_high_scores()
        
        # Mostrar las 10 mejores puntuaciones con fuente más pequeña
        font = pygame.font.SysFont('Arial', 14)  # Reducido de 18 a 14
        y_offset = 100
        
        if not scores:
            no_scores_text = font.render("No hay puntuaciones guardadas", True, COLORS['white'])
            no_scores_rect = no_scores_text.get_rect(center=(200, 250))
            scores_surface.blit(no_scores_text, no_scores_rect)
        else:
            # Encabezados de la tabla
            headers = ["Pos", "Nombre", "Tuberías"]
            header_x_positions = [80, 150, 280]
            
            for i, header in enumerate(headers):
                header_text = font.render(header, True, (255, 255, 0))  # Amarillo para encabezados
                header_rect = header_text.get_rect(center=(header_x_positions[i], y_offset))
                scores_surface.blit(header_text, header_rect)
            
            y_offset += 25  # Espacio después de los encabezados
            
            # Mostrar las puntuaciones
            for i, score_data in enumerate(scores[:10]):  # Mostrar solo las 10 mejores
                # Posición
                pos_text = font.render(f"{i+1}", True, COLORS['white'])
                pos_rect = pos_text.get_rect(center=(header_x_positions[0], y_offset))
                scores_surface.blit(pos_text, pos_rect)
                
                # Nombre (truncado si es muy largo)
                name = score_data['name']
                if len(name) > 12:
                    name = name[:12] + "..."
                name_text = font.render(name, True, COLORS['white'])
                name_rect = name_text.get_rect(center=(header_x_positions[1], y_offset))
                scores_surface.blit(name_text, name_rect)
                
                # Puntuación
                score_text = font.render(str(score_data['score']), True, COLORS['white'])
                score_rect = score_text.get_rect(center=(header_x_positions[2], y_offset))
                scores_surface.blit(score_text, score_rect)
                
                y_offset += 25  # Reducido de 30 a 25 para acomodar más puntuaciones
        
        # Mostrar puntuación actual si existe
        current_score, current_name = load_current_score()
        if current_score > 0:
            current_text = font.render(f"Progreso actual de {current_name}: {current_score} tuberías", True, (255, 255, 0))  # Amarillo para destacar
            current_rect = current_text.get_rect(center=(200, y_offset + 20))
            scores_surface.blit(current_text, current_rect)
        
        # Instrucción para cerrar
        close_font = pygame.font.SysFont('Arial', 14)  # Reducido de 18 a 14
        close_text = close_font.render("Haz clic fuera para cerrar", True, COLORS['white'])
        close_rect = close_text.get_rect(center=(200, 460))
        scores_surface.blit(close_text, close_rect)
        
        # Dibujar la tabla en la pantalla
        SCREEN.blit(IMAGES['background'], (0, 0))  # Redibujar fondo
        SCREEN.blit(scores_surface, (scores_x, scores_y))
        
        # Dibujar el botón de borrar en la nueva posición centrada
        SCREEN.blit(IMAGES['clear_button'], (clear_button_x, clear_button_y))
        
        pygame.display.update()
        FPSCLOCK.tick(FPS)

def mainGame(movementInfo, player_name):
    # Cargar puntuación actual si existe
    score, _ = load_current_score()
    playerIndex = loopIter = 0
    playerIndexGen = movementInfo['playerIndexGen']
    playerx, playery = int(SCREENWIDTH * 0.2), movementInfo['playery']
    
    basex = movementInfo['basex']
    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()
    
    # Obtener 2 tuberías nuevas para añadir a las listas upperPipes y lowerPipes
    newPipe1 = getRandomPipe()
    newPipe2 = getRandomPipe()
    
    # Lista de tuberías superiores
    upperPipes = [
        {'x': SCREENWIDTH + 200, 'y': newPipe1[0]['y']},
        {'x': SCREENWIDTH + 200 + (SCREENWIDTH / 2), 'y': newPipe2[0]['y']},
    ]
    
    # Lista de tuberías inferiores
    lowerPipes = [
        {'x': SCREENWIDTH + 200, 'y': newPipe1[1]['y']},
        {'x': SCREENWIDTH + 200 + (SCREENWIDTH / 2), 'y': newPipe2[1]['y']},
    ]
    
    pipeVelX = -4
    
    # Velocidad del jugador, velocidad máxima, aceleración descendente, aceleración al aletear
    playerVelY = -9  # Velocidad del jugador a lo largo de Y, igual que playerFlapped por defecto
    playerMaxVelY = 10  # Velocidad máxima a lo largo de Y, velocidad máxima de descenso
    playerMinVelY = -8  # Velocidad mínima a lo largo de Y, velocidad máxima de ascenso
    playerAccY = 1  # Aceleración descendente del jugador
    playerRot = 45  # Rotación del jugador
    playerVelRot = 3  # Velocidad angular
    playerRotThr = 20  # Umbral de rotación
    playerFlapAcc = -9  # Velocidad del jugador al aletear
    playerFlapped = False  # Verdadero cuando el jugador aletea
    
    # Contador para guardar la puntuación periódicamente
    save_counter = 0
    
    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                # Guardar puntuación actual antes de salir
                save_current_score(score, player_name)
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP) or event.type == MOUSEBUTTONDOWN:
                if playery > -2 * IMAGES['player'][0].get_height():
                    playerVelY = playerFlapAcc
                    playerFlapped = True
                    if 'wing' in SOUNDS:
                        SOUNDS['wing'].play()
        
        # Comprobar colisión aquí
        crashTest = checkCrash({'x': playerx, 'y': playery, 'index': playerIndex}, upperPipes, lowerPipes)
        if crashTest[0]:
            # Limpiar archivo de puntuación actual al terminar el juego
            save_current_score(0, player_name)
            return {
                'y': playery, 
                'groundCrash': crashTest[1], 
                'basex': basex, 
                'upperPipes': upperPipes, 
                'lowerPipes': lowerPipes, 
                'score': score, 
                'playerVelY': playerVelY, 
                'playerRot': playerRot
            }
        
        # Comprobar puntuación
        playerMidPos = playerx + IMAGES['player'][0].get_width() / 2
        for pipe in upperPipes:
            pipeMidPos = pipe['x'] + IMAGES['pipe'][0].get_width() / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                score += 1
                # Guardar puntuación actual cada vez que se gana un punto
                save_current_score(score, player_name)
                if 'point' in SOUNDS:
                    SOUNDS['point'].play()
        
        # Guardar puntuación periódicamente (cada 60 frames = 2 segundos)
        save_counter += 1
        if save_counter >= 60:
            save_current_score(score, player_name)
            save_counter = 0
        
        # Cambio de playerIndex y basex
        if (loopIter + 1) % 3 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 100) % baseShift)
        
        # Rotar el jugador
        if playerRot > -90:
            playerRot -= playerVelRot
        
        # Movimiento del jugador
        if playerVelY < playerMaxVelY and not playerFlapped:
            playerVelY += playerAccY
        if playerFlapped:
            playerFlapped = False
            # Más rotación para cubrir el umbral (calculado en rotación visible)
            playerRot = 45
        
        playerHeight = IMAGES['player'][playerIndex].get_height()
        playery += min(playerVelY, BASEY - playery - playerHeight)
        
        # Mover tuberías a la izquierda
        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            uPipe['x'] += pipeVelX
            lPipe['x'] += pipeVelX
        
        # Añadir nueva tubería cuando la primera esté a punto de tocar el lado izquierdo de la pantalla
        if len(upperPipes) > 0 and 0 < upperPipes[0]['x'] < 5:
            newPipe = getRandomPipe()
            upperPipes.append(newPipe[0])
            lowerPipes.append(newPipe[1])
        
        # Eliminar la primera tubería si está fuera de la pantalla
        if len(upperPipes) > 0 and upperPipes[0]['x'] < -IMAGES['pipe'][0].get_width():
            upperPipes.pop(0)
            lowerPipes.pop(0)
        
        # Dibujar sprites
        SCREEN.blit(IMAGES['background'], (0, 0))
        
        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))
        
        SCREEN.blit(IMAGES['base'], (basex, BASEY))
        # Mostrar puntuación para que el jugador se superponga a la puntuación
        showScore(score)
        
        # Mostrar nombre del jugador
        font = pygame.font.SysFont(None, 24)
        name_text = font.render(f"Jugador: {player_name}", True, (255, 255, 255))
        name_rect = name_text.get_rect(center=(SCREENWIDTH/2, 30))
        SCREEN.blit(name_text, name_rect)
        
        # La rotación del jugador tiene un umbral
        visibleRot = playerRotThr
        if playerRot <= playerRotThr:
            visibleRot = playerRot
        
        playerSurface = pygame.transform.rotate(IMAGES['player'][playerIndex], visibleRot)
        SCREEN.blit(playerSurface, (playerx, playery))
        
        pygame.display.update()
        FPSCLOCK.tick(FPS)

def showGameOverScreen(crashInfo, player_name):
    """Hace que el jugador caiga y muestra la imagen de game over"""
    score = crashInfo['score']
    playerx = SCREENWIDTH * 0.2
    playery = crashInfo['y']
    playerHeight = IMAGES['player'][0].get_height()
    playerVelY = crashInfo['playerVelY']
    playerAccY = 2
    playerRot = crashInfo['playerRot']
    playerVelRot = 7
    
    basex = crashInfo['basex']
    
    upperPipes, lowerPipes = crashInfo['upperPipes'], crashInfo['lowerPipes']
    
    # Actualizar tabla de puntuaciones con la puntuación actual
    update_high_scores(score, player_name)
    
    # Reproducir sonidos de golpe y muerte
    if 'hit' in SOUNDS:
        SOUNDS['hit'].play()
    if not crashInfo['groundCrash'] and 'die' in SOUNDS:
        SOUNDS['die'].play()
    
    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP) or event.type == MOUSEBUTTONDOWN:
                if playery + playerHeight >= BASEY - 1:
                    return
        
        # Desplazamiento y del jugador
        if playery + playerHeight < BASEY - 1:
            playery += min(playerVelY, BASEY - playery - playerHeight)
        
        # Cambio de velocidad del jugador
        if playerVelY < 15:
            playerVelY += playerAccY
        
        # Rotar solo cuando es una colisión con tubería
        if not crashInfo['groundCrash']:
            if playerRot > -90:
                playerRot -= playerVelRot
        
        # Dibujar sprites
        SCREEN.blit(IMAGES['background'], (0, 0))
        
        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))
        
        SCREEN.blit(IMAGES['base'], (basex, BASEY))
        showScore(score)
        
        playerSurface = pygame.transform.rotate(IMAGES['player'][1], playerRot)
        SCREEN.blit(playerSurface, (playerx, playery))
        SCREEN.blit(IMAGES['gameover'], (100, 360))  # Ajustado para pantalla más grande
        
        # Mostrar mensaje de puntuación
        font = pygame.font.SysFont(None, 36)
        score_text = font.render(f"Tuberías superadas: {score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(SCREENWIDTH/2, 300))
        SCREEN.blit(score_text, score_rect)
        
        # Instrucciones en pantalla (texto más pequeño)
        font = pygame.font.SysFont(None, 32)  # Reducido de 48 a 32
        text = font.render("Presiona ESPACIO o haz clic para jugar de nuevo", True, (255, 255, 255))
        text_rect = text.get_rect(center=(SCREENWIDTH/2, SCREENHEIGHT - 80))  # Ajustado de 100 a 80
        SCREEN.blit(text, text_rect)
        
        text_quit = font.render("Presiona ESC para salir", True, (255, 255, 255))
        text_quit_rect = text_quit.get_rect(center=(SCREENWIDTH/2, SCREENHEIGHT - 50))  # Ajustado de 50 a 50
        SCREEN.blit(text_quit, text_quit_rect)
        
        FPSCLOCK.tick(FPS)
        pygame.display.update()

def playerShm(playerShm):
    """Oscila el valor de playerShm['val'] entre 8 y -8"""
    if abs(playerShm['val']) == 8:
        playerShm['dir'] *= -1
    
    if playerShm['dir'] == 1:
        playerShm['val'] += 1
    else:
        playerShm['val'] -= 1

def getRandomPipe():
    """Devuelve una tubería generada aleatoriamente"""
    # y del espacio entre tubería superior e inferior
    gapY = random.randrange(0, int(BASEY * 0.6 - PIPEGAPSIZE))
    gapY += int(BASEY * 0.2)
    pipeHeight = IMAGES['pipe'][0].get_height()
    pipeX = SCREENWIDTH + 10
    
    return [
        {'x': pipeX, 'y': gapY - pipeHeight},  # tubería superior
        {'x': pipeX, 'y': gapY + PIPEGAPSIZE},  # tubería inferior
    ]

def showScore(score):
    """Muestra la puntuación en el centro de la pantalla"""
    scoreDigits = [int(x) for x in list(str(score))]
    totalWidth = 0  # ancho total de todos los números a imprimir
    
    for digit in scoreDigits:
        totalWidth += IMAGES[str(digit)].get_width()
    
    Xoffset = (SCREENWIDTH - totalWidth) / 2
    
    for digit in scoreDigits:
        SCREEN.blit(IMAGES[str(digit)], (Xoffset, SCREENHEIGHT * 0.1))
        Xoffset += IMAGES[str(digit)].get_width()

def checkCrash(player, upperPipes, lowerPipes):
    """Devuelve True si el jugador colisiona con la base o las tuberías."""
    pi = player['index']
    player['w'] = IMAGES['player'][0].get_width()
    player['h'] = IMAGES['player'][0].get_height()
    
    # Si el jugador choca contra el suelo
    if player['y'] + player['h'] >= BASEY - 1:
        return [True, True]
    else:
        # Determinar el tamaño de colisión según el tipo de jugador
        if 'redbox' in PLAYERS_LIST[pi][0]:  # Si es el bloque rojo
            collision_size = 25  # Área de colisión más pequeña para el bloque rojo
        else:
            collision_size = 40  # Área de colisión normal para otros bloques
        
        # Crear un rectángulo de colisión más pequeño que el visual
        collision_offset = (player['w'] - collision_size) / 2
        playerRect = pygame.Rect(
            player['x'] + collision_offset, 
            player['y'] + collision_offset, 
            collision_size, collision_size
        )
        pipeW = IMAGES['pipe'][0].get_width()
        pipeH = IMAGES['pipe'][0].get_height()
        
        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            # Rectángulos de tubería superior e inferior
            uPipeRect = pygame.Rect(uPipe['x'], uPipe['y'], pipeW, pipeH)
            lPipeRect = pygame.Rect(lPipe['x'], lPipe['y'], pipeW, pipeH)
            
            # Máscaras de colisión del jugador y tuberías superior/inferior
            pHitMask = HITMASKS['player'][pi]
            uHitmask = HITMASKS['pipe'][0]
            lHitmask = HITMASKS['pipe'][1]
            
            # Si el jugador colisiona con tubería superior o inferior
            uCollide = pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)
            lCollide = pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)
            
            if uCollide or lCollide:
                return [True, False]
    
    return [False, False]

def pixelCollision(rect1, rect2, hitmask1, hitmask2):
    """Comprueba si dos objetos colisionan y no solo sus rectángulos"""
    rect = rect1.clip(rect2)
    
    if rect.width == 0 or rect.height == 0:
        return False
    
    x1, y1 = rect.x - rect1.x, rect.y - rect1.y
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y
    
    for x in xrange(rect.width):
        for y in xrange(rect.height):
            if hitmask1[x1 + x][y1 + y] and hitmask2[x2 + x][y2 + y]:
                return True
    return False

def getHitmask(image):
    """Devuelve una máscara de colisión usando el alfa de una imagen."""
    mask = []
    for x in xrange(image.get_width()):
        mask.append([])
        for y in xrange(image.get_height()):
            mask[x].append(bool(image.get_at((x, y))[3]))
    return mask

def getReducedHitmask(image):
    """Devuelve una máscara de colisión reducida para el jugador."""
    # Obtener dimensiones de la imagen
    width, height = image.get_width(), image.get_height()
    
    # Determinar el tamaño de colisión según el tipo de imagen
    if 'redbox' in str(image):  # Si es el bloque rojo
        collision_size = 25  # Tamaño de colisión más pequeño para el bloque rojo
    else:
        collision_size = 40  # Tamaño de colisión normal para otros bloques
    
    # Crear una máscara más pequeña (centrada)
    offset_x = (width - collision_size) // 2
    offset_y = (height - collision_size) // 2
    
    mask = []
    for x in xrange(width):
        mask.append([])
        for y in xrange(height):
            # Solo considerar píxeles dentro del área de colisión reducida
            if offset_x <= x < offset_x + collision_size and offset_y <= y < offset_y + collision_size:
                mask[x].append(bool(image.get_at((x, y))[3]))
            else:
                mask[x].append(False)  # Fuera del área de colisión
    
    return mask

if __name__ == '__main__':
    main()