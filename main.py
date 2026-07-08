## Libraries
import pygame, json, os, random, math, worldgen

## Constants
WIDTH = 800
HEIGHT = 800
FPS = 60
GRAVITY = 1
GRID_SIZE = 50
CELLS_X = WIDTH // GRID_SIZE
CELLS_Y = HEIGHT // GRID_SIZE
PLAYER_ACCEL = 1
MAX_PLAYER_SPEED = 5
BG_COLOR = (97, 185, 222)
CHUNKS_X = 16
CHUNKS_Y = 16
PLAYER_REACH = 4 * GRID_SIZE
image_scale = GRID_SIZE / 16

## Debug Mode
debug = False

## Load Block Data
with open('blocks.json') as file:
    block_data = json.load(file)

## Load Item Data
with open('items.json') as file:
    item_data = json.load(file)

## Placing
def place_block(grid_position, block):
    grid_x, grid_y = grid_position
    map[chunk_y][chunk_x][grid_y][grid_x] = {'block':block, 'health':block_data[block]['strength']}

## Structure
def place_structure(root_position, id):
    with open(f'structures/{id}.json') as file:
        data = json.load(file)
        for block in data:
            relative_position = block['position']
            block_name = block['block']
            position = root_position[0] + relative_position[0], root_position[1] + relative_position[1]
            place_block(position, block_name)

## Worldgen
chunk_x = 0
chunk_y = 0
def create_blank_chunk():
    return [[{'block':'', 'health':0} for x in range(CELLS_X)] for y in range(CELLS_Y)]

def get_underground_block(chunk_y, local_y):
    if chunk_y < 2:
        return "dirt"

    if chunk_y == 2:
        dirt_chances = [
            1.0, 1.0, 1.0,
            0.9, 0.8, 0.7,
            0.6, 0.5, 0.4,
            0.3, 0.2, 0.1,
            0.0, 0.0, 0.0, 0.0
        ]

        if random.random() < dirt_chances[local_y]:
            return "dirt"
        else:
            return "stone"

    return "stone"

map = [[create_blank_chunk() for x in range(CHUNKS_X)] for y in range(CHUNKS_Y)]

for global_x in range(CHUNKS_X * CELLS_X):
    surface_y = worldgen.get_surface_height(global_x)

    chunk_x = global_x // CELLS_X
    local_x = global_x % CELLS_X
    chunk_y = surface_y // CELLS_Y
    if (14 >= local_x >= 2):
        match random.randint(0, 12):
            case 0: place_structure((local_x, (surface_y - 1) % CELLS_Y), "oak_tree")
            case 1|2: place_block((local_x, (surface_y - 1) % CELLS_Y), 'flower')
            case 3|4|5: place_block((local_x, (surface_y - 1) % CELLS_Y), 'bush')
    for global_y in range(surface_y, CHUNKS_Y * CELLS_Y):
        chunk_y = global_y // CELLS_Y
        local_y = global_y % CELLS_Y

        if global_y == surface_y:
            block = "grass"
        else:
            block = get_underground_block(chunk_y, local_y)

        map[chunk_y][chunk_x][local_y][local_x] = {
            "block": block,
            "health": block_data[block]["strength"]
        }

chunk_x = 0
chunk_y = 0

## Pygame Setup
window = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
pygame.font.init()
tiny_font = pygame.font.Font('font.ttf', 32)
pygame.mixer.init()

## Music
songs = os.listdir('music')
song_index = -1
def shuffle_songs():
    random.shuffle(songs)

def next_song():
    global song_index
    song_index += 1
    if song_index >= len(songs):
        shuffle_songs()
        song_index = 0
    song = songs[song_index]
    path = f'music/{song}'
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()

shuffle_songs()

## Font
def draw_text(font, position, text, color):
    window.blit(font.render(text, True, color), position)

## Load Images
images = {}
for path in os.listdir('assets'):
    images[path] = pygame.transform.scale_by(pygame.image.load('assets/'+path), image_scale)

## Grid
grid_layer = pygame.Surface((WIDTH, HEIGHT), masks=(0, 0, 0))
grid_layer.set_alpha(48)

