#!/usr/bin/env python3
"""
Raspberry Pi Smart Weather & News Dashboard (1280x720 Touch UI)
Clean, minimal dark cockpit theme with Live Animated Rain Radar.
"""

import sys
import os
import time
import json
import threading
import webbrowser
import pygame

from weather_service import WeatherService
from news_service import NewsService
from radar_service import RadarService
from fact_service import FactService
from weather_icons import render_weather_icon, draw_refresh_icon

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "location_name": "Default Location",
    "latitude": 51.5074,
    "longitude": -0.1278,
    "met_office_api_key": "",
    "refresh_interval_sec": 300,
    "fullscreen": True,
    "rss_feeds": {
        "bbc": "http://feeds.bbci.co.uk/news/rss.xml",
        "tvp": "https://www.tvp.info/tvp.info/rss+xml.php"
    }
}

# Color Palette - Clean Dark Cockpit
COLOR_BG = (11, 14, 20)           # #0B0E14
COLOR_PANEL = (22, 28, 38)        # #161C26
COLOR_PANEL_BORDER = (40, 52, 70) # #283446
COLOR_ACCENT = (0, 180, 216)      # #00B4D8
COLOR_TEXT_MAIN = (240, 243, 246) # #F0F3F6
COLOR_TEXT_MUTED = (140, 155, 170)# #8C9BAA
COLOR_GOLD = (242, 186, 73)       # #F2BA49
COLOR_HIGHLIGHT = (72, 202, 228)  # #48CAE4
COLOR_BBC = (235, 40, 50)         # BBC Red
COLOR_TVP = (245, 140, 30)        # TVP Amber/Orange
COLOR_GREEN = (46, 196, 182)      # Tech Green
COLOR_BUTTON_ACTIVE = (0, 119, 182)
COLOR_BUTTON_INACTIVE = (30, 40, 55)
COLOR_HOVER = (32, 42, 56)        # Hover background for interactive elements

