import math
import random
from enum import Enum
import time
from pygame import Rect

# Game constants
GRID_SIZE = 32
WIDTH = 800
HEIGHT = 600
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE


class GameState(Enum):
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


class SoundManager:
    """Sound manager using PgZero's built-in sound system"""

    def __init__(self):
        self.music_enabled = True
        self.sounds_enabled = True
        self.background_music_timer = 0
        self.current_track = 0

        # Try to load sounds using PgZero's sound system
        self.sounds_available = self._check_sounds()

        if self.sounds_available:
            print("Sound system ready!")
        else:
            print("No sound files found - using placeholder sounds")
            self._create_placeholder_sounds()

    def _check_sounds(self):
        """Check if sound files are available"""
        try:
            return hasattr(__builtins__, 'sounds')
        except:
            return False

    def _create_placeholder_sounds(self):
        """Create a simple sound system using tone generation"""
        self.tone_sounds = {
            'swim': {'freq': 200, 'duration': 0.1},
            'bubble': {'freq': 400, 'duration': 0.2},
            'shark_bite': {'freq': 100, 'duration': 0.3},
            'menu_select': {'freq': 440, 'duration': 0.1},
            'game_over': {'freq': 80, 'duration': 0.5}
        }

    def _play_tone_sound(self, sound_name):
        """Play a simple tone sound (placeholder)"""
        if sound_name in self.tone_sounds:
            tone = self.tone_sounds[sound_name]
            print(f"SOUND {sound_name.upper()}: {tone['freq']}Hz for {tone['duration']}s")

    def play_background_music(self, dt):
        """Play background music"""
        if not self.music_enabled:
            return

        self.background_music_timer += dt

        if self.sounds_available:
            try:
                music.play('ocean_ambient')
            except:
                pass
        else:
            if self.background_music_timer >= 15.0:
                self.background_music_timer = 0
                print("Ocean ambient music playing...")

    def play_swim_sound(self):
        if not self.sounds_enabled:
            return
        if self.sounds_available:
            try:
                sounds.swim.play()
            except:
                pass
        else:
            self._play_tone_sound('swim')

    def play_bubble_collect(self):
        if not self.sounds_enabled:
            return
        if self.sounds_available:
            try:
                sounds.bubble_collect.play()
            except:
                pass
        else:
            self._play_tone_sound('bubble')

    def play_shark_bite(self, shark_type):
        if not self.sounds_enabled:
            return
        if self.sounds_available:
            try:
                sounds.shark_bite.play()
            except:
                pass
        else:
            self._play_tone_sound('shark_bite')

    def play_menu_select(self):
        if not self.sounds_enabled:
            return
        if self.sounds_available:
            try:
                sounds.menu_beep.play()
            except:
                pass
        else:
            self._play_tone_sound('menu_select')

    def play_game_over(self):
        if not self.sounds_enabled:
            return
        if self.sounds_available:
            try:
                sounds.game_over.play()
            except:
                pass
        else:
            self._play_tone_sound('game_over')

    def play_ambient_bubbles(self):
        if not self.sounds_enabled:
            return
        if random.random() < 0.001:
            if self.sounds_available:
                try:
                    sounds.ambient_bubble.play()
                except:
                    pass
            else:
                if random.random() < 0.1:
                    print("bubble...")


class AnimatedSprite:
    """Base class for animated sprites using two-frame animation"""

    def __init__(self, x, y, image_base_name, animation_speed=0.5):
        self.grid_x = x
        self.grid_y = y
        self.pixel_x = x * GRID_SIZE
        self.pixel_y = y * GRID_SIZE
        self.target_x = self.pixel_x
        self.target_y = self.pixel_y
        self.moving = False
        self.move_speed = 4

        # Two-frame sprite animation
        self.image_base_name = image_base_name
        self.animation_speed = animation_speed
        self.animation_timer = 0
        self.current_frame = 0  # 0 or 1

        # Create actors for both frames
        self.actors = []
        try:
            self.actors.append(Actor(f"{image_base_name}_1"))
            self.actors.append(Actor(f"{image_base_name}_2"))
            print(f"Loaded sprites: {image_base_name}_1, {image_base_name}_2")
        except:
            print(f"Failed to load sprites for {image_base_name}")
            # Create placeholder actors
            self.actors = [None, None]

        self.update_actor_position()

    def update(self, dt):
        # Update sprite animation (alternate between two frames)
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = 1 - self.current_frame  # Toggle between 0 and 1

        # Update position movement
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
        """Update actor position"""
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
        """Draw current animation frame"""
        current_actor = self.actors[self.current_frame]
        if current_actor:
            current_actor.draw()


