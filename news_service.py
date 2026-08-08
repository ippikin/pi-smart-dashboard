#!/usr/bin/env python3
"""
News Service Module for BBC News & TVP.info Headlines.
Fetches, cleans, and structures RSS news articles.
"""

import time
import re
import html
import logging
import urllib.request
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NewsService")

class NewsService:
    def __init__(self, bbc_url="http://feeds.bbci.co.uk/news/rss.xml",
                 tvp_url="https://www.tvp.info/tvp.info/rss+xml.php"):
        self.bbc_url = bbc_url
        self.tvp_url = tvp_url
        
        self._cache = {"bbc": [], "tvp": []}
        self._last_fetch_time = {"bbc": 0, "tvp": 0}
        self.cache_ttl_sec = 600  # 10 minutes cache

    def fetch_bbc_news(self, force_refresh=False):
        now = time.time()
        if not force_refresh and self._cache["bbc"] and (now - self._last_fetch_time["bbc"] < self.cache_ttl_sec):
            return self._cache["bbc"]

        articles = self._parse_rss_url(self.bbc_url, source_name="BBC News")
        if articles:
            self._cache["bbc"] = articles
            self._last_fetch_time["bbc"] = now
        return self._cache["bbc"]

    def fetch_tvp_news(self, force_refresh=False):
        now = time.time()
        if not force_refresh and self._cache["tvp"] and (now - self._last_fetch_time["tvp"] < self.cache_ttl_sec):
            return self._cache["tvp"]

        articles = self._parse_rss_url(self.tvp_url, source_name="TVP.info")
        if articles:
            self._cache["tvp"] = articles
            self._last_fetch_time["tvp"] = now
        return self._cache["tvp"]

    def _clean_text(self, text):
        if not text:
            return ""
        # Remove CDATA
        text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text, flags=re.DOTALL)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Unescape HTML entities (&quot;, &amp;, etc.)
        text = html.unescape(text)
        # Normalize spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _parse_rss_url(self, url, source_name="News"):
        articles = []
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
            )
            raw_data = urllib.request.urlopen(req, timeout=10).read()
            raw_str = raw_data.decode("utf-8", errors="ignore")

            # Extract <item> blocks using regex for robustness against malformed XML / CDATA
            item_blocks = re.findall(r'<item>(.*?)</item>', raw_str, re.DOTALL)

            for block in item_blocks[:15]:
                title_match = re.search(r'<title>(.*?)</title>', block, re.DOTALL)
                desc_match = re.search(r'<description>(.*?)</description>', block, re.DOTALL)
                pub_match = re.search(r'<pubDate>(.*?)</pubDate>', block, re.DOTALL)
                link_match = re.search(r'<link>(.*?)</link>', block, re.DOTALL)

                title = self._clean_text(title_match.group(1)) if title_match else "No Title"
                desc = self._clean_text(desc_match.group(1)) if desc_match else ""
                pub_date = self._clean_text(pub_match.group(1)) if pub_match else ""
                link = self._clean_text(link_match.group(1)) if link_match else ""

                if title and title != source_name:
                    articles.append({
                        "source": source_name,
                        "title": title,
                        "description": desc,
                        "pub_date": pub_date,
                        "link": link
                    })
        except Exception as e:
            logger.warning(f"Error parsing RSS from {url}: {e}")

        return articles

if __name__ == "__main__":
    service = NewsService()
    print("Testing BBC News...")
    bbc = service.fetch_bbc_news()
    for item in bbc[:3]:
        print(f"- [{item['source']}] {item['title']}")
    
    print("\nTesting TVP Info...")
    tvp = service.fetch_tvp_news()
    for item in tvp[:3]:
        print(f"- [{item['source']}] {item['title']}")