def draw_grid_lines():
    for y in range(CELLS_Y):
        pygame.draw.line(
            grid_layer, (255, 255, 255),
            (0, y * GRID_SIZE),
            (WIDTH, y * GRID_SIZE), 1
        )

    for x in range(CELLS_X):
        pygame.draw.line(
            grid_layer, (255, 255, 255),
            (x * GRID_SIZE, 0),
            (x * GRID_SIZE, HEIGHT), 1
        )

## Draw World
def draw_blocks():
    for y in range(CELLS_Y):
        for x in range(CELLS_X):
            if map[chunk_y][chunk_x][y][x]['block']:
                block = block_data[map[chunk_y][chunk_x][y][x]['block']]
                texture = images[block['texture']]
                window.blit(texture, (x * GRID_SIZE, y * GRID_SIZE))

## Helpers
def is_solid_grid(x, y):
    check_chunk_x = chunk_x
    check_chunk_y = chunk_y

    while x < 0:
        check_chunk_x -= 1
        x += CELLS_X

    while x >= CELLS_X:
        check_chunk_x += 1
        x -= CELLS_X

    while y < 0:
        check_chunk_y -= 1
        y += CELLS_Y

    while y >= CELLS_Y:
        check_chunk_y += 1
        y -= CELLS_Y

    if check_chunk_x < 0 or check_chunk_x >= CHUNKS_X:
        return False

    if check_chunk_y < 0 or check_chunk_y >= CHUNKS_Y:
        return False

    block_name = map[check_chunk_y][check_chunk_x][y][x]['block']
    if not block_name:
        return False

    return not block_data[block_name]['passable']

def get_nearby_solid_rects(rect):
    rects = []

    left = rect.left // GRID_SIZE
    right = rect.right // GRID_SIZE
    top = rect.top // GRID_SIZE
    bottom = rect.bottom // GRID_SIZE

    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            check_chunk_x = chunk_x
            check_chunk_y = chunk_y
            local_x = x
            local_y = y

            while local_x < 0:
                check_chunk_x -= 1
                local_x += CELLS_X

            while local_x >= CELLS_X:
                check_chunk_x += 1
                local_x -= CELLS_X

            while local_y < 0:
                check_chunk_y -= 1
                local_y += CELLS_Y

            while local_y >= CELLS_Y:
                check_chunk_y += 1
                local_y -= CELLS_Y

            if check_chunk_x < 0 or check_chunk_x >= CHUNKS_X:
                continue

            if check_chunk_y < 0 or check_chunk_y >= CHUNKS_Y:
                continue

            block_name = map[check_chunk_y][check_chunk_x][local_y][local_x]['block']
            if not block_name:
                continue

            if block_data[block_name]['passable']:
                continue

            rects.append(pygame.Rect(
                x * GRID_SIZE,
                y * GRID_SIZE,
                GRID_SIZE,
                GRID_SIZE
            ))

    return rects

## World Interaction
def hit_block(grid_position, particles=True):
    grid_x, grid_y = grid_position

    if map[chunk_y][chunk_x][grid_y][grid_x]['block']:
        if particles:
            if random.randint(0, 1) == 0:
                dir = random.uniform(0, 6.28)
                speed = random.uniform(1, 5)
                x = (grid_x * GRID_SIZE) + random.randint(0, GRID_SIZE)
                y = (grid_y * GRID_SIZE) + random.randint(0, GRID_SIZE)
                dx = math.cos(dir) * speed
                dy = math.sin(dir) * speed
                size = random.uniform(3, 6)
                lifespan = random.randint(10, 40)
                color = [max(0, c - 30) for c in block_data[map[chunk_y][chunk_x][grid_y][grid_x]['block']]['color']]

                Particle((x, y), (dx, dy), size, lifespan, color)

        damage = 1
        block_tool = block_data[map[chunk_y][chunk_x][grid_y][grid_x]['block']]['tool']
        held_item = inventory[selected_slot]['item']
        if held_item:
            player_tool = item_data[held_item]['tool'] 
            if block_tool and player_tool:
                if block_tool == player_tool:
                    damage *= item_data[inventory[selected_slot]['item']]['efficiency'] 
                
        map[chunk_y][chunk_x][grid_y][grid_x]['health'] -= damage

        if map[chunk_y][chunk_x][grid_y][grid_x]['health'] <= 0:
            break_block(grid_position, particles)

