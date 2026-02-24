import pytest

from src.ingestion.parse_faq import parse_faq_from_html


def test_parse_faq_extracts_and_dedups():
    html = """
    <html><body>
      <dl>
        <dt>Comment creer un compte ?</dt>
        <dd>Allez sur la page inscription.</dd>
      </dl>
      <dl>
        <dt>Comment creer un compte ?</dt>
        <dd>Allez sur la page inscription.</dd>
      </dl>
    </body></html>
    """
    items = parse_faq_from_html(html, "https://support.workways.com/")
    assert len(items) == 1
    assert items[0].question.startswith("Comment creer")


def test_parse_faq_empty_html():
    items = parse_faq_from_html("<html><body></body></html>", "https://support.workways.com/")
    assert items == []