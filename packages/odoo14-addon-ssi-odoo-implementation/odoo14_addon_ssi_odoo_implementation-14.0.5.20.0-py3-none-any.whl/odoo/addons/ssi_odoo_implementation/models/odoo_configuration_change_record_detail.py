# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class OdooConfigurationChangeRecordDetail(models.Model):
    _name = "odoo_configuration_change_record.detail"
    _description = "Odoo Configuration Change Record Detail"
    _order = "configuration_change_record_id, sequence, id"

    configuration_change_record_id = fields.Many2one(
        comodel_name="odoo_configuration_change_record",
        string="Configuration Change Record",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(string="Sequence", required=True, default=10)
    model_name = fields.Char(string="Model Name", required=True)
    mode = fields.Selection(
        selection=[
            ("audit_log_url", "Audit Log URL"),
            ("video_log_url", "Video Log URL"),
            ("manual", "Manual"),
        ],
        string="Mode",
        required=True,
        default="manual",
    )
    audit_log_url = fields.Char(string="Audit Log URL", required=False)
    video_log_url = fields.Char(string="Video Log URL", required=False)
    before_attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        string="Before Attachments",
        relation="odoo_configuration_change_record_detail_before_attachment_rel",
        column1="detail_id",
        column2="attachment_id",
    )
    after_attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        string="After Attachments",
        relation="odoo_configuration_change_record_detail_after_attachment_rel",
        column1="detail_id",
        column2="attachment_id",
    )
    note = fields.Text(string="Note")
