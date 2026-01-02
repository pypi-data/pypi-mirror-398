from odoo import models, fields

class EditorialLiquidacion(models.Model):
    """ Legacy model of editorial liquidation """

    _description = "Liquidacion Editorial"
    _inherit = ['account.move']

    is_liquidacion = fields.Boolean("Es liquidacion", default=False)
    is_sales_deposit_return = fields.Boolean(
        "Es devolución de depósito de ventas", default=False
    )
