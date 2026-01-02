from odoo import models, fields


class EditorialAccountMoveLine(models.Model):
    """ Extend account.move.line template for editorial management """

    _description = "Editorial Account Move Line"
    _inherit = 'account.move.line'  # odoo/addons/account/models/account_move.py

    product_barcode = fields.Char(
        string="Código de barras / ISBN", related='product_id.barcode', readonly=True
    )
