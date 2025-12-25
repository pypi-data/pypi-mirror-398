# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.ssi_decorator import ssi_decorator


class OdooFeatureIssue(models.Model):
    _name = "odoo_feature_issue"
    _inherit = [
        "mixin.transaction_cancel",
        "mixin.transaction_done",
        "mixin.transaction_open",
        "mixin.transaction_ready",
        "mixin.transaction_confirm",
        "mixin.task",
    ]
    _description = "Odoo Feature Issue"
    _approval_from_state = "draft"
    _approval_to_state = "ready"
    _approval_state = "confirm"
    _after_approved_method = "action_ready"

    # Attributes related to add element on view automatically
    _automatically_insert_view_element = True
    _automatically_insert_ready_policy_fields = False
    _automatically_insert_ready_button = False

    _task_create_page = True
    _task_page_xpath = "//page[2]"
    _task_template_position = "before"

    _statusbar_visible_label = "draft,confirm,ready,open"

    _policy_field_order = [
        "ready_ok",
        "open_ok",
        "confirm_ok",
        "approve_ok",
        "reject_ok",
        "restart_approval_ok",
        "cancel_ok",
        "restart_ok",
        "manual_number_ok",
    ]
    _header_button_order = [
        "action_open",
        "action_confirm",
        "action_approve_approval",
        "action_reject_approval",
        "%(ssi_transaction_cancel_mixin.base_select_cancel_reason_action)d",
        "action_restart",
    ]

    # Attributes related to add element on search view automatically
    _state_filter_order = [
        "dom_draft",
        "dom_ready",
        "dom_open",
        "dom_confirm",
        "dom_reject",
        "dom_done",
        "dom_cancel",
    ]

    _create_sequence_state = "ready"

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
    description = fields.Char(
        string="Description",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    precondition = fields.Text(
        string="Precondition",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    steps_to_reproduce = fields.Text(
        string="Steps to Reproduce",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    current_behavior = fields.Text(
        string="Current Behavior",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    expected_behavior = fields.Text(
        string="Expected Behavior",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    error_log = fields.Text(
        string="Error Log",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    feature_id = fields.Many2one(
        string="Feature",
        comodel_name="odoo_feature",
        ondelete="restrict",
        required=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    version_id = fields.Many2one(
        string="Version",
        comodel_name="odoo_version",
        ondelete="restrict",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    use_case_ids = fields.Many2many(
        string="Related Use Cases",
        comodel_name="odoo_use_case",
        relation="odoo_feature_issue_use_case_rel",
        column1="feature_issue_id",
        column2="use_case_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    module_ids = fields.Many2many(
        string="Related Modules",
        comodel_name="odoo_module",
        relation="odoo_feature_issue_module_rel",
        column1="feature_issue_id",
        column2="module_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.model
    def _default_date(self):
        return fields.Date.today()

    @api.model
    def _get_policy_field(self):
        res = super()._get_policy_field()
        policy_field = [
            "ready_ok",
            "open_ok",
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
