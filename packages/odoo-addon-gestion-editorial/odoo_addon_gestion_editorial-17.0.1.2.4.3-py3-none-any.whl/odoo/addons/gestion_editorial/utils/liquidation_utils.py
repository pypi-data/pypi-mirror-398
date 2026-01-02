from collections import defaultdict
from odoo import exceptions

def get_order_lines_sum_quantity_by_product(order_lines):
    """Group order lines by product and sum quantities"""
    totals = defaultdict(int)
    for order_line in order_lines:
        qty = getattr(order_line, 'product_qty', None) or order_line.product_uom_qty
        totals[order_line.product_id] += qty
    return totals.items()

def validate_stock_availability(products_dict, error_prefix):
    """Validate that there is stock available for the products"""
    products_not_available = {}
    
    for product, qty in products_dict.items():
        if qty['total_liquidation'] > qty['total_deposit']:
            products_not_available[product.name] = qty['total_deposit']
    
    if products_not_available:
        msg = f"{error_prefix}:"
        for product_name, product_qty in products_not_available.items():
            msg += f"\n* {product_name}: {product_qty}"
        raise exceptions.UserError(msg)
