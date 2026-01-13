from pathlib import Path

from es_scraper.product_page import ProductPageParser

FIXTURES = Path(__file__).parent / "fixtures"


def test_product_page_parser_extracts_metadata():
    html = (FIXTURES / "product_page.html").read_text()
    url = "https://www.eshouseware.com/product-page/801361-kiwi-peeler-218"

    parser = ProductPageParser()
    record = parser.parse(html, url=url)

    assert record.product_id == "801361"
    assert "KIWI" in record.name
    assert not record.name.startswith("#801361")
    assert record.slug.startswith("801361")
    assert record.image_urls
    assert record.product_url == url
