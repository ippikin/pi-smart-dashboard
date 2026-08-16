#!/usr/bin/env python3
"""
Live Animated Rain Radar Service for UK Locations.
Fetches CartoDB base map tiles & RainViewer precipitation overlays.
Supports smooth digital scaling for zoom levels above RainViewer's max limit (Zoom 7).
"""

import math
import time
import io
import json
import logging
import urllib.request
import pygame

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RadarService")

def latlon_to_tile(lat, lon, zoom):
    """Convert Latitude/Longitude to Mercator Tile Coordinates (x, y) and pixel offsets within tile."""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x_exact = (lon + 180.0) / 360.0 * n
    y_exact = (1.0 - math.log(math.tan(lat_rad) + (1.0 / math.cos(lat_rad))) / math.pi) / 2.0 * n
    
    xtile = int(x_exact)
    ytile = int(y_exact)
    
    # Sub-tile pixel offset (0..255)
    px = int((x_exact - xtile) * 256)
    py = int((y_exact - ytile) * 256)
    
    return xtile, ytile, px, py

class RadarService:
    def __init__(self, latitude=51.5074, longitude=-0.1278, zoom=8, color_scheme=2, smooth=1, min_alpha=85, canvas_w=580, canvas_h=445):
        self.latitude = latitude
        self.longitude = longitude
        self.zoom = zoom
        self.color_scheme = color_scheme
        self.smooth = smooth
        self.min_alpha = min_alpha  # Filter out radar pixels with alpha below this threshold (suppressing faint non-precipitating clouds)
        
        # RainViewer API maximum supported tile zoom is 7
        self.tile_zoom = min(zoom, 7)
        self.scale_factor = 2.0 ** (zoom - self.tile_zoom)
        
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h

        self.center_x, self.center_y, self.target_px, self.target_py = latlon_to_tile(latitude, longitude, self.tile_zoom)

        self.base_map_surface = None
        self.radar_frames = []  # List of {"time_str": "HH:MM", "surface": pygame.Surface}
        self.current_frame_idx = 0
        self.last_frame_swap = 0
        self.frame_delay_sec = 0.6  # 600ms per frame

        self.is_fetching = False
        self.last_update_time = 0
        self.cache_ttl_sec = 600  # Refresh radar data every 10 mins

    def _filter_low_intensity(self, surf):
        """
        Zero out low-intensity cloud, virga, and faint drizzle echoes.
        Filters by alpha threshold as well as low-reflectivity blue/cyan cloud bands.
        """
        if self.min_alpha <= 0:
            return surf
        try:
            w, h = surf.get_size()
            raw = pygame.image.tobytes(surf, "RGBA")
            arr = bytearray(raw)
            
            # Sensitivity scale based on min_alpha (0..255)
            # Higher min_alpha (e.g. 100-200) aggressively filters out faint blue/cyan drizzle/clouds
            filter_clouds = self.min_alpha >= 80
            filter_light_drizzle = self.min_alpha >= 140
            
            for i in range(0, len(arr), 4):
                r, g, b, a = arr[i], arr[i+1], arr[i+2], arr[i+3]
                if a == 0:
                    continue
                
                # 1. Standard Alpha transparency check
                if a < self.min_alpha:
                    arr[i+3] = 0
                    continue
                
                # 2. Spectral reflectivity filter for low-dBZ blue/cyan cloud echoes (which are fully opaque A=255)
                # Faint cloud/virga tier: Cyan (B > 180, G > 130, R < 140) and dark muted blues (R == 0, G < 120, B > 100)
                if filter_clouds:
                    if (b > 180 and g > 130 and r < 140) or (r == 0 and g < 120 and b > 100):
                        arr[i+3] = 0
                        continue
                
                # Light drizzle tier: Moderate blues (B > 150, R < 80, G < 170)
                if filter_light_drizzle:
                    if b > 150 and r < 80 and g < 170:
                        arr[i+3] = 0
                        continue
                        
            filtered = pygame.image.frombytes(bytes(arr), (w, h), "RGBA")
            if pygame.display.get_surface():
                filtered = filtered.convert_alpha()
            return filtered
        except Exception as e:
            logger.warning(f"Error filtering radar intensity: {e}")
            return surf

    def _fetch_url_bytes(self, url):
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
        return urllib.request.urlopen(req, timeout=8).read()

    def fetch_base_map(self):
        """Fetch and stitch a 3x3 tile grid for the base dark map centered on target coordinates."""
        if self.base_map_surface:
            return self.base_map_surface

        grid_surf = pygame.Surface((768, 768))
        grid_surf.fill((15, 20, 28))

        # 3x3 tiles centered on center_x, center_y at tile_zoom
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                tx = self.center_x + dx
                ty = self.center_y + dy
                url = f"https://basemaps.cartocdn.com/dark_all/{self.tile_zoom}/{tx}/{ty}.png"
                try:
                    raw_data = self._fetch_url_bytes(url)
                    tile_surf = pygame.image.load(io.BytesIO(raw_data))
                    if pygame.display.get_surface():
                        tile_surf = tile_surf.convert()
                    grid_surf.blit(tile_surf, ((dx + 1) * 256, (dy + 1) * 256))
                except Exception as e:
                    logger.warning(f"Failed to fetch base map tile {tx},{ty}: {e}")

        # Target point on the 768x768 grid: tile (0,0) starts at grid (256, 256)
        center_pixel_x = 256 + self.target_px
        center_pixel_y = 256 + self.target_py

        # Effective unscaled crop window size
        crop_w = max(100, int(self.canvas_w / self.scale_factor))
        crop_h = max(100, int(self.canvas_h / self.scale_factor))

        crop_x = max(0, min(768 - crop_w, center_pixel_x - crop_w // 2))
        crop_y = max(0, min(768 - crop_h, center_pixel_y - crop_h // 2))

        crop_rect = pygame.Rect(crop_x, crop_y, crop_w, crop_h)
        cropped_surf = pygame.Surface((crop_w, crop_h))
        cropped_surf.blit(grid_surf, (0, 0), crop_rect)

        # Smooth scale cropped area to target canvas dimensions
        scaled_surf = pygame.transform.smoothscale(cropped_surf, (self.canvas_w, self.canvas_h))

        # Store crop offset and target pixel coords on scaled screen
        self.crop_offset_x = crop_x
        self.crop_offset_y = crop_y
        self.crop_w = crop_w
        self.crop_h = crop_h
        self.target_screen_x = int((center_pixel_x - crop_x) * self.scale_factor)
        self.target_screen_y = int((center_pixel_y - crop_y) * self.scale_factor)

        self.base_map_surface = scaled_surf
        return self.base_map_surface

    def fetch_radar_data(self, force_refresh=False):
        """Fetch latest precipitation radar timestamps and stitch radar animation frames."""
        now = time.time()
        if not force_refresh and self.radar_frames and (now - self.last_update_time < self.cache_ttl_sec):
            return

        if self.is_fetching:
            return

        self.is_fetching = True
        try:
            self.fetch_base_map()

            # Query RainViewer API
            meta_raw = self._fetch_url_bytes("https://api.rainviewer.com/public/weather-maps.json")
            meta = json.loads(meta_raw.decode("utf-8"))

            host = meta.get("host", "https://tilecache.rainviewer.com")
            past_frames = meta.get("radar", {}).get("past", [])
            
            # Select last 6 frames (~1 hour of animation)
            recent_frames = past_frames[-6:] if len(past_frames) >= 6 else past_frames
            
            new_frames = []
            for item in recent_frames:
                path = item.get("path")
                ts = item.get("time", 0)
                time_str = time.strftime("%H:%M", time.localtime(ts)) if ts else "LIVE"

                grid_surf = pygame.Surface((768, 768), pygame.SRCALPHA)
                
                # Fetch 3x3 radar tile grid at tile_zoom (supported by RainViewer)
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        tx = self.center_x + dx
                        ty = self.center_y + dy
                        tile_url = f"{host}{path}/256/{self.tile_zoom}/{tx}/{ty}/{self.color_scheme}/{self.smooth}_1.png"
                        try:
                            t_raw = self._fetch_url_bytes(tile_url)
                            t_surf = pygame.image.load(io.BytesIO(t_raw))
                            if pygame.display.get_surface():
                                t_surf = t_surf.convert_alpha()
                            grid_surf.blit(t_surf, ((dx + 1) * 256, (dy + 1) * 256))
                        except Exception:
                            pass

                # Crop to match base map crop rect
                crop_rect = pygame.Rect(self.crop_offset_x, self.crop_offset_y, self.crop_w, self.crop_h)
                cropped_frame = pygame.Surface((self.crop_w, self.crop_h), pygame.SRCALPHA)
                cropped_frame.blit(grid_surf, (0, 0), crop_rect)

                # Filter out faint, non-precipitating cloud/virga pixels
                filtered_frame = self._filter_low_intensity(cropped_frame)

                # Smooth scale to canvas dimensions
                frame_surf = pygame.transform.smoothscale(filtered_frame, (self.canvas_w, self.canvas_h))

                new_frames.append({
                    "time_str": time_str,
                    "surface": frame_surf
                })

            if new_frames:
                self.radar_frames = new_frames
                self.last_update_time = now
                self.current_frame_idx = 0
        except Exception as e:
            logger.warning(f"Error updating radar frames: {e}")
        finally:
            self.is_fetching = False

    def update_animation(self):
        """Advance animation frame timer."""
        if not self.radar_frames:
            return
        now = time.time()
        if now - self.last_frame_swap >= self.frame_delay_sec:
            self.current_frame_idx = (self.current_frame_idx + 1) % len(self.radar_frames)
            self.last_frame_swap = now

    def draw_radar_widget(self, surface, rect):
        """Render the complete animated rain radar widget into the given pygame rect."""
        pygame.draw.rect(surface, (22, 28, 38), rect, border_radius=10)
        pygame.draw.rect(surface, (40, 52, 70), rect, width=2, border_radius=10)

        # 1. Base Map Layer
        if self.base_map_surface:
            surface.blit(self.base_map_surface, rect.topleft)
        else:
            pygame.draw.rect(surface, (15, 20, 28), rect, border_radius=10)

        # 2. Animated Rain Radar Layer
        time_label = "LOADING RADAR..."
        if self.radar_frames:
            frame = self.radar_frames[self.current_frame_idx]
            surface.blit(frame["surface"], rect.topleft)
            time_label = f"RADAR: {frame['time_str']}"

        # 3. Location Target Marker over Coordinates
        if hasattr(self, "target_screen_x"):
            tx = rect.x + self.target_screen_x
            ty = rect.y + self.target_screen_y
            
            # Pulse ring
            pulse_r = 10 + int((time.time() * 4) % 6)
            pygame.draw.circle(surface, (255, 60, 60), (tx, ty), pulse_r, width=2)
            # Center dot
            pygame.draw.circle(surface, (0, 220, 255), (tx, ty), 5)
            pygame.draw.circle(surface, (255, 255, 255), (tx, ty), 2)

        # 4. Header Bar
        font_header = pygame.font.SysFont("Helvetica", 14, bold=True)
        
        # Title
        t_surf = font_header.render("LIVE RAIN RADAR", True, (0, 210, 255))
        surface.blit(t_surf, (rect.x + 12, rect.y + 10))
        
        # Time badge
        time_surf = font_header.render(time_label, True, (255, 200, 50))
        surface.blit(time_surf, (rect.right - time_surf.get_width() - 12, rect.y + 10))
