import logging
from odoo import api, SUPERUSER_ID
from odoo.tools import sql

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.registry.clear_cache()
    env.invalidate_all()
    _logger.info("=== INICIANDO POST-MIGRATE SCRIPT ===")

    try:
        ## Update DDAA products
        ddaa_products = env['product.template'].search([
            ('categ_id', '=', env.company.product_category_ddaa_id.id),
        ])

        for product in ddaa_products:
            _logger.info(f"# Updating DDAA product: {product.name} (ID: {product.id})")
            product.purchase_method = 'purchase'

        _logger.info(f"### TOTAL UPDATED DDAA ORDERS: {len(ddaa_products)} ")

    except Exception as e:
        _logger.error(f"Error en post-migrate: {str(e)}")
        raise
    
    _logger.info("=== POST-MIGRATE COMPLETADO ===")