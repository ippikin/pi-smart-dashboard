# 🌤️ Raspberry Pi Smart Weather & News Dashboard

A high-density **7-Inch Raspberry Pi Touch Display 2** (1280x720) and **Mac Desktop Emulator** dashboard application.

Features:
- 🌤️ **Local Weather Station**: Met Office Weather DataHub integration with high-accuracy Open-Meteo fallback.
- 📰 **BBC News Headlines**: Real-time RSS news ticker for UK news.
- 🇵🇱 **TVP.info News Headlines**: Real-time RSS news ticker for Polish news.
- 🔒 **Privacy & Config Protection**: `config.json` stores your location and credentials locally and is strictly ignored by `.gitignore`.
- 🖥️ **Mac Desktop Emulation**: Runs in a windowed or fullscreen Pygame window on macOS or Raspberry Pi OS.

---

## 🚀 Quick Start (Mac Emulation)

1. Make sure Python 3 and dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application on your Mac:
   ```bash
   python3 gui_dashboard.py
   ```

## 🎮 Controls & Shortcuts

- **Touch / Click Tabs**: Toggle between `Combined View`, `Local Weather`, `BBC News`, `TVP Info`, and `Refresh`.
- **`R` key**: Manually trigger live news & weather refresh.
- **`F` key**: Toggle Fullscreen.
- **`ESC` / `Q` key**: Quit dashboard.

---

## 🔒 Configuration (`config.json`)

Your local configuration stores your location settings:

```json
{
  "location_name": "City Name",
  "latitude": 0.0,
  "longitude": 0.0,
  "met_office_api_key": "",
  "met_office_client_secret": "",
  "refresh_interval_sec": 300,
  "fullscreen": false
}
```

*Note: `config.json` is listed in `.gitignore` and will never be committed to GitHub.*
