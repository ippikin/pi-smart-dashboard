#!/usr/bin/env python3
"""
UK-Centric Fact & General Knowledge Service.
Fetches British trivia, UK history, science, geography, and Wikipedia British heritage articles.
"""

import json
import logging
import random
import urllib.request
import urllib.parse
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FactService")

# Rich curated pool of UK & British general knowledge facts
UK_FACTS_POOL = [
    # Geography & Landmarks
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
    {"source": "British Science", "text": "Isaac Newton discovered the laws of universal gravitation while studying at the University of Cambridge and at his family home in Woolsthorpe Manor, Lincolnshire.", "tag": "BRITISH SCIENCE"},
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

# Prominent UK Wikipedia topics for live article summary rotation
UK_WIKIPEDIA_TOPICS = [
    "Hadrian's_Wall",
    "Iron_Bridge",
    "Stonehenge",
    "Palace_of_Westminster",
    "Tower_of_London",
    "Loch_Ness",
    "Giant's_Causeway",
    "White_Cliffs_of_Dover",
    "Ben_Nevis",
    "Snowdon",
    "Lake_District_National_Park",
    "Sherwood_Forest",
    "Royal_Observatory,_Greenwich",
    "British_Museum",
    "Roman_Baths_(Bath)",
    "Blenheim_Palace",
    "Edinburgh_Castle",
    "Caernarfon_Castle",
    "Conwy_Castle",
    "Clifton_Suspension_Bridge",
    "Kew_Gardens",
    "Jodrell_Bank_Observatory",
    "Eden_Project",
    "Peak_District",
    "Dartmoor",
    "Isle_of_Skye",
    "Angel_of_the_North",
    "Shrewsbury_Castle",
]

class FactService:
    def __init__(self):
        self.current_fact = random.choice(UK_FACTS_POOL)
        self.is_fetching = False
        self._pool = list(UK_FACTS_POOL)
        random.shuffle(self._pool)
        self._pool_idx = 0

    def _fetch_url_json(self, url, headers=None, timeout=5):
        default_headers = {"User-Agent": "PiSmartDashboard/1.0 (https://github.com/ippikin/pi-smart-dashboard)"}
        if headers:
            default_headers.update(headers)
        req = urllib.request.Request(url, headers=default_headers)
        res = urllib.request.urlopen(req, timeout=timeout).read()
        return json.loads(res.decode("utf-8"))

    def fetch_new_fact(self):
        """Fetch a fresh UK-centric general knowledge fact or Wikipedia UK summary."""
        self.is_fetching = True
        try:
            # 50% chance to fetch live Wikipedia summary of notable UK landmarks / heritage
            if random.random() < 0.5:
                topic = random.choice(UK_WIKIPEDIA_TOPICS)
                try:
                    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(topic)}"
                    data = self._fetch_url_json(url, timeout=4)
                    title = data.get("title", "")
                    extract = data.get("extract", "")
                    if title and extract and len(extract) > 40:
                        clean_extract = extract if len(extract) < 310 else extract[:307] + "..."
                        self.current_fact = {
                            "source": f"Wikipedia: {title}",
                            "text": clean_extract,
                            "tag": "BRITISH HERITAGE"
                        }
                        return self.current_fact
                except Exception as e:
                    logger.debug(f"Wikipedia UK fetch failed: {e}")

            # Cycle cleanly through the rich curated UK pool
            self._pool_idx = (self._pool_idx + 1) % len(self._pool)
            if self._pool_idx == 0:
                random.shuffle(self._pool)
            self.current_fact = self._pool[self._pool_idx]

        finally:
            self.is_fetching = False

        return self.current_fact
