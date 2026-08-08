#!/usr/bin/env python3
"""
Custom Pygame Vector Weather Icon Renderer.
Renders high-resolution, crisp weather graphics without relying on OS system fonts or broken emoji glyphs.
"""

import math
import pygame

# Icon Colors
COLOR_SUN = (255, 210, 50)
COLOR_SUN_GLOW = (255, 170, 30)
COLOR_CLOUD_BASE = (200, 215, 230)
COLOR_CLOUD_SHADOW = (140, 160, 185)
COLOR_STORM_CLOUD = (80, 95, 115)
COLOR_RAIN_DROP = (72, 202, 228)
COLOR_SNOW_FLAKE = (235, 245, 255)
COLOR_LIGHTNING = (255, 230, 80)
COLOR_FOG_LINE = (160, 175, 195)

def draw_sun(surface, cx, cy, size=24):
    """Draw a glowing sun icon with radiating rays."""
    # Sun rays
    num_rays = 8
    ray_inner = size * 0.7
    ray_outer = size * 1.15
    for i in range(num_rays):
        angle = i * (2 * math.pi / num_rays)
        x1 = cx + math.cos(angle) * ray_inner
        y1 = cy + math.sin(angle) * ray_inner
        x2 = cx + math.cos(angle) * ray_outer
        y2 = cy + math.sin(angle) * ray_outer
        pygame.draw.line(surface, COLOR_SUN_GLOW, (x1, y1), (x2, y2), max(2, int(size * 0.12)))

    # Main core
    pygame.draw.circle(surface, COLOR_SUN, (cx, cy), int(size * 0.6))

def draw_cloud(surface, cx, cy, size=24, dark=False):
    """Draw a smooth volumetric cloud."""
    base_color = COLOR_STORM_CLOUD if dark else COLOR_CLOUD_BASE
    shadow_color = (60, 75, 95) if dark else COLOR_CLOUD_SHADOW

    r1 = int(size * 0.45)
    r2 = int(size * 0.6)
    r3 = int(size * 0.4)

    # Cloud shadow base
    pygame.draw.circle(surface, shadow_color, (cx - int(size * 0.5), cy + int(size * 0.1)), r1)
    pygame.draw.circle(surface, shadow_color, (cx, cy - int(size * 0.15)), r2)
    pygame.draw.circle(surface, shadow_color, (cx + int(size * 0.5), cy + int(size * 0.1)), r3)
    rect_shadow = pygame.Rect(cx - int(size * 0.7), cy, int(size * 1.4), int(size * 0.35))
    pygame.draw.rect(surface, shadow_color, rect_shadow, border_radius=int(size * 0.2))

    # Cloud main surface
    cy_off = -2
    pygame.draw.circle(surface, base_color, (cx - int(size * 0.5), cy + cy_off + int(size * 0.1)), r1)
    pygame.draw.circle(surface, base_color, (cx, cy + cy_off - int(size * 0.15)), r2)
    pygame.draw.circle(surface, base_color, (cx + int(size * 0.5), cy + cy_off + int(size * 0.1)), r3)
    rect_main = pygame.Rect(cx - int(size * 0.7), cy + cy_off + int(size * 0.1), int(size * 1.4), int(size * 0.3))
    pygame.draw.rect(surface, base_color, rect_main, border_radius=int(size * 0.15))

def draw_partly_cloudy(surface, cx, cy, size=24):
    """Draw sun behind cloud."""
    draw_sun(surface, cx + int(size * 0.35), cy - int(size * 0.35), size=int(size * 0.75))
    draw_cloud(surface, cx - int(size * 0.1), cy + int(size * 0.15), size=size)

