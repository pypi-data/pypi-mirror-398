# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class OdooUseCase(models.Model):
    _name = "odoo_use_case"
    _inherit = ["mixin.master_data"]
    _description = "Odoo Use Case"

    feature_id = fields.Many2one(
        string="Feature",
        comodel_name="odoo_feature",
        ondelete="restrict",
    )
    use_case = fields.Html(
        string="Use Case",
        required=True,
    )
