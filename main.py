## Libraries
import pygame, json, os, random, math

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

image_scale = GRID_SIZE / 16

grid = [[{'block':'', 'health':0} for x in range(CELLS_X)] for y in range(CELLS_Y)]

## Load Block Data
with open('blocks.json') as file:
    block_data = json.load(file)

## Load Item Data
with open('items.json') as file:
    item_data = json.load(file)

## World Generation
for i in range(CELLS_X):
    # Loops through every column and fills it out with blocks
    # 00 air
    # 01 air
    # 02 air 
    # 03 air
    # 04 air
    # 05 grass
    # 06 dirt
    # 07 dirt
    # 08 33% stone 66% dirt
    # 09 50% stone 50% dirt
    # 10 66% stone 33% dirt
    # 11 stone
    # 12 stone
    # 13 stone
    # 14 stone
    # 15 stone

    grid[5][i]['block'] = 'grass'
    grid[6][i]['block'] = 'dirt'
    grid[7][i]['block'] = 'dirt'
    grid[8][i]['block'] = 'stone' if random.randint(0, 2) == 0 else 'dirt'
    grid[9][i]['block'] = 'stone' if random.randint(0, 1) else 'dirt'
    grid[10][i]['block'] = 'stone' if random.randint(0, 2) != 0 else 'dirt'
    grid[11][i]['block'] = 'stone'
    grid[12][i]['block'] = 'stone'
    grid[13][i]['block'] = 'stone'
    grid[14][i]['block'] = 'stone'
    grid[15][i]['block'] = 'stone'

    for y in range(5, 16):
        grid[y][i]['health'] = block_data[grid[y][i]['block']]['strength']

grid[4][6]['block'] = 'flower'

## Pygame Setup
window = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
pygame.font.init()
tiny_font = pygame.font.Font('font.ttf', 32)

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
            if grid[y][x]['block']:
                block = block_data[grid[y][x]['block']]
                texture = images[block['texture']]
                window.blit(texture, (x * GRID_SIZE, y * GRID_SIZE))

## Helpers
def is_solid_grid(x, y):
    if x < 0 or x >= CELLS_X or y < 0 or y >= CELLS_Y:
        return False

    block_name = grid[y][x]['block']
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
            if is_solid_grid(x, y):
                rects.append(pygame.Rect(
                    x * GRID_SIZE,
                    y * GRID_SIZE,
                    GRID_SIZE,
                    GRID_SIZE
                ))

    return rects

## World Interaction
def hit_block(grid_position):
    grid_x, grid_y = grid_position

    if grid[grid_y][grid_x]['block']:
        if random.randint(0, 1) == 0:
            dir = random.uniform(0, 6.28)
            speed = random.uniform(1, 5)
            x = (grid_x * GRID_SIZE) + random.randint(0, GRID_SIZE)
            y = (grid_y * GRID_SIZE) + random.randint(0, GRID_SIZE)
            dx = math.cos(dir) * speed
            dy = math.sin(dir) * speed
            size = random.uniform(3, 6)
            lifespan = random.randint(10, 40)
            color = [max(0, c - 30) for c in block_data[grid[grid_y][grid_x]['block']]['color']]

            Particle((x, y), (dx, dy), size, lifespan, color)

        grid[grid_y][grid_x]['health'] -= 1
        if grid[grid_y][grid_x]['health'] <= 0:
            break_block(grid_position, '')

def break_block(grid_position, tool):
    grid_x, grid_y = grid_position
    drop = block_data[grid[grid_y][grid_x]['block']]['drop']
    drop_min = block_data[grid[grid_y][grid_x]['block']]['drop_min']
    drop_max = block_data[grid[grid_y][grid_x]['block']]['drop_max']
    if drop: give_player_item(drop, random.randint(drop_min, drop_max))


    for i in range(15):
        dir = random.uniform(0, 6.28)
        speed = random.uniform(1, 5)
        x = (grid_x * GRID_SIZE) + random.randint(0, GRID_SIZE)
        y = (grid_y * GRID_SIZE) + random.randint(0, GRID_SIZE)
        dx = math.cos(dir) * speed
        dy = math.sin(dir) * speed
        size = random.uniform(3, 6)
        lifespan = random.randint(10, 40)
        color = [max(0, c - 30) for c in block_data[grid[grid_y][grid_x]['block']]['color']]

        Particle((x, y), (dx, dy), size, lifespan, color)

    grid[grid_y][grid_x] = {'block':'', 'health':0}

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
        self.velocity[1] += GRAVITY

        #### Collision
        self.rect = pygame.Rect(
            self.position[0],
            self.position[1],
            GRID_SIZE,
            GRID_SIZE * 2
        )

        ## Move X
        self.rect.x += self.velocity[0]

        for block_rect in get_nearby_solid_rects(self.rect):
            if self.rect.colliderect(block_rect):
                if self.velocity[0] > 0:
                    self.rect.right = block_rect.left
                elif self.velocity[0] < 0:
                    self.rect.left = block_rect.right

        ## Move Y
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
        ####

        if self.on_ground:
            if keys[pygame.K_SPACE]:
                self.velocity[1] = -17

        if keys[pygame.K_d]: self.velocity[0] += PLAYER_ACCEL
        elif keys[pygame.K_a]: self.velocity[0] -= PLAYER_ACCEL
        else: self.velocity[0] *= 0.85
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

## Placing
def place_block(grid_position, block):
    grid_x, grid_y = grid_position
    grid[grid_y][grid_x] = {'block':block, 'health':block_data[block]['strength']}

## Main Loop
while True:
    ## Event Loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT: quit()
        if event.type == pygame.MOUSEWHEEL:
            selected_slot -= event.y
            selected_slot %= 9
    
    ## Input Gathering
    mouse_pos = pygame.mouse.get_pos()
    mouse_down = pygame.mouse.get_pressed()
    keys = pygame.key.get_pressed()

    ## Clear Screen
    window.fill(BG_COLOR)

    ## Draw Blocks
    draw_blocks()

    ## Draw Grid
    grid_layer.fill((0, 0, 0))
    #draw_grid_lines()

    ## Update Player
    player.update()

    ## Draw Inventory
    draw_inventory()

    ## Mouse Hover
    mouse_grid_x = mouse_pos[0] // GRID_SIZE
    mouse_grid_y = mouse_pos[1] // GRID_SIZE
    pygame.draw.rect(grid_layer, (128, 128, 128), (mouse_grid_x * GRID_SIZE, mouse_grid_y * GRID_SIZE, GRID_SIZE, GRID_SIZE))
    
    ## Breaking & Placing
    if mouse_down[0]: hit_block((mouse_grid_x, mouse_grid_y))
    if mouse_down[2]:
        if not grid[mouse_grid_y][mouse_grid_x]['block']:
            item = inventory[selected_slot]['item']
            if item:
                block = item_data[item]['places']
                take_item_from_player(item, 1)
                place_block((mouse_grid_x, mouse_grid_y), block)

    ## Particles
    for particle in particles:
        particle.update()



    ## Update Screen
    window.blit(grid_layer, (0, 0))
    pygame.display.flip()

    ## Timing Control
    clock.tick(FPS)