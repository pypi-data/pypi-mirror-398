# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class OdooImplementationUpdate(models.Model):
    _name = "odoo_implementation.update"
    _description = "Odoo Implementation - Update"
    _order = "implementation_id, date_maintenance"

    implementation_id = fields.Many2one(
        string="# Odoo Implementation",
        comodel_name="odoo_implementation",
        required=True,
        ondelete="cascade",
    )
    date_maintenance = fields.Date(
        string="Maintenance Date",
        required=True,
    )
    user_id = fields.Many2one(
        string="Responsible",
        comodel_name="res.users",
        required=True,
        ondelete="restrict",
    )