def break_block(grid_position, particles):
    grid_x, grid_y = grid_position
    drop = block_data[map[chunk_y][chunk_x][grid_y][grid_x]['block']]['drop']
    drop_min = block_data[map[chunk_y][chunk_x][grid_y][grid_x]['block']]['drop_min']
    drop_max = block_data[map[chunk_y][chunk_x][grid_y][grid_x]['block']]['drop_max']
    if drop: give_player_item(drop, random.randint(drop_min, drop_max))

    if particles:
        for i in range(15):
            dir = random.uniform(0, 6.28)
            speed = random.uniform(1, 5)
            x = (grid_x * GRID_SIZE) + random.randint(0, GRID_SIZE)
            y = (grid_y * GRID_SIZE) + random.randint(0, GRID_SIZE)
            dx = math.cos(dir) * speed
            dy = math.sin(dir) * speed
            size = random.uniform(3, 6)
            lifespan = random.randint(10, 40)
            color = [max(0, c - 30) for c in block_data[map[chunk_y][chunk_x][grid_y][grid_x]['block']]['color']]

            Particle((x, y), (dx, dy), size, lifespan, color)

    map[chunk_y][chunk_x][grid_y][grid_x] = {'block':'', 'health':0}

def can_reach_block(player, grid_x, grid_y):
    block_center_x = grid_x * GRID_SIZE + GRID_SIZE // 2
    block_center_y = grid_y * GRID_SIZE + GRID_SIZE // 2

    player_center_x = player.position[0] + GRID_SIZE // 2
    player_center_y = player.position[1] + GRID_SIZE

    dx = block_center_x - player_center_x
    dy = block_center_y - player_center_y

    distance = math.sqrt(dx*dx + dy*dy)
    return distance <= PLAYER_REACH

## Particles
particles = []
class Particle:
    def __init__(self, position, velocity, size, lifespan, color):
        particles.append(self)
        self.x, self.y = position
        self.vx, self.vy = velocity
        self.start_size = size
        self.size = size
        self.lifespan = lifespan
        self.life = lifespan
        self.life_percentage = 1
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life_percentage = self.life / self.lifespan
        self.size = self.start_size * self.life_percentage

        pygame.draw.circle(window, self.color, (self.x, self.y), self.size)
        
        self.life -= 1
        if self.life <= 0:
            particles.remove(self)

## Player
class Player:
    def __init__(self, position):
        self.position = list(position)
        self.velocity = [0, 0]

    def update(self):
        global chunk_x, chunk_y

        self.velocity[1] += GRAVITY

        self.rect = pygame.Rect(
            self.position[0],
            self.position[1],
            GRID_SIZE,
            GRID_SIZE * 2
        )

        ## Horizontal collision
        self.rect.x += self.velocity[0]
        for block_rect in get_nearby_solid_rects(self.rect):
            if self.rect.colliderect(block_rect):
                if self.velocity[0] > 0:
                    self.rect.right = block_rect.left
                elif self.velocity[0] < 0:
                    self.rect.left = block_rect.right

        ## Vertical collision
        self.rect.y += self.velocity[1]
        self.on_ground = False
        for block_rect in get_nearby_solid_rects(self.rect):
            if self.rect.colliderect(block_rect):
                if self.velocity[1] > 0:
                    self.rect.bottom = block_rect.top
                    self.velocity[1] = 0
                    self.on_ground = True
                elif self.velocity[1] < 0:
                    self.rect.top = block_rect.bottom
                    self.velocity[1] = 0

        self.position = [self.rect.x, self.rect.y]

        ## Chunk movement
        changed_chunk = False

        if self.position[0] >= CELLS_X * GRID_SIZE:
            chunk_x += 1
            self.position[0] = 1
            changed_chunk = True

        if self.position[0] < 0:
            chunk_x -= 1
            self.position[0] = CELLS_X * GRID_SIZE - GRID_SIZE - 1
            changed_chunk = True

        if self.position[1] >= CELLS_Y * GRID_SIZE:
            chunk_y += 1
            self.position[1] = 1
            changed_chunk = True

        if self.position[1] < 0:
            chunk_y -= 1
            self.position[1] = CELLS_Y * GRID_SIZE - GRID_SIZE - 1
            changed_chunk = True

        ## Re-check collision after entering new chunk
        if changed_chunk:
            self.rect.topleft = self.position

            for block_rect in get_nearby_solid_rects(self.rect):
                if self.rect.colliderect(block_rect):
                    if self.velocity[1] >= 0:
                        self.rect.bottom = block_rect.top
                        self.velocity[1] = 0
                        self.on_ground = True

            self.position = [self.rect.x, self.rect.y]

        ## Jumping
        if self.on_ground:
            if keys[pygame.K_SPACE]:
                self.velocity[1] = -17

        ## Walking
        if keys[pygame.K_d]:
            self.velocity[0] += PLAYER_ACCEL
        elif keys[pygame.K_a]:
            self.velocity[0] -= PLAYER_ACCEL
        else:
            self.velocity[0] *= 0.85

        self.velocity[0] = min(MAX_PLAYER_SPEED, max(-MAX_PLAYER_SPEED, self.velocity[0]))

        window.blit(images['gleeb.png'], self.position)
        
