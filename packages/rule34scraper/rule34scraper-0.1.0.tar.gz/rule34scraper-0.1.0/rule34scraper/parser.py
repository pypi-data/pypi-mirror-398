import re
from typing import List, Optional, Tuple
from selectolax.lexbor import LexborHTMLParser, LexborNode

from .models import Post, Tag, PostComment, PostDetails, UserProfile

DEFAULT_BASE_URL = "https://rule34.xxx"


class PostParser:
    SCORE_PATTERN = re.compile(r"score:(\d+)")
    RATING_PATTERN = re.compile(r"rating:(\w+)")

    @classmethod
    def parse_html(cls, html: str, base_url: str = DEFAULT_BASE_URL) -> List[Post]:
        parser = LexborHTMLParser(html)
        posts = []

        for thumb in parser.css("span.thumb"):
            post = cls._parse_thumb(thumb, base_url)
            if post:
                posts.append(post)

        return posts

    @classmethod
    def _parse_thumb(cls, thumb: LexborNode, base_url: str = DEFAULT_BASE_URL) -> Optional[Post]:
        anchor = thumb.css_first("a")
        img = thumb.css_first("a > img")

        if not anchor or not img:
            return None

        attrs = anchor.attributes
        img_attrs = img.attributes

        raw_id = attrs.get("id", "")
        post_id = int(raw_id.lstrip("p")) if raw_id and raw_id.lstrip("p").isdigit() else 0

        preview_url = img_attrs.get("src", "")

        alt_text = img_attrs.get("alt", "")
        tags = alt_text.split() if alt_text else []

        title = img_attrs.get("title", "")
        score = cls._extract_score(title)
        rating = cls._extract_rating(title)

        href = attrs.get("href", "")
        if href.startswith("http"):
            detail_url = href
        else:
            detail_url = f"{base_url.rstrip('/')}/{href.lstrip('/')}"

        img_class = img_attrs.get("class", "")
        is_video = "webm-thumb" in img_class

        return Post(
            id=post_id,
            preview_url=preview_url,
            tags=tags,
            score=score,
            rating=rating,
            detail_url=detail_url,
            is_video=is_video,
        )

    @classmethod
    def _extract_score(cls, title: str) -> int:
        match = cls.SCORE_PATTERN.search(title)
        return int(match.group(1)) if match else 0

    @classmethod
    def _extract_rating(cls, title: str) -> str:
        match = cls.RATING_PATTERN.search(title)
        return match.group(1) if match else "unknown"


class SidebarParser:
    COUNT_CLEAN = re.compile(r"[^\d]")

    @classmethod
    def parse_html(cls, html: str) -> List[Tag]:
        parser = LexborHTMLParser(html)
        tags = []

        sidebar = parser.css_first("#tag-sidebar")
        if not sidebar:
            return tags

        for li in sidebar.css("li"):
            tag = cls._parse_tag_item(li)
            if tag:
                tags.append(tag)

        return tags

    @classmethod
    def _parse_tag_item(cls, li: LexborNode) -> Optional[Tag]:
        attrs = li.attributes

        classes = attrs.get("class", "")
        tag_type = "general"
        for c in classes.split():
            if c.startswith("tag-type-"):
                tag_type = c.replace("tag-type-", "")
                break

        tag_link = li.css_first('a[href*="tags="]')
        if not tag_link:
            return None
        name = tag_link.text(strip=True)

        count_span = li.css_first("span.tag-count")
        count = 0
        if count_span:
            count_text = count_span.text(strip=True)
            count_text = cls.COUNT_CLEAN.sub("", count_text)
            count = int(count_text) if count_text else 0

        return Tag(name=name, count=count, type=tag_type)


class PostDetailsParser:
    ID_PATTERN = re.compile(r"Id:\s*(\d+)")
    POSTED_PATTERN = re.compile(r"Posted:\s*(.*?)\s*by")
    IMAGE_JS_PATTERN = re.compile(r"image\s*=\s*(\{[^}]+\})")
    WIDTH_PATTERN = re.compile(r"['\"]?width['\"]?\s*:\s*(\d+)")
    HEIGHT_PATTERN = re.compile(r"['\"]?height['\"]?\s*:\s*(\d+)")

    @classmethod
    def parse_html(cls, html: str) -> Optional[PostDetails]:
        parser = LexborHTMLParser(html)

        width, height = cls._parse_image_js(html)

        img = parser.css_first("img#image")
        image_url = img.attributes.get("src", "") if img else ""
        sample_url = image_url

        if not image_url:
            orig_link = parser.css_first('a[href*="images"]')
            if orig_link:
                image_url = orig_link.attributes.get("href", "")

        post_id = 0
        rating = "unknown"
        score = 0
        uploader = ""
        posted_at = ""
        source_url = None

        stats = parser.css_first("#stats")
        if stats:
            for li in stats.css("li"):
                text = li.text(strip=True)

                if "Id:" in text:
                    match = cls.ID_PATTERN.search(text)
                    post_id = int(match.group(1)) if match else 0

                elif "Rating:" in text:
                    rating = text.replace("Rating:", "").strip().lower()

                elif "Score:" in text:
                    score_span = li.css_first("span")
                    if score_span:
                        try:
                            score = int(score_span.text(strip=True))
                        except ValueError:
                            score = 0

                elif "Posted:" in text:
                    match = cls.POSTED_PATTERN.search(text)
                    posted_at = match.group(1).strip() if match else ""
                    uploader_link = li.css_first("a")
                    if uploader_link:
                        uploader = uploader_link.text(strip=True)

                elif "Source:" in text:
                    source_link = li.css_first("a")
                    if source_link:
                        source_url = source_link.attributes.get("href")

        tags = SidebarParser.parse_html(html)
        comments = CommentParser.parse_html(html)

        return PostDetails(
            id=post_id,
            image_url=image_url,
            sample_url=sample_url,
            width=width,
            height=height,
            rating=rating,
            score=score,
            uploader=uploader,
            posted_at=posted_at,
            source_url=source_url,
            tags=tags,
            comments=comments,
        )

    @classmethod
    def _parse_image_js(cls, html: str) -> Tuple[int, int]:
        match = cls.IMAGE_JS_PATTERN.search(html)
        if not match:
            return 0, 0

        js_obj = match.group(1)
        width_match = cls.WIDTH_PATTERN.search(js_obj)
        height_match = cls.HEIGHT_PATTERN.search(js_obj)

        width = int(width_match.group(1)) if width_match else 0
        height = int(height_match.group(1)) if height_match else 0

        return width, height


