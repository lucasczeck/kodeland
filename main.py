import math
import random

from pgzero import music
from pgzero.actor import Actor
from pgzero.loaders import sounds
from pygame import Rect

# Constantes do jogo
GRID_SIZE = 32
WIDTH = 800
HEIGHT = 600
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE

# Estados e direções do jogo (para não usar enum)
GAME_STATE_MENU = 1
GAME_STATE_PLAYING = 2
GAME_STATE_GAME_OVER = 3
DIRECTION_UP = (0, -1)
DIRECTION_DOWN = (0, 1)
DIRECTION_LEFT = (-1, 0)
DIRECTION_RIGHT = (1, 0)

# Contador global (para não usar time)
global_timer = 0


class SoundManager:
    """Gerenciador de sons usando o sistema de áudio do PgZero"""

    def __init__(self):
        self.music_enabled = True
        self.sounds_enabled = True
        self.background_music_timer = 0
        self.background_music_limit = 30
        self.current_track = 0

    def play_background_music(self):
        """Toca a música de fundo do oceano"""
        if not self.music_enabled:
            # Para a música se estiver desabilitada
            music.stop()
            return

        # Só toca se não estiver tocando
        if not music.is_playing('ocean_ambient'):
            music.play('ocean_ambient')
            music.set_volume(0.3)

    def play_swim_sound(self):
        if not self.sounds_enabled:
            return
        sounds.swim.play()

    def play_bubble_collect(self):
        if not self.sounds_enabled:
            return
        sounds.bubble_collect.play()

    def play_shark_bite(self):
        if not self.sounds_enabled:
            return
        sounds.shark_bite.play()

    def play_menu_select(self):
        if not self.sounds_enabled:
            return
        sounds.menu_beep.play()

    def play_game_over(self):
        if not self.sounds_enabled:
            return
        sounds.game_over.play()

    def play_ambient_bubbles(self):
        if not self.sounds_enabled:
            return
        sounds.ambient_bubble.play()


