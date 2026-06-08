import re

import requests
from bs4 import BeautifulSoup, Comment, NavigableString, Tag

_REDDIT_URL_RE = re.compile(r"reddit\.com")

BLOCK_ELEMENTS = {
    "p", "div", "h1", "h2", "h3", "h4", "h5", "h6",
    "blockquote", "pre", "section", "article",
    "header", "main", "aside",
    "figure", "figcaption", "address", "details", "summary",
}

SKIP_ELEMENTS = {"script", "style", "head", "meta", "link", "noscript", "svg", "iframe", "htdig_noindex"}

# ARIA roles that identify navigation/footer chrome
_CHROME_ROLES = {"navigation", "contentinfo", "banner"}

# Class/id substrings that indicate nav, menu, or footer regions
_CHROME_PATTERN = re.compile(
    r"\b(nav|menu|footer|navigation|breadcrumb|sidebar|print)\b",
    re.IGNORECASE,
)

# Accessibility/utility link text to discard (skip-links, back-to-top, etc.)
_UTILITY_LINK_PATTERN = re.compile(r"^(skip\b|back to top)", re.IGNORECASE)


def _strip_chrome(root: Tag) -> None:
    for tag in root.find_all(["nav", "footer"]):
        tag.decompose()

    for tag in root.find_all(attrs={"role": True}):
        if tag.parent and tag.get("role", "").lower() in _CHROME_ROLES:
            tag.decompose()

    for tag in root.find_all(True):
        if not tag.parent:
            continue
        classes = " ".join(tag.get("class", []))
        tag_id = tag.get("id", "")
        if _CHROME_PATTERN.search(classes) or _CHROME_PATTERN.search(tag_id):
            tag.decompose()

    for a in root.find_all("a"):
        if a.parent and _UTILITY_LINK_PATTERN.match(a.get_text(strip=True)):
            a.decompose()


def _format_dl(dl: Tag) -> str:
    lines = []
    current_dt = None
    current_dds: list[str] = []

    for child in dl.children:
        if not isinstance(child, Tag):
            continue
        if child.name == "dt":
            if current_dt is not None:
                dd_text = ", ".join(current_dds)
                lines.append(f"{current_dt}: {dd_text}" if current_dds else current_dt)
                current_dds = []
            current_dt = child.get_text(separator=" ", strip=True).rstrip(":")
        elif child.name == "dd":
            t = child.get_text(separator=" ", strip=True)
            if t:
                current_dds.append(t)

    if current_dt is not None:
        dd_text = ", ".join(current_dds)
        lines.append(f"{current_dt}: {dd_text}" if current_dds else current_dt)

    return "\n".join(lines)


def _format_table(table: Tag) -> str:
    rows = []
    for tr in table.find_all("tr"):
        cells = [
            cell.get_text(separator=" ", strip=True)
            for cell in tr.find_all(["td", "th"])
        ]
        if cells:
            rows.append(cells)

    if not rows:
        return ""

    num_cols = max(len(row) for row in rows)
    rows = [row + [""] * (num_cols - len(row)) for row in rows]
    col_widths = [max(len(row[i]) for row in rows) for i in range(num_cols)]

    lines = []
    for idx, row in enumerate(rows):
        padded = [row[i].ljust(col_widths[i]) for i in range(num_cols)]
        lines.append("| " + " | ".join(padded) + " |")
        if idx == 0:
            lines.append("|-" + "-|-".join("-" * w for w in col_widths) + "-|")

    return "\n".join(lines)


def _format_list(lst: Tag, depth: int = 0) -> str:
    lines = []
    ordered = lst.name == "ol"
    counter = 1

    for item in lst.find_all("li", recursive=False):
        bullet = f"{counter}." if ordered else "-"
        counter += 1

        text_parts = []
        nested = []
        for child in item.children:
            if isinstance(child, Comment):
                continue
            if isinstance(child, NavigableString):
                t = child.strip()
                if t:
                    text_parts.append(t)
            elif isinstance(child, Tag):
                if child.name in ("ul", "ol"):
                    nested.append(child)
                elif child.name not in SKIP_ELEMENTS:
                    t = child.get_text(separator=" ", strip=True)
                    if t:
                        text_parts.append(t)

        indent = "  " * depth
        lines.append(f"{indent}{bullet} {' '.join(text_parts)}")
        for nested_list in nested:
            lines.append(_format_list(nested_list, depth + 1))

    return "\n".join(lines)


def _node_to_text(node) -> str:
    if isinstance(node, Comment):
        return ""
    if isinstance(node, NavigableString):
        return str(node)

    if not isinstance(node, Tag):
        return ""

    if node.name in SKIP_ELEMENTS:
        return ""

    if node.name == "br":
        return "\n"

    if node.name == "table":
        return "\n" + _format_table(node) + "\n"

    if node.name in ("ul", "ol"):
        return "\n" + _format_list(node) + "\n"

    if node.name == "dl":
        return "\n" + _format_dl(node) + "\n"

    if node.name == "a":
        inner = "".join(_node_to_text(c) for c in node.children)
        href = node.get("href", "")
        if href.startswith("http"):
            return f"{inner} {href}"
        return inner

    parts = [_node_to_text(child) for child in node.children]
    text = "".join(parts)

    if node.name in BLOCK_ELEMENTS:
        return "\n" + text.strip() + "\n"

    return text


