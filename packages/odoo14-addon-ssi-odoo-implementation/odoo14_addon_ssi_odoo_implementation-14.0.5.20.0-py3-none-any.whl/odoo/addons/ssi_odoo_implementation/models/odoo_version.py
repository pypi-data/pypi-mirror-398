# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class OdooVersion(models.Model):
    _name = "odoo_version"
    _inherit = ["mixin.master_data"]
    _description = "Odoo Version"

    all_module_ids = fields.Many2many(
        string="All Modules",
        comodel_name="odoo_module",
        relation="rel_odoo_version_2_module",
        column1="version_id",
        column2="module_id",
    )
    default_module_ids = fields.Many2many(
        string="Default Modules",
        comodel_name="odoo_module",
        relation="rel_odoo_version_2_default_module",
        column1="version_id",
        column2="module_id",
    )
