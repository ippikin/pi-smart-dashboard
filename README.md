# 🌤️ Raspberry Pi Smart Weather & News Dashboard

A high-density **7-Inch Raspberry Pi Touch Display 2** (1280x720) and **Mac Desktop Emulator** dashboard application.

Features:
- 🌤️ **Local Weather Station**: Official Met Office Weather DataHub integration with high-accuracy Open-Meteo fallback.
- 🌧️ **Live Animated Rain Radar Map**: Real-time precipitation radar animation with dark theme map tiles and target location marker.
- 🌅 **Astronomy Integration**: Live sunrise & sunset times integrated across current weather cards and 5-day forecast modals.
- 🏷️ **Data Source Indicator**: Dynamic badge indicating live weather provider (`Met Office DataHub` vs `Open-Meteo`).
- 📰 **BBC News Headlines**: Real-time RSS news ticker for UK news.
- 🇵🇱 **TVP.info News Headlines**: Real-time RSS news ticker for Polish news.
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

- **Touch / Click Tabs**: Toggle between `Combined View`, `Weather & Radar`, `BBC News`, `TVP Info`, and `Refresh`.
- **Forecast Days**: Tap any day in the 5-day forecast row to open an interactive detailed weather popup modal.
- **`R` key**: Manually trigger live news & weather refresh.
- **`F` key**: Toggle Fullscreen.
- **`ESC` / `Q` key**: Quit dashboard.

---

## 🔒 Configuration (`config.json`)

Your local configuration stores your location settings and API keys:

```json
{
  "location_name": "City Name",
  "latitude": 0.0,
  "longitude": 0.0,
  "met_office_api_key": "YOUR_MET_OFFICE_DATAHUB_API_KEY",
  "refresh_interval_sec": 300,
  "fullscreen": true
}
```

*Note: `config.json` is listed in `.gitignore` and will never be committed to GitHub.*
