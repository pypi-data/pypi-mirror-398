import html
import json
import re


class TextSimplifier:
    """Utilidades para limpieza y simplificación de texto"""
    
    @staticmethod
    def compact_data(data: dict) -> str:
        """
        Removes keys with empty values (None, "", [], {}) from a dictionary
        and returns a compact JSON string without unnecessary spaces.

        Args:
            data(dict): Original dictionary.
        Returns:
            str: Compact JSON representation of the filtered dictionary.
        """
        data = {k: v for k, v in data.items() if v not in (None, "", [], {})}
        return json.dumps(data, separators=(",", ":"))

    @staticmethod
    def clear_text(text: str) -> str:
        """
        Cleans text by removing HTML tags, Markdown links,
        decoding HTML characters, removing escaped quotes, and
        normalizing spaces.

        Args:
            text (str): Original text.
        Returns:
            str: Cleaned and simplified text.
        """
        if not text:
            return ""

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Replace Markdown links [Text](URLxt
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

        # Decode HTML characters (&nbsp;, &lt;, etc.)
        text = html.unescape(text)

        # Remove escaped quotes
        text = text.replace('\\"', '"').replace("\\'", "'")

        # Remove line breaks, tabs, and multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()

        return text
