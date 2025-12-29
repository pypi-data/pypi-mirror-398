"""
Exceptions métier propres au domaine
"""

class DomainError(Exception):
    """
    Exception générique pour le domaine
    """
    pass

class NoSalesError(DomainError):
    """
    Levée lorsque l'on tente de calculer un bénéfice sans ventes
    """
    pass
