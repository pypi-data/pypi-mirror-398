# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class OdooUseCaseSpecificationAlternateFlow(models.Model):
    _name = "odoo_use_case_specification.alternate_flow"
    _description = "Odoo Use Case Specification Alternate Flow"
    _order = "use_case_specification_id, sequence, id"

    use_case_specification_id = fields.Many2one(
        comodel_name="odoo_use_case_specification",
        string="Use Case Specification",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(string="Sequence", required=True, default=10)
    name = fields.Char(string="Alternate Flow Name", required=True)
    condition = fields.Text(string="Condition", required=True)
    fork_point = fields.Char(string="Fork Point")
    description = fields.Text(string="Steps")
