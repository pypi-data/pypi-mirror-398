# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class OdooWebsiteTheme(models.Model):
    _name = "odoo_website_theme"
    _inherit = ["mixin.master_data"]
    _description = "Odoo Website Theme"

    version_ids = fields.Many2many(
        string="Versions",
        comodel_name="odoo_version",
        relation="rel_odoo_website_theme_2_version",
        column1="theme_id",
        column2="version_id",
    )
    default_module_ids = fields.Many2many(
        string="Default Modules",
        comodel_name="odoo_module",
        relation="rel_odoo_website_theme_2_default_module",
        column1="feature_id",
        column2="module_id",
    )
