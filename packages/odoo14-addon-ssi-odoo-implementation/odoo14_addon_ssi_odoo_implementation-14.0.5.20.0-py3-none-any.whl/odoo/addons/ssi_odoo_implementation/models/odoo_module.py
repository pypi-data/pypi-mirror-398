# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class OdooModule(models.Model):
    _name = "odoo_module"
    _inherit = ["mixin.master_data"]
    _description = "Odoo Module"

    version_ids = fields.Many2many(
        string="Versions",
        comodel_name="odoo_version",
        relation="rel_odoo_version_2_module",
        column1="module_id",
        column2="version_id",
    )
    dependency_ids = fields.Many2many(
        string="Dependencies",
        comodel_name="odoo_module",
        relation="rel_odoo_module_2_dependency",
        column1="module_id",
        column2="dependency_id",
    )
    upstream_dependency_ids = fields.Many2many(
        string="Upstream Dependencies",
        comodel_name="odoo_module",
        relation="rel_odoo_module_2_dependency",
        column1="dependency_id",
        column2="module_id",
    )
    all_dependency_ids = fields.Many2many(
        string="Dependencies",
        comodel_name="odoo_module",
        compute="_compute_dependency",
        store=False,
    )

    @api.depends(
        "dependency_ids",
    )
    def _compute_dependency(self):
        for record in self:
            record.all_dependency_ids = record.dependency_ids
            for module in record.dependency_ids:
                record.all_dependency_ids += module.all_dependency_ids
