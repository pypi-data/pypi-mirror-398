from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import feedparser

ParsedTime = Tuple[int, ...]


@dataclass
class Detail:
    type: str
    language: str
    base: str
    value: str


@dataclass
class Link:
    rel: str
    type: str
    href: str


@dataclass
class Tag:
    term: str
    scheme: str
    label: str


@dataclass
class Person:
    name: str


@dataclass
class MediaContent:
    url: str
    type: str
    medium: str
    width: str
    height: str
    file_size: str
    expression: str
    duration: str


@dataclass
class MediaThumbnail:
    url: str
    width: str
    height: str


@dataclass
class FeedEntry:
    title: str
    title_detail: Detail
    link: str
    links: List[Link]
    id: str
    guidislink: bool
    published: str
    published_parsed: ParsedTime
    media_content: List[MediaContent]
    summary: str
    summary_detail: Detail
    tags: List[Tag]
    media_keywords: str
    authors: List[Person]
    author: str
    author_detail: Person
    publisher: str
    publisher_detail: Person
    media_thumbnail: List[MediaThumbnail]
    href: str


@dataclass
class FeedInfo:
    title: str
    title_detail: Detail
    subtitle: str
    subtitle_detail: Detail
    links: List[Link]
    link: str
    rights: str
    language: str
    updated: str
    updated_parsed: ParsedTime


@dataclass
class WiredRSSFeed:
    bozo: bool
    entries: List[FeedEntry]
    feed: FeedInfo
    headers: Dict[str, str]
    href: str
    status: int
    encoding: str
    version: str
    namespaces: Dict[str, str]


def detail_from(raw: Mapping[str, Any]) -> Detail:
    return Detail(
        type=raw.get("type", "") or "",
        language=raw.get("language", "") or "",
        base=raw.get("base", "") or "",
        value=raw.get("value", "") or "",
    )


def to_parsed_time(raw: Sequence[int]) -> ParsedTime:
    return tuple(raw or ())


def build_link(raw: Mapping[str, Any]) -> Link:
    return Link(rel=raw.get("rel", "") or "", type=raw.get("type", "") or "", href=raw.get("href", "") or "")


def build_tag(raw: Mapping[str, Any]) -> Tag:
    return Tag(term=raw.get("term", "") or "", scheme=raw.get("scheme", "") or "", label=raw.get("label", "") or "")


def build_person(raw: Mapping[str, Any]) -> Person:
    return Person(name=raw.get("name", "") or "")


def build_media_content(raw: Mapping[str, Any]) -> MediaContent:
    return MediaContent(
        url=raw.get("url", "") or "",
        type=raw.get("type", "") or "",
        medium=raw.get("medium", "") or "",
        width=raw.get("width", "") or "",
        height=raw.get("height", "") or "",
        file_size=raw.get("file_size", "") or "",
        expression=raw.get("expression", "") or "",
        duration=raw.get("duration", "") or "",
    )


def build_media_thumbnail(raw: Mapping[str, Any]) -> MediaThumbnail:
    return MediaThumbnail(url=raw.get("url", "") or "", width=raw.get("width", "") or "", height=raw.get("height", "") or "")


def entry_from(raw: Mapping[str, Any]) -> FeedEntry:
    return FeedEntry(
        title=raw.get("title", "") or "",
        title_detail=detail_from(raw.get("title_detail", {})),
        link=raw.get("link", "") or "",
        links=[build_link(link) for link in raw.get("links", []) or []],
        id=raw.get("id", "") or "",
        guidislink=bool(raw.get("guidislink", False)),
        published=raw.get("published", "") or "",
        published_parsed=to_parsed_time(raw.get("published_parsed") or ()),
        media_content=[build_media_content(item) for item in raw.get("media_content", []) or []],
        summary=raw.get("summary", "") or "",
        summary_detail=detail_from(raw.get("summary_detail", {})),
        tags=[build_tag(tag) for tag in raw.get("tags", []) or []],
        media_keywords=raw.get("media_keywords", "") or "",
        authors=[build_person(author) for author in raw.get("authors", []) or []],
        author=raw.get("author", "") or "",
        author_detail=build_person(raw.get("author_detail", {})),
        publisher=raw.get("publisher", "") or "",
        publisher_detail=build_person(raw.get("publisher_detail", {})),
        media_thumbnail=[build_media_thumbnail(media) for media in raw.get("media_thumbnail", []) or []],
        href=raw.get("href", "") or "",
    )


def feed_info_from(raw: Mapping[str, Any]) -> FeedInfo:
    return FeedInfo(
        title=raw.get("title", "") or "",
        title_detail=detail_from(raw.get("title_detail", {})),
        subtitle=raw.get("subtitle", "") or "",
        subtitle_detail=detail_from(raw.get("subtitle_detail", {})),
        links=[build_link(link) for link in raw.get("links", []) or []],
        link=raw.get("link", "") or "",
        rights=raw.get("rights", "") or "",
        language=raw.get("language", "") or "",
        updated=raw.get("updated", "") or "",
        updated_parsed=to_parsed_time(raw.get("updated_parsed") or ()),
    )


def fetch_wiredrss(url: str) -> WiredRSSFeed:
    parsed = feedparser.parse(url)
    return WiredRSSFeed(
        bozo=bool(parsed.get("bozo", False)),
        entries=sorted(
            [entry_from(entry) for entry in parsed.get("entries", []) or []],
            key=lambda entry: entry.published_parsed,
            reverse=True,
        ),
        feed=feed_info_from(parsed.get("feed", {})),
        headers=dict(parsed.get("headers") or {}),
        href=parsed.get("href", "") or "",
        status=int(parsed.get("status", 0)),
        encoding=parsed.get("encoding", "") or "",
        version=parsed.get("version", "") or "",
        namespaces=dict(parsed.get("namespaces") or {}),
    )
