# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class OdooUseCaseSpecificationTrigger(models.Model):
    _name = "odoo_use_case_specification.trigger"
    _description = "Odoo Use Case Specification Trigger"
    _order = "use_case_specification_id, sequence, id"

    use_case_specification_id = fields.Many2one(
        comodel_name="odoo_use_case_specification",
        string="Use Case Specification",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(string="Sequence", required=True, default=10)
    code = fields.Char(string="Trigger Code")
    trigger = fields.Text(string="Trigger")
