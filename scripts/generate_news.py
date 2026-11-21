#!/usr/bin/env python3
"""Generate the weekly "AI for Research" digest.

1. Reads the public feeds listed in scripts/sources.json.
2. Keeps items from the last 7 days, removes duplicates and items already covered.
3. Asks Claude Haiku to pick and summarise the stories most useful to researchers.
   The model refers to stories by ID only, so every link in the article comes
   from the feeds and never from the model.
4. Validates the result and writes src/content/news/<slug>.md.

Usage:
    python scripts/generate_news.py            # normal run (needs ANTHROPIC_API_KEY)
    python scripts/generate_news.py --dry-run  # fetch feeds only, print candidates
"""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import html
import json
import re
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path
from typing import Literal

import feedparser
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
SOURCES_FILE = ROOT / "scripts" / "sources.json"
NEWS_DIR = ROOT / "src" / "content" / "news"

MODEL = "claude-haiku-5-5"
WINDOW_DAYS = 7
MAX_PER_SOURCE = 12
MAX_CANDIDATES = 220
MIN_STORIES = 5
MAX_STORIES = 10
USER_AGENT = "AIforResearchDigest/1.0 (+https://aiforresearch.eu/ai-transparency/)"

AI_KEYWORDS = re.compile(
    r"\b(AI|A\.I\.|artificial intelligence|machine learning|deep learning|neural|LLMs?|"
    r"language models?|chatbots?|ChatGPT|GPT-?\d|Claude|Gemini|Llama|generative|algorithm\w*|"
    r"foundation models?|agents?|AlphaFold|automation)\b",
    re.IGNORECASE,
)

# Writing rules from the "no AI slop" style guide, enforced after generation.
BANNED_WORDS = [
    "delve", "foster", "leverage", "utilize", "utilise", "facilitate", "empower", "streamline",
    "robust", "cutting-edge", "paradigm shift", "game changer", "game-changer", "tapestry",
    "realm", "beacon", "multifaceted", "meticulous", "intricate", "paramount", "transformative",
    "elevate", "embark", "supercharge", "harness", "ever-evolving", "groundbreaking",
    "revolutionize", "revolutionise", "landscape", "unlock", "seamless", "pivotal",
    "testament", "underscore", "it's worth noting", "it is worth noting", "it's important to note",
    "in today's world", "in the age of", "at the end of the day", "let's dive in",
    "in conclusion", "this changes everything", "stands as", "plays a vital role", "plays a crucial role",
]

SYSTEM_PROMPT = """You are the editor of "AI for Research", a weekly digest for scientists, PhD students, research managers and grant writers, mostly in Europe. Readers are busy and sceptical. They want to know which AI developments change how they do research, find literature, analyse data, write papers or apply for funding.

## Your job
From the numbered candidate items, choose the stories that matter most to researchers this week and write the issue.

Selection rules:
- Pick 6 to 10 top stories and 3 to 8 quick hits. Never use the same item twice.
- Prefer, in this order: AI tools and models researchers can use now; AI for science (co-scientist systems, research agents, agent skills for research, AI in the lab); important papers; EU policy, AI Act and research funding news; open science and research integrity. Include general AI industry news only if it changes what researchers can do.
- Skip marketing fluff, funding rounds, stock news, product deals and items that are only loosely related to research.
- If two items cover the same story, pick the better source.
- Use only facts present in the candidate's title and summary. Do not add numbers, dates, names or claims that are not there. If a summary is thin, write less.

## How to write
Write like a sharp human science journalist, in British English. Follow these rules strictly:
- Lead with the concrete fact: who released or found what, and what it does. Names, numbers and mechanisms beat abstractions.
- Active voice. Plain words. Short to medium sentences with varied length.
- "Why it matters for researchers" must name a concrete use, risk or action for a researcher (for example: "If you run literature reviews, ..."). Never write generic lines such as "this could change research".
- Never use these words or phrases: delve, foster, leverage, utilize, facilitate, empower, streamline, robust, cutting-edge, groundbreaking, paradigm shift, game changer, tapestry, realm, beacon, multifaceted, meticulous, intricate, paramount, transformative, elevate, embark, supercharge, harness, ever-evolving, landscape, unlock, seamless, pivotal, revolutionize, testament, underscore, "it's worth noting", "in today's world", "in the age of", "let's dive in", "in conclusion", "plays a vital role".
- No binary contrasts ("This is not X, it's Y"), no rhetorical questions, no colon reveals ("The best part: ..."), no hype, no exclamation marks, no emoji.
- Do not use em dashes. Use commas, full stops or parentheses.
- No "-ing" tails that pretend to add meaning ("..., highlighting the importance of ...").
- Do not tell the reader what to think ("This is important", "Interestingly"). Show the fact.
- The takeaway is one or two plain sentences with a practical suggestion for the coming week. No recap, no aphorism.

## Fields
- title: a specific headline for the issue that names the one or two biggest stories, max 70 characters. No "Issue", no date, no colon at the start.
- seo_slug: 3 to 6 lowercase words, hyphen-separated, naming the main topics (for example "ai-co-scientist-eu-ai-act").
- description: a 130 to 155 character summary for search results, naming two or three of the stories.
- intro: two or three sentences on what this week's issue covers. No greeting.
- tags: 3 to 6 short topic tags in Title Case (for example "AI for Science", "EU AI Act").
"""

