# 🌤️ Raspberry Pi Smart Weather & News Dashboard

A high-density **7-Inch Raspberry Pi Touch Display 2** (1280x720) and **Mac Desktop Emulator** dashboard application.

Features:
- 🌤️ **Local Weather Station**: Official Met Office Weather DataHub integration with high-accuracy Open-Meteo fallback.
- 🌧️ **Live Animated Rain Radar Map**: Real-time precipitation radar animation with dark theme map tiles, smooth regional zoom (level 8), and target location marker.
- 🎯 **Reflectivity & Cloud Filtering**: Smart spectral and alpha thresholding to suppress non-precipitating clouds/virga so only genuine drizzle and active rain bands are rendered.
- ⏱️ **Interactive 5-Day & Hourly Outlook**: Tap any forecast day to view an interactive popup with detailed metrics and an hour-by-hour forecast breakdown.
- 🌅 **Astronomy Integration**: Live sunrise & sunset times integrated across current weather cards and 5-day forecast modals.
- 🏷️ **Data Source Indicator**: Dynamic badge indicating live weather provider (`Met Office DataHub` vs `Open-Meteo`).
- 📰 **BBC News Headlines**: Real-time RSS news ticker for UK news.
- 🇵🇱 **TVP.info News Headlines**: Real-time RSS news ticker for Polish news.
- 💡 **UK General Knowledge & Wikipedia Live Feeds**: Dedicated tab featuring live Wikipedia "Did You Know...", "On This Day in History", dynamic UK category explorers (British Inventions, Castles, Geography, Heritage, Shropshire), and curated British facts with an interactive touch button to generate new facts on demand.
- 🔒 **Privacy & Config Protection**: `config.json` stores your location and credentials locally and is strictly ignored by `.gitignore`.
- 🖥️ **Cross-Platform**: Runs seamlessly in windowed or fullscreen mode on macOS and Raspberry Pi OS.

---

## 🚀 Quick Start (Mac Emulation)

1. Make sure Python 3 and dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python3 gui_dashboard.py
   ```

## 🎮 Controls & Touch Shortcuts

- **Touch / Click Tabs**: Toggle between `Combined View`, `Weather & Radar`, `BBC News`, `TVP Info`, `Fun Facts`, and `Refresh`.
- **`Generate New Fact` / `Space` / `N` key**: Fetch and display a fresh general knowledge fact or Wikipedia summary.
- **Forecast Days**: Tap any day in the 5-day forecast row to open an interactive detailed weather modal with an hour-by-hour breakdown.
- **`R` key**: Manually trigger live news & weather refresh.
- **`F` key**: Toggle Fullscreen.
- **`ESC` / `Q` key**: Quit dashboard.

---

## 🔒 Configuration (`config.json`)

Your local configuration stores your location settings, API keys, and radar tuning:

```json
{
  "location_name": "City Name",
  "latitude": 0.0,
  "longitude": 0.0,
  "met_office_api_key": "YOUR_MET_OFFICE_DATAHUB_API_KEY",
  "refresh_interval_sec": 300,
  "fullscreen": true,
  "radar_zoom": 8,
  "radar_min_alpha": 85,
  "radar_smooth": 1,
  "radar_color_scheme": 2,
  "rss_feeds": {
    "bbc": "http://feeds.bbci.co.uk/news/rss.xml",
    "tvp": "https://www.tvp.info/tvp.info/rss+xml.php"
  }
}
```

### Radar Configuration Parameters:
- **`radar_zoom`** *(default: `8`)*: Map zoom level. Uses smooth digital scaling to provide closer regional views without hitting API tile limits.
- **`radar_min_alpha`** *(default: `85`)*: Reflectivity and cloud filter threshold (0–255).
  - `0`: No filtering (shows raw cloud returns and virga).
  - `85`: Standard filter (removes faint cloud haze/virga; shows drizzle and rain).
  - `140–200`: Aggressive precipitation filter (isolates clearly defined, active rain bands).
- **`radar_smooth`** *(default: `1`)*: `1` for smoothed radar interpolation, `0` for raw radar pixels.
- **`radar_color_scheme`** *(default: `2`)*: Palette selection (`1` = Classic Green/Yellow/Red, `2` = Universal Blue, `4` = The Weather Channel, `6` = NEXRAD, `8` = Dark Sky).

*Note: `config.json` is listed in `.gitignore` and will never be committed to GitHub.*