class Hero(AnimatedSprite):
    """Nemo - animated clownfish hero with directional sprites"""

    def __init__(self, x, y):
        # Don't call super().__init__ because we need custom sprite handling
        self.grid_x = x
        self.grid_y = y
        self.pixel_x = x * GRID_SIZE
        self.pixel_y = y * GRID_SIZE
        self.health = 100
        self.alive = True

        # Fluid movement system
        self.current_direction = Direction.RIGHT
        self.next_direction = None
        self.move_speed = 80

        # Real position (float) for smooth movement
        self.real_x = float(x * GRID_SIZE)
        self.real_y = float(y * GRID_SIZE)

        # Swimming animation
        self.swim_timer = 0
        self.swim_amplitude = 2
        self.swim_frequency = 12

        # Timer for swimming sounds
        self.swim_sound_timer = 0

        # Directional sprite animation
        self.animation_speed = 0.4
        self.animation_timer = 0
        self.current_frame = 0  # 0 or 1

        # Create actors for each direction (2 frames each)
        self.direction_actors = {}
        directions = ['right', 'left', 'up', 'down']

        for direction in directions:
            try:
                actor1 = Actor(f"nemo_{direction}_1")
                actor2 = Actor(f"nemo_{direction}_2")
                self.direction_actors[direction] = [actor1, actor2]
                print(f"Loaded Nemo sprites: nemo_{direction}_1, nemo_{direction}_2")
            except:
                print(f"Failed to load Nemo sprites for direction: {direction}")
                self.direction_actors[direction] = [None, None]

    def update(self, dt, dungeon, sound_manager):
        if not self.alive:
            return

        # Update sprite animation
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = 1 - self.current_frame  # Toggle between 0 and 1

        # Apply direction change if pending
        if self.next_direction:
            self.current_direction = self.next_direction
            self.next_direction = None

            # Play direction change sound occasionally
            if random.random() < 0.3:
                sound_manager.play_swim_sound()

        # Continuous fluid movement
        dx = self.current_direction.value[0] * self.move_speed * dt
        dy = self.current_direction.value[1] * self.move_speed * dt

        # New position
        new_real_x = self.real_x + dx
        new_real_y = self.real_y + dy

        # Convert to grid for collision checking
        new_grid_x = int(new_real_x // GRID_SIZE)
        new_grid_y = int(new_real_y // GRID_SIZE)

        # Check collision
        if dungeon.is_walkable(new_grid_x, new_grid_y):
            self.real_x = new_real_x
            self.real_y = new_real_y
            self.grid_x = new_grid_x
            self.grid_y = new_grid_y

            # Occasional swimming sound
            self.swim_sound_timer += dt
            if self.swim_sound_timer >= 4.0:
                self.swim_sound_timer = 0
                if random.random() < 0.3:
                    sound_manager.play_swim_sound()

        # Swimming animation
        self.swim_timer += dt

        # Calculate offset perpendicular to movement direction
        swim_offset_x = 0
        swim_offset_y = 0

        if self.current_direction in [Direction.LEFT, Direction.RIGHT]:
            swim_offset_y = math.sin(self.swim_timer * self.swim_frequency) * self.swim_amplitude
        else:
            swim_offset_x = math.sin(self.swim_timer * self.swim_frequency) * self.swim_amplitude

        # Final position for drawing
        self.pixel_x = self.real_x + swim_offset_x
        self.pixel_y = self.real_y + swim_offset_y

        # Update actor positions
        self.update_actor_positions()

    def update_actor_positions(self):
        """Update all actor positions"""
        for direction_actors in self.direction_actors.values():
            for actor in direction_actors:
                if actor:
                    actor.pos = (self.pixel_x + GRID_SIZE // 2, self.pixel_y + GRID_SIZE // 2)

    def change_direction(self, new_direction):
        """Change the direction of continuous movement"""
        self.next_direction = new_direction

    def draw(self, screen):
        """Draw Nemo with current direction and animation frame"""
        # Get direction name
        direction_name = {
            Direction.RIGHT: 'right',
            Direction.LEFT: 'left',
            Direction.UP: 'up',
            Direction.DOWN: 'down'
        }[self.current_direction]

        # Get current actors for this direction
        current_actors = self.direction_actors.get(direction_name, [None, None])
        current_actor = current_actors[self.current_frame]

        if current_actor:
            current_actor.draw()


class Enemy(AnimatedSprite):
    """Sharks with two-frame sprite animation"""

    def __init__(self, x, y, enemy_type='reef_shark'):
        super().__init__(x, y, enemy_type, 0.6)  # Slower animation for sharks
        self.enemy_type = enemy_type

        # Set size based on shark type
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
        self.patrol_radius = random.randint(2, 4)

        # Fatigue system
        self.damage_dealt = 0
        self.tired = False
        self.tired_timer = 0
        self.tired_duration = 5.0

        # Fluid movement
        self.real_x = float(x * GRID_SIZE)
        self.real_y = float(y * GRID_SIZE)
        self.current_direction = random.choice([Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT])

        # Swimming animation
        self.swim_timer = 0
        self.swim_amplitude = 1
        self.swim_frequency = 4

    def update(self, dt, dungeon, hero_pos):
        # Update sprite animation
        super().update(dt)

        # Fatigue system
        if self.tired:
            self.tired_timer += dt
            if self.tired_timer >= self.tired_duration:
                self.tired = False
                self.tired_timer = 0
                self.damage_dealt = 0
            return

        # Calculate distance to hero
        hero_distance = math.sqrt(
            (self.grid_x - hero_pos[0]) ** 2 +
            (self.grid_y - hero_pos[1]) ** 2
        )

        # AI movement timer
        self.move_timer += dt

        # Different movement speeds based on shark type
        if self.enemy_type == 'bull_shark':
            move_frequency = 0.8
            enemy_speed = 35
        elif self.enemy_type == 'great_white':
            move_frequency = 1.0
            enemy_speed = 30
        elif self.enemy_type == 'reef_shark':
            move_frequency = 0.4
            enemy_speed = 40
        else:  # hammer_shark
            move_frequency = 1.5
            enemy_speed = 25

        # Only decide new direction at intervals
        if self.move_timer >= move_frequency:
            self.move_timer = 0

            new_direction = None

            # Hunter behavior for great whites
            if hero_distance <= 6 and not self.tired:
                dx = hero_pos[0] - self.grid_x
                dy = hero_pos[1] - self.grid_y

                if abs(dx) > abs(dy):
                    new_direction = Direction.RIGHT if dx > 0 else Direction.LEFT
                else:
                    new_direction = Direction.DOWN if dy > 0 else Direction.UP
            else:
                # Normal patrol behavior
                if hero_distance <= 4:
                    patrol_radius = 6
                else:
                    patrol_radius = self.patrol_radius

                directions = [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]
                random.shuffle(directions)

                for direction in directions:
                    new_x = self.grid_x + direction.value[0]
                    new_y = self.grid_y + direction.value[1]

                    distance_from_center = math.sqrt(
                        (new_x - self.patrol_center_x) ** 2 +
                        (new_y - self.patrol_center_y) ** 2
                    )

                    if (distance_from_center <= patrol_radius and
                            dungeon.is_walkable(new_x, new_y)):
                        new_direction = direction
                        break

            if new_direction:
                self.current_direction = new_direction

        # Continuous movement
        if hasattr(self, 'current_direction'):
            dx = self.current_direction.value[0] * enemy_speed * dt
            dy = self.current_direction.value[1] * enemy_speed * dt

            new_real_x = self.real_x + dx
            new_real_y = self.real_y + dy

            new_grid_x = int(new_real_x // GRID_SIZE)
            new_grid_y = int(new_real_y // GRID_SIZE)

            if dungeon.is_walkable(new_grid_x, new_grid_y):
                self.real_x = new_real_x
                self.real_y = new_real_y
                self.grid_x = new_grid_x
                self.grid_y = new_grid_y

                # Swimming animation
                self.swim_timer += dt
                swim_offset_x = 0
                swim_offset_y = 0

                if self.current_direction in [Direction.LEFT, Direction.RIGHT]:
                    swim_offset_y = math.sin(self.swim_timer * self.swim_frequency) * self.swim_amplitude
                else:
                    swim_offset_x = math.sin(self.swim_timer * self.swim_frequency) * self.swim_amplitude

                self.pixel_x = self.real_x + swim_offset_x
                self.pixel_y = self.real_y + swim_offset_y
            else:
                directions = [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]
                self.current_direction = random.choice(directions)

        # Update actor positions
        self.update_actor_position()

        # Rotate shark based on direction
        for actor in self.actors:
            if actor:
                direction_angles = {
                    Direction.RIGHT: 0,
                    Direction.DOWN: 90,
                    Direction.LEFT: 180,
                    Direction.UP: 270
                }
                actor.angle = direction_angles.get(self.current_direction, 0)

    def deal_damage(self):
        """Called when shark deals damage"""
        self.damage_dealt += 1
        if self.damage_dealt >= 1:
            self.tired = True
            self.tired_timer = 0
        return True


class HealthPowerUp(AnimatedSprite):
    """Air bubbles with two-frame sprite animation"""

    def __init__(self, x, y):
        super().__init__(x, y, 'bubble', 0.3)  # Fast animation for bubbles
        self.float_timer = 0
        self.float_amplitude = 5
        self.base_y = y * GRID_SIZE

    def update(self, dt):
        # Update sprite animation
        super().update(dt)

        self.float_timer += dt
        self.pixel_y = self.base_y + math.sin(self.float_timer * 2) * self.float_amplitude

        # Update actor positions with floating animation
        for actor in self.actors:
            if actor:
                actor.pos = (self.pixel_x + GRID_SIZE // 2, self.pixel_y + GRID_SIZE // 2)
                # Add floating rotation animation
                actor.angle = math.sin(self.float_timer * 3) * 10


class Dungeon:
    """Ocean floor with animated seaweed using two-frame sprites"""

    def __init__(self):
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT
        self.seaweed = set()
        self.seaweed_types = {}
        self.seaweed_sprites = {}  # Store animated sprites for each seaweed
        self.generate_ocean_floor()

    def generate_ocean_floor(self):
        # Create border seaweed
        for x in range(self.width):
            self.seaweed.add((x, 0))
            self.seaweed.add((x, self.height - 1))

            # Assign seaweed types and create animated sprites
            for y_pos in [0, self.height - 1]:
                seaweed_type = random.choice(['kelp', 'coral', 'anemone'])
                self.seaweed_types[(x, y_pos)] = seaweed_type
                self.seaweed_sprites[(x, y_pos)] = AnimatedSprite(x, y_pos, seaweed_type, 0.8)

        for y in range(self.height):
            self.seaweed.add((0, y))
            self.seaweed.add((self.width - 1, y))

            # Assign seaweed types for side borders
            for x_pos in [0, self.width - 1]:
                seaweed_type = random.choice(['kelp', 'coral', 'anemone'])
                self.seaweed_types[(x_pos, y)] = seaweed_type
                self.seaweed_sprites[(x_pos, y)] = AnimatedSprite(x_pos, y, seaweed_type, 0.8)

        # Add random seaweed patches
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
        # Update all seaweed sprite animations
        for sprite in self.seaweed_sprites.values():
            sprite.update(dt)

    def draw(self, screen):
        # Ocean background
        try:
            screen.blit('ocean_bg', (0, 0))
        except:
            screen.fill('midnightblue')

        # Draw seaweed with sprite animations
        for pos, sprite in self.seaweed_sprites.items():
            sprite.draw(screen)

        # Floating particles
        current_time = time.time()
        for i in range(15):
            particle_x = (current_time * 8 + i * 50) % WIDTH
            particle_y = (current_time * 3 + i * 40) % HEIGHT
            particle_size = 1 + (i % 2)

            screen.draw.filled_circle((particle_x, particle_y), particle_size, 'lightcyan')


class Game:
    """Main game class"""

    def __init__(self):
        self.powerup_spawn_interval = None
        self.powerup_spawn_timer = None
        self.enemy_spawn_interval = None
        self.enemy_spawn_timer = None
        self.state = GameState.MENU
        self.dungeon = Dungeon()
        self.hero = None
        self.enemies = []
        self.health_powerups = []
        self.sound_manager = SoundManager()
        self.game_over_timer = 0
        self.reset_game()

    def reset_game(self):
        # Find a walkable position for Nemo
        while True:
            x = random.randint(1, GRID_WIDTH - 2)
            y = random.randint(1, GRID_HEIGHT - 2)
            if self.dungeon.is_walkable(x, y):
                self.hero = Hero(x, y)
                break

        # Create sharks
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

        # Reset power-ups
        self.health_powerups = []

        # Add spawn timers
        self.enemy_spawn_timer = 0
        self.enemy_spawn_interval = 8.0

        self.powerup_spawn_timer = 0
        self.powerup_spawn_interval = 12.0

    def update_game(self, dt):
        # Play background music
        self.sound_manager.play_background_music(dt)

        # Ambient sounds
        self.sound_manager.play_ambient_bubbles()

        self.dungeon.update(dt)

        if self.state == GameState.PLAYING:
            if self.hero.alive:
                self.hero.update(dt, self.dungeon, self.sound_manager)

                # Continuous shark spawning
                self.enemy_spawn_timer += dt
                if self.enemy_spawn_timer >= self.enemy_spawn_interval and len(self.enemies) < 50:
                    self.enemy_spawn_timer = 0
                    self.spawn_new_shark()

                # Bubble spawning
                self.powerup_spawn_timer += dt
                if self.powerup_spawn_timer >= self.powerup_spawn_interval:
                    self.powerup_spawn_timer = 0
                    self.spawn_air_bubble()

            hero_pos = (self.hero.grid_x, self.hero.grid_y)

            # Update all sharks
            for enemy in self.enemies:
                enemy.update(dt, self.dungeon, hero_pos)

            # Update bubbles
            for powerup in self.health_powerups:
                powerup.update(dt)

            # Check collisions with sharks
            for enemy in self.enemies:
                if (enemy.grid_x == self.hero.grid_x and
                        enemy.grid_y == self.hero.grid_y):

                    if enemy.tired:
                        continue

                    # Play attack sound
                    self.sound_manager.play_shark_bite(enemy.enemy_type)

                    # Damage based on shark type
                    if enemy.enemy_type == 'reef_shark':
                        self.hero.health -= 2
                    elif enemy.enemy_type == 'bull_shark':
                        self.hero.health -= 4
                    elif enemy.enemy_type == 'great_white':
                        self.hero.health -= 6
                    else:  # hammer_shark
                        self.hero.health -= 8

                    enemy.deal_damage()

                    if self.hero.health <= 0:
                        self.hero.alive = False
                        self.state = GameState.GAME_OVER
                        self.game_over_timer = 0
                        self.sound_manager.play_game_over()
                        break

            # Check collisions with air bubbles
            for powerup in self.health_powerups[:]:
                if (powerup.grid_x == self.hero.grid_x and
                        powerup.grid_y == self.hero.grid_y):
                    self.hero.health = min(100, self.hero.health + 20)
                    self.health_powerups.remove(powerup)
                    self.sound_manager.play_bubble_collect()

        elif self.state == GameState.GAME_OVER:
            self.game_over_timer += dt

    def spawn_new_shark(self):
        """Spawn a new shark at a random location"""
        shark_type = random.choice(
            ['reef_shark'] * 40 + ['bull_shark'] * 30 + ['great_white'] * 20 + ['hammer_shark'] * 10)

        for _ in range(20):
            x = random.randint(2, GRID_WIDTH - 3)
            y = random.randint(2, GRID_HEIGHT - 3)

            if (self.dungeon.is_walkable(x, y) and
                    abs(x - self.hero.grid_x) + abs(y - self.hero.grid_y) > 8):
                self.enemies.append(Enemy(x, y, shark_type))
                break

    def spawn_air_bubble(self):
        """Spawn air bubbles for health recovery"""
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
        if self.state == GameState.PLAYING and self.hero.alive:
            if key == keys.UP or key == keys.W:
                self.hero.change_direction(Direction.UP)
            elif key == keys.DOWN or key == keys.S:
                self.hero.change_direction(Direction.DOWN)
            elif key == keys.LEFT or key == keys.A:
                self.hero.change_direction(Direction.LEFT)
            elif key == keys.RIGHT or key == keys.D:
                self.hero.change_direction(Direction.RIGHT)
            elif key == keys.ESCAPE:
                self.state = GameState.MENU

        elif self.state == GameState.GAME_OVER:
            if key == keys.SPACE:
                self.reset_game()
                self.state = GameState.PLAYING

    def handle_mouse_click(self, pos):
        if self.state == GameState.MENU:
            x, y = pos

            if 300 <= x <= 500 and 200 <= y <= 250:
                self.state = GameState.PLAYING
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
        if self.state == GameState.MENU:
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

        elif self.state == GameState.PLAYING:
            self.dungeon.draw(screen)

            for powerup in self.health_powerups:
                powerup.draw(screen)

            if self.hero.alive:
                self.hero.draw(screen)

            for enemy in self.enemies:
                enemy.draw(screen)

            # Draw UI
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

        elif self.state == GameState.GAME_OVER:
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


# Global game instance
game = Game()


# PgZero required functions
def update(dt):
    game.update_game(dt)


def on_key_down(key):
    game.handle_key(key)


def on_mouse_down(pos):
    game.handle_mouse_click(pos)


def draw():
    game.draw_game(screen)
