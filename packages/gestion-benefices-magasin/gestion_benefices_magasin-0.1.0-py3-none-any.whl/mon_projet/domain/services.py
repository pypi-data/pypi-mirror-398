"""
Services métier : logique de calcul et gestion des ventes
"""

from typing import List
from .models import Sale
from .exceptions import NoSalesError

class StoreService:
    """
    Service central pour gérer les ventes et calculer les bénéfices
    """

    def __init__(self):
        self._sales: List[Sale] = []

    def add_sale(self, sale: Sale):
        """
        Ajoute une vente à la liste des ventes
        """
        self._sales.append(sale)

    def calculate_total_revenue(self) -> float:
        """
        Calcule le chiffre d'affaires total
        """
        if not self._sales:
            raise NoSalesError("Aucune vente enregistrée")
        return sum(sale.total_revenue() for sale in self._sales)

    def calculate_total_profit(self) -> float:
        """
        Calcule le bénéfice total
        """
        if not self._sales:
            raise NoSalesError("Aucune vente enregistrée")
        return sum(sale.total_profit() for sale in self._sales)