player = Player((50, 50))

## Inventory
inventory = [{'item':'', 'count':0} for i in range(9)]
selected_slot = 0
def give_player_item(item, count):
    inventory_items = [slot['item'] for slot in inventory]
    if item in inventory_items:
        index = inventory_items.index(item)
        inventory[index]['count'] += count
    else:
        if '' in inventory_items:
            index = inventory_items.index('')
            inventory[index] = {'item':item, 'count':count}
        else:
            print('inventory full!')

def take_item_from_player(item, count):
    inventory_items = [slot['item'] for slot in inventory]
    index = inventory_items.index(item)
    inventory[index]['count'] -= count
    if inventory[index]['count'] == 0:
        inventory[index]['item'] = ''

def draw_inventory():
    for i in range(9):
        x = i * (GRID_SIZE)
        pygame.draw.rect(grid_layer, (255, 255, 255), (x, 0, GRID_SIZE, GRID_SIZE), 2)
        if selected_slot == i:
            pygame.draw.rect(grid_layer, (255, 255, 255), (x, 0, GRID_SIZE, GRID_SIZE))

        item = inventory[i]['item']
        if item:
            texture = images[item_data[item]['texture']]
            texture = pygame.transform.scale_by(texture, (12/16, 12/16))
            window.blit(texture, (x+GRID_SIZE / 8, GRID_SIZE / 8))
        draw_text(tiny_font, (x + 6, 2), str(inventory[i]['count']), (255, 255, 255))

give_player_item('wooden_axe', 1)
give_player_item('wooden_pickaxe', 1)
give_player_item('wooden_shovel', 1)

## Block Info
def draw_block_info():
    block = map[chunk_y][chunk_x][mouse_grid_y][mouse_grid_x]
    id = block['block']
    if not id: return
    name = block_data[id]['name']
    health = block['health']
    draw_text(tiny_font, (4, HEIGHT - 100), name, (255, 255, 255))
    draw_text(tiny_font, (4, HEIGHT - 80), id, (255, 255, 255))
    draw_text(tiny_font, (4, HEIGHT - 60), str(health), (255, 255, 255))

## Random Tick
def random_tick():
    x = random.randint(0, CELLS_X-1)
    y = random.randint(0, CELLS_Y-1)
    if debug: pygame.draw.rect(grid_layer, (0, 100, 255), (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE))
    
    if map[chunk_y][chunk_x][y][x]['block'] == 'oak_sapling':
        if random.randint(0, 9) == 0:
            place_structure((x, y), 'oak_tree')

## Alerts
def show_alert(position, texture):
    scaled_texture = pygame.transform.scale_by(images[texture], 6/16)
    window.blit(images['alert_frame.png'], position)
    window.blit(scaled_texture, (position[0] + (GRID_SIZE * .2), position[1] + (GRID_SIZE * .2)))

