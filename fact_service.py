#!/usr/bin/env python3
"""
UK-Centric Fact & General Knowledge Service.
Gathers infinite live British history, landmarks, science, and trivia from Wikipedia & curated pools:
1. Live Wikipedia Category Explorer (British Inventions, Castles, Geography, Heritage, Monuments, Shropshire).
2. Live Wikipedia "Did You Know..." (DYK) Daily Front-Page Trivia.
3. Live Wikipedia "On This Day" (OTD) Historical Events for today's date.
4. Rich Curated UK General Knowledge Pool as instant zero-latency fallback.
"""

import json
import logging
import random
import re
import urllib.request
import urllib.parse
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FactService")

# Diverse UK categories across Wikipedia for infinite dynamic article discovery
UK_WIKIPEDIA_CATEGORIES = [
    ("BRITISH CASTLES", "Category:Castles_in_England"),
    ("BRITISH CASTLES", "Category:Castles_in_Scotland"),
    ("BRITISH CASTLES", "Category:Castles_in_Wales"),
    ("NATIONAL TRUST", "Category:National_Trust_properties_in_England"),
    ("BRITISH INVENTIONS", "Category:English_inventions"),
    ("BRITISH INVENTIONS", "Category:Scottish_inventions"),
    ("BRITISH INVENTIONS", "Category:Welsh_inventions"),
    ("BRITISH GEOGRAPHY", "Category:Mountains_and_hills_of_the_United_Kingdom"),
    ("BRITISH GEOGRAPHY", "Category:Rivers_of_England"),
    ("ANCIENT BRITAIN", "Category:Archaeological_sites_in_England"),
    ("UK MONUMENTS", "Category:Monuments_and_memorials_in_the_United_Kingdom"),
    ("LONDON HERITAGE", "Category:Historic_buildings_in_London"),
    ("LOCAL HERITAGE", "Category:Shropshire"),
    ("BRITISH SCIENCE", "Category:British_discoveries"),
    ("BRITISH ASTRONOMY", "Category:Astronomical_observatories_in_the_United_Kingdom"),
]

