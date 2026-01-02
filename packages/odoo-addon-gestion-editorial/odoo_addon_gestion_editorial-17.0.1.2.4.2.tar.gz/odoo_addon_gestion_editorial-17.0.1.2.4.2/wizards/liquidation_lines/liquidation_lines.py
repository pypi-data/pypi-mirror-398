from odoo import api, fields, models, exceptions


class LiquidationWizard(models.TransientModel):
    """ Wizard: Ayuda para seleccionar las stock.move.lines pendientes de liquidar """
    _name = 'liquidation.wizard.editorial'
    _description = "Wizard Depósito"

    partner_id = fields.Many2one('res.partner', string='Cliente')
    liquidation_sales_id = fields.Many2one('sale.order')
    liquidation_purchases_id = fields.Many2one('purchase.order')
    liquidation_type = fields.Selection([
        ('SALE_LIQ', 'Sale liquidation'), 
        ('SALE_DEPR', 'Sale deposit return'), 
        ('PURCHASE_LIQ', 'Purchase liquidation'), 
        ('PURCHASE_DEPR', 'Purchase deposit return')
    ])
    is_sale_liq = fields.Boolean(compute="_compute_liq_type")
    is_purchase_liq= fields.Boolean(compute="_compute_liq_type")

    liquidation_line_ids = fields.One2many('liquidation.line.editorial', 'liquidation_wizard_id', string="Lineas de Liquidacion", copy=True)

    @api.depends('liquidation_type')
    def _compute_liq_type(self):
        for record in self:
            record.is_sale_liq = record.liquidation_type in ['SALE_LIQ', 'SALE_DEPR']
            record.is_purchase_liq = record.liquidation_type in ['PURCHASE_LIQ', 'PURCHASE_DEPR']

    @api.onchange('partner_id')
    def _update_invoice_lines(self):
        self.liquidation_line_ids = self.env['liquidation.line.editorial'] # Empty liquidation lines
        if self.partner_id.property_account_position_id:
            self.fiscal_position_id = self.partner_id.property_account_position_id

        if self.is_sale_liq:
            liq_lines = self.partner_id.get_sales_deposit_lines()
            for product_id, qty in liq_lines.items():
                if qty > 0:
                    liq_line = self._update_liq_line(product_id=product_id, product_qty=qty)
                    self.liquidation_line_ids |= liq_line
        else:   # purchase liq
            liq_lines = self.partner_id.get_purchases_deposit_lines(alphabetical_order=True)
            for move_line in liq_lines:
                liq_line = self._update_liq_line(move_line=move_line)
                self.liquidation_line_ids |= liq_line

        if self.is_purchase_liq:
            for liquidation_line in self.liquidation_line_ids:
                products_sold = liquidation_line.product_id.get_liquidated_sales_qty()
                products_purchased_and_liquidated = liquidation_line.product_id.get_liquidated_purchases_qty()
                liquidation_line.vendidos_sin_liquidar = max(0, products_sold - products_purchased_and_liquidated)
                liquidation_line.vendidos_sin_liquidar = min(liquidation_line.vendidos_sin_liquidar, liquidation_line.total_qty_disponibles)

    def _update_liq_line(self, move_line=None, product_id=None, product_qty=None):
        product_id = move_line.product_id.id if move_line else product_id
        liq_line = self.liquidation_line_ids.filtered(
            lambda line: line.product_id.id == product_id)
        if liq_line:
            liq_line = liq_line[0]
        else:
            liq_line = self.env['liquidation.line.editorial'].create({})
            liq_line.product_id = self.env["product.product"].browse(product_id)

        if self.is_sale_liq:
            total_product_uom_qty = product_qty
            liq_line.total_qty_done = 0
            liq_line.update({'total_product_uom_qty': total_product_uom_qty})
        else:   # purchase liq
            total_product_uom_qty = liq_line.total_product_uom_qty + move_line.qty_received
            liq_line.total_qty_done += move_line.liquidated_qty
            liq_line.update({'total_product_uom_qty': total_product_uom_qty})
        return liq_line

    @api.onchange('liquidation_line_ids')
    def _check_liquidation_lines(self):
        for wizard in self:
            for liquidation_line in wizard.liquidation_line_ids:
                if liquidation_line.total_qty_a_liquidar and liquidation_line.total_qty_a_liquidar > 0.0:
                    if wizard.liquidation_type in ['SALE_LIQ', 'SALE_DEPR', 'PURCHASE_LIQ'] and liquidation_line.total_qty_a_liquidar > liquidation_line.total_qty_disponibles:
                        raise exceptions.ValidationError("La cantidad seleccionada no puede ser mayor que la cantidad disponible en depósito.")
                    elif wizard.liquidation_type == 'PURCHASE_DEPR' and liquidation_line.total_qty_a_liquidar > liquidation_line.total_qty_disponibles_devolver_dep_com:
                        raise exceptions.ValidationError("La cantidad a liquidar no puede ser mayor que la cantidad disponible para devolver.")

    @api.model
    def default_get(self, fields):
        res = super(LiquidationWizard, self).default_get(fields)
        res['partner_id'] = self.env.context.get('partner_id')
        order_type = self.env.context.get('order_type')
        res['liquidation_type'] = order_type
        if order_type in ('SALE_LIQ', 'SALE_DEPR'):
            res['liquidation_sales_id'] = self.env.context.get('liquidation_id')
        elif order_type in ('PURCHASE_LIQ', 'PURCHASE_DEPR'):
            res['liquidation_purchases_id'] = self.env.context.get('liquidation_id')
        return res

    def add_selected_products(self):
        valid_liq_lines = self.liquidation_line_ids.filtered(
            lambda line: line.total_qty_a_liquidar > 0.0
        )
        
        if valid_liq_lines:        
            self._add_lines_to_order(valid_liq_lines)
        return {'type': 'ir.actions.act_window_close'}

    def select_all_liquidation_lines(self):
        for liq_line in self.liquidation_line_ids:
            liq_line.total_qty_a_liquidar = liq_line.total_qty_disponibles
        
        self._add_lines_to_order(self.liquidation_line_ids)
        return {'type': 'ir.actions.act_window_close'}
    
    def _prepare_order_line_vals(self, liq_line, quantity):
        product = liq_line.product_id
        price_unit = self._get_liq_product_price_unit(liq_line)
        taxes = self._get_mapped_taxes(product)
        order_id = self._get_order_id()
        
        vals = {
            'name': product.name,
            'order_id': order_id.id,
            'product_id': product.id,
            'price_unit': price_unit,
        }
        
        if self.is_sale_liq:
            vals['tax_id'] = taxes
            vals['product_uom_qty'] = quantity
        else:  # purchase liq
            vals['taxes_id'] = taxes
            vals['product_qty'] = quantity
        
        return vals, order_id

    def _add_lines_to_order(self, liq_lines):
        for liq_line in liq_lines:
            quantity = liq_line.total_qty_a_liquidar
            vals, order_id = self._prepare_order_line_vals(liq_line, quantity)
            order_id.write({'order_line': [(0, 0, vals)]})
    
    def _get_liq_product_price_unit(self, liq_line):
        product = liq_line.product_id

        if self.is_purchase_liq:
            return product.list_price
        else:   # sale liq
            pricelist = self.liquidation_sales_id.pricelist_id
            if pricelist:
                return pricelist._get_product_price(
                    product,
                    1,
                    currency=pricelist.currency_id,
                    uom=product.uom_id,
                )
            
    def _get_mapped_taxes(self, product):
        if self.is_sale_liq:
            taxes = product.taxes_id
            fiscal_position = self.liquidation_sales_id.fiscal_position_id
        else:
            taxes = product.supplier_taxes_id
            fiscal_position = self.liquidation_purchases_id.fiscal_position_id
        
        return fiscal_position.map_tax(taxes) if fiscal_position else taxes
    
    def _get_order_id(self):
        return (self.liquidation_sales_id if self.is_sale_liq 
                else self.liquidation_purchases_id)


