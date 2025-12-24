# WiredRSS

Typed helpers for consuming WIRED’s RSS feed with the minimal Glue code needed to work with `feedparser`.

## Installation

```bash
pip install wiredrss
```

## Usage

```python
from wiredrss import fetch_wiredrss

feed = fetch_wiredrss("https://www.wired.com/feed/rss")

print(feed.feed.title)
print("newest entry:", feed.entries[0].title)
```

## Available information

- Feed-level metadata: `feed.title`, `feed.title_detail`, `feed.subtitle`, `feed.subtitle_detail`, `feed.links`, `feed.link`, `feed.rights`, `feed.language`, `feed.updated`, `feed.updated_parsed`.
- Entry-level metadata: `title`, `title_detail`, `link`, `links`, `id`, `guidislink`, `published`, `published_parsed`, `summary`, `summary_detail`, `href`, and entry `tags`.
- Media-related data: ordered `media_content`, `media_thumbnail`, `media_keywords`, plus `authors`/`author`/`author_detail` and `publisher`/`publisher_detail` fields.
- Supporting structures: `Detail`, `Link`, `Tag`, `Person`, `MediaContent`, and `MediaThumbnail` fields repeat the raw feed attributes for reliable typing.
- Request metadata returned with each call: `bozo`, `headers`, `href`, `status`, `encoding`, `version`, and `namespaces` from `feedparser`.

## Requirements

- Python 3.11+
- `feedparser>=6.0`

## License

MIT
