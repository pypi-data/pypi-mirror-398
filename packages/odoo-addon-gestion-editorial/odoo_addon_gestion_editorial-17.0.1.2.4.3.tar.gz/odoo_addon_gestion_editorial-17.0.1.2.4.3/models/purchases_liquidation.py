from collections import defaultdict
from odoo import models, fields, api, exceptions
from odoo import _
from markupsafe import Markup
from ..utils import liquidation_utils
import logging
_logger = logging.getLogger(__name__)


class EditorialPurchasesLiquidation(models.Model):
    """ Model to manage editorial purchases liquidation """

    _description = "Editorial purchases liquidation"
    _inherit = ['purchase.order']

    order_type = fields.Selection([
        ('PURCHASE_DEPR', 'Purchases deposit return'),
        ('PURCHASE_LIQ', 'Purchases liquidation'),
        ('PURCHASE_ORDER', 'Normal sale order'),
    ])

    @api.model
    def default_get(self, fields):
        res = super(EditorialPurchasesLiquidation, self).default_get(fields)
        res['order_type'] = self.env.context.get('order_type')
        return res
    
    def button_confirm(self):
        if not self.order_type in ['PURCHASE_DEPR', 'PURCHASE_LIQ']:
            return super(EditorialPurchasesLiquidation, self).button_confirm()
        
        deposit_data = self.partner_id.get_purchases_deposit_lines(alphabetical_order=True)
        self.check_stock_in_deposit(deposit_data)
        if self.order_type == 'PURCHASE_LIQ':
            order_name_sufix = " [Liq]"
            self.process_liquidation(deposit_data)
        elif self.order_type == 'PURCHASE_DEPR':
            order_name_sufix = " [Dev]"
            self.process_deposit_return(deposit_data)

        self.name += order_name_sufix if self.state == 'draft' else ""
        res = super(EditorialPurchasesLiquidation, self).button_confirm()
        self.picking_ids.unlink()
        return res
    
    def check_stock_in_deposit(self, deposit_data):
        products_to_check = defaultdict(lambda: {'total_liquidation': 0, 'total_deposit': 0})

        for order_line in self.order_line:
            # Only check lines for storable products
            if order_line.product_id.type != "product":
                continue

            if order_line.product_qty < 0:
                raise exceptions.ValidationError(f"No se pueden introducir cantidades negativas.")

            products_to_check[order_line.product_id]['total_liquidation'] += order_line.product_qty
            qty_total_deposit = 0

            deposit_lines_to_check = deposit_data.filtered(
                lambda deposito_line: deposito_line.product_id
                == order_line.product_id
            )
            if deposit_lines_to_check:
                if self.order_type == 'PURCHASE_LIQ':
                    qty_total_deposit = sum(p.qty_received - p.liquidated_qty for p in deposit_lines_to_check)
                elif self.order_type == 'PURCHASE_DEPR':
                    order_line.product_id._compute_on_hand_qty()
                    stock = order_line.product_id.on_hand_qty
                    qty_total_deposit = min(sum(p.qty_received - p.liquidated_qty for p in deposit_lines_to_check), stock)

                products_to_check[order_line.product_id]['total_deposit'] = qty_total_deposit

        liquidation_utils.validate_stock_availability(products_to_check,
            "No hay stock suficiente disponible en depósito con estos valores. Estos son valores disponibles en depósito:"
        )

    def process_liquidation(self, deposit_data):
        order_data = liquidation_utils.get_order_lines_sum_quantity_by_product(self.order_line)

        for product_id, quantity in order_data:

            order_line_qty = quantity
            purchase_deposit_lines = deposit_data.filtered(
                lambda deposit_line: deposit_line.product_id
                == product_id
            )
            for purchase_line in purchase_deposit_lines:
                if order_line_qty > 0:
                    qty_to_liquidate = purchase_line.qty_received - purchase_line.liquidated_qty
                    # If qty from liquidation is greater than qty available to liquidate in purchase line
                    if order_line_qty >= qty_to_liquidate:
                        new_liquidated_qty = purchase_line.qty_received
                        order_line_qty -= qty_to_liquidate
                        self.post_note_purchase_liq(purchase_line.order_id, qty_to_liquidate, product_id)
                    else:
                        new_liquidated_qty = purchase_line.liquidated_qty + order_line_qty
                        self.post_note_purchase_liq(purchase_line.order_id, order_line_qty, product_id)
                        order_line_qty = 0

                    purchase_line.write({'liquidated_qty': new_liquidated_qty})

    def process_deposit_return(self, deposit_data):
        pickings_return = {}    # relation between done_picking (key) and the created_return (value)

        order_data = liquidation_utils.get_order_lines_sum_quantity_by_product(self.order_line)

        for product_id, qty in order_data:
            product_qty = qty
            if product_qty <= 0:
                continue

            deposit_lines = deposit_data.filtered(
                lambda deposit_line: deposit_line.product_id == product_id)

            for deposit_line in deposit_lines:
                if product_qty <= 0:
                    break
                qty_deposito = deposit_line.qty_received - deposit_line.liquidated_qty
                qty_difference = product_qty - qty_deposito

                associated_done_picking = (
                    deposit_line.order_id.picking_ids.filtered(
                        lambda picking: (
                        picking.picking_type_id.id == self.env.company.stock_picking_type_compra_deposito_id.id
                        and picking.state == 'done'
                        and product_id.id in [li.product_id.id for li in picking.move_line_ids_without_package]
                        )
                    )
                )
                if len(associated_done_picking) > 1:
                    associated_done_picking = associated_done_picking[0]
                elif len(associated_done_picking) <= 0:
                    continue

                # Check if we have already created a return for this done_picking
                if associated_done_picking not in pickings_return:
                    # New Wizard to make the return of one line
                    return_picking = self.env['stock.return.picking'].create(
                        {'picking_id': associated_done_picking.id}
                    )
                    pickings_return[associated_done_picking] = return_picking
                    for line in return_picking.product_return_moves:
                        line.write({'quantity': 0})
                return_picking = pickings_return.get(associated_done_picking)

                return_picking_line = return_picking.product_return_moves.filtered(
                    lambda line: line.product_id == product_id
                )
                return_qty = qty_deposito if qty_difference >= 0 else product_qty
                return_picking_line.write(
                    {'quantity': return_picking_line.quantity + return_qty}
                )
                product_qty = qty_difference
                self.post_note_purchase_liq(deposit_line.order_id, 
                    return_qty, product_id, is_return=True)

        new_return_pickings = []

        for return_picking in pickings_return.values():
            new_stock_picking_data = return_picking.create_returns()
            new_stock_picking = self.env['stock.picking'].browse(
                new_stock_picking_data['res_id']
            )
            new_stock_picking['location_dest_id'] = self.env.ref("stock.stock_location_suppliers").id
            # Set quantity_done to move and move lines
            for stock_move in new_stock_picking.move_ids_without_package:
                stock_move.quantity = stock_move.product_uom_qty
            for move_line in new_stock_picking.move_line_ids_without_package:
                move_line.quantity = move_line.move_id.product_uom_qty

            new_stock_picking.button_validate()
            new_return_pickings.append(new_stock_picking)

        return new_return_pickings
    
    def post_note_purchase_liq(self, purchase_order, liquidated_qty, product_id, is_return=False):
        word_action = "Liquidando" if not is_return else "Devolviendo"
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        picking_url = f"{base_url}/web#id={purchase_order.id}&model=purchase.order&view_type=form"
        message = Markup(
            "Se ha modificado la orden de compra <a href='{url}' target='_blank'>{name}</a> "
            "al procesar esta operación. {word_action} {liquidated_qty} unidades de: {product_name}<br/>"
        ).format(url=picking_url, name=purchase_order.name, liquidated_qty=liquidated_qty,
                 product_name=product_id.name, word_action=word_action)

        self.message_post(
            body=message,
            message_type='comment',
            subtype_xmlid='mail.mt_note'
        )

    # Set qty_to_invoice for purchase liq invoices 
    # Because purchase liq does not have received qty used to compute it
    # So we set qty_to_invoice = product_qty instead of qty_received
    def action_create_invoice(self):
        if self.order_type == 'PURCHASE_LIQ':
            for line in self.order_line:
                line.qty_to_invoice = line.product_qty
        return super(EditorialPurchasesLiquidation, self).action_create_invoice()

    # Set partner default pricelist for purchase liq invoices
    def action_view_invoice(self, invoices=False):
        result = super().action_view_invoice(invoices)

        if self.order_type != 'PURCHASE_LIQ':
            return result
        default_partner_pricelist = self.partner_id.purchase_liq_pricelist
        if not default_partner_pricelist:
            return result
        
        if invoices:
            target_invoices = invoices
        else:
            target_invoices = self.invoice_ids

        for inv in target_invoices:
            inv.pricelist_id = default_partner_pricelist.id

        return result