def _parse_reddit_comment(tag: Tag, depth: int = 0) -> list[str]:
    lines = []
    indent = "  " * depth

    author_tag = tag.select_one(".author")
    score_tag = tag.select_one(".score.unvoted, .score.likes, .score.dislikes")
    body_tag = tag.select_one(".usertext-body .md")

    if not body_tag:
        return lines

    author = author_tag.get_text(strip=True) if author_tag else "[deleted]"
    score = score_tag.get("title", "?") if score_tag else "?"
    body = body_tag.get_text(separator="\n", strip=True)

    if not body or body in ("[deleted]", "[removed]"):
        return lines

    lines.append(f"{indent}[u/{author} | {score} points]")
    for line in body.splitlines():
        lines.append(f"{indent}{line}")
    lines.append("")

    child_div = tag.find("div", class_="child", recursive=False)
    if child_div:
        sitetable = child_div.find("div", class_="sitetable", recursive=False)
        if sitetable:
            for reply in sitetable.find_all("div", class_="comment", recursive=False):
                lines.extend(_parse_reddit_comment(reply, depth + 1))

    return lines


def _scrape_reddit(url: str) -> str:
    base = re.sub(r"^https?://(www\.)?reddit\.com", "https://old.reddit.com", url)
    base = base.split("?")[0].rstrip("/").removesuffix(".json")

    response = requests.get(
        base,
        timeout=10,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.select_one("#siteTable .title a.title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    selftext_tag = soup.select_one(".self .usertext-body .md")
    selftext = selftext_tag.get_text(separator="\n", strip=True) if selftext_tag else ""

    lines: list[str] = []
    if selftext and selftext not in ("[deleted]", "[removed]"):
        lines.append(selftext)
        lines.append("")

    lines.append("Comments:")
    lines.append("")
    for comment in soup.select(".commentarea > .sitetable.nestedlisting > .comment"):
        lines.extend(_parse_reddit_comment(comment))

    raw = "\n".join(lines).strip()
    raw = re.sub(r"\n{3,}", "\n\n", raw)

    header = f"URL_SOURCE: {url}\nTITLE: {title}\n\n" if title else f"URL_SOURCE: {url}\n\n"
    return header + raw


def scrape_page(url: str) -> str:
    if _REDDIT_URL_RE.search(url):
        return _scrape_reddit(url)

    response = requests.get(
        url,
        timeout=10,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""
    root = soup.body if soup.body else soup
    _strip_chrome(root)

    raw = _node_to_text(root)
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r" *\n", "\n", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    # collapse blank line between a heading/paragraph and an immediately following list
    raw = re.sub(r"(\n\S[^\n]*)\n\n(-|\d+\.)", r"\1\n\2", raw)
    raw = raw.strip()

    header = f"URL_SOURCE: {url}\nTITLE: {title}\n\n" if title else f"URL_SOURCE: {url}\n\n"
    return header + raw

# allow overwrite existing files for easier debugging
def save_to_txt(text: str, filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)

if __name__ == "__main__":
    # URLS = [
    #     "https://dining.umd.edu/hours-locations/dining-halls",
    #     "https://dining.umd.edu/home/hours-locations/dining-halls/door-prices",
    #     "https://academiccatalog.umd.edu/undergraduate/campus-administration-resources-student-services/student-programs-services/dining-services",
    #     "https://campusvisitorguides.com/umd/where-to-eat",
    #     "https://dining.umd.edu/nutrition-allergies-and-special-diets/allergy",
    #     "https://dining.umd.edu/students/sick-meals",
    #     "https://dining.umd.edu/students/resident-plans",
    #     "https://dining.umd.edu/students/connector-plans",
    #     "https://dining.umd.edu/students/dining-dollars-flexible-discounted-and-convenient"
    # ]
    # for url in URLS:
    #     try:
    #         text = scrape_page(url)
    #     except Exception as e:
    #         print(f"Error scraping {url}: {e}")
    #     else:
    #         save_to_txt(text, f"documents/{url.split('/')[-1]}2.txt")

    # read reddit urls as json
    REDDIT_URLS = [
        "https://www.reddit.com/r/UMD/comments/1sngnlo/charging_in_dining_halls.json",
        "https://www.reddit.com/r/UMD/comments/1s1ol7n/whats_cheaper_choosing_a_meal_plan_or_buying.json",
    ]

    for url in REDDIT_URLS:
        try:
            text = _scrape_reddit(url)
        except Exception as e:
            print(f"Error scraping {url}: {e}")
        else:
            save_to_txt(text, f"documents/{url.split('/')[-1][:-5]}.txt")
    