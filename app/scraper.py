from __future__ import annotations
import asyncio, re
from datetime import datetime, timedelta, timezone
import httpx
from selectolax.parser import HTMLParser
from app.datasource.types import ArticleDTO, MatchDTO
import re
from datetime import datetime, timedelta, timezone
from selectolax.parser import HTMLParser
from app.datasource.types import ArticleDTO
from datetime import datetime, timedelta, timezone

MONTHS = (
        "JANUARY","FEBRUARY","MARCH","APRIL","MAY","JUNE",
        "JULY","AUGUST","SEPTEMBER","OCTOBER","NOVEMBER","DECEMBER"
    )
def _log(msg: str):
    print(f"[scraper] {msg}")

def _is_date_heading(txt: str) -> bool:
        """Heading like 'AUGUST 20' or the special 'TODAY' / 'YESTERDAY' tokens."""
        MONTHS = (
        "JANUARY","FEBRUARY","MARCH","APRIL","MAY","JUNE",
        "JULY","AUGUST","SEPTEMBER","OCTOBER","NOVEMBER","DECEMBER"
    )
        if not txt:
            return False
        t = txt.strip().upper()
        if t in ("TODAY", "YESTERDAY"):
            return True
        return any(t.startswith(m + " ") for m in MONTHS)

def _parse_heading_to_date(txt: str) -> datetime:
        """
        Convert 'AUGUST 20' / 'TODAY' / 'YESTERDAY' to a timezone-aware UTC datetime
        at 00:00 of that day (so comparisons are consistent).
        """
        t = (txt or "").strip().upper()
        now = datetime.now(timezone.utc)
        if t == "TODAY":
            d = now.date()
        elif t == "YESTERDAY":
            d = (now - timedelta(days=1)).date()
        else:
            try:
                d = datetime.strptime(t + f" {now.year}", "%B %d %Y").date()
            except ValueError:
                d = now.date()
        return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    

    # ---------- end helpers ----------

# You asked to keep this base:
BASE = "https://vlr.gg"
UA = "vlr-newsletter/0.1 (personal project; https://vlr.gg)"

def _utcnow():
    return datetime.now(timezone.utc)

