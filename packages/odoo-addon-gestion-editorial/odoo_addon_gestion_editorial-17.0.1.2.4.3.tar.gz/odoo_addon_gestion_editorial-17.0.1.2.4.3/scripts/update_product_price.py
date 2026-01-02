import odoo
import logging

_logger = logging.getLogger(__name__)

odoo.tools.config.parse_config([])
db_names = odoo.service.db.list_dbs()

if not db_names:
    raise ValueError("No database found.")

for db_name in db_names:
    # Remove tax from product price
    _logger.info("### UPDATING PRODUCT PRICE: ", db_name)
    registry = odoo.registry(db_name)
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        products = env['product.template'].search([])
        for product in products:
            product.list_price = product.list_price / 1.04

    _logger.info("### PRODUCT PRICE UPDATED: ", db_name)
