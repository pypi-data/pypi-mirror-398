# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class OdooFeature(models.Model):
    _name = "odoo_feature"
    _inherit = ["mixin.master_data"]
    _description = "Odoo Feature"

    category_id = fields.Many2one(
        string="Category",
        comodel_name="odoo_feature_category",
    )
    version_ids = fields.Many2many(
        string="Versions",
        comodel_name="odoo_version",
        relation="rel_odoo_feature_2_version",
        column1="feature_id",
        column2="version_id",
    )
    default_module_ids = fields.Many2many(
        string="Default Modules",
        comodel_name="odoo_module",
        relation="rel_odoo_feature_2_default_module",
        column1="feature_id",
        column2="module_id",
    )
    ttype = fields.Selection(
        string="Type",
        selection=[
            ("transaction", "Transaction"),
            ("master", "Master Data"),
            ("report", "Report"),
        ],
        required=True,
        default="transaction",
    )
    specific_use_case_ids = fields.One2many(
        string="Specific Use Cases",
        comodel_name="odoo_use_case",
        inverse_name="feature_id",
    )
    common_use_case_ids = fields.Many2many(
        string="Common Use Cases",
        comodel_name="odoo_use_case",
        relation="rel_odoo_feature_2_common_use_case",
        column1="feature_id",
        column2="use_case_id",
    )
