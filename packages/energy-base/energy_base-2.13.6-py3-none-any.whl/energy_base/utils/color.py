import random

random.seed(1)


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])


def darken_color(hex_color, factor):
    if not (0 <= factor <= 1):
        raise ValueError("Factor must be between 0 and 1")

    r, g, b = hex_to_rgb(hex_color)
    darkened_rgb = (int(r * factor), int(g * factor), int(b * factor))
    return rgb_to_hex(darkened_rgb)


def generate_random_color(seed=None):
    if seed:
        random.seed(seed)

    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return "#{:02X}{:02X}{:02X}".format(r, g, b)
