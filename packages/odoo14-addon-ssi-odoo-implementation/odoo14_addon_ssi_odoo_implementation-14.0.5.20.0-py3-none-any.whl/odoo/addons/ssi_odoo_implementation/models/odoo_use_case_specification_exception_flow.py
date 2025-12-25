# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class OdooUseCaseSpecificationExceptionFlow(models.Model):
    _name = "odoo_use_case_specification.exception_flow"
    _description = "Odoo Use Case Specification Exception Flow"
    _order = "use_case_specification_id, sequence, id"

    use_case_specification_id = fields.Many2one(
        comodel_name="odoo_use_case_specification",
        string="Use Case Specification",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(string="Sequence", required=True, default=10)
    name = fields.Char(string="Name", required=True)
    trigger = fields.Text(string="Trigger")
    condition = fields.Text(string="Condition")
    system_response = fields.Text(string="System Response")
    correction_procedure = fields.Text(string="Correction Procedure")
    description = fields.Text(string="Description")
