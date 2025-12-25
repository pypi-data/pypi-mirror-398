# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class OdooFeatureAdditionalFunctionality(models.Model):
    _name = "odoo_feature_additional_functionality"
    _inherit = ["mixin.master_data"]
    _description = "Odoo Feature Additional Functionality"

    feature_id = fields.Many2one(
        string="Feature",
        comodel_name="odoo_feature",
        ondelete="restrict",
        required=True,
    )
    additional_functionality_id = fields.Many2one(
        string="Additional Functionality",
        comodel_name="odoo_additional_functionality",
        ondelete="restrict",
        required=True,
    )
    default_module_ids = fields.Many2many(
        string="Default Modules",
        comodel_name="odoo_module",
        relation="rel_odoo_feature_additional_functionality_2_default_module",
        column1="feature_additional_functionality_id",
        column2="module_id",
    )
