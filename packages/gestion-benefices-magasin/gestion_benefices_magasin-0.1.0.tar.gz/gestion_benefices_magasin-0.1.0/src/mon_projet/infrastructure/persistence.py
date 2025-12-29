"""
Gestion de la persistance des ventes et produits
"""

from typing import List
from mon_projet.domain.models import Sale, Product

class InMemoryDatabase:
    """
    Base de données en mémoire pour les ventes et produits
    (simulation sans base réelle)
    """

    def __init__(self):
        self.products: List[Product] = []
        self.sales: List[Sale] = []

    def add_product(self, product: Product):
        self.products.append(product)

    def add_sale(self, sale: Sale):
        self.sales.append(sale)

    def get_all_products(self) -> List[Product]:
        return self.products

    def get_all_sales(self) -> List[Sale]:
        return self.sales

    def clear(self):
        self.products.clear()
        self.sales.clear()
