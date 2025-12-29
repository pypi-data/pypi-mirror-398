"""
Fonctions utilitaires génériques
"""

from typing import List, Any

def format_currency(amount: float, currency: str = "€") -> str:
    """
    Formate un montant numérique en chaîne monétaire.
    
    Exemple :
        format_currency(1234.567) -> '1 234,57 €'
    """
    return f"{amount:,.2f} {currency}".replace(",", " ").replace(".", ",")

def average(values: List[float]) -> float:
    """
    Calcule la moyenne d'une liste de nombres.
    
    Lève ValueError si la liste est vide.
    """
    if not values:
        raise ValueError("La liste est vide, impossible de calculer la moyenne")
    return sum(values) / len(values)

def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Limite une valeur entre min_value et max_value.
    """
    return max(min_value, min(max_value, value))

def safe_get(lst: List[Any], index: int, default=None) -> Any:
    """
    Récupère un élément d'une liste de façon sûre.
    Renvoie 'default' si l'index est hors limites.
    """
    try:
        return lst[index]
    except IndexError:
        return default
