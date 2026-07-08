import math, random

seed = random.randint(0, 99999)
random.seed(seed)

def smoothstep(t):
    return t * t * (3 - 2 * t)

def value_noise_1d(x, scale, amplitude):
    x /= scale

    x0 = math.floor(x)
    x1 = x0 + 1
    t = x - x0
    t = smoothstep(t)

    random.seed(x0 + seed * 999)
    y0 = random.uniform(-1, 1)

    random.seed(x1 + seed * 999)
    y1 = random.uniform(-1, 1)

    return (y0 * (1 - t) + y1 * t) * amplitude

def anchored_noise_1d(x, scale, amplitude):
    return value_noise_1d(x, scale, amplitude) - value_noise_1d(0, scale, amplitude)

def get_surface_height(global_x):
    base_height = 8

    small_hills = anchored_noise_1d(global_x, scale=20, amplitude=2)
    big_landforms = anchored_noise_1d(global_x, scale=80, amplitude=5)

    return int(base_height + small_hills + big_landforms)