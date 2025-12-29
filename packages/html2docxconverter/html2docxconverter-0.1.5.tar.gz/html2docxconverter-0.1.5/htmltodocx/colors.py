import colorsys
import re


def rgba_to_rgb(rgba_color: str) -> tuple:
    try:
        rgba = rgba_color.replace("rgba(", "").replace(")", "").replace("%", "").split(",")
        return int(rgba[0]), int(rgba[1]), int(rgba[2])
    except (ValueError, IndexError):
        print(f'rgba_color: "{rgba_color}" is not valid')
        return 0, 0, 0


def hex_to_rgb(hex_color: str) -> tuple:
    try:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        print(f'hex_color: "{hex_color}" is not valid')
        return 0, 0, 0


def hsl_to_rgb(hsl_color):
    try:
        hsl_parts = hsl_color.replace("hsl(", "").replace(")", "").replace("%", "").split(",")
        h = float(hsl_parts[0].strip()) / 360
        s = float(hsl_parts[1].strip()) / 100
        l = float(hsl_parts[2].strip()) / 100
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return round(r * 255), round(g * 255), round(b * 255)
    except (ValueError, IndexError):
        print(f'hsl_color: "{hsl_color}" is not valid')
        return 0, 0, 0


def hsl_to_hex(hsl_str: str) -> str:
    match = re.match(r"hsl\(\s*(\d+),\s*(\d+)%?,\s*(\d+)%?\)", hsl_str)
    if not match:
        print(f'hsl_color: "{hsl_str}" is not valid')
        return "FFFFFF"

    h, s, l = [int(match.group(i)) for i in range(1, 4)]
    h /= 360
    s /= 100
    l /= 100

    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "{:02X}{:02X}{:02X}".format(int(r * 255), int(g * 255), int(b * 255))


def rgb_to_hex(rgb: str) -> str:
    nums = list(map(int, re.findall(r"\d+", rgb)))
    try:
        return "".join(f"{v:02X}" for v in nums[:3])
    except IndexError:
        print(f'rgb_color: "{rgb}" is not valid')
        return "FFFFFF"


def get_color_rgb(enter_color: str) -> tuple[int, int, int]:
    color = (0, 0, 0)
    try:
        if re.search(r"#", enter_color):
            color = hex_to_rgb(enter_color)
        elif re.search(r"rgba", enter_color):
            color = rgba_to_rgb(enter_color)
        elif re.search(r"hsl", enter_color):
            color = hsl_to_rgb(enter_color)
    except ValueError:
        pass

    if color == (255, 255, 255):
        color = (0, 0, 0)

    return color


def get_color_hex(enter_color: str) -> str:
    color = "#000000"
    try:
        if re.search(r"#", enter_color):
            color = enter_color
        elif re.search(r"rgba", enter_color):
            color = rgb_to_hex(enter_color)
        elif re.search(r"hsl", enter_color):
            color = hsl_to_hex(enter_color)
    except ValueError:
        print(f'enter_color: "{enter_color}" is not valid')

    return color