def draw_rain(surface, cx, cy, size=24, heavy=False):
    """Draw cloud with rain drops."""
    draw_cloud(surface, cx, cy - int(size * 0.2), size=size)
    drops = [(-0.4, 0.4), (0.0, 0.45), (0.4, 0.4)] if not heavy else [(-0.5, 0.35), (-0.2, 0.5), (0.1, 0.35), (0.4, 0.5)]
    drop_len = int(size * 0.35)
    for dx, dy in drops:
        x1 = cx + int(dx * size)
        y1 = cy + int(dy * size)
        x2 = x1 - int(size * 0.1)
        y2 = y1 + drop_len
        pygame.draw.line(surface, COLOR_RAIN_DROP, (x1, y1), (x2, y2), max(2, int(size * 0.08)))

def draw_snow(surface, cx, cy, size=24):
    """Draw cloud with snow flakes."""
    draw_cloud(surface, cx, cy - int(size * 0.2), size=size)
    flakes = [(-0.4, 0.4), (0.0, 0.5), (0.4, 0.4)]
    for dx, dy in flakes:
        fx = cx + int(dx * size)
        fy = cy + int(dy * size)
        pygame.draw.circle(surface, COLOR_SNOW_FLAKE, (fx, fy), max(2, int(size * 0.09)))

def draw_thunderstorm(surface, cx, cy, size=24):
    """Draw dark storm cloud with yellow lightning bolt."""
    draw_cloud(surface, cx, cy - int(size * 0.25), size=size, dark=True)
    # Lightning bolt polygon
    lx = cx - int(size * 0.1)
    ly = cy + int(size * 0.1)
    pts = [
        (lx + int(size * 0.15), ly),
        (lx - int(size * 0.1), ly + int(size * 0.3)),
        (lx + int(size * 0.05), ly + int(size * 0.3)),
        (lx - int(size * 0.2), ly + int(size * 0.65)),
        (lx + int(size * 0.25), ly + int(size * 0.25)),
        (lx + int(size * 0.08), ly + int(size * 0.25))
    ]
    pygame.draw.polygon(surface, COLOR_LIGHTNING, pts)

def draw_fog(surface, cx, cy, size=24):
    """Draw horizontal fog bars."""
    for i in range(3):
        fy = cy - int(size * 0.3) + i * int(size * 0.3)
        w = int(size * 1.2) if i != 1 else int(size * 1.5)
        rect = pygame.Rect(cx - w // 2, fy, w, max(3, int(size * 0.12)))
        pygame.draw.rect(surface, COLOR_FOG_LINE, rect, border_radius=2)

def draw_refresh_icon(surface, cx, cy, size=16, color=(240, 243, 246)):
    """Draw circular refresh arrow icon."""
    r = int(size * 0.55)
    rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
    pygame.draw.arc(surface, color, rect, math.radians(45), math.radians(310), max(2, int(size * 0.12)))
    # Arrow head
    arrow_angle = math.radians(310)
    ax = cx + int(math.cos(arrow_angle) * r)
    ay = cy - int(math.sin(arrow_angle) * r)
    pts = [
        (ax, ay - int(size * 0.25)),
        (ax + int(size * 0.25), ay + int(size * 0.1)),
        (ax - int(size * 0.1), ay + int(size * 0.2))
    ]
    pygame.draw.polygon(surface, color, pts)

def render_weather_icon(surface, category, cx, cy, size=24):
    """Render category-based vector weather graphic."""
    cat = (category or "").upper()
    if "SUNNY" in cat or "CLEAR" in cat:
        draw_sun(surface, cx, cy, size)
    elif "PARTLY" in cat or "MAINLY" in cat:
        draw_partly_cloudy(surface, cx, cy, size)
    elif "RAIN_HEAVY" in cat or "THUNDER" in cat:
        draw_thunderstorm(surface, cx, cy, size)
    elif "RAIN" in cat or "DRIZZLE" in cat:
        draw_rain(surface, cx, cy, size)
    elif "SNOW" in cat:
        draw_snow(surface, cx, cy, size)
    elif "FOG" in cat:
        draw_fog(surface, cx, cy, size)
    else:
        # Default cloudy
        draw_cloud(surface, cx, cy, size)