class Scraper:
    """
    Polite, resilient scraper for VLR:
      - follows redirects (vlr.gg -> www.vlr.gg)
      - throttles requests
      - uses flexible selectors
    """
    def __init__(self, delay: float = 0.8, max_pages: int = 3):
        self.delay = delay
        self.max_pages = max_pages

    async def _get(self, client: httpx.AsyncClient, url: str) -> str:
        await asyncio.sleep(self.delay)
        r = await client.get(url, headers={"User-Agent": UA}, follow_redirects=True)
        r.raise_for_status()
        return r.text
    
    # ---------- add near top of file (below imports) ----------
    

    # ------------------ Articles ------------------

        # ---------- REPLACE YOUR ARTICLE SECTION WITH THIS ----------
    async def fetch_articles(self, since: datetime) -> list[ArticleDTO]:
        seen_ids: set[str] = set()
        articles: list[ArticleDTO] = []
        now = datetime.now(timezone.utc)

        async with httpx.AsyncClient(base_url=BASE, timeout=25, follow_redirects=True) as client:
            # 1) Homepage
            try:
                home_html = await self._get(client, "/")
                hp = self._parse_homepage_news(home_html, since, seen_ids)
                _log(f"homepage articles: {len(hp)}")
                articles.extend(hp)
            except Exception as e:
                _log(f"homepage parse failed: {e!r}")

            # 2) /news pages
            if len(articles) < 6:
                for p in range(1, self.max_pages + 1):
                    try:
                        html = await self._get(client, f"/news?p={p}")
                        items, stop = self._parse_news_index(html, since)
                        new_items = [it for it in items if it.source_id not in seen_ids]
                        for it in new_items:
                            seen_ids.add(it.source_id)
                        articles.extend(new_items)
                        _log(f"/news?p={p} articles: +{len(new_items)} (stop={stop})")
                        if stop or len(articles) >= 20:
                            break
                    except Exception as e:
                        _log(f"/news?p={p} parse failed: {e!r}")

            # 3) Fallback — regex across page to capture article links no matter the DOM
            if len(articles) == 0:
                try:
                    html = home_html  # from step 1
                except NameError:
                    html = ""
                if not html:
                    try:
                        html = await self._get(client, "/")
                    except Exception:
                        html = ""

                regex_items = self._extract_article_links_regex(html, limit=12)
                _log(f"regex fallback items: {len(regex_items)}")
                # stamp with now so they pass 7-day filter
                for rid, title, url in regex_items:
                    if rid in seen_ids:
                        continue
                    articles.append(ArticleDTO(
                        source_id=rid, url=url, title=title or "News",
                        published_at=now, author=None, tags=None, body_text=None
                    ))
                    seen_ids.add(rid)

        # Final: keep only >= since (regex already stamped with now)
        articles = [a for a in articles if (a.published_at or now) >= since]
        articles.sort(key=lambda a: a.published_at or now, reverse=True)
        _log(f"total articles returned: {len(articles)}")
        return articles


    def _parse_homepage_news(self, html: str, since: datetime, seen_ids: set[str]) -> list[ArticleDTO]:
        doc = HTMLParser(html)
        body = doc.body
        if not body:
            return []

        results: list[ArticleDTO] = []
        current_date: datetime | None = None
        now = datetime.now(timezone.utc)

        for node in body.traverse():
            if node.tag is None:
                continue

            text = node.text(strip=True)
            if text and _is_date_heading(text):
                current_date = _parse_heading_to_date(text)
                continue

            if current_date is None:
                continue
            if current_date < since:
                continue

            if node.tag == "a":
                href = (node.attributes.get("href") or "").strip()
                m = re.match(r"^/(\d+)(?:/|$)", href)
                if not m:
                    continue
                if any(seg in href for seg in ("/match/", "/thread/", "/event/", "/player/", "/team/")):
                    continue

                art_id = m.group(1)
                if art_id in seen_ids:
                    continue
                title = node.text(strip=True)
                if not title:
                    continue

                url = href if href.startswith("http") else f"{BASE}{href}"
                results.append(ArticleDTO(
                    source_id=art_id, url=url, title=title,
                    published_at=current_date, author=None, tags=None, body_text=None
                ))
                seen_ids.add(art_id)

        return results


    def _parse_news_index(self, html: str, since: datetime):
        doc = HTMLParser(html)
        cards = doc.css(".news-container .wf-module-item, .news-container .news-item, .wf-card .news-item, .m-item, a")
        results: list[ArticleDTO] = []
        stop = False
        now = datetime.now(timezone.utc)

        for c in cards:
            a = c if c.tag == "a" else c.css_first("a")
            if not a:
                continue
            href = (a.attributes.get("href") or "").strip()
            m = re.match(r"^/(\d+)(?:/|$)", href)
            if not m:
                continue
            if any(seg in href for seg in ("/match/", "/thread/", "/event/", "/player/", "/team/")):
                continue

            art_id = m.group(1)
            title_el = c.css_first(".m-item-title, .news-item-title, h3, h2") if c is not a else None
            title = (title_el.text(strip=True) if title_el else a.text(strip=True)) or "News"

            time_el = c.css_first("time, .moment-tz-convert, .m-item-date, .time") if c is not a else None
            dt = None
            if time_el:
                raw = time_el.attributes.get("datetime") if "datetime" in time_el.attributes else time_el.text(strip=True)
                dt = self._parse_date(raw)
            if not dt:
                dt = now  # optimistic so it won't be filtered out

            if dt < since:
                stop = True
                continue

            url = href if href.startswith("http") else f"{BASE}{href}"
            results.append(ArticleDTO(
                source_id=art_id, url=url, title=title,
                published_at=dt, author=None, tags=None, body_text=None
            ))

        return results, stop


    def _extract_article_links_regex(self, html: str, limit: int = 12):
        """
        Last-resort: pull any anchors that look like '/<digits>/...' and
        produce (id, title, url) tuples. Very tolerant.
        """
        out = []
        if not html:
            return out
        # Find anchors like <a href="/123456/...">Title</a>
        for m in re.finditer(r'<a[^>]+href="/(\d+)[^"]*"[^>]*>(.*?)</a>', html, flags=re.I|re.S):
            art_id = m.group(1)
            # strip HTML tags inside the anchor text
            raw = re.sub(r"<[^>]+>", "", m.group(2))
            title = re.sub(r"\s+", " ", raw).strip()
            if not title:
                continue
            href = f"{BASE}/{art_id}"
            out.append((art_id, title, href))
            # de-dup by ID
            ids = {i for i, *_ in out}
            if len(ids) >= limit:
                break
        return out
    # ---------- end article section ----------
    # ------------------ Match Results (last week) ------------------
    async def fetch_matches(self, since: datetime) -> list[MatchDTO]:
        """
        Use /matches/results (includes scores + event).
        """
        out: list[MatchDTO] = []
        async with httpx.AsyncClient(base_url=BASE, timeout=25, follow_redirects=True) as client:
            for p in range(1, self.max_pages + 1):
                html = await self._get(client, f"/matches/results?p={p}")
                items, stop = self._parse_results_index(html, since)
                out.extend(items)
                if stop:
                    break
        return out

    def _parse_results_index(self, html: str, since: datetime):
        doc = HTMLParser(html)
        # Rows for results; be generous with selectors.
        rows = doc.css(".wf-card .match-item, .wf-module-item.match-item, .match-item, .mod-match")
        results: list[MatchDTO] = []
        stop = False

        for row in rows:
            teams = row.css(".match-item-vs-team-name, .m-item-team, .team-name")
            if len(teams) < 2:
                continue
            team_a = teams[0].text(strip=True)
            team_b = teams[1].text(strip=True)

            score_el = row.css_first(".match-item-vs-score, .m-item-result, .m-item-score, .score")
            score_a = score_b = None
            if score_el:
                nums = re.findall(r"(\d+)", score_el.text())
                if len(nums) >= 2:
                    score_a, score_b = int(nums[0]), int(nums[1])

            link = row.css_first("a")
            href = link.attributes.get("href") if link else ""
            url = href if (href and href.startswith("http")) else (f"{BASE}{href}" if href else None)

            event_el = row.css_first(".match-item-event, .m-item-event, .event")
            stage_el = row.css_first(".match-item-event-series, .m-item-stage, .stage")
            time_el  = row.css_first(".moment-tz-convert, .m-item-time, time")
            raw_time = time_el.attributes.get("datetime") if (time_el and "datetime" in time_el.attributes) else (time_el.text(strip=True) if time_el else None)
            dt = self._parse_date(raw_time)

            if dt and dt < since:
                stop = True
                continue

            results.append(MatchDTO(
                event=event_el.text(strip=True) if event_el else None,
                stage=stage_el.text(strip=True) if stage_el else None,
                date_time=dt or _utcnow(),
                team_a=team_a, team_b=team_b,
                score_a=score_a, score_b=score_b,
                bo=None,
                url=url
            ))
        return results, stop

    # ------------------ helpers ------------------
    def _source_id(self, url: str) -> str:
        m = re.search(r"/(\d+)", url or "")
        return m.group(1) if m else (url or "unknown")

    def _parse_date(self, s: str | None):
        if not s:
            return None
        s = s.strip()
        # Absolute formats first
        fmts = [
            "%Y-%m-%dT%H:%M:%S%z",  # ISO w/ offset
            "%Y-%m-%d %H:%M",       # yyyy-mm-dd hh:mm
            "%Y-%m-%d",             # yyyy-mm-dd
            "%b %d, %Y %H:%M",      # Aug 20, 2025 13:45
            "%b %d, %Y",            # Aug 20, 2025
            "%d %b %Y",             # 20 Aug 2025
        ]
        for f in fmts:
            try:
                dt = datetime.strptime(s, f)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except ValueError:
                pass

        # Relative forms like "Yesterday", "2h", "3d"
        low = s.lower()
        now = _utcnow()
        if low == "yesterday":
            return now - timedelta(days=1)
        m = re.match(r"(\d+)\s*h", low)
        if m:
            return now - timedelta(hours=int(m.group(1)))
        m = re.match(r"(\d+)\s*d", low)
        if m:
            return now - timedelta(days=int(m.group(1)))
        return now  # fallback so last-week filter won't drop it