class EditorialLiquidationLine(models.TransientModel):
    _name = "liquidation.line.editorial"
    _description = "Editorial liquidation line"

    liquidation_wizard_id = fields.Many2one('liquidation.wizard.editorial', "Liquidation Wizard", index=True, ondelete="cascade")
    product_id = fields.Many2one('product.product', 'Producto')
    product_barcode = fields.Char('Código de barras / ISBN', related='product_id.barcode', readonly=True)
    product_name = fields.Char('Nombre', related='product_id.name', readonly=True)
    total_product_uom_qty = fields.Float('Total en Depósito', default=0.0, digits='Product Unit of Measure', required=True, copy=False)
    total_qty_done = fields.Float('Total Hecho', default=0.0, digits='Product Unit of Measure', copy=False)
    total_qty_disponibles = fields.Float('Total en depósito', default=0.0, digits='Product Unit of Measure', copy=False, compute="_compute_available")
    total_qty_disponibles_devolver_dep_com = fields.Float('Total disponible', default=0.0, digits='Product Unit of Measure', copy=False, compute="_compute_available_dep_com")
    total_qty_a_liquidar = fields.Float('A liquidar', default=0.0, digits='Product Unit of Measure', copy=False)
    vendidos_sin_liquidar = fields.Float('Vendidos sin liquidar', default=0.0, digits='Product Unit of Measure', copy=False, readonly=True)

    @api.depends('total_qty_done', 'total_product_uom_qty')
    def _compute_available(self):
        for record in self:
            if self.env.context.get('liquidation_type') in ['SALE_LIQ', 'SALE_DEPR']:
                record.total_qty_disponibles = record.total_product_uom_qty
            else:
                record.total_qty_disponibles = record.total_product_uom_qty - record.total_qty_done

    @api.depends('total_qty_done', 'total_product_uom_qty')
    def _compute_available_dep_com(self):
        for record in self:
            record.product_id._compute_on_hand_qty()
            stock = record.product_id.on_hand_qty
            record.total_qty_disponibles_devolver_dep_com = min(record.total_qty_disponibles, stock)