class SmartDashboardApp:
    def __init__(self):
        self.config = self._load_config()
        
        # Pygame Initialization
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption(f"Pi Dashboard - {self.config.get('location_name', 'Default Location')}")

        self.width = 1280
        self.height = 720
        
        flags = pygame.DOUBLEBUF
        if self.config.get("fullscreen", False):
            flags |= pygame.FULLSCREEN
        
        self.screen = pygame.display.set_mode((self.width, self.height), flags)
        self.clock = pygame.time.Clock()

        # System Fonts
        self.font_title = pygame.font.SysFont("Helvetica", 26, bold=True)
        self.font_header = pygame.font.SysFont("Helvetica", 19, bold=True)
        self.font_body = pygame.font.SysFont("Arial", 16)
        self.font_small = pygame.font.SysFont("Arial", 13)
        self.font_temp_large = pygame.font.SysFont("Helvetica", 58, bold=True)
        self.font_fact_body = pygame.font.SysFont("Helvetica", 24)
        self.font_fact_source = pygame.font.SysFont("Arial", 16, italic=True)

        lat = self.config.get("latitude", 51.5074)
        lon = self.config.get("longitude", -0.1278)
        loc_name = self.config.get("location_name", "Default Location")

        # Services & State
        self.weather_service = WeatherService(
            latitude=lat,
            longitude=lon,
            location_name=loc_name,
            met_office_api_key=self.config.get("met_office_api_key", "")
        )
        self.news_service = NewsService(
            bbc_url=self.config.get("rss_feeds", {}).get("bbc", "http://feeds.bbci.co.uk/news/rss.xml"),
            tvp_url=self.config.get("rss_feeds", {}).get("tvp", "https://www.tvp.info/tvp.info/rss+xml.php")
        )
        self.radar_service = RadarService(
            latitude=lat,
            longitude=lon,
            zoom=self.config.get("radar_zoom", 8),
            color_scheme=self.config.get("radar_color_scheme", 2),
            smooth=self.config.get("radar_smooth", 1),
            min_alpha=self.config.get("radar_min_alpha", 85),
            canvas_w=600,
            canvas_h=580
        )
        self.fact_service = FactService()

        self.weather_data = {}
        self.bbc_articles = []
        self.tvp_articles = []
        
        self.active_tab = "COMBINED"  # Options: COMBINED, WEATHER, BBC, TVP, FACTS
        self.is_loading = True
        self.status_message = "Updating..."
        self.running = True
        
        # Track mouse activity to prevent startup false hover highlights
        self.mouse_active = False
        self.selected_forecast_day = None
        
        # Clickable zones list rebuilt every frame
        self.click_zones = []

        self.start_background_updates()

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    cfg = json.load(f)
                    merged = DEFAULT_CONFIG.copy()
                    merged.update(cfg)
                    return merged
            except Exception as e:
                print(f"Error loading {CONFIG_FILE}: {e}")
        return DEFAULT_CONFIG

    def start_background_updates(self):
        def update_task():
            while self.running:
                try:
                    self.status_message = "Updating..."
                    w_data = self.weather_service.fetch_weather()
                    bbc_data = self.news_service.fetch_bbc_news()
                    tvp_data = self.news_service.fetch_tvp_news()
                    self.radar_service.fetch_radar_data()
                    
                    self.weather_data = w_data
                    self.bbc_articles = bbc_data
                    self.tvp_articles = tvp_data
                    
                    self.is_loading = False
                    self.status_message = f"Updated {time.strftime('%H:%M')}"
                except Exception as e:
                    self.status_message = f"Error: {e}"
                
                for _ in range(self.config.get("refresh_interval_sec", 900)):
                    if not self.running:
                        break
                    time.sleep(1)

        t = threading.Thread(target=update_task, daemon=True)
        t.start()

    def trigger_manual_refresh(self):
        self.is_loading = True
        self.status_message = "Refreshing..."
        def refresh_task():
            w_data = self.weather_service.fetch_weather(force_refresh=True)
            bbc_data = self.news_service.fetch_bbc_news(force_refresh=True)
            tvp_data = self.news_service.fetch_tvp_news(force_refresh=True)
            self.radar_service.fetch_radar_data(force_refresh=True)
            
            self.weather_data = w_data
            self.bbc_articles = bbc_data
            self.tvp_articles = tvp_data
            
            self.is_loading = False
            self.status_message = f"Updated {time.strftime('%H:%M')}"

        t = threading.Thread(target=refresh_task, daemon=True)
        t.start()

    def draw_text(self, text, font, color, surface, x, y, align="left"):
        try:
            rendered = font.render(str(text), True, color)
        except Exception:
            clean_text = "".join(c for c in str(text) if ord(c) < 128)
            rendered = font.render(clean_text, True, color)
            
        rect = rendered.get_rect()
        if align == "left":
            rect.topleft = (x, y)
        elif align == "center":
            rect.center = (x, y)
        elif align == "right":
            rect.topright = (x, y)
        surface.blit(rendered, rect)
        return rect

    def draw_header(self):
        pygame.draw.rect(self.screen, COLOR_PANEL, (0, 0, self.width, 60))
        pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (0, 60), (self.width, 60), 2)

        # Clock & Date (Top Left)
        curr_time = time.strftime("%H:%M:%S")
        curr_date = time.strftime("%A, %d %b %Y")
        self.draw_text(curr_time, self.font_header, COLOR_GOLD, self.screen, 20, 10)
        self.draw_text(curr_date, self.font_small, COLOR_TEXT_MUTED, self.screen, 20, 34)

        # Status Indicator (Top Right)
        self.draw_text(self.status_message, self.font_small, COLOR_GREEN if not self.is_loading else COLOR_GOLD, self.screen, self.width - 55, 22, align="right")

        # Hidden Close Button Touch Target (Top Right Corner)
        close_rect = pygame.Rect(self.width - 45, 10, 35, 35)
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.mouse_active and pygame.mouse.get_focused() and close_rect.collidepoint(mouse_pos)
        
        if is_hover:
            pygame.draw.circle(self.screen, (210, 40, 50), close_rect.center, 15)
            self.draw_text("x", self.font_header, (255, 255, 255), self.screen, close_rect.centerx, close_rect.centery - 1, align="center")
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            self.draw_text("x", self.font_small, (60, 75, 95), self.screen, close_rect.centerx, close_rect.centery - 1, align="center")
            
        self.click_zones.append((close_rect, "CLOSE", None))

    def draw_nav_tabs(self):
        nav_y = 65
        nav_height = 45
        pygame.draw.rect(self.screen, COLOR_BG, (0, nav_y, self.width, nav_height))

        tabs = [
            ("COMBINED", "Combined View"),
            ("WEATHER", "Weather & Radar"),
            ("BBC", "BBC News"),
            ("TVP", "TVP Info"),
            ("FACTS", "💡 Fun Facts"),
            ("REFRESH", "Refresh")
        ]

        tab_width = 190
        start_x = 20
        spacing = 15
        
        mouse_pos = pygame.mouse.get_pos()

        for idx, (tab_key, label) in enumerate(tabs):
            x = start_x + idx * (tab_width + spacing)
            is_active = (self.active_tab == tab_key)
            rect = pygame.Rect(x, nav_y + 4, tab_width, nav_height - 8)
            
            is_hover = self.mouse_active and pygame.mouse.get_focused() and rect.collidepoint(mouse_pos)
            
            bg_color = COLOR_BUTTON_ACTIVE if is_active else COLOR_BUTTON_INACTIVE
            if tab_key == "REFRESH":
                bg_color = (40, 70, 90)
            elif tab_key == "FACTS" and is_active:
                bg_color = (180, 110, 20)
                
            if is_hover and not is_active:
                bg_color = (min(255, bg_color[0]+20), min(255, bg_color[1]+20), min(255, bg_color[2]+20))

            pygame.draw.rect(self.screen, bg_color, rect, border_radius=6)
            pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, rect, width=1, border_radius=6)

            text_color = COLOR_TEXT_MAIN if is_active else COLOR_TEXT_MUTED
            
            if tab_key == "REFRESH":
                draw_refresh_icon(self.screen, rect.centerx - 40, rect.centery, size=18, color=COLOR_TEXT_MAIN)
                self.draw_text(label, self.font_header, text_color, self.screen, rect.centerx + 10, rect.centery, align="center")
            else:
                self.draw_text(label, self.font_header, text_color, self.screen, rect.centerx, rect.centery, align="center")
                
            self.click_zones.append((rect, "TAB", tab_key))

    def draw_weather_card(self, rect):
        pygame.draw.rect(self.screen, COLOR_PANEL, rect, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, rect, width=2, border_radius=10)

        # Clean Location Title
        self.draw_text(self.weather_data.get("location", "Default Location"), self.font_title, COLOR_TEXT_MAIN, self.screen, rect.x + 20, rect.y + 22)

        # Data Source Badge (Top Right of Weather Card)
        source_name = self.weather_data.get("source", "Unknown")
        self.draw_text(f"Data: {source_name}", self.font_small, COLOR_TEXT_MUTED, self.screen, rect.right - 20, rect.y + 26, align="right")

        # Main Temperature Display & Vector Icon
        temp = self.weather_data.get("temp", "--")
        feels_like = self.weather_data.get("feels_like", "--")
        desc = self.weather_data.get("description", "Loading...")
        category = self.weather_data.get("category", "UNKNOWN")

        temp_rect = self.draw_text(f"{temp} °C", self.font_temp_large, COLOR_GOLD, self.screen, rect.x + 20, rect.y + 68)

        # Render Weather Vector Graphics Icon right next to Temperature
        icon_cx = temp_rect.right + 45
        icon_cy = rect.y + 100
        render_weather_icon(self.screen, category, icon_cx, icon_cy, size=30)

        # Condition & Feels Like
        text_x = icon_cx + 45
        self.draw_text(desc, self.font_header, COLOR_HIGHLIGHT, self.screen, text_x, rect.y + 86)
        self.draw_text(f"Feels like {feels_like} °C", self.font_body, COLOR_TEXT_MUTED, self.screen, text_x, rect.y + 112)

        # Weather Details Grid
        details_y = rect.y + 160
        wind_sp = self.weather_data.get("wind_speed_mph", "--")
        wind_dir = self.weather_data.get("wind_direction", "N/A")
        humidity = self.weather_data.get("humidity", "--")
        precip = self.weather_data.get("precipitation", 0.0)
        
        forecast_0 = self.weather_data.get("forecast", [{}])[0] if self.weather_data.get("forecast") else {}
        sunrise = self.weather_data.get("sunrise") or forecast_0.get("sunrise", "--")
        sunset = self.weather_data.get("sunset") or forecast_0.get("sunset", "--")

        # Left Column
        self.draw_text(f"Wind: {wind_sp} mph ({wind_dir})", self.font_body, COLOR_TEXT_MAIN, self.screen, rect.x + 20, details_y)
        self.draw_text(f"Humidity: {humidity}%", self.font_body, COLOR_TEXT_MAIN, self.screen, rect.x + 20, details_y + 25)
        self.draw_text(f"Precipitation: {precip} mm", self.font_body, COLOR_TEXT_MAIN, self.screen, rect.x + 20, details_y + 50)

        # Right Column
        self.draw_text(f"Sunrise: {sunrise}", self.font_body, COLOR_TEXT_MAIN, self.screen, rect.x + 290, details_y)
        self.draw_text(f"Sunset: {sunset}", self.font_body, COLOR_TEXT_MAIN, self.screen, rect.x + 290, details_y + 25)

        # 5-Day Forecast Row
        forecast_y = rect.y + 250
        self.draw_text("5-DAY OUTLOOK", self.font_header, COLOR_ACCENT, self.screen, rect.x + 20, forecast_y)
        
        forecast = self.weather_data.get("forecast", [])
        box_w = (rect.width - 40 - (len(forecast) - 1) * 10) // max(1, len(forecast)) if forecast else 100
        
        mouse_pos = pygame.mouse.get_pos()
        for idx, day in enumerate(forecast):
            f_x = rect.x + 20 + idx * (box_w + 10)
            f_rect = pygame.Rect(f_x, forecast_y + 28, box_w, 145)
            
            is_hover = self.mouse_active and pygame.mouse.get_focused() and f_rect.collidepoint(mouse_pos)
            bg_color = COLOR_HOVER if is_hover and not self.selected_forecast_day else COLOR_BG
            
            pygame.draw.rect(self.screen, bg_color, f_rect, border_radius=6)
            pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, f_rect, width=1, border_radius=6)
            
            if is_hover and not self.selected_forecast_day:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)

            # Day Name & UK Date
            self.draw_text(day.get("day_name", "Day"), self.font_header, COLOR_GOLD, self.screen, f_rect.centerx, f_rect.y + 8, align="center")
            self.draw_text(day.get("date_uk", ""), self.font_small, COLOR_TEXT_MUTED, self.screen, f_rect.centerx, f_rect.y + 26, align="center")
            
            # Vector Weather Icon inside forecast box
            f_desc = day.get("desc", "")
            render_weather_icon(self.screen, f_desc, f_rect.centerx, f_rect.y + 54, size=18)

            # Max / Min Temp
            self.draw_text(f"{day.get('temp_max', 0)}° / {day.get('temp_min', 0)}°", self.font_body, COLOR_TEXT_MAIN, self.screen, f_rect.centerx, f_rect.y + 82, align="center")
            # Rain Probability
            self.draw_text(f"Rain {day.get('pop', 0)}%", self.font_small, COLOR_HIGHLIGHT, self.screen, f_rect.centerx, f_rect.y + 114, align="center")
            
            self.click_zones.append((f_rect, "FORECAST_DAY", idx))

    def draw_news_panel(self, rect, title, articles, tag_color):
        pygame.draw.rect(self.screen, COLOR_PANEL, rect, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, rect, width=2, border_radius=10)

        tag_rect = pygame.Rect(rect.x + 20, rect.y + 15, 12, 24)
        pygame.draw.rect(self.screen, tag_color, tag_rect, border_radius=3)
        self.draw_text(title, self.font_header, COLOR_TEXT_MAIN, self.screen, rect.x + 40, rect.y + 15)

        start_y = rect.y + 48
        item_h = 74
        max_items = (rect.height - 45) // item_h
        
        mouse_pos = pygame.mouse.get_pos()

        for idx, item in enumerate(articles[:max_items]):
            item_y = start_y + idx * item_h
            item_rect = pygame.Rect(rect.x + 5, item_y, rect.width - 10, item_h)
            
            # Interactive Hover Effect
            is_hover = self.mouse_active and pygame.mouse.get_focused() and item_rect.collidepoint(mouse_pos)
            if is_hover and item.get("link"):
                pygame.draw.rect(self.screen, COLOR_HOVER, item_rect, border_radius=6)
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            
            # Separator line if not hovered
            if not is_hover and idx < max_items - 1:
                pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (rect.x + 20, item_y + item_h - 2), (rect.x + rect.width - 20, item_y + item_h - 2), 1)
            
            pygame.draw.circle(self.screen, tag_color, (rect.x + 28, item_y + 16), 4)

            # Dynamic text length calculation based on landscape panel width
            max_title_len = max(60, int((rect.width - 55) / 7.5))
            max_desc_len = max(80, int((rect.width - 180) / 6.0))

            art_title = item.get("title", "")
            if len(art_title) > max_title_len:
                art_title = art_title[:max_title_len - 3] + "..."
            
            # Change title color on hover
            title_color = COLOR_GOLD if is_hover else COLOR_TEXT_MAIN
            self.draw_text(art_title, self.font_body, title_color, self.screen, rect.x + 42, item_y + 5)

            desc = item.get("description", "")
            if len(desc) > max_desc_len:
                desc = desc[:max_desc_len - 3] + "..."
            self.draw_text(desc, self.font_small, COLOR_TEXT_MUTED, self.screen, rect.x + 42, item_y + 27)

            pub_date = item.get("pub_date", "")
            if pub_date:
                pub_short = pub_date[:22]
                self.draw_text(pub_short, self.font_small, COLOR_HIGHLIGHT, self.screen, rect.x + rect.width - 20, item_y + 48, align="right")
                
            # Add to clickable zones
            if item.get("link"):
                self.click_zones.append((item_rect, "LINK", item.get("link")))

    def draw_combined_view(self):
        content_rect = pygame.Rect(20, 120, self.width - 40, self.height - 140)

        weather_rect = pygame.Rect(content_rect.x, content_rect.y, 560, content_rect.height)
        self.draw_weather_card(weather_rect)

        right_x = content_rect.x + 580
        right_w = content_rect.width - 580
        split_h = (content_rect.height - 15) // 2

        bbc_rect = pygame.Rect(right_x, content_rect.y, right_w, split_h)
        self.draw_news_panel(bbc_rect, "BBC NEWS (UK)", self.bbc_articles, COLOR_BBC)

        tvp_rect = pygame.Rect(right_x, content_rect.y + split_h + 15, right_w, split_h)
        self.draw_news_panel(tvp_rect, "TVP.INFO (POLAND)", self.tvp_articles, COLOR_TVP)

    def draw_weather_view(self):
        content_rect = pygame.Rect(20, 120, self.width - 40, self.height - 140)

        # Left Column: Weather Station Card
        weather_rect = pygame.Rect(content_rect.x, content_rect.y, 610, content_rect.height)
        self.draw_weather_card(weather_rect)

        # Right Column: Live Animated Rain Radar Map
        radar_rect = pygame.Rect(content_rect.x + 630, content_rect.y, 610, content_rect.height)
        self.radar_service.draw_radar_widget(self.screen, radar_rect)

    def draw_full_news_view(self, title, articles, tag_color):
        content_rect = pygame.Rect(20, 120, self.width - 40, self.height - 140)
        self.draw_news_panel(content_rect, title, articles, tag_color)

    def trigger_new_fact(self):
        """Fetch a new fact in a background thread."""
        def task():
            self.status_message = "Finding fact..."
            self.fact_service.fetch_new_fact()
            self.status_message = f"Updated {time.strftime('%H:%M')}"
        threading.Thread(target=task, daemon=True).start()

    def draw_facts_view(self):
        content_rect = pygame.Rect(20, 120, self.width - 40, self.height - 140)
        
        # Outer Card Container
        pygame.draw.rect(self.screen, COLOR_PANEL, content_rect, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, content_rect, width=2, border_radius=12)

        fact = self.fact_service.current_fact

        # Header Badge & Title
        tag_text = fact.get("tag", "💡 GENERAL KNOWLEDGE")
        self.draw_text(tag_text, self.font_header, COLOR_GOLD, self.screen, content_rect.x + 35, content_rect.y + 35)

        source_text = fact.get("source", "Knowledge Feed")
        self.draw_text(f"Source: {source_text}", self.font_fact_source, COLOR_HIGHLIGHT, self.screen, content_rect.right - 35, content_rect.y + 38, align="right")

        # Horizontal separator line
        pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (content_rect.x + 35, content_rect.y + 75), (content_rect.right - 35, content_rect.y + 75), 1)

        # Fact Content Box with decorative card
        quote_rect = pygame.Rect(content_rect.x + 35, content_rect.y + 105, content_rect.width - 70, 310)
        pygame.draw.rect(self.screen, (15, 20, 28), quote_rect, border_radius=10)
        pygame.draw.rect(self.screen, (35, 48, 65), quote_rect, width=1, border_radius=10)

        # Large quotation mark icon
        font_quote = pygame.font.SysFont("Helvetica", 72, bold=True)
        self.draw_text("“", font_quote, (50, 70, 95), self.screen, quote_rect.x + 25, quote_rect.y + 20)

        # Multi-line wrapped text for fact
        fact_text = fact.get("text", "Loading general knowledge fact...")
        words = fact_text.split()
        lines = []
        current_line = []
        max_chars_per_line = 65

        for word in words:
            if sum(len(w) for w in current_line) + len(current_line) + len(word) <= max_chars_per_line:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))

        # Render lines centered vertically in quote box
        y_text_start = quote_rect.y + (quote_rect.height - (len(lines) * 40)) // 2 + 10
        for line_idx, line in enumerate(lines):
            self.draw_text(line, self.font_fact_body, COLOR_TEXT_MAIN, self.screen, quote_rect.centerx, y_text_start + line_idx * 40, align="center")

        # Action Button: "✨ Generate New Fact"
        btn_w, btn_h = 320, 52
        btn_rect = pygame.Rect(content_rect.centerx - btn_w // 2, content_rect.bottom - 75, btn_w, btn_h)
        
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.mouse_active and pygame.mouse.get_focused() and btn_rect.collidepoint(mouse_pos)
        btn_bg = (210, 130, 25) if is_hover else (180, 105, 18)

        pygame.draw.rect(self.screen, btn_bg, btn_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_GOLD, btn_rect, width=2, border_radius=8)

        if is_hover:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)

        btn_label = "⏳ Fetching Fact..." if self.fact_service.is_fetching else "✨ Generate New Fact"
        self.draw_text(btn_label, self.font_header, (255, 255, 255), self.screen, btn_rect.centerx, btn_rect.centery, align="center")

        self.click_zones.append((btn_rect, "NEW_FACT", None))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEMOTION:
                self.mouse_active = True
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    self.running = False
                elif event.key == pygame.K_f:
                    pygame.display.toggle_fullscreen()
                elif event.key == pygame.K_r:
                    self.trigger_manual_refresh()
                elif event.key in (pygame.K_SPACE, pygame.K_n):
                    if self.active_tab == "FACTS":
                        self.trigger_new_fact()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                # Evaluate from top-most to bottom-most (reverse order of drawing)
                for rect, action_type, action_data in reversed(self.click_zones):
                    if rect.collidepoint(pos):
                        if action_type == "TAB":
                            if action_data == "REFRESH":
                                self.trigger_manual_refresh()
                            else:
                                self.active_tab = action_data
                        elif action_type == "NEW_FACT":
                            self.trigger_new_fact()
                        elif action_type == "LINK":
                            try:
                                webbrowser.open(action_data)
                            except Exception as e:
                                print(f"Could not open link: {e}")
                        elif action_type == "CLOSE":
                            self.running = False
                        elif action_type == "FORECAST_DAY":
                            self.selected_forecast_day = action_data
                        elif action_type == "CLOSE_POPUP":
                            self.selected_forecast_day = None
                        elif action_type == "NONE":
                            pass # Consume click but do nothing
                        break # Stop evaluating zones underneath

    def draw_forecast_popup(self):
        if self.selected_forecast_day is None:
            return
            
        forecast_list = self.weather_data.get("forecast", [])
        if self.selected_forecast_day >= len(forecast_list):
            self.selected_forecast_day = None
            return
            
        day_data = forecast_list[self.selected_forecast_day]
        
        # 1. Draw semi-transparent dark overlay over entire screen
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) # Dark transparent
        self.screen.blit(overlay, (0, 0))
        
        # Click outside to close
        self.click_zones.append((pygame.Rect(0, 0, self.width, self.height), "CLOSE_POPUP", None))
        
        # 2. Draw Popup Card in center
        card_w, card_h = 560, 520
        card_rect = pygame.Rect((self.width - card_w) // 2, (self.height - card_h) // 2, card_w, card_h)
        pygame.draw.rect(self.screen, COLOR_PANEL, card_rect, border_radius=15)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, card_rect, width=2, border_radius=15)
        
        # Prevent clicks inside card from closing it (clicking outside closes popup)
        inner_card_zone = pygame.Rect(card_rect.x, card_rect.y, card_rect.width, card_rect.height)
        self.click_zones.append((inner_card_zone, "NONE", None))
        
        # Content layout
        day_date_str = f"{day_data.get('day_name', '')}, {day_data.get('date_uk', day_data.get('date', ''))}"
        self.draw_text(day_date_str, self.font_title, COLOR_GOLD, self.screen, card_rect.centerx, card_rect.y + 30, align="center")
        
        # Large Icon
        render_weather_icon(self.screen, day_data.get('desc', ''), card_rect.centerx, card_rect.y + 100, size=40)
        self.draw_text(day_data.get('desc', ''), self.font_header, COLOR_HIGHLIGHT, self.screen, card_rect.centerx, card_rect.y + 155, align="center")
        
        # Grid details
        y_start = card_rect.y + 205
        x_left = card_rect.x + 40
        x_right = card_rect.centerx + 30
        
        # Left column
        self.draw_text(f"High Temp: {day_data.get('temp_max', 0)} °C", self.font_body, COLOR_TEXT_MAIN, self.screen, x_left, y_start)
        self.draw_text(f"Low Temp: {day_data.get('temp_min', 0)} °C", self.font_body, COLOR_TEXT_MAIN, self.screen, x_left, y_start + 35)
        self.draw_text(f"Rain Chance: {day_data.get('pop', 0)} %", self.font_body, COLOR_TEXT_MAIN, self.screen, x_left, y_start + 70)
        self.draw_text(f"Rain Amount: {day_data.get('precip_sum', 0.0)} mm", self.font_body, COLOR_TEXT_MAIN, self.screen, x_left, y_start + 105)
        self.draw_text(f"UV Index: {day_data.get('uv_index', 0)}", self.font_body, COLOR_TEXT_MAIN, self.screen, x_left, y_start + 140)
        
        # Right column
        self.draw_text(f"Wind Max: {day_data.get('wind_max_mph', 0)} mph", self.font_body, COLOR_TEXT_MAIN, self.screen, x_right, y_start)
        self.draw_text(f"Wind Dir: {day_data.get('wind_dir', 'N/A')}", self.font_body, COLOR_TEXT_MAIN, self.screen, x_right, y_start + 35)
        self.draw_text(f"Sunrise: {day_data.get('sunrise', '--')}", self.font_body, COLOR_TEXT_MAIN, self.screen, x_right, y_start + 70)
        self.draw_text(f"Sunset: {day_data.get('sunset', '--')}", self.font_body, COLOR_TEXT_MAIN, self.screen, x_right, y_start + 105)

        # Hourly Breakdown
        hourly = day_data.get("hourly", [])
        if hourly:
            pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (card_rect.x + 30, card_rect.y + 395), (card_rect.right - 30, card_rect.y + 395), 1)
            num_hours = len(hourly)
            if num_hours > 0:
                spacing = (card_rect.width - 60) / num_hours
                start_x = card_rect.x + 30 + (spacing / 2)
                for h_idx, h_data in enumerate(hourly):
                    h_x = start_x + (h_idx * spacing)
                    self.draw_text(h_data.get("hour", "00:00"), self.font_small, COLOR_TEXT_MUTED, self.screen, h_x, card_rect.y + 415, align="center")
                    render_weather_icon(self.screen, h_data.get("desc", ""), h_x, card_rect.y + 448, size=15)
                    self.draw_text(f"{h_data.get('temp', 0)}°", self.font_body, COLOR_TEXT_MAIN, self.screen, h_x, card_rect.y + 482, align="center")

    def run(self):
        while self.running:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            self.click_zones = []
            
            # Update animation frame timer for Live Rain Radar
            self.radar_service.update_animation()

            self.screen.fill(COLOR_BG)
            self.draw_header()
            self.draw_nav_tabs()

            if self.active_tab == "COMBINED":
                self.draw_combined_view()
            elif self.active_tab == "WEATHER":
                self.draw_weather_view()
            elif self.active_tab == "BBC":
                self.draw_full_news_view("BBC NEWS HEADLINES (UK)", self.bbc_articles, COLOR_BBC)
            elif self.active_tab == "TVP":
                self.draw_full_news_view("TVP.INFO HEADLINES (POLAND)", self.tvp_articles, COLOR_TVP)
            elif self.active_tab == "FACTS":
                self.draw_facts_view()

            self.draw_forecast_popup()
            self.handle_events()
            
            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()

if __name__ == "__main__":
    app = SmartDashboardApp()
    app.run()