## Main Loop
while True:
    ## Event Loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT: quit()
        if event.type == pygame.MOUSEWHEEL:
            selected_slot -= event.y
            selected_slot %= 9
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1: debug = not debug

            if event.key == pygame.K_1: selected_slot = 0
            if event.key == pygame.K_2: selected_slot = 1
            if event.key == pygame.K_3: selected_slot = 2
            if event.key == pygame.K_4: selected_slot = 3
            if event.key == pygame.K_5: selected_slot = 4
            if event.key == pygame.K_6: selected_slot = 5
            if event.key == pygame.K_7: selected_slot = 6
            if event.key == pygame.K_8: selected_slot = 7
            if event.key == pygame.K_9: selected_slot = 8

    ## Input Gathering
    mouse_pos = pygame.mouse.get_pos()
    mouse_down = pygame.mouse.get_pressed()
    keys = pygame.key.get_pressed()

    ## Music
    if not pygame.mixer.music.get_busy(): next_song()
    
    ## Clear Screen
    window.fill(BG_COLOR)

    ## Draw Blocks
    draw_blocks()

    ## Draw Grid
    grid_layer.fill((0, 0, 0))
    if debug:
        draw_grid_lines()
        draw_text(tiny_font, (4, 50), str(player.position), (255, 255, 255))
        draw_text(tiny_font, (4, 80), f'[{chunk_x}, {chunk_y}]', (255, 255, 255))
    
    ## Update Player
    player.update()

    ## Draw Inventory
    draw_inventory()
    
    ## Out-of-Chunk Interaction
    if player.position[1] // GRID_SIZE >= 14:
        block = map[chunk_y + 1][chunk_x][0][player.position[0] // GRID_SIZE]
        position = (player.position[0] + (GRID_SIZE / 5), HEIGHT - GRID_SIZE)
        if block['block']:
            show_alert(position, block_data[block['block']]['texture'])

        if keys[pygame.K_LCTRL]:
            chunk_y += 1
            dy = 0 if player.position[1] // GRID_SIZE == 14 else 1
            hit_block((player.position[0] // GRID_SIZE, dy), False)
            chunk_y -= 1
            
    if player.position[1] // GRID_SIZE <= 0:
        block = map[chunk_y - 1][chunk_x][15][player.position[0] // GRID_SIZE]
        position = (player.position[0] + (GRID_SIZE / 5), 0)
        if block['block']:
            show_alert(position, block_data[block['block']]['texture'])

        if keys[pygame.K_LCTRL]:
            chunk_y -= 1
            dy = 15 if player.position[1] // GRID_SIZE == 0 else 14
            hit_block((player.position[0] // GRID_SIZE, dy), False)
            chunk_y += 1
    
    ## Mouse Hover
    mouse_grid_x = mouse_pos[0] // GRID_SIZE
    mouse_grid_y = mouse_pos[1] // GRID_SIZE
    if can_reach_block(player, mouse_grid_x, mouse_grid_y):
        pygame.draw.rect(grid_layer, (128, 128, 128), (mouse_grid_x * GRID_SIZE, mouse_grid_y * GRID_SIZE, GRID_SIZE, GRID_SIZE))
    
    ## Draw Block Info
    draw_block_info()

    ## Breaking & Placing
    player_rect = pygame.Rect(player.position, (GRID_SIZE, GRID_SIZE * 2))
    if debug: pygame.draw.rect(window, (255, 0, 0), player_rect, 3)

    if can_reach_block(player, mouse_grid_x, mouse_grid_y):
        if mouse_down[0]:
            hit_block((mouse_grid_x, mouse_grid_y))

        if mouse_down[2]:
            block_rect = pygame.Rect(mouse_grid_x * GRID_SIZE, mouse_grid_y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            if debug: pygame.draw.rect(window, (255, 0, 0), block_rect, 3)
            if not player_rect.colliderect(block_rect):
                if not map[chunk_y][chunk_x][mouse_grid_y][mouse_grid_x]['block']:
                    item = inventory[selected_slot]['item']
                    if item:
                        block = item_data[item]['places']
                        if block:
                            take_item_from_player(item, 1)
                            place_block((mouse_grid_x, mouse_grid_y), block)

    ## Particles
    for particle in particles:
        particle.update()

    ## Update World
    random_tick()

    ## Update Screen
    window.blit(grid_layer, (0, 0))
    pygame.display.flip()

    ## Timing Control
    clock.tick(FPS)