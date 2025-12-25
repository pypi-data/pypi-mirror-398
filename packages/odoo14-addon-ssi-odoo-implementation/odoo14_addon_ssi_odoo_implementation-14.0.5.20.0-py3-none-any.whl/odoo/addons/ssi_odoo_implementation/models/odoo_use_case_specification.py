# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import api, fields, models

from odoo.addons.ssi_decorator import ssi_decorator


class OdooUseCaseSpecification(models.Model):
    _name = "odoo_use_case_specification"
    _inherit = [
        "mixin.transaction_cancel",
        "mixin.transaction_done",
        "mixin.transaction_confirm",
        "mixin.transaction_partner",
    ]
    _description = "Odoo Use Case Specification"
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
    feature_id = fields.Many2one(
        comodel_name="odoo_feature",
        string="Feature",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    use_case_id = fields.Many2one(
        comodel_name="odoo_use_case",
        string="Use Case",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    partner_id = fields.Many2one(
        required=False,
    )
    odoo_implementation_id = fields.Many2one(
        comodel_name="odoo_implementation",
        string="Odoo Implementation",
        required=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    actor = fields.Text(
        string="Actor",
        required=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    actor_ids = fields.One2many(
        comodel_name="odoo_use_case_specification.actor",
        inverse_name="use_case_specification_id",
        string="Actors",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=True,
    )
    precondition = fields.Text(
        string="Precondition",
        required=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    precondition_ids = fields.One2many(
        comodel_name="odoo_use_case_specification.precondition",
        inverse_name="use_case_specification_id",
        string="Preconditions",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=True,
    )
    trigger = fields.Text(
        string="Trigger",
        required=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    trigger_ids = fields.One2many(
        comodel_name="odoo_use_case_specification.trigger",
        inverse_name="use_case_specification_id",
        string="Triggers",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=True,
    )
    main_flow = fields.Text(
        string="Main Flow",
        required=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    sub_flow_ids = fields.One2many(
        comodel_name="odoo_use_case_specification.sub_flow",
        inverse_name="use_case_specification_id",
        string="Sub Flows",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=True,
    )
    alternate_flow_ids = fields.One2many(
        comodel_name="odoo_use_case_specification.alternate_flow",
        inverse_name="use_case_specification_id",
        string="Alternate Flows",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=True,
    )
    exception_flow_ids = fields.One2many(
        comodel_name="odoo_use_case_specification.exception_flow",
        inverse_name="use_case_specification_id",
        string="Exception Flows",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=True,
    )
    business_rule = fields.Text(
        string="Business Rules",
        required=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    computed_value_ids = fields.One2many(
        comodel_name="odoo_use_case_specification.computed_value",
        inverse_name="use_case_specification_id",
        string="Computed Values",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=True,
    )
    onchange_ids = fields.One2many(
        comodel_name="odoo_use_case_specification.onchange",
        inverse_name="use_case_specification_id",
        string="Onchanges",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=True,
    )
    default_value_ids = fields.One2many(
        comodel_name="odoo_use_case_specification.default_value",
        inverse_name="use_case_specification_id",
        string="Default Values",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=True,
    )
    domain_ids = fields.One2many(
        comodel_name="odoo_use_case_specification.domain",
        inverse_name="use_case_specification_id",
        string="Domains",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=True,
    )
    button_ids = fields.One2many(
        comodel_name="odoo_use_case_specification.button",
        inverse_name="use_case_specification_id",
        string="Buttons",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=True,
    )
    postcondition = fields.Text(
        string="Postcondition",
        required=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    conditional_postcondition_ids = fields.One2many(
        comodel_name="odoo_use_case_specification.conditional_postcondition",
        inverse_name="use_case_specification_id",
        string="Conditional Postconditions",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=True,
    )

    @api.model
    def _default_date(self):
        return date.today()

    @api.onchange("feature_id")
    def onchange_use_case_id(self):
        self.use_case_id = False

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
