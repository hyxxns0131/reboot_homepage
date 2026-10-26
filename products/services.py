import json
from pathlib import Path

PRODUCTS = json.loads((Path(__file__).parent / 'data/products.json').read_text(encoding='utf-8'))


def get_all_products():
    return PRODUCTS


def get_product(slug):
    return next((p for p in PRODUCTS if p['slug'] == slug), None)

