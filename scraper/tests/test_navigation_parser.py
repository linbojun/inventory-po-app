from pathlib import Path

from es_scraper.navigation import parse_navigation_html

FIXTURES = Path(__file__).parent / "fixtures"


def test_navigation_parser_discovers_categories():
    html = (FIXTURES / "homepage.html").read_text()
    categories = parse_navigation_html(html)

    assert len(categories) >= 8
    names = [cat.name for cat in categories]
    assert any("Cookware" in name for name in names)
    assert any("Tableware" in name for name in names)

    cookware = next(cat for cat in categories if "Cookware" in cat.name)
    sub_names = [sub.name for sub in cookware.subcategories]
    assert any("Casserole" in name for name in sub_names)
