# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.ssi_decorator import ssi_decorator


class OdooDeployment(models.Model):
    _name = "odoo_deployment"
    _inherit = [
        "mixin.transaction_confirm",
        "mixin.transaction_open",
        "mixin.transaction_cancel",
        "mixin.transaction_done",
    ]
    _description = "Odoo Deployment"
    _approval_from_state = "draft"
    _approval_to_state = "open"
    _approval_state = "confirm"
    _after_approved_method = "action_open"

    # Attributes related to add element on view automatically
    _automatically_insert_view_element = True

    # Attributes related to add element on form view automatically
    _automatically_insert_open_policy_fields = False
    _automatically_insert_done_policy_fields = True
    _automatically_insert_open_button = False

    _statusbar_visible_label = "draft,confirm,open"

    _policy_field_order = [
        "confirm_ok",
        "approve_ok",
        "reject_ok",
        "done_ok",
        "restart_approval_ok",
        "cancel_ok",
        "restart_ok",
        "manual_number_ok",
    ]
    _header_button_order = [
        "action_confirm",
        "action_approve_approval",
        "action_reject_approval",
        "action_done",
        "%(ssi_transaction_cancel_mixin.base_select_cancel_reason_action)d",
        "action_restart",
    ]

    # Attributes related to add element on search view automatically
    _state_filter_order = [
        "dom_draft",
        "dom_confirm",
        "dom_reject",
        "dom_open",
        "dom_done",
        "dom_cancel",
    ]

    _create_sequence_state = "open"

    date = fields.Date(
        string="Date",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: self._default_date(),
    )
    partner_id = fields.Many2one(
        string="Client",
        comodel_name="res.partner",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    contact_id = fields.Many2one(
        string="Contact",
        comodel_name="res.partner",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    implementation_id = fields.Many2one(
        string="# Implementation",
        comodel_name="odoo_implementation",
        ondelete="restrict",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    install_core_module = fields.Boolean(
        string="Install Missing Core Modules",
        default=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    install_new_feature = fields.Boolean(
        string="Install New Features",
        default=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    install_missing_feature_module = fields.Boolean(
        string="Install Missing Feature Modules",
        default=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    install_extra_module = fields.Boolean(
        string="Install Extra Modules",
        default=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    install_website_theme = fields.Boolean(
        string="Install Website Theme",
        default=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    extra_module_ids = fields.Many2many(
        string="Extra Modules",
        comodel_name="odoo_module",
        relation="rel_odoo_deployment_2_extra_module",
        column1="deployment_id",
        column2="module_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    website_theme_ids = fields.Many2many(
        string="Website Themes",
        comodel_name="odoo_website_theme",
        relation="rel_odoo_deployment_2_website_theme",
        column1="deployment_id",
        column2="website_theme_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    missing_website_theme_module_ids = fields.Many2many(
        string="Missing Website Themes Modules",
        comodel_name="odoo_module",
        relation="rel_odoo_deployment_2_missing_website_theme_module",
        column1="deployment_id",
        column2="module_id",
        readonly=True,
    )
    core_module_ids = fields.Many2many(
        string="Core Modules",
        comodel_name="odoo_module",
        relation="rel_odoo_deployment_2_core_module",
        column1="deployment_id",
        column2="module_id",
        readonly=True,
    )
    missing_feature_module_ids = fields.Many2many(
        string="Missing Feature Modules",
        comodel_name="odoo_module",
        relation="rel_odoo_deployment_2_missing_feature_module",
        column1="deployment_id",
        column2="module_id",
        readonly=True,
    )
    installed_module_ids = fields.Many2many(
        string="Installed Modules",
        comodel_name="odoo_module",
        relation="rel_odoo_deployment_2_installed_module",
        column1="deployment_id",
        column2="module_id",
        readonly=True,
    )
    new_feature_ids = fields.One2many(
        string="New Features",
        comodel_name="odoo_deployment.new_feature",
        inverse_name="deployment_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    new_feature_module_ids = fields.Many2many(
        string="New Modules To Install",
        comodel_name="odoo_module",
        relation="rel_odoo_deployment_2_new_module",
        column1="deployment_id",
        column2="module_id",
        readonly=True,
    )
    new_module_ids = fields.Many2many(
        string="New Feature Modules",
        comodel_name="odoo_module",
        relation="rel_odoo_deployment_2_new_module",
        column1="deployment_id",
        column2="module_id",
        readonly=True,
    )
    state = fields.Selection(
        string="State",
        selection=[
            ("draft", "Draft"),
            ("confirm", "Waiting for Appoval"),
            ("open", "In Progress"),
            ("done", "Done"),
            ("reject", "Rejected"),
            ("cancel", "Cancelled"),
        ],
        copy=False,
        default="draft",
        required=True,
        readonly=True,
    )

    @api.model
    def _default_date(self):
        return fields.Date.today()

    @api.model
    def _get_policy_field(self):
        res = super()._get_policy_field()
        policy_field = [
            "confirm_ok",
            "approve_ok",
            "reject_ok",
            "open_ok",
            "done_ok",
            "cancel_ok",
            "restart_ok",
            "restart_approval_ok",
            "manual_number_ok",
        ]
        res += policy_field
        return res

    @api.onchange(
        "partner_id",
    )
    def onchange_contact_id(self):
        self.contact_id = False

    @api.onchange(
        "partner_id",
    )
    def onchange_implementation_id(self):
        self.implementation_id = False

    @api.onchange(
        "install_extra_module",
    )
    def onchange_extra_module_ids(self):
        if not self.install_extra_module:
            self.extra_module_ids = False

    @api.onchange(
        "implementation_id",
    )
    def onchange_installed_module_ids(self):
        self.installed_module_ids = False
        if self.implementation_id:
            self.installed_module_ids = (
                self.implementation_id.installed_version_module_ids
            )

    @api.onchange(
        "install_core_module",
        "implementation_id",
    )
    def onchange_core_module_ids(self):
        self.core_module_ids = False
        if self.install_core_module and self.implementation_id:
            self.core_module_ids = (
                self.implementation_id.version_id.default_module_ids
                - self.implementation_id.installed_version_module_ids
            )

    @api.onchange(
        "install_missing_feature_module",
        "implementation_id",
    )
    def onchange_missing_feature_module_ids(self):
        self.missing_feature_module_ids = False
        if self.install_missing_feature_module and self.implementation_id:
            result = self.env["odoo_module"]
            for feature in self.implementation_id.feature_implementation_ids:
                result = result + feature.feature_id.default_module_ids
                for module in feature.feature_id.default_module_ids:
                    result = result + module.all_dependency_ids
            if len(result) > 0:
                self.missing_feature_module_ids = (
                    result - self.implementation_id.installed_version_module_ids
                )

    @api.onchange(
        "install_new_feature",
        "implementation_id",
    )
    def onchange_new_feature_module_ids(self):
        self.new_feature_module_ids = False
        if self.install_new_feature and self.implementation_id:
            result = self.env["odoo_module"]
            for feature in self.new_feature_ids:
                result = result + feature.feature_id.default_module_ids
                for module in feature.feature_id.default_module_ids:
                    result = result + module.all_dependency_ids
            if len(result) > 0:
                self.new_feature_module_ids = (
                    result - self.implementation_id.installed_version_module_ids
                )

    @api.onchange(
        "install_website_theme",
        "implementation_id",
    )
    def onchange_website_theme_ids(self):
        self.missing_website_theme_module_ids = False
        if self.install_website_theme and self.implementation_id:
            result = self.env["odoo_module"]
            for website_thene in self.website_theme_ids:
                result = result + website_thene.default_module_ids
                for module in website_thene.default_module_ids:
                    result = result + module.all_dependency_ids
            if len(result) > 0:
                self.missing_website_theme_module_ids = (
                    result - self.implementation_id.installed_version_module_ids
                )

    @api.onchange(
        "new_feature_module_ids",
        "missing_feature_module_ids",
        "core_module_ids",
        "extra_module_ids",
        "missing_website_theme_module_ids",
    )
    def onchange_new_module_ids(self):
        self.new_module_ids = (
            self.new_feature_module_ids
            + self.missing_feature_module_ids
            + self.core_module_ids
            + self.extra_module_ids
            + self.missing_website_theme_module_ids
        )

    @ssi_decorator.post_done_action()
    def _10_create_feature_implementation(self):
        for new_feature in self.new_feature_ids:
            new_feature._create_feature_implementation()

    @ssi_decorator.post_done_action()
    def _20_update_installed_modules(self):
        modules = (
            self.implementation_id.installed_version_module_ids + self.new_module_ids
        )
        self.implementation_id.write(
            {
                "installed_version_module_ids": [(6, 0, modules.ids)],
            }
        )

    @ssi_decorator.post_done_action()
    def _30_update_website_theme(self):
        website_themes = (
            self.implementation_id.installed_website_theme_ids + self.website_theme_ids
        )
        self.implementation_id.write(
            {
                "installed_website_theme_ids": [(6, 0, website_themes.ids)],
            }
        )

    @ssi_decorator.post_cancel_action()
    def _10_delete_feature_implementation(self):
        for new_feature in self.new_feature_ids:
            new_feature._delete_feature_implementation()

    @ssi_decorator.post_cancel_action()
    def _20_delete_installed_modules(self):
        modules = (
            self.implementation_id.installed_version_module_ids - self.new_module_ids
        )
        self.implementation_id.write(
            {
                "installed_version_module_ids": [(6, 0, modules.ids)],
            }
        )

    @ssi_decorator.post_cancel_action()
    def _30_delete_website_theme(self):
        website_themes = (
            self.implementation_id.installed_website_theme_ids - self.website_theme_ids
        )
        self.implementation_id.write(
            {
                "installed_website_theme_ids": [(6, 0, website_themes.ids)],
            }
        )