class CommentParser:
    TIMESTAMP_PATTERN = re.compile(r"Posted on (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")
    COMMENT_ID_PATTERN = re.compile(r"^c(\d+)$")

    @classmethod
    def parse_html(cls, html: str) -> List[PostComment]:
        parser = LexborHTMLParser(html)
        comments = []

        comment_list = parser.css_first("#comment-list")
        if not comment_list:
            return comments

        for div in comment_list.css('div[id^="c"]'):
            raw_id = div.attributes.get("id", "")
            if not cls.COMMENT_ID_PATTERN.match(raw_id):
                continue
            comment = cls._parse_comment(div)
            if comment:
                comments.append(comment)

        return comments

    @classmethod
    def _parse_comment(cls, div: LexborNode) -> Optional[PostComment]:
        attrs = div.attributes

        raw_id = attrs.get("id", "")
        match = cls.COMMENT_ID_PATTERN.match(raw_id)
        comment_id = int(match.group(1)) if match else 0

        col1 = div.css_first(".col1")
        username = ""
        timestamp = ""
        score = 0

        if col1:
            user_link = col1.css_first("a")
            if user_link:
                username = user_link.text(strip=True)

            col1_text = col1.text(strip=True)
            ts_match = cls.TIMESTAMP_PATTERN.search(col1_text)
            timestamp = ts_match.group(1) if ts_match else ""

            score_link = col1.css_first('a[id^="sc"]')
            if score_link:
                try:
                    score = int(score_link.text(strip=True))
                except ValueError:
                    score = 0

        col2 = div.css_first(".col2")
        text = ""
        if col2:
            text = col2.html or ""
            text = re.sub(r"<br\s*/?>", "\n", text)
            text = re.sub(r"<[^>]+>", "", text).strip()

        return PostComment(
            id=comment_id,
            username=username,
            text=text,
            score=score,
            timestamp=timestamp,
        )


class UserProfileParser:
    USER_ID_PATTERN = re.compile(r"id=(\d+)")
    NUM_CLEAN = re.compile(r"[^\d]")

    @classmethod
    def parse_html(cls, html: str, base_url: str = DEFAULT_BASE_URL) -> Optional[UserProfile]:
        parser = LexborHTMLParser(html)

        h2 = parser.css_first("#content > h2")
        username = h2.text(strip=True) if h2 else ""

        user_id = 0
        fav_link = parser.css_first('a[href*="page=favorites"]')
        if fav_link:
            href = fav_link.attributes.get("href", "")
            match = cls.USER_ID_PATTERN.search(href)
            user_id = int(match.group(1)) if match else 0

        join_date = ""
        level = ""
        post_count = 0
        deleted_post_count = 0
        favorite_count = 0

        for tr in parser.css("table tr"):
            tds = tr.css("td")
            if len(tds) < 2:
                continue

            label = tds[0].text(strip=True).lower()
            value_td = tds[1]

            if "join date" in label:
                join_date = value_td.text(strip=True)
            elif "level" in label:
                level = value_td.text(strip=True)
            elif "deleted" in label:
                text = value_td.text(strip=True)
                text = cls.NUM_CLEAN.sub("", text)
                deleted_post_count = int(text) if text else 0
            elif "posts" in label:
                link = value_td.css_first("a")
                if link:
                    text = link.text(strip=True)
                    text = cls.NUM_CLEAN.sub("", text)
                    post_count = int(text) if text else 0
            elif "favorites" in label:
                link = value_td.css_first("a")
                if link:
                    text = link.text(strip=True)
                    text = cls.NUM_CLEAN.sub("", text)
                    favorite_count = int(text) if text else 0

        image_lists = parser.css(".image-list")
        recent_favorites: List[Post] = []
        recent_uploads: List[Post] = []

        if len(image_lists) >= 1:
            recent_favorites = cls._parse_image_list(image_lists[0], base_url)
        if len(image_lists) >= 2:
            recent_uploads = cls._parse_image_list(image_lists[1], base_url)

        return UserProfile(
            username=username,
            id=user_id,
            join_date=join_date,
            level=level,
            post_count=post_count,
            deleted_post_count=deleted_post_count,
            favorite_count=favorite_count,
            recent_uploads=recent_uploads,
            recent_favorites=recent_favorites,
        )

    @classmethod
    def _parse_image_list(cls, container: LexborNode, base_url: str) -> List[Post]:
        posts = []
        for thumb in container.css("span.thumb"):
            post = PostParser._parse_thumb(thumb, base_url)
            if post:
                posts.append(post)
        return posts
