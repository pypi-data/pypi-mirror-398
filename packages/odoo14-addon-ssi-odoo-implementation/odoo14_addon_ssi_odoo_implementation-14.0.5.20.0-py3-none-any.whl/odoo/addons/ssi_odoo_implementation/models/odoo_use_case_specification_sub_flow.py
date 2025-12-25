# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class OdooUseCaseSpecificationSubFlow(models.Model):
    _name = "odoo_use_case_specification.sub_flow"
    _description = "Odoo Use Case Specification Sub Flow"
    _order = "use_case_specification_id, sequence, id"

    use_case_specification_id = fields.Many2one(
        comodel_name="odoo_use_case_specification",
        string="Use Case Specification",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(string="Sequence", required=True, default=10)
    name = fields.Char(string="Sub Flow Name", required=True)
    condition = fields.Text(string="Condition", required=True)
    fork_point = fields.Char(string="Fork Point")
    join_point = fields.Char(string="Join Point")
    description = fields.Text(string="Steps")
