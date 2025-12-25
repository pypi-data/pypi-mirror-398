# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import xmlrpc.client

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OdooImplementation(models.Model):
    _name = "odoo_implementation"
    _inherit = [
        "mixin.transaction_open",
        "mixin.transaction_done",
    ]
    _description = "Odoo Implementation"
    _approval_from_state = "draft"

    # Attributes related to add element on view automatically
    _automatically_insert_view_element = True

    _statusbar_visible_label = "draft,open,done"

    _policy_field_order = [
        "open_ok",
        "restart_approval_ok",
        "restart_ok",
        "done_ok",
        "manual_number_ok",
    ]
    _header_button_order = [
        "action_open",
        "action_done",
        "action_restart",
    ]

    # Attributes related to add element on search view automatically
    _state_filter_order = [
        "dom_draft",
        "dom_open",
        "dom_done",
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
        domain=[
            ("is_company", "=", True),
            ("parent_id", "=", False),
        ],
        ondelete="restrict",
    )
    domain = fields.Char(
        string="Domain",
        required=True,
    )
    version_id = fields.Many2one(
        string="Version",
        comodel_name="odoo_version",
        ondelete="restrict",
        required=True,
    )
    installed_version_module_ids = fields.Many2many(
        string="Installed Modules",
        comodel_name="odoo_module",
        relation="rel_odoo_implementation_2_installed_version_module",
        column1="implementation_id",
        column2="module_id",
    )
    available_module_ids = fields.Many2many(
        string="Available Modules",
        comodel_name="odoo_module",
        relation="rel_odoo_implementation_2_available_module",
        column1="implementation_id",
        column2="module_id",
    )
    installed_website_theme_ids = fields.Many2many(
        string="Installed Website Theme",
        comodel_name="odoo_website_theme",
        relation="rel_odoo_implementation_2_installed_website_theme",
        column1="implementation_id",
        column2="theme_id",
    )
    default_module_ids = fields.Many2many(
        string="Default Modules",
        comodel_name="odoo_module",
        compute="_compute_module",
        store=False,
    )
    extra_module_ids = fields.Many2many(
        string="Extra Modules",
        comodel_name="odoo_module",
        compute="_compute_module",
        store=False,
    )
    missing_module_ids = fields.Many2many(
        string="Missing Modules",
        comodel_name="odoo_module",
        compute="_compute_module",
        store=False,
    )
    missing_core_module_ids = fields.Many2many(
        string="Missing Core Modules",
        comodel_name="odoo_module",
        compute="_compute_module",
        store=False,
    )
    missing_website_theme_module_ids = fields.Many2many(
        string="Missing Website Theme Modules",
        comodel_name="odoo_module",
        compute="_compute_module",
        store=False,
    )
    missing_module_count = fields.Integer(
        string="Missing Module Count",
        compute="_compute_module",
        store=True,
    )

    # To-Be Installed Modules
    to_be_installed_module_ids = fields.Many2many(
        string="Modules To Be Installed",
        comodel_name="odoo_module",
        compute="_compute_module",
        store=False,
    )
    to_be_installed_core_module_ids = fields.Many2many(
        string="Core Modules To Be Installed",
        comodel_name="odoo_module",
        compute="_compute_module",
        store=False,
    )
    to_be_installed_feature_module_ids = fields.Many2many(
        string="Feature Modules To Be Installed",
        comodel_name="odoo_module",
        compute="_compute_module",
        store=False,
    )
    to_be_installed_website_theme_module_ids = fields.Many2many(
        string="Website Theme Modules To Be Installed",
        comodel_name="odoo_module",
        compute="_compute_module",
        store=False,
    )
    to_be_installed_module_count = fields.Integer(
        string="To Be Installed Module Count",
        compute="_compute_module",
        store=True,
    )

    environment_id = fields.Many2one(
        string="Environment",
        comodel_name="odoo_environment",
        ondelete="restrict",
        required=True,
    )
    # XMLRPC
    xmlrpc_url = fields.Char(
        string="XMLRPC URL",
    )
    xmlrpc_login = fields.Char(
        string="XMLRPC Login",
    )
    xmlrpc_password = fields.Char(
        string="XMLRPC Password",
    )
    xmlrpc_db = fields.Char(
        string="XMLRPC DB",
    )
    xmlrpc_port = fields.Char(
        string="XMLRPC Port",
    )
    temp_odoo_module_list = fields.Text(
        string="Temp Odoo Module List",
    )
    feature_implementation_ids = fields.One2many(
        string="Feature Implementations",
        comodel_name="odoo_feature_implementation",
        inverse_name="implementation_id",
    )
    feature_ids = fields.Many2many(
        string="Features",
        comodel_name="odoo_feature",
        relation="rel_odoo_implementation_2_feature",
        column1="implementation_id",
        column2="feature_id",
    )
    feature_additional_functionality_ids = fields.Many2many(
        string="Feature Additional Functionalities",
        comodel_name="odoo_feature_additional_functionality",
        relation="rel_odoo_implementation_2_feature_additional_functionality",
        column1="implementation_id",
        column2="feature_additional_functionality_id",
    )

    # Update related fields
    update_ids = fields.One2many(
        string="Updates",
        comodel_name="odoo_implementation.update",
        inverse_name="implementation_id",
    )

    state = fields.Selection(
        string="State",
        selection=[
            ("draft", "Not Deployed"),
            ("open", "Running"),
            ("done", "Finish"),
        ],
        copy=False,
        default="draft",
        required=True,
        readonly=True,
    )

    @api.depends(
        "version_id",
        "installed_version_module_ids",
        "available_module_ids",
        "feature_ids",
    )
    def _compute_module(self):
        for record in self:
            core_modules = default_modules = record.version_id.default_module_ids
            website_modules = feature_modules = to_be_installed_modules = (
                to_be_installed_core_modules
            ) = to_be_installed_feature_modules = (
                to_be_installed_website_theme_modules
            ) = self.env["odoo_module"]
            for core_module in core_modules:
                default_modules += core_module.all_dependency_ids
                core_modules += core_module.all_dependency_ids
            for feature in record.feature_ids:
                default_modules += feature.default_module_ids
                feature_modules += feature.default_module_ids
                for default_module in feature.default_module_ids:
                    default_modules += default_module.all_dependency_ids
                    feature_modules += default_module.all_dependency_ids

            for additional in record.feature_additional_functionality_ids:
                default_modules += additional.default_module_ids
                feature_modules += additional.default_module_ids
                for default_module in additional.default_module_ids:
                    default_modules += default_module.all_dependency_ids
                    feature_modules += default_module.all_dependency_ids

            for theme in record.installed_website_theme_ids:
                website_modules += theme.default_module_ids
                default_modules += theme.default_module_ids
                for theme_module in theme.default_module_ids:
                    website_modules += theme_module.all_dependency_ids
                    default_modules += theme_module.all_dependency_ids
            extra_modules = record.installed_version_module_ids - default_modules
            missing_modules = default_modules - record.available_module_ids
            missing_core_modules = core_modules - record.available_module_ids
            missing_website_theme_modules = (
                website_modules - record.available_module_ids
            )
            to_be_installed_modules = (
                default_modules & record.available_module_ids
            ) - record.installed_version_module_ids
            to_be_installed_core_modules = (
                core_modules & record.available_module_ids
            ) - record.installed_version_module_ids
            to_be_installed_feature_modules = (
                feature_modules & record.available_module_ids
            ) - record.installed_version_module_ids
            to_be_installed_website_theme_modules = (
                website_modules & record.available_module_ids
            ) - record.installed_version_module_ids
            record.default_module_ids = default_modules
            record.extra_module_ids = extra_modules
            record.missing_module_ids = missing_modules
            record.missing_core_module_ids = missing_core_modules
            record.missing_website_theme_module_ids = missing_website_theme_modules
            record.to_be_installed_module_ids = to_be_installed_modules
            record.to_be_installed_core_module_ids = to_be_installed_core_modules
            record.to_be_installed_feature_module_ids = to_be_installed_feature_modules
            record.to_be_installed_website_theme_module_ids = (
                to_be_installed_website_theme_modules
            )
            record.missing_module_count = len(missing_modules)
            record.to_be_installed_module_count = len(to_be_installed_modules)

    @api.model
    def _default_date(self):
        return fields.Date.today()

    @api.model
    def _get_policy_field(self):
        res = super()._get_policy_field()
        policy_field = [
            "open_ok",
            "done_ok",
            "restart_ok",
            "manual_number_ok",
        ]
        res += policy_field
        return res

    def name_get(self):
        result = []
        for record in self:
            if getattr(record, self._document_number_field) == "/":
                name = record.domain
            else:
                name = record.domain + " (" + record.name + ")"
            result.append((record.id, name))
        return result

    def action_get_installed_module_xmlrpc(self):
        for record in self.sudo():
            record._get_installed_module_xmlrpc()
            record._get_installed_module()

    def action_get_available_module_xmlrpc(self):
        for record in self.sudo():
            record._get_available_module_xmlrpc()
            record._get_available_module()

    def action_get_installed_module(self):
        for record in self.sudo():
            record._get_installed_module()

    def action_get_available_module(self):
        for record in self.sudo():
            record._get_available_module()

    def _get_credentials(self):
        if not self.xmlrpc_url:
            raise UserError(_("XMLRPC Url not found"))
        if not self.xmlrpc_login:
            raise UserError(_("XMLRPC Login not found"))
        if not self.xmlrpc_password:
            raise UserError(_("XMLRPC Password not found"))
        if not self.xmlrpc_db:
            raise UserError(_("XMLRPC DB not found"))
        return {
            "url": self.xmlrpc_url,
            "login": self.xmlrpc_login,
            "password": self.xmlrpc_password,
            "db": self.xmlrpc_db,
        }

    def _get_installed_module_xmlrpc(self):
        self.ensure_one()
        resultList = ""
        self.temp_odoo_module_list = resultList
        credentials = self._get_credentials()
        url = credentials["url"]
        db = credentials["db"]
        username = credentials["login"]
        password = credentials["password"]

        try:
            common = xmlrpc.client.ServerProxy("{}/xmlrpc/2/common".format(url))
            uid = common.authenticate(db, username, password, {})
            object = xmlrpc.client.ServerProxy("{}/xmlrpc/2/object".format(url))
            result = object.execute_kw(
                db,
                uid,
                password,
                "ir.module.module",
                "search_read",
                [[["state", "=", "installed"]]],
                {"fields": ["name", "installed_version"]},
            )
        except Exception as e:
            raise UserError(_("%s") % (e))

        for value in result:
            resultList += value["name"] + ","

        self.temp_odoo_module_list = resultList

    def _get_available_module_xmlrpc(self):
        self.ensure_one()
        resultList = ""
        self.temp_odoo_module_list = resultList
        credentials = self._get_credentials()
        url = credentials["url"]
        db = credentials["db"]
        username = credentials["login"]
        password = credentials["password"]

        try:
            common = xmlrpc.client.ServerProxy("{}/xmlrpc/2/common".format(url))
            uid = common.authenticate(db, username, password, {})
            object = xmlrpc.client.ServerProxy("{}/xmlrpc/2/object".format(url))
            result = object.execute_kw(
                db,
                uid,
                password,
                "ir.module.module",
                "search_read",
                [[]],
                {"fields": ["name", "installed_version"]},
            )
        except Exception as e:
            raise UserError(_("%s") % (e))

        for value in result:
            resultList += value["name"] + ","

        self.temp_odoo_module_list = resultList

    def _get_installed_module(self):
        self.ensure_one()
        if self.temp_odoo_module_list:
            module_list = self.temp_odoo_module_list.split(",")
            valid_module_ids = []
            failed_module_list = []
            for module in module_list:
                module_id, failed_module = self._add_installed_module(module)
                if module_id:
                    valid_module_ids.append(module_id)

                if failed_module:
                    failed_module_list.append(module)
            installed_module_ids = (
                self.installed_version_module_ids.ids + valid_module_ids
            )
            self.write({"installed_version_module_ids": [(6, 0, installed_module_ids)]})

            if len(failed_module_list) > 0:
                self.write({"temp_odoo_module_list": ",".join(failed_module_list)})
            else:
                self.write(
                    {
                        "temp_odoo_module_list": "",
                    }
                )

    def _get_available_module(self):
        self.ensure_one()
        if self.temp_odoo_module_list:
            module_list = self.temp_odoo_module_list.split(",")
            valid_module_ids = []
            failed_module_list = []
            for module in module_list:
                module_id, failed_module = self._add_available_module(module)
                if module_id:
                    valid_module_ids.append(module_id)

                if failed_module:
                    failed_module_list.append(module)
            available_module_ids = self.available_module_ids.ids + valid_module_ids
            self.write({"available_module_ids": [(6, 0, available_module_ids)]})

            if len(failed_module_list) > 0:
                self.write({"temp_odoo_module_list": ",".join(failed_module_list)})
            else:
                self.write(
                    {
                        "temp_odoo_module_list": "",
                    }
                )

    def _add_installed_module(self, module_name):
        self.ensure_one()

        criteria = [("name", "=", module_name)]
        OdooModule = self.env["odoo_module"]
        module = OdooModule.search(criteria)
        if len(module) != 1:
            return False, module_name

        if module.id in self.installed_version_module_ids.ids:
            return False, False

        return module.id, False

    def _add_available_module(self, module_name):
        self.ensure_one()

        criteria = [("name", "=", module_name)]
        OdooModule = self.env["odoo_module"]
        module = OdooModule.search(criteria)
        if len(module) != 1:
            return False, module_name

        if module.id in self.available_module_ids.ids:
            return False, False

        return module.id, False