Category = Literal[
    "Tools & models",
    "AI for science",
    "Papers",
    "EU policy & funding",
    "Open science & integrity",
    "Industry",
]


class Story(BaseModel):
    source_id: str
    headline: str
    summary: str
    why_it_matters: str
    category: Category


class QuickHit(BaseModel):
    source_id: str
    text: str


class Issue(BaseModel):
    title: str
    seo_slug: str
    description: str
    intro: str
    top_stories: list[Story]
    quick_hits: list[QuickHit]
    takeaway: str
    tags: list[str]


# --------------------------------------------------------------------------- feeds

def clean_text(value: str, limit: int = 500) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) > limit:
        value = value[:limit].rsplit(" ", 1)[0] + "…"
    return value


def fetch_feed(url: str) -> feedparser.FeedParserDict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (fixed https URLs)
        data = resp.read()
    return feedparser.parse(data)


def entry_time(entry) -> float | None:
    t = entry.get("published_parsed") or entry.get("updated_parsed")
    return calendar.timegm(t) if t else None


def normalise_title(title: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


def already_used_urls() -> set[str]:
    urls: set[str] = set()
    for md in NEWS_DIR.glob("*.md"):
        urls.update(re.findall(r"\]\((https?://[^)\s]+)\)", md.read_text(encoding="utf-8")))
    return urls


def collect_candidates(now: float) -> list[dict]:
    sources = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    used = already_used_urls()
    seen_titles: set[str] = set()
    seen_urls: set[str] = set()
    candidates: list[dict] = []
    cutoff = now - WINDOW_DAYS * 86400

    for src in sources:
        try:
            feed = fetch_feed(src["url"])
        except Exception as exc:  # one broken feed must not stop the issue
            print(f"  ! {src['name']}: {exc}", file=sys.stderr)
            continue
        kept = []
        for entry in feed.entries:
            ts = entry_time(entry)
            link = (entry.get("link") or "").strip()
            title = clean_text(entry.get("title", ""), 220)
            if not ts or ts < cutoff or ts > now + 86400 or not link.startswith("http") or not title:
                continue
            summary = clean_text(entry.get("summary", "") or entry.get("description", ""))
            if src.get("keywords") and not AI_KEYWORDS.search(f"{title} {summary}"):
                continue
            norm = normalise_title(title)
            if link in used or link in seen_urls or norm in seen_titles:
                continue
            publisher = src["name"]
            # Google News items carry the real publisher in <source>.
            if "news.google.com" in src["url"]:
                publisher = (entry.get("source") or {}).get("title") or publisher
                title = re.sub(rf"\s+-\s+{re.escape(publisher)}$", "", title)
                if summary.startswith(title[:40]):
                    summary = ""
            if len(re.sub(r"[^A-Za-z]", "", title)) < 12:
                continue
            kept.append({
                "title": title,
                "summary": summary,
                "url": link,
                "source": publisher,
                "feed": src["name"],
                "category": src["category"],
                "date": dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d"),
                "ts": ts,
            })
        kept.sort(key=lambda c: c["ts"], reverse=True)
        kept = kept[:MAX_PER_SOURCE]
        for c in kept:
            seen_urls.add(c["url"])
            seen_titles.add(normalise_title(c["title"]))
        candidates.extend(kept)
        print(f"  {len(kept):3d}  {src['name']}", file=sys.stderr)

    candidates.sort(key=lambda c: c["ts"], reverse=True)
    candidates = candidates[:MAX_CANDIDATES]
    for i, c in enumerate(candidates, 1):
        c["id"] = f"S{i:03d}"
    return candidates


def candidates_prompt(candidates: list[dict], start: dt.date, end: dt.date) -> str:
    lines = [
        f"Week covered: {start.isoformat()} to {end.isoformat()}.",
        f"{len(candidates)} candidate items follow. Refer to them only by their ID.",
        "",
    ]
    for c in candidates:
        lines.append(f"[{c['id']}] {c['title']}")
        lines.append(f"Source: {c['source']} ({c['category']}), {c['date']}")
        if c["summary"]:
            lines.append(f"Summary: {c['summary']}")
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- model

def call_model(user_prompt: str, feedback: str | None = None) -> Issue:
    import anthropic

    client = anthropic.Anthropic(max_retries=4, timeout=300)
    messages = [{"role": "user", "content": user_prompt}]
    if feedback:
        messages[0]["content"] += "\n\n" + feedback
    response = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        output_config={"effort": "medium"},
        output_format=Issue,
        messages=messages,
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"Model refused: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Model output was cut off (max_tokens).")
    if response.parsed_output is None:
        raise RuntimeError("Model returned no parsable output.")
    u = response.usage
    print(f"  tokens: in={u.input_tokens} out={u.output_tokens}", file=sys.stderr)
    return response.parsed_output


