from odoo import models, fields

class InfoMessageWizard(models.TransientModel):
    _name = "editorial.info.message.wizard"
    _description = "Wizard for displaying an info message."

    message = fields.Text(string='Message', readonly=True)

