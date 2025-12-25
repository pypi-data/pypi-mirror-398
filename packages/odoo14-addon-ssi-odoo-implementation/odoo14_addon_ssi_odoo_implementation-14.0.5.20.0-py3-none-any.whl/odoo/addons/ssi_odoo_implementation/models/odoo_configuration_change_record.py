# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import api, fields, models

from odoo.addons.ssi_decorator import ssi_decorator


class OdooConfigurationChangeRecord(models.Model):
    _name = "odoo_configuration_change_record"
    _inherit = [
        "mixin.transaction_cancel",
        "mixin.transaction_done",
        "mixin.transaction_confirm",
        "mixin.transaction_partner",
    ]
    _description = "Odoo Configuration Change Record"
    _approval_from_state = "draft"
    _approval_to_state = "done"
    _approval_state = "confirm"
    _after_approved_method = "action_done"

    # Attributes related to add element on view automatically
    _automatically_insert_view_element = True
    _automatically_insert_done_policy_fields = False
    _automatically_insert_done_button = False

    _statusbar_visible_label = "draft,confirm"

    _policy_field_order = [
        "confirm_ok",
        "approve_ok",
        "reject_ok",
        "restart_approval_ok",
        "cancel_ok",
        "restart_ok",
        "manual_number_ok",
    ]
    _header_button_order = [
        "action_confirm",
        "action_approve_approval",
        "action_reject_approval",
        "%(ssi_transaction_cancel_mixin.base_select_cancel_reason_action)d",
        "action_restart",
    ]

    # Attributes related to add element on search view automatically
    _state_filter_order = [
        "dom_draft",
        "dom_confirm",
        "dom_reject",
        "dom_done",
        "dom_cancel",
    ]

    _create_sequence_state = "done"

    date = fields.Date(
        string="Date",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: self._default_date(),
    )
    summary = fields.Char(
        string="Summary",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    odoo_implementation_id = fields.Many2one(
        comodel_name="odoo_implementation",
        string="Odoo Implementation",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    detail_ids = fields.One2many(
        comodel_name="odoo_configuration_change_record.detail",
        inverse_name="configuration_change_record_id",
        string="Details",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.model
    def _default_date(self):
        return date.today()

    @api.onchange("partner_id")
    def onchange_odoo_implementation_id(self):
        self.odoo_implementation_id = False

    @api.model
    def _get_policy_field(self):
        res = super()._get_policy_field()
        policy_field = [
            "confirm_ok",
            "approve_ok",
            "reject_ok",
            "restart_approval_ok",
            "done_ok",
            "cancel_ok",
            "restart_ok",
            "manual_number_ok",
        ]
        res += policy_field
        return res

    @ssi_decorator.insert_on_form_view()
    def _insert_form_element(self, view_arch):
        if self._automatically_insert_view_element:
            view_arch = self._reconfigure_statusbar_visible(view_arch)
        return view_arch