# Rich curated pool of verified British trivia and general knowledge
UK_FACTS_POOL = [
    # Geography & Coast
    {"source": "British Geography", "text": "Nowhere in the UK is more than 70 miles (113 km) away from the coast, with Coton in the Elms in Derbyshire being the furthest point inland.", "tag": "BRITISH GEOGRAPHY"},
    {"source": "British Landmarks", "text": "Big Ben is actually the name of the 13.7-tonne Great Bell inside the clock tower at the Palace of Westminster, which is officially named the Elizabeth Tower.", "tag": "LANDMARKS"},
    {"source": "London Heritage", "text": "London Underground is the oldest underground railway network in the world, opening on 10 January 1863 between Paddington and Farringdon.", "tag": "UK HERITAGE"},
    {"source": "British Heritage", "text": "Stonehenge in Wiltshire is older than the Great Pyramid of Giza in Egypt, with its earliest earthen circle dating back to around 3000 BC.", "tag": "ANCIENT HISTORY"},
    {"source": "British Geography", "text": "The British coastline is approximately 11,073 miles long when including all of its islands and sea inlets.", "tag": "BRITISH GEOGRAPHY"},
    {"source": "British History", "text": "The shortest war in history involved Britain: the Anglo-Zanzibar War of 27 August 1896 lasted between 38 and 45 minutes before Zanzibar surrendered.", "tag": "BRITISH HISTORY"},
    {"source": "British Wildlife", "text": "The UK is home to over 4,000 species of beetles, which make up about one-sixth of all known British insect species.", "tag": "NATURE & WILDLIFE"},
    {"source": "British Inventions", "text": "Tim Berners-Lee, a British computer scientist born in London, invented the World Wide Web in 1989 while working at CERN.", "tag": "BRITISH INVENTIONS"},
    {"source": "British Inventions", "text": "The adhesive postage stamp (the Penny Black) was invented in Britain in 1840 by Sir Rowland Hill, featuring Queen Victoria's profile.", "tag": "BRITISH INVENTIONS"},
    {"source": "British Culture", "text": "People in the United Kingdom drink approximately 100 million cups of tea every single day, which works out to almost 36 billion cups a year.", "tag": "CULTURE & TRIVIA"},
    {"source": "British Heritage", "text": "Windsor Castle in Berkshire is the oldest and largest occupied castle in the world, having been founded by William the Conqueror in the 11th century.", "tag": "ROYAL HERITAGE"},
    {"source": "British Language", "text": "The town of Llanfairpwllgwyngyllgogerychwyrndrobwllllantysiliogogogoch in Anglesey, Wales, has the longest official place name in the UK with 58 letters.", "tag": "BRITISH TRIVIA"},
    {"source": "British Geography", "text": "Ben Nevis in the Scottish Highlands is the highest mountain in the British Isles, standing at 1,345 metres (4,413 ft) above sea level.", "tag": "BRITISH GEOGRAPHY"},
    {"source": "British Inventions", "text": "The first modern chocolate bar was created in Bristol in 1847 by British chocolatier J.S. Fry & Sons.", "tag": "BRITISH INVENTIONS"},
    {"source": "British Science", "text": "Isaac Newton discovered the laws of universal gravitation while studying at Cambridge and at Woolsthorpe Manor in Lincolnshire.", "tag": "BRITISH SCIENCE"},
    {"source": "British Inventions", "text": "The steam locomotive was pioneered in the UK by Richard Trevithick in 1804 and George Stephenson with the Stockton and Darlington Railway in 1825.", "tag": "BRITISH INVENTIONS"},
    {"source": "British Heritage", "text": "The Roman Baths in the city of Bath are fed by natural thermal springs that discharge 1,170,000 litres of water at 46°C every single day.", "tag": "UK HERITAGE"},
    {"source": "British Nature", "text": "The Major Oak in Sherwood Forest, Nottinghamshire, is estimated to be between 800 and 1,000 years old and has a canopy circumference of over 28 metres.", "tag": "NATURE & WILDLIFE"},
    {"source": "British Science", "text": "The structure of DNA was famously uncovered in 1953 at the Cavendish Laboratory in Cambridge by Francis Crick, James Watson, and Rosalind Franklin.", "tag": "BRITISH SCIENCE"},
    {"source": "British Heritage", "text": "The Tower of London has been guarded by ravens for centuries; legend has it that if the six resident ravens ever leave, the Crown and Britain will fall.", "tag": "ROYAL HERITAGE"},
    {"source": "British Geography", "text": "Lough Neagh in Northern Ireland is the largest lake in the British Isles by surface area, covering roughly 151 square miles (392 sq km).", "tag": "BRITISH GEOGRAPHY"},
    {"source": "British History", "text": "The Magna Carta, agreed by King John at Runnymede near Windsor in June 1215, established for the first time the principle that everyone is subject to the law.", "tag": "BRITISH HISTORY"},
    {"source": "British Heritage", "text": "The Eden Project in Cornwall contains the largest indoor rainforest in the world inside its distinctive geodesic biomes.", "tag": "UK HERITAGE"},
    {"source": "British Inventions", "text": "The television was first publicly demonstrated in Soho, London, in 1926 by Scottish inventor John Logie Baird.", "tag": "BRITISH INVENTIONS"},
    {"source": "British Nature", "text": "The red squirrel is native to the UK, though its population is now largely conserved in Scotland, the Lake District, and Brownsea Island in Dorset.", "tag": "NATURE & WILDLIFE"},
    {"source": "British Culture", "text": "The iconic red telephone box (the K2) was designed in 1924 by British architect Sir Giles Gilbert Scott, who also designed Battersea Power Station.", "tag": "CULTURE & TRIVIA"},
    {"source": "British Geography", "text": "The Giant's Causeway in County Antrim consists of about 40,000 interlocking basalt columns created by ancient volcanic fissure eruptions.", "tag": "BRITISH GEOGRAPHY"},
    {"source": "British Science", "text": "Charles Darwin published 'On the Origin of Species' in 1859 while living and working at Down House in Kent.", "tag": "BRITISH SCIENCE"},
]

