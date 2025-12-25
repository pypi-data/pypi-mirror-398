from typing import Optional

from ...vocab.activity.like import Like


class EmojiReact(Like):
    content: Optional[str]
