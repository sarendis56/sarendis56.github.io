"""Render the site's geometric H mark without external dependencies."""
from pathlib import Path
import math
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'img'
PALETTES = {
    'favicon-h': ('#043361', '#f5f9ff', '#3eb7f0'),
    'favicon-h-dark': ('#dceefa', '#043361', '#087ea4'),
}


def rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def segment_distance(x, y, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - a[0] - t * dx, y - a[1] - t * dy)


def pixel(x, y, colors):
    # A rounded 30 x 30 tile, with a one-unit transparent margin.
    dx, dy = max(abs(x - 16) - 8, 0), max(abs(y - 16) - 8, 0)
    if math.hypot(dx, dy) > 7:
        return (0, 0, 0, 0)
    color = colors[0]
    if min(segment_distance(x, y, (10, 8), (10, 24)),
           segment_distance(x, y, (22, 8), (22, 24))) <= 2:
        color = colors[1]
    bridge = [(10, 18), (16, 18), (16, 14), (22, 14)]
    if min(segment_distance(x, y, a, b) for a, b in zip(bridge, bridge[1:])) <= 2:
        color = colors[2]
    return (*color, 255)


def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))


def render_png(colors, size=64, samples=4):
    rows = bytearray()
    for y in range(size):
        rows.append(0)
        for x in range(size):
            values = [pixel((x + (sx + .5) / samples) * 32 / size,
                            (y + (sy + .5) / samples) * 32 / size, colors)
                      for sy in range(samples) for sx in range(samples)]
            alpha = sum(p[3] for p in values)
            channels = [round(sum(p[c] * p[3] for p in values) / alpha) if alpha else 0
                        for c in range(3)]
            rows.extend((*channels, round(alpha / len(values))))
    header = struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b'')


for name, palette in PALETTES.items():
    background, foreground, accent = palette
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <title>Peichun Hua — Connected H</title>
  <rect x="1" y="1" width="30" height="30" rx="7" fill="{background}"/>
  <path d="M10 8V24 M22 8V24" fill="none" stroke="{foreground}" stroke-width="4" stroke-linecap="round"/>
  <path d="M10 18H16V14H22" fill="none" stroke="{accent}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
'''
    (OUT / f'{name}.svg').write_text(svg)
    (OUT / f'{name}.png').write_bytes(render_png(tuple(map(rgb, palette))))
    # Actual tab-size previews for visual inspection.
    Path(f'/tmp/{name}-16.png').write_bytes(render_png(tuple(map(rgb, palette)), size=16, samples=8))
    Path(f'/tmp/{name}-preview.png').write_bytes(render_png(tuple(map(rgb, palette)), size=256, samples=2))
    print(f'Generated {name}.svg and {name}.png')