# --------------------------------------------------------------------------- validation

def tidy(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s*—\s*", ", ", text)  # no em dashes
    text = re.sub(r"\s+–\s+", ", ", text)  # spaced en dash used as a dash
    text = text.replace("!", ".")
    return re.sub(r"\s{2,}", " ", text)


def style_problems(issue: Issue) -> list[str]:
    blob = " ".join(
        [issue.title, issue.description, issue.intro, issue.takeaway]
        + [f"{s.headline} {s.summary} {s.why_it_matters}" for s in issue.top_stories]
        + [q.text for q in issue.quick_hits]
    ).lower()
    found = [w for w in BANNED_WORDS if re.search(rf"\b{re.escape(w)}\w*\b", blob)]
    problems = [f"banned word or phrase used: '{w}'" for w in found]
    if re.search(r"\b(?:is|was|isn't|wasn't) not (?:just|only|merely)\b", blob) or re.search(r"\bnot just\b.*\bbut\b", blob):
        problems.append("binary contrast ('not just X but Y') used")
    return problems


def validate(issue: Issue, by_id: dict[str, dict]) -> list[str]:
    errors = []
    ids = [s.source_id for s in issue.top_stories] + [q.source_id for q in issue.quick_hits]
    unknown = [i for i in ids if i not in by_id]
    if unknown:
        errors.append(f"unknown source IDs: {unknown}")
    if len(ids) != len(set(ids)):
        errors.append("the same item is used twice")
    valid_top = [s for s in issue.top_stories if s.source_id in by_id]
    if len(valid_top) < MIN_STORIES:
        errors.append(f"only {len(valid_top)} valid top stories (minimum {MIN_STORIES})")
    return errors


# --------------------------------------------------------------------------- output

def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return "-".join(value.split("-")[:7]) or "weekly-digest"


def yaml_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def next_issue_number() -> int:
    numbers = []
    for md in NEWS_DIR.glob("*.md"):
        m = re.search(r"^issue:\s*(\d+)", md.read_text(encoding="utf-8"), re.MULTILINE)
        if m:
            numbers.append(int(m.group(1)))
    return max(numbers, default=0) + 1


def render_markdown(issue: Issue, by_id: dict[str, dict], number: int, pub: dt.datetime) -> str:
    top, seen = [], set()
    for s in issue.top_stories:
        if s.source_id in by_id and s.source_id not in seen:
            seen.add(s.source_id)
            top.append(s)
    top = top[:MAX_STORIES]
    hits = [q for q in issue.quick_hits if q.source_id in by_id and q.source_id not in seen]
    sources_used = len(top) + len(hits)

    description = tidy(issue.description)
    if len(description) > 160:
        description = description[:157].rsplit(" ", 1)[0] + "…"
    tags = [t.strip() for t in issue.tags if t.strip()][:6]

    out = [
        "---",
        f"title: {yaml_str(tidy(issue.title))}",
        f"description: {yaml_str(description)}",
        f"pubDate: {pub.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"issue: {number}",
        f"tags: {json.dumps(tags, ensure_ascii=False)}",
        f"sources: {sources_used}",
        "aiGenerated: true",
        f"model: {yaml_str(MODEL)}",
        "---",
        "",
        tidy(issue.intro),
        "",
        "## Top stories",
        "",
    ]
    for i, s in enumerate(top, 1):
        c = by_id[s.source_id]
        out += [
            f"### {i}. {tidy(s.headline)}",
            "",
            f"*{s.category}* · {c['source']} · {c['date']}",
            "",
            tidy(s.summary),
            "",
            f"**Why it matters for researchers:** {tidy(s.why_it_matters)}",
            "",
            f"Source: [{c['source']}: {c['title']}]({c['url']})",
            "",
        ]
    if hits:
        out += ["## Quick hits", ""]
        for q in hits:
            c = by_id[q.source_id]
            out.append(f"- {tidy(q.text)} ([{c['source']}]({c['url']}))")
        out.append("")
    out += ["## This week's takeaway", "", tidy(issue.takeaway), ""]
    return "\n".join(out)


# --------------------------------------------------------------------------- main

def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="fetch feeds and print candidates; no API call")
    args = parser.parse_args()

    now_dt = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    now = now_dt.timestamp()
    start = (now_dt - dt.timedelta(days=WINDOW_DAYS)).date()
    end = now_dt.date()

    print("Fetching feeds…", file=sys.stderr)
    candidates = collect_candidates(now)
    print(f"{len(candidates)} candidates", file=sys.stderr)
    if len(candidates) < MIN_STORIES * 2:
        print("Not enough fresh items to build an issue.", file=sys.stderr)
        return 1

    prompt = candidates_prompt(candidates, start, end)
    if args.dry_run:
        print(prompt)
        return 0

    by_id = {c["id"]: c for c in candidates}
    issue = call_model(prompt)
    errors = validate(issue, by_id)
    problems = style_problems(issue)
    if errors or problems:
        print(f"  retrying: {errors + problems}", file=sys.stderr)
        feedback = (
            "Your previous draft had these problems. Write the issue again and fix them:\n- "
            + "\n- ".join(errors + problems)
        )
        issue = call_model(prompt, feedback)
        errors = validate(issue, by_id)
        if errors:
            print(f"Validation failed: {errors}", file=sys.stderr)
            return 1
        remaining = style_problems(issue)
        if remaining:
            print(f"  warning, style issues left: {remaining}", file=sys.stderr)

    number = next_issue_number()
    slug = f"{slugify(issue.seo_slug)}-{end.isoformat()}"
    path = NEWS_DIR / f"{slug}.md"
    NEWS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(issue, by_id, number, now_dt), encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
