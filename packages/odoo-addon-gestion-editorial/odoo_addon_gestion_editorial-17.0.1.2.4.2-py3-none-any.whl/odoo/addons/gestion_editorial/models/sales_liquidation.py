from collections import defaultdict
from odoo import models, fields, api, exceptions
from odoo import _
from markupsafe import Markup
from ..utils import liquidation_utils


class EditorialSalesLiquidation(models.Model):
    """ Model to manage editorial sales liquidations """

    _description = "Editorial sales liquidations"
    _inherit = ['sale.order']

    order_type = fields.Selection([
        ('SALE_DEPR', 'Sales deposit return'),
        ('SALE_LIQ', 'Sales liquidation'),
        ('SALE_RLIQ', 'Sales return liquidation'),
        ('SALE_ORDER', 'Normal sale order'),
    ])
    liquidation_warning_displayed = fields.Boolean(
        string="Se ha mostrado la alerta cuando la liquidación no es válida.", 
        default=False, required=False
    )

    @api.model
    def default_get(self, fields):
        res = super(EditorialSalesLiquidation, self).default_get(fields)
        res['order_type'] = self.env.context.get('order_type')
        return res

    @api.onchange("order_line")
    def reset_warning_message(self):
        self.liquidation_warning_displayed = False

    def action_confirm(self):
        if not self.order_type in ['SALE_DEPR', 'SALE_LIQ']:
            return super(EditorialSalesLiquidation, self).action_confirm()

        valid, errors = self.check_stock_in_deposit()

        if not valid and not self.liquidation_warning_displayed:
            self.liquidation_warning_displayed = True
            return self.display_info_message(errors)

        order_name_sufix = " [Liq]" if self.order_type == 'SALE_LIQ' else " [Dev]"
        self.name += order_name_sufix if self.state == 'draft' else ""

        res = super(EditorialSalesLiquidation, self).action_confirm()

        # Delete draft pickings created by default and create liquidation pickings
        self.picking_ids.unlink()
        self.create_liq_pickings()
        return res

    def check_stock_in_deposit(self):
        deposit_data = self.partner_id.get_sales_deposit_lines()

        products_to_check = defaultdict(lambda: {'total_liquidation': 0, 'total_deposit': 0})
        negative_lines_to_check = defaultdict(int)

        for order_line in self.order_line:
            # Only check lines for storable products
            if order_line.product_id.type != "product":
                continue

            if order_line.product_uom_qty < 0:
                if self.order_type == 'SALE_DEPR':
                    raise exceptions.ValidationError(f"No se pueden introducir cantidades negativas para devoluciones de depósito.")
                negative_lines_to_check[order_line.product_id] += -order_line.product_uom_qty
                continue
            products_to_check[order_line.product_id]['total_liquidation'] += order_line.product_uom_qty
            qty_total_deposit = 0

            qty_total_deposit = deposit_data.get(order_line.product_id.id, 0)
            products_to_check[order_line.product_id]['total_deposit'] = qty_total_deposit

        liquidation_utils.validate_stock_availability(products_to_check,
            "No hay stock suficiente disponible en depósito con estos valores. Estos son valores disponibles en depósito:"
        )

        negative_lines_error_messages = []

        for product, return_qty in negative_lines_to_check.items():
            product_liquidated_qty = product.get_liquidated_sales_qty_per_partner(self.partner_id.id)
            if return_qty > product_liquidated_qty:
                negative_lines_error_messages.append(f"La cantidad que intentas devolver es mayor a la cantidad que has liquidado para el producto: {product.name}. Cantidad disponible: {product_liquidated_qty}")

        if negative_lines_error_messages:
            error_message = "\n".join(negative_lines_error_messages)
            return False, error_message
        return True, None

    def return_products_from_negative_lines(self, order_data):
        order_data_without_negatives = {}
        products_to_return = {}

        for product, quantity in order_data:
            if quantity >= 0:
                order_data_without_negatives[product] = quantity
            else:
                products_to_return[product] = -quantity     # Negative to invert negative value

        if self.order_type == 'SALE_DEPR' and products_to_return:
            raise exceptions.ValidationError(
                "No puede haber líneas negativas en una devolución de depósito."
            )

        if products_to_return:
            picking = self.create_pickings_from_data(products_to_return.items(), picking_type="SALE_RLIQ")
            self.post_note_with_picking_ref(picking)
        # return array without negative lines    
        return order_data_without_negatives.items()

    # Create normal and return pickings for liqs
    def create_liq_pickings(self):
        order_data = liquidation_utils.get_order_lines_sum_quantity_by_product(self.order_line)

        # Get array without negative products after returning them
        order_data = self.return_products_from_negative_lines(order_data)

        # Return if there are no invoice lines
        # It can be because liquidation with only negative lines
        if not order_data:
            return

        picking = self.create_pickings_from_data(order_data, picking_type=self.order_type)
        self.post_note_with_picking_ref(picking)

    def create_pickings_from_data(self, order_data, picking_type="SALE_LIQ"):
        if picking_type == "SALE_LIQ":
            picking_type_id = self.env.ref('stock.picking_type_out').id
            location_id = self.env.company.location_venta_deposito_id.id
            location_dest_id = self.env.ref("stock.stock_location_customers").id
        elif picking_type == "SALE_DEPR":
            picking_type_id = self.env.ref('stock.picking_type_in').id
            location_id = self.env.company.location_venta_deposito_id.id
            location_dest_id = self.env.ref("stock.stock_location_stock").id
        elif picking_type == "SALE_RLIQ":
            picking_type_id = self.env.ref('stock.picking_type_in').id
            location_id = self.env.ref("stock.stock_location_customers").id
            location_dest_id = self.env.company.location_venta_deposito_id.id
 
        picking_vals = {
            'partner_id': self.partner_id.id,
            'picking_type_id': picking_type_id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'origin': self.name,
            'sale_id': self.id,
            'move_type': 'direct',
        }

        picking = self.env['stock.picking'].create(picking_vals)

        # Add products from liquidation to picking
        for product_id, product_qty in order_data:
            # Only check lines for storable products
            if product_id.type != "product":
                continue

            # Create stock move of product and associate to picking
            new_stock_move = self.env['stock.move'].create({
                'name': product_id.name,
                'product_id': product_id.id,
                'product_uom': product_id.uom_id.id,
                'product_uom_qty': product_qty,
                'picking_id': picking.id,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'picking_type_id': picking_type_id,
                'partner_id': self.partner_id.id,
            })

            self.env['stock.move.line'].create({
                'move_id': new_stock_move.id,
                'product_id': product_id.id,
                'product_uom_id': product_id.uom_id.id,
                'quantity': product_qty,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'picking_id': picking.id,
            })

        # Set move lines qty_done to liquidation qty
        for stock_move in picking.move_ids_without_package:
            stock_move.quantity = stock_move.product_uom_qty
        for move_line in picking.move_line_ids_without_package:
            move_line.quantity = move_line.move_id.product_uom_qty

        picking.button_validate()
        self.write({'picking_ids': [(4, picking.id)]})

        return picking

    def display_info_message(self, error_message):
        view_id = self.env["editorial.info.message.wizard"].create({
            "message": _("Esta liquidación contiene discrepancias. Si aun así quieres continuar con la liquidación, vuelve a hacer click en el botón 'Confirmar'.") + "\n" +
                    _("Errores") + ":\n" +
                     error_message
        }).id

        return {
            'name': _('Advertencia'),
            'type': 'ir.actions.act_window',
            'res_model':  "editorial.info.message.wizard",
            'res_id': view_id,
            'views': [(False, 'form')],
            'target': 'new',
            'view_mode': 'form',
            'view_type': 'form',
        }

    def post_note_with_picking_ref(self, picking):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        picking_url = f"{base_url}/web#id={picking.id}&model=stock.picking&view_type=form"
        message = Markup(
            "Se ha creado una transferencia al procesar esta operación.<br/>"
            "Referencia: <a href='{url}' target='_blank'>{name}</a>"
        ).format(url=picking_url, name=picking.name)

        self.message_post(
            body=message,
            message_type='comment',
            subtype_xmlid='mail.mt_note'
        )
