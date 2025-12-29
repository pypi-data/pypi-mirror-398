"""
Point d'entrée de l'application.

Permet de lancer l'application et de calculer les bénéfices d'un magasin
en utilisant les services du domaine.
"""

from mon_projet.domain.models import Product, Sale
from mon_projet.domain.services import StoreService


def main():
    # Création d'exemples de produits
    produit1 = Product(name="Stylo", cost_price=1.0, sale_price=2.5)
    produit2 = Product(name="Cahier", cost_price=2.0, sale_price=4.5)

    # Création d'exemples de ventes
    vente1 = Sale(product=produit1, quantity=100)
    vente2 = Sale(product=produit2, quantity=50)

    # Initialisation du service du magasin
    store_service = StoreService()
    store_service.add_sale(vente1)
    store_service.add_sale(vente2)

    # Calcul et affichage des bénéfices
    total_benefit = store_service.calculate_total_profit()
    print(f"Le bénéfice total du magasin est : {total_benefit:.2f} €")


if __name__ == "__main__":
    main()
