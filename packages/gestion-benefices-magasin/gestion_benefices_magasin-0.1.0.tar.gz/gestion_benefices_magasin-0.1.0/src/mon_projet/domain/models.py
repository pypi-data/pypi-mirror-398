"""
Modèles du domaine : entités métier du magasin
"""

from dataclasses import dataclass

@dataclass
class Product:
    """
    Représente un produit du magasin
    """
    name: str
    cost_price: float   # prix d'achat
    sale_price: float   # prix de vente

    def profit_per_unit(self) -> float:
        """
        Calcule le bénéfice par unité vendue
        """
        return self.sale_price - self.cost_price


@dataclass
class Sale:
    """
    Représente une vente d'un produit
    """
    product: Product
    quantity: int

    def total_revenue(self) -> float:
        """
        Chiffre d'affaires généré par cette vente
        """
        return self.product.sale_price * self.quantity

    def total_profit(self) -> float:
        """
        Bénéfice généré par cette vente
        """
        return self.product.profit_per_unit() * self.quantity