class AnimatedSprite:
    """Classe base para sprites animados com dois quadros de animação"""

    def __init__(self, x, y, image_base_name, animation_speed=0.5):
        self.grid_x = x
        self.grid_y = y
        self.pixel_x = x * GRID_SIZE
        self.pixel_y = y * GRID_SIZE
        self.target_x = self.pixel_x
        self.target_y = self.pixel_y
        self.moving = False
        self.move_speed = 4

        # Animação de dois quadros
        self.image_base_name = image_base_name
        self.animation_speed = animation_speed
        self.animation_timer = 0
        self.current_frame = 0  # 0 ou 1

        # Cria atores para ambos os quadros
        self.actors = []
        self.actors.append(Actor(f"{image_base_name}_1"))
        self.actors.append(Actor(f"{image_base_name}_2"))

        self.update_actor_position()

    def update(self, dt):
        # Atualiza a animação do sprite (alterna entre dois quadros)
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = 1 - self.current_frame  # Alterna entre 0 e 1

        # Atualiza o movimento da posição
        if self.moving:
            dx = self.target_x - self.pixel_x
            dy = self.target_y - self.pixel_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < self.move_speed:
                self.pixel_x = self.target_x
                self.pixel_y = self.target_y
                self.moving = False
            else:
                self.pixel_x += (dx / distance) * self.move_speed
                self.pixel_y += (dy / distance) * self.move_speed

        self.update_actor_position()

    def update_actor_position(self):
        """Atualiza a posição do ator"""
        for actor in self.actors:
            if actor:
                actor.pos = (self.pixel_x + GRID_SIZE // 2, self.pixel_y + GRID_SIZE // 2)

    def move_to(self, grid_x, grid_y):
        if not self.moving:
            self.grid_x = grid_x
            self.grid_y = grid_y
            self.target_x = grid_x * GRID_SIZE
            self.target_y = grid_y * GRID_SIZE
            self.moving = True

    def draw(self, screen):
        """Desenha o quadro atual da animação"""
        current_actor = self.actors[self.current_frame]
        if current_actor:
            current_actor.draw()


class Hero(AnimatedSprite):
    def __init__(self, x, y):
        # Não chama super().__init__ porque precisa de tratamento personalizado para os sprites
        self.grid_x = x
        self.grid_y = y
        self.pixel_x = x * GRID_SIZE
        self.pixel_y = y * GRID_SIZE
        self.health = 100
        self.alive = True

        # Sistema de movimento fluido
        self.current_direction = DIRECTION_RIGHT
        self.next_direction = None
        self.move_speed = 80

        # Posição real (float) para movimento suave
        self.real_x = float(x * GRID_SIZE)
        self.real_y = float(y * GRID_SIZE)

        # Animação de natação
        self.swim_timer = 0
        self.swim_amplitude = 2
        self.swim_frequency = 12

        # Temporizador para sons de bolhas
        self.bubble_sound_timer = 0
        self.bubble_sound_interval = 6.5

        # Animação de sprite direcional
        self.animation_speed = 0.4
        self.animation_timer = 0
        self.current_frame = 0  # 0 ou 1

        # Cria atores para cada direção (2 quadros cada)
        self.direction_actors = {}
        directions = ['right', 'left', 'up', 'down']

        for direction in directions:
            try:
                actor1 = Actor(f"nemo_{direction}_1")
                actor2 = Actor(f"nemo_{direction}_2")
                self.direction_actors[direction] = [actor1, actor2]
            except:
                self.direction_actors[direction] = [None, None]

    def update(self, dt, dungeon, sound_manager):
        if not self.alive:
            return

        self.bubble_sound_timer += dt
        if self.bubble_sound_timer >= self.bubble_sound_interval:
            self.bubble_sound_timer = 0
            sound_manager.play_ambient_bubbles()

        # Atualiza a animação do sprite
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = 1 - self.current_frame  # Alterna entre 0 e 1

        # Aplica mudança de direção se pendente
        if self.next_direction:
            self.current_direction = self.next_direction
            self.next_direction = None

            # Toca som de mudança de direção ocasionalmente
            sound_manager.play_swim_sound()

        # Movimento fluido contínuo
        dx = self.current_direction[0] * self.move_speed * dt
        dy = self.current_direction[1] * self.move_speed * dt

        # Nova posição
        new_real_x = self.real_x + dx
        new_real_y = self.real_y + dy

        # Converte para grade para verificação de colisão
        new_grid_x = int(new_real_x // GRID_SIZE)
        new_grid_y = int(new_real_y // GRID_SIZE)

        # Verifica colisão
        if dungeon.is_walkable(new_grid_x, new_grid_y):
            self.real_x = new_real_x
            self.real_y = new_real_y
            self.grid_x = new_grid_x
            self.grid_y = new_grid_y

        # Animação de natação
        self.swim_timer += dt

        # Calcula deslocamento perpendicular à direção do movimento
        swim_offset_x = 0
        swim_offset_y = 0

        if self.current_direction in [DIRECTION_LEFT, DIRECTION_RIGHT]:
            swim_offset_y = math.sin(self.swim_timer * self.swim_frequency) * self.swim_amplitude
        else:
            swim_offset_x = math.sin(self.swim_timer * self.swim_frequency) * self.swim_amplitude

        # Posição final para desenho
        self.pixel_x = self.real_x + swim_offset_x
        self.pixel_y = self.real_y + swim_offset_y

        # Atualiza posições dos atores
        self.update_actor_positions()

    def update_actor_positions(self):
        """Atualiza todas as posições dos atores"""
        for direction_actors in self.direction_actors.values():
            for actor in direction_actors:
                if actor:
                    actor.pos = (self.pixel_x + GRID_SIZE // 2, self.pixel_y + GRID_SIZE // 2)

    def change_direction(self, new_direction):
        """Muda a direção do movimento contínuo"""
        self.next_direction = new_direction

    def draw(self, screen):
        """Desenha o Nemo com a direção e quadro de animação atuais"""
        direction_map = {
            DIRECTION_RIGHT: 'right',
            DIRECTION_LEFT: 'left',
            DIRECTION_UP: 'up',
            DIRECTION_DOWN: 'down'
        }
        direction_name = direction_map.get(self.current_direction, 'right')

        current_actors = self.direction_actors.get(direction_name, [None, None])
        current_actor = current_actors[self.current_frame]

        if current_actor:
            current_actor.draw()


class Enemy(AnimatedSprite):
    """Tubarões com animação de sprite de dois quadros"""

    def __init__(self, x, y, enemy_type='reef_shark'):
        super().__init__(x, y, enemy_type, 0.6)  # Animação mais lenta para tubarões
        self.enemy_type = enemy_type

        # Define o tamanho com base no tipo de tubarão
        if enemy_type == 'reef_shark':
            self.size_multiplier = 1.0
            self.length = 28
        elif enemy_type == 'bull_shark':
            self.size_multiplier = 1.3
            self.length = 36
        elif enemy_type == 'great_white':
            self.size_multiplier = 1.6
            self.length = 44
        else:  # hammer_shark
            self.size_multiplier = 1.4
            self.length = 40

        self.move_timer = 0
        self.move_interval = random.uniform(1.0, 3.0)
        self.patrol_center_x = x
        self.patrol_center_y = y

        # Sistema de cansaço
        self.damage_dealt = 0
        self.tired = False
        self.tired_timer = 0
        self.tired_duration = 5.0

        # Movimento fluido
        self.real_x = float(x * GRID_SIZE)
        self.real_y = float(y * GRID_SIZE)
        self.current_direction = random.choice([DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_RIGHT])

        # Animação de natação
        self.swim_timer = 0
        self.swim_amplitude = 1
        self.swim_frequency = 4

    def update(self, dt, dungeon, hero_pos):
        # Atualiza a animação do sprite
        super().update(dt)

        # Sistema de cansaço
        if self.tired:
            self.tired_timer += dt
            if self.tired_timer >= self.tired_duration:
                self.tired = False
                self.tired_timer = 0
                self.damage_dealt = 0
            return

        # Calcula a distância até o herói
        hero_distance = math.sqrt(
            (self.grid_x - hero_pos[0]) ** 2 +
            (self.grid_y - hero_pos[1]) ** 2
        )

        # Temporizador de movimento da IA
        self.move_timer += dt

        # Diferentes velocidades de movimento com base no tipo de tubarão
        if self.enemy_type == 'bull_shark':
            move_frequency = 0.8
            enemy_speed = 35
        elif self.enemy_type == 'great_white':
            move_frequency = 1.0
            enemy_speed = 30
        elif self.enemy_type == 'reef_shark':
            move_frequency = 0.4
            enemy_speed = 40
        else:  # Chefão
            move_frequency = 1.5
            enemy_speed = 25

        # Só decide nova direção em intervalos
        if self.move_timer >= move_frequency:
            self.move_timer = 0

            new_direction = None

            # Comportamento de caçador para tubarões próximos do herói
            if hero_distance <= 8 and not self.tired:
                dx = hero_pos[0] - self.grid_x
                dy = hero_pos[1] - self.grid_y

                if abs(dx) > abs(dy):
                    new_direction = DIRECTION_RIGHT if dx > 0 else DIRECTION_LEFT
                else:
                    new_direction = DIRECTION_DOWN if dy > 0 else DIRECTION_UP
            else:
                # Comportamento normal de patrulha
                directions = [DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_RIGHT]
                random.shuffle(directions)

                for direction in directions:
                    new_x = self.grid_x + direction[0]
                    new_y = self.grid_y + direction[1]

                    distance_from_center = math.sqrt(
                        (new_x - self.patrol_center_x) ** 2 +
                        (new_y - self.patrol_center_y) ** 2
                    )

                    if (distance_from_center <= 4 and
                            dungeon.is_walkable(new_x, new_y)):
                        new_direction = direction
                        break

            if new_direction:
                self.current_direction = new_direction

        # Movimento contínuo
        if hasattr(self, 'current_direction'):
            dx = self.current_direction[0] * enemy_speed * dt
            dy = self.current_direction[1] * enemy_speed * dt

            new_real_x = self.real_x + dx
            new_real_y = self.real_y + dy

            new_grid_x = int(new_real_x // GRID_SIZE)
            new_grid_y = int(new_real_y // GRID_SIZE)

            if dungeon.is_walkable(new_grid_x, new_grid_y):
                self.real_x = new_real_x
                self.real_y = new_real_y
                self.grid_x = new_grid_x
                self.grid_y = new_grid_y

                # Animação de natação
                self.swim_timer += dt
                swim_offset_x = 0
                swim_offset_y = 0

                if self.current_direction in [DIRECTION_LEFT, DIRECTION_RIGHT]:
                    swim_offset_y = math.sin(self.swim_timer * self.swim_frequency) * self.swim_amplitude
                else:
                    swim_offset_x = math.sin(self.swim_timer * self.swim_frequency) * self.swim_amplitude

                self.pixel_x = self.real_x + swim_offset_x
                self.pixel_y = self.real_y + swim_offset_y
            else:
                directions = [DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_RIGHT]
                self.current_direction = random.choice(directions)

        # Atualiza posições dos atores
        self.update_actor_position()

        # Rotaciona o tubarão com base na direção
        for actor in self.actors:
            if actor:
                # Mapeamento de direções para ângulos
                direction_angles = {
                    DIRECTION_RIGHT: 0,
                    DIRECTION_DOWN: 90,
                    DIRECTION_LEFT: 180,
                    DIRECTION_UP: 270
                }
                actor.angle = direction_angles.get(self.current_direction, 0)

    def deal_damage(self):
        """Chamado quando o tubarão causa dano"""
        self.damage_dealt += 1
        if self.damage_dealt >= 1:
            self.tired = True
            self.tired_timer = 0
        return True


class HealthPowerUp(AnimatedSprite):
    """Bolhas de ar com animação de sprite de dois quadros"""

    def __init__(self, x, y):
        super().__init__(x, y, 'bubble', 0.3)  # Animação rápida para bolhas
        self.float_timer = 0
        self.float_amplitude = 5
        self.base_y = y * GRID_SIZE

    def update(self, dt):
        # Atualiza a animação do sprite
        super().update(dt)

        self.float_timer += dt
        self.pixel_y = self.base_y + math.sin(self.float_timer * 2) * self.float_amplitude

        # Atualiza posições dos atores com animação flutuante
        for actor in self.actors:
            if actor:
                actor.pos = (self.pixel_x + GRID_SIZE // 2, self.pixel_y + GRID_SIZE // 2)
                # Adiciona animação de rotação flutuante
                actor.angle = math.sin(self.float_timer * 3) * 10


class Dungeon:
    """Fundo do oceano com algas marinhas animadas usando sprites de dois quadros"""

    def __init__(self):
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT
        self.seaweed = set()
        self.seaweed_types = {}
        self.seaweed_sprites = {}  # Armazena sprites animados para cada alga marinha
        self.generate_ocean_floor()

    def generate_ocean_floor(self):
        # Cria algas marinhas na borda
        for x in range(self.width):
            self.seaweed.add((x, 0))
            self.seaweed.add((x, self.height - 1))

            # Atribui tipos de algas marinhas e cria sprites animados
            for y_pos in [0, self.height - 1]:
                seaweed_type = random.choice(['kelp', 'coral', 'anemone'])
                self.seaweed_types[(x, y_pos)] = seaweed_type
                self.seaweed_sprites[(x, y_pos)] = AnimatedSprite(x, y_pos, seaweed_type, 0.8)

        for y in range(self.height):
            self.seaweed.add((0, y))
            self.seaweed.add((self.width - 1, y))

            # Atribui tipos de algas marinhas para bordas laterais
            for x_pos in [0, self.width - 1]:
                seaweed_type = random.choice(['kelp', 'coral', 'anemone'])
                self.seaweed_types[(x_pos, y)] = seaweed_type
                self.seaweed_sprites[(x_pos, y)] = AnimatedSprite(x_pos, y, seaweed_type, 0.8)

        # Adiciona manchas aleatórias de algas marinhas
        for _ in range(60):
            x = random.randint(2, self.width - 3)
            y = random.randint(2, self.height - 3)
            self.seaweed.add((x, y))

            seaweed_type = random.choice(['kelp', 'coral', 'anemone'])
            self.seaweed_types[(x, y)] = seaweed_type
            self.seaweed_sprites[(x, y)] = AnimatedSprite(x, y, seaweed_type, 0.8)

    def is_walkable(self, x, y):
        return (x, y) not in self.seaweed and 0 <= x < self.width and 0 <= y < self.height

    def update(self, dt):
        # Atualiza todas as animações de sprites de algas marinhas
        for sprite in self.seaweed_sprites.values():
            sprite.update(dt)

    def draw(self, screen):
        global global_timer

        # Fundo do oceano
        try:
            screen.blit('ocean_bg', (0, 0))
        except:
            screen.fill('midnightblue')

        # Desenha algas marinhas com animações de sprites
        for pos, sprite in self.seaweed_sprites.items():
            sprite.draw(screen)

        # Partículas flutuantes (usando contador global em vez de time.time())
        for i in range(15):
            particle_x = (global_timer * 8 + i * 50) % WIDTH
            particle_y = (global_timer * 3 + i * 40) % HEIGHT
            particle_size = 1 + (i % 2)

            screen.draw.filled_circle((particle_x, particle_y), particle_size, 'lightcyan')


class Game:
    """Classe principal do jogo"""

    def __init__(self):
        self.powerup_spawn_interval = None
        self.powerup_spawn_timer = None
        self.enemy_spawn_interval = None
        self.enemy_spawn_timer = None
        self.state = GAME_STATE_MENU
        self.dungeon = Dungeon()
        self.hero = None
        self.enemies = []
        self.health_powerups = []
        self.sound_manager = SoundManager()
        self.game_over_timer = 0
        self.reset_game()

    def reset_game(self):
        # Encontra uma posição navegável para o Nemo
        while True:
            x = random.randint(1, GRID_WIDTH - 2)
            y = random.randint(1, GRID_HEIGHT - 2)
            if self.dungeon.is_walkable(x, y):
                self.hero = Hero(x, y)
                break

        # Cria tubarões para o ínicio
        self.enemies = []
        shark_types = ['reef_shark'] * 10 + ['bull_shark'] * 7 + ['great_white'] * 3

        for shark_type in shark_types:
            attempts = 0
            while attempts < 50:
                x = random.randint(2, GRID_WIDTH - 3)
                y = random.randint(2, GRID_HEIGHT - 3)
                if (self.dungeon.is_walkable(x, y) and
                        abs(x - self.hero.grid_x) + abs(y - self.hero.grid_y) > 4):
                    self.enemies.append(Enemy(x, y, shark_type))
                    break
                attempts += 1

        # Reinicia power-ups
        self.health_powerups = []

        # Adiciona temporizadores de spawn
        self.enemy_spawn_timer = 0
        self.enemy_spawn_interval = 5.0

        self.powerup_spawn_timer = 0
        self.powerup_spawn_interval = 8.0

    def update_game(self, dt):
        global global_timer
        global_timer += dt  # Atualiza contador global

        # Toca música de fundo
        self.sound_manager.play_background_music()

        self.dungeon.update(dt)

        if self.state == GAME_STATE_PLAYING:
            if self.hero.alive:
                self.hero.update(dt, self.dungeon, self.sound_manager)

                # Spawn contínuo de tubarões
                self.enemy_spawn_timer += dt
                if self.enemy_spawn_timer >= self.enemy_spawn_interval and len(self.enemies) < 100:
                    self.enemy_spawn_timer = 0
                    self.spawn_new_shark()

                # Spawn de bolhas
                self.powerup_spawn_timer += dt
                if self.powerup_spawn_timer >= self.powerup_spawn_interval:
                    self.powerup_spawn_timer = 0
                    self.spawn_air_bubble()

            hero_pos = (self.hero.grid_x, self.hero.grid_y)

            # Atualiza todos os tubarões
            for enemy in self.enemies:
                enemy.update(dt, self.dungeon, hero_pos)

            # Atualiza bolhas
            for powerup in self.health_powerups:
                powerup.update(dt)

            # Verifica colisões com tubarões
            for enemy in self.enemies:
                if (enemy.grid_x == self.hero.grid_x and
                        enemy.grid_y == self.hero.grid_y):

                    if enemy.tired:
                        continue

                    # Toca som de ataque
                    self.sound_manager.play_shark_bite()

                    # Dano baseado no tipo de tubarão
                    if enemy.enemy_type == 'reef_shark':
                        self.hero.health -= 2
                    elif enemy.enemy_type == 'bull_shark':
                        self.hero.health -= 4
                    elif enemy.enemy_type == 'great_white':
                        self.hero.health -= 6
                    else:  # Chefão
                        self.hero.health -= 25

                    enemy.deal_damage()

                    if self.hero.health <= 0:
                        self.hero.alive = False
                        self.state = GAME_STATE_GAME_OVER
                        self.game_over_timer = 0
                        self.sound_manager.play_game_over()
                        break

            # Verifica colisões com bolhas de ar
            for powerup in self.health_powerups[:]:
                if (powerup.grid_x == self.hero.grid_x and
                        powerup.grid_y == self.hero.grid_y):
                    self.hero.health = min(100, self.hero.health + 20)
                    self.health_powerups.remove(powerup)
                    self.sound_manager.play_bubble_collect()

        elif self.state == GAME_STATE_GAME_OVER:
            self.game_over_timer += dt

    def spawn_new_shark(self):
        """Gera um novo tubarão em um local aleatório"""

        # Lista de possíveis novos tubarão dando maiores possibilidades
        shark_type = random.choice(['reef_shark'] * 40 + ['bull_shark'] * 30 +
                                   ['great_white'] * 20 + ['hammer_shark'] * 10)

        for _ in range(20):
            x = random.randint(2, GRID_WIDTH - 3)
            y = random.randint(2, GRID_HEIGHT - 3)

            if (self.dungeon.is_walkable(x, y) and
                    abs(x - self.hero.grid_x) + abs(y - self.hero.grid_y) > 8):
                self.enemies.append(Enemy(x, y, shark_type))
                break

    def spawn_air_bubble(self):
        """Gera bolhas de ar para recuperação de saúde"""
        for _ in range(30):
            x = random.randint(1, GRID_WIDTH - 2)
            y = random.randint(1, GRID_HEIGHT - 2)

            if self.dungeon.is_walkable(x, y):
                if x == self.hero.grid_x and y == self.hero.grid_y:
                    continue

                occupied = False
                for enemy in self.enemies:
                    if enemy.grid_x == x and enemy.grid_y == y:
                        occupied = True
                        break

                for powerup in self.health_powerups:
                    if powerup.grid_x == x and powerup.grid_y == y:
                        occupied = True
                        break

                if not occupied:
                    self.health_powerups.append(HealthPowerUp(x, y))
                    break

    def handle_key(self, key):
        if self.state == GAME_STATE_PLAYING and self.hero.alive:
            if key == keys.UP or key == keys.W:
                self.hero.change_direction(DIRECTION_UP)
            elif key == keys.DOWN or key == keys.S:
                self.hero.change_direction(DIRECTION_DOWN)
            elif key == keys.LEFT or key == keys.A:
                self.hero.change_direction(DIRECTION_LEFT)
            elif key == keys.RIGHT or key == keys.D:
                self.hero.change_direction(DIRECTION_RIGHT)
            elif key == keys.ESCAPE:
                self.state = GAME_STATE_MENU

        elif self.state == GAME_STATE_GAME_OVER:
            if key == keys.SPACE:
                self.reset_game()
                self.state = GAME_STATE_PLAYING

    def handle_mouse_click(self, pos):
        if self.state == GAME_STATE_MENU:
            x, y = pos

            if 300 <= x <= 500 and 200 <= y <= 250:
                self.state = GAME_STATE_PLAYING
                self.sound_manager.play_menu_select()

            elif 300 <= x <= 500 and 270 <= y <= 320:
                self.sound_manager.music_enabled = not self.sound_manager.music_enabled
                self.sound_manager.play_menu_select()

            elif 300 <= x <= 500 and 340 <= y <= 390:
                self.sound_manager.sounds_enabled = not self.sound_manager.sounds_enabled
                self.sound_manager.play_menu_select()

            elif 300 <= x <= 500 and 410 <= y <= 460:
                import sys
                sys.exit()

    def draw_game(self, screen):
        if self.state == GAME_STATE_MENU:
            screen.fill('darkblue')

            screen.draw.text(
                "NEMO'S OCEAN ADVENTURE",
                center=(WIDTH // 2, 100),
                fontsize=42,
                color='orange'
            )

            screen.draw.text(
                "Escape the Sharks!",
                center=(WIDTH // 2, 140),
                fontsize=24,
                color='lightcyan'
            )

            buttons = [
                ("Start Game", 200),
                (f"Music: {'ON' if self.sound_manager.music_enabled else 'OFF'}", 270),
                (f"Sounds: {'ON' if self.sound_manager.sounds_enabled else 'OFF'}", 340),
                ("Exit", 410)
            ]

            for text, y in buttons:
                button_rect = Rect(300, y, 200, 50)
                screen.draw.filled_rect(button_rect, 'darkslateblue')
                screen.draw.rect(button_rect, 'orange')
                screen.draw.text(
                    text,
                    center=(400, y + 25),
                    fontsize=24,
                    color='white'
                )

        elif self.state == GAME_STATE_PLAYING:
            self.dungeon.draw(screen)

            for powerup in self.health_powerups:
                powerup.draw(screen)

            if self.hero.alive:
                self.hero.draw(screen)

            for enemy in self.enemies:
                enemy.draw(screen)

            # Desenha UI
            screen.draw.text(
                f"Health: {self.hero.health}",
                (10, 10),
                fontsize=24,
                color='orange'
            )

            screen.draw.text(
                "Help Nemo escape the sharks! Use WASD or Arrow Keys",
                (10, HEIGHT - 30),
                fontsize=18,
                color='lightcyan'
            )

            screen.draw.text(
                f"Sharks: {len(self.enemies)}",
                (10, 40),
                fontsize=20,
                color='red'
            )

            screen.draw.text(
                f"Air Bubbles: {len(self.health_powerups)}",
                (10, 70),
                fontsize=20,
                color='cyan'
            )

        elif self.state == GAME_STATE_GAME_OVER:
            screen.fill('darkred')
            screen.draw.text(
                "NEMO WAS CAUGHT!",
                center=(WIDTH // 2, HEIGHT // 2 - 50),
                fontsize=48,
                color='orange'
            )
            screen.draw.text(
                "Press SPACE to try again",
                center=(WIDTH // 2, HEIGHT // 2 + 20),
                fontsize=24,
                color='white'
            )


# Instância global do jogo
game = Game()


# Funções necessárias para o PgZero
def update(dt):
    game.update_game(dt)


def on_key_down(key):
    game.handle_key(key)


def on_mouse_down(pos):
    game.handle_mouse_click(pos)


def draw():
    game.draw_game(screen)