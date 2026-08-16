#!/usr/bin/env python3
"""
Fact & General Knowledge Service.
Fetches fun trivia, science facts, and Wikipedia 'On this day' history.
"""

import json
import logging
import random
import urllib.request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FactService")

FALLBACK_FACTS = [
    {"source": "Science & Space", "text": "The Earth is estimated to be around 4.54 billion years old.", "tag": "🌎 SCIENCE"},
    {"source": "Did You Know?", "text": "Over 5 billion pizzas are consumed worldwide every single year, with Saturday night being the most popular pizza night.", "tag": "🍕 FUN FACT"},
    {"source": "Nature & Animals", "text": "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible.", "tag": "🍯 NATURE"},
    {"source": "Science & Space", "text": "A day on Venus is longer than a year on Venus. It takes Venus 243 Earth days to rotate once, but only 225 Earth days to orbit the Sun.", "tag": "🪐 SPACE"},
    {"source": "Nature & Animals", "text": "Octopuses have three hearts and blue blood because it uses copper rather than iron to transport oxygen.", "tag": "🐙 NATURE"},
    {"source": "Technology & Inventions", "text": "The first computer mouse was invented in 1964 by Douglas Engelbart and was made of wood.", "tag": "💻 TECH"},
    {"source": "Did You Know?", "text": "Bananas are curved because they grow towards the sun against gravity, a process known as negative geotropism.", "tag": "🍌 FUN FACT"},
    {"source": "History & Earth", "text": "Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid of Giza.", "tag": "🏛️ HISTORY"},
    {"source": "Science & Space", "text": "Light from the Sun takes approximately 8 minutes and 20 seconds to reach the Earth.", "tag": "☀️ SCIENCE"},
    {"source": "Nature & Animals", "text": "Cows have best friends and get stressed when they are separated from them.", "tag": "🐮 NATURE"},
]

class FactService:
    def __init__(self):
        self.current_fact = random.choice(FALLBACK_FACTS)
        self.is_fetching = False

    def _fetch_url_json(self, url, headers=None, timeout=6):
        default_headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        if headers:
            default_headers.update(headers)
        req = urllib.request.Request(url, headers=default_headers)
        res = urllib.request.urlopen(req, timeout=timeout).read()
        return json.loads(res.decode("utf-8"))

    def fetch_new_fact(self):
        """Fetch a fresh random general knowledge fact from online sources or curated pool."""
        self.is_fetching = True
        try:
            # Source 1: UselessFacts API
            try:
                data = self._fetch_url_json("https://uselessfacts.jsph.pl/api/v2/facts/random?language=en", timeout=4)
                text = data.get("text", "").strip()
                if text and len(text) > 15:
                    self.current_fact = {
                        "source": "General Knowledge",
                        "text": text,
                        "tag": "💡 GENERAL KNOWLEDGE"
                    }
                    return self.current_fact
            except Exception as e:
                logger.debug(f"UselessFacts fetch failed: {e}")

            # Source 2: Wikipedia Random Featured Article Summary
            try:
                data = self._fetch_url_json("https://en.wikipedia.org/api/rest_v1/page/random/summary", timeout=4)
                title = data.get("title", "")
                extract = data.get("extract", "")
                if title and extract and len(extract) > 40:
                    clean_extract = extract if len(extract) < 320 else extract[:317] + "..."
                    self.current_fact = {
                        "source": f"Wikipedia: {title}",
                        "text": clean_extract,
                        "tag": "📚 WIKIPEDIA"
                    }
                    return self.current_fact
            except Exception as e:
                logger.debug(f"Wikipedia fetch failed: {e}")

            # Fallback to rich curated list
            self.current_fact = random.choice(FALLBACK_FACTS)
        finally:
            self.is_fetching = False

        return self.current_fact