class FactService:
    def __init__(self):
        self.current_fact = random.choice(UK_FACTS_POOL)
        self.is_fetching = False
        self._pool = list(UK_FACTS_POOL)
        random.shuffle(self._pool)
        self._pool_idx = 0

    def _fetch_url_json(self, url, timeout=5):
        headers = {"User-Agent": "PiSmartDashboard/1.0 (https://github.com/ippikin/pi-smart-dashboard)"}
        req = urllib.request.Request(url, headers=headers)
        res = urllib.request.urlopen(req, timeout=timeout).read()
        return json.loads(res.decode("utf-8"))

    def _clean_html_markup(self, text):
        """Remove any HTML tags and format quotes nicely."""
        clean = re.sub(r"<[^>]+>", "", text)
        clean = clean.replace("&quot;", '"').replace("&#039;", "'").replace("&amp;", "&")
        return clean.strip()

    def fetch_new_fact(self):
        """Fetch an infinite stream of live UK history, British landmarks, or Wikipedia trivia."""
        self.is_fetching = True
        try:
            mode = random.choice(["WIKI_CATEGORY", "WIKI_OTD", "WIKI_DYK", "CURATED_POOL"])

            # Mode 1: Live Wikipedia UK Category Crawler (Infinite UK Landmarks/Inventions/Castles)
            if mode == "WIKI_CATEGORY":
                try:
                    tag_name, cat_title = random.choice(UK_WIKIPEDIA_CATEGORIES)
                    cat_url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&list=categorymembers&cmtitle={urllib.parse.quote(cat_title)}&cmlimit=60"
                    cat_data = self._fetch_url_json(cat_url, timeout=4)
                    members = [
                        m["title"] for m in cat_data.get("query", {}).get("categorymembers", [])
                        if not m["title"].startswith("Category:") and not m["title"].startswith("Template:") and not m["title"].startswith("List of")
                    ]
                    if members:
                        article_title = random.choice(members)
                        sum_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(article_title)}"
                        sum_data = self._fetch_url_json(sum_url, timeout=4)
                        extract = sum_data.get("extract", "").strip()
                        if extract and len(extract) > 40:
                            clean_extract = extract if len(extract) < 310 else extract[:307] + "..."
                            self.current_fact = {
                                "source": f"Wikipedia: {article_title}",
                                "text": clean_extract,
                                "tag": tag_name
                            }
                            return self.current_fact
                except Exception as e:
                    logger.debug(f"Wikipedia Category fetch failed: {e}")

            # Mode 2: Live Wikipedia "On This Day" (Historical Events for today's date)
            if mode == "WIKI_OTD":
                try:
                    now = datetime.datetime.now()
                    otd_url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{now.month}/{now.day}"
                    otd_data = self._fetch_url_json(otd_url, timeout=4)
                    events = otd_data.get("events", [])
                    if events:
                        ev = random.choice(events[:15])
                        ev_year = ev.get("year", "")
                        ev_text = self._clean_html_markup(ev.get("text", ""))
                        if ev_text:
                            clean_text = f"In {ev_year}: {ev_text}" if ev_year else ev_text
                            if len(clean_text) > 310:
                                clean_text = clean_text[:307] + "..."
                            self.current_fact = {
                                "source": f"Wikipedia On This Day ({now.strftime('%d %B')})",
                                "text": clean_text,
                                "tag": "ON THIS DAY IN HISTORY"
                            }
                            return self.current_fact
                except Exception as e:
                    logger.debug(f"Wikipedia OnThisDay fetch failed: {e}")

            # Mode 3: Live Wikipedia "Did You Know..." Front Page Trivia
            if mode == "WIKI_DYK":
                try:
                    now = datetime.datetime.now()
                    feat_url = f"https://en.wikipedia.org/api/rest_v1/feed/featured/{now.strftime('%Y/%m/%d')}"
                    feat_data = self._fetch_url_json(feat_url, timeout=4)
                    dyk_list = feat_data.get("dyk", [])
                    if isinstance(dyk_list, dict):
                        dyk_list = dyk_list.get("elements", [])
                    if dyk_list:
                        dyk_item = random.choice(dyk_list)
                        raw_text = dyk_item.get("text", "")
                        clean_text = self._clean_html_markup(raw_text)
                        if clean_text.startswith("... that "):
                            clean_text = "Did you know that " + clean_text[9:]
                        if clean_text:
                            if len(clean_text) > 310:
                                clean_text = clean_text[:307] + "..."
                            self.current_fact = {
                                "source": "Wikipedia: Did You Know?",
                                "text": clean_text,
                                "tag": "DID YOU KNOW?"
                            }
                            return self.current_fact
                except Exception as e:
                    logger.debug(f"Wikipedia DYK fetch failed: {e}")

            # Mode 4 / Fallback: Cycle through curated UK general knowledge pool
            self._pool_idx = (self._pool_idx + 1) % len(self._pool)
            if self._pool_idx == 0:
                random.shuffle(self._pool)
            self.current_fact = self._pool[self._pool_idx]

        finally:
            self.is_fetching = False

        return self.current_fact
