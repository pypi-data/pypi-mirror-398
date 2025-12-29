import pytest
from mon_projet.domain.models import Product, Sale
from mon_projet.domain.services import StoreService
from mon_projet.domain.exceptions import NoSalesError

# -----------------------------
# Tests pour les modèles
# -----------------------------

def test_product_profit_per_unit():
    product = Product(name="Stylo", cost_price=1.0, sale_price=2.5)
    assert product.profit_per_unit() == 1.5

def test_sale_total_revenue_and_profit():
    product = Product(name="Cahier", cost_price=2.0, sale_price=4.5)
    sale = Sale(product=product, quantity=10)
    assert sale.total_revenue() == 45.0
    assert sale.total_profit() == 25.0

# -----------------------------
# Tests pour les services
# -----------------------------

def test_store_service_add_and_calculate_profit():
    service = StoreService()
    product1 = Product(name="Stylo", cost_price=1.0, sale_price=2.5)
    product2 = Product(name="Cahier", cost_price=2.0, sale_price=4.5)
    
    sale1 = Sale(product=product1, quantity=100)
    sale2 = Sale(product=product2, quantity=50)
    
    service.add_sale(sale1)
    service.add_sale(sale2)
    
    total_revenue = service.calculate_total_revenue()
    total_profit = service.calculate_total_profit()
    
    assert total_revenue == (100*2.5 + 50*4.5)
    assert total_profit == (100*1.5 + 50*2.5)

def test_store_service_no_sales_error():
    service = StoreService()
    with pytest.raises(NoSalesError):
        service.calculate_total_revenue()
    with pytest.raises(NoSalesError):
        service.calculate_total_profit()
