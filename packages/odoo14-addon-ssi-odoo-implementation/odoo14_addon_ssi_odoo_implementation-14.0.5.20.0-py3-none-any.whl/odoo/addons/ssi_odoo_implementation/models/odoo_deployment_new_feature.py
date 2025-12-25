# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class OdooDeploymentNewFeature(models.Model):
    _name = "odoo_deployment.new_feature"
    _description = "Odoo Deployment - New Feature"

    deployment_id = fields.Many2one(
        string="# Odoo Deployment",
        comodel_name="odoo_deployment",
        required=True,
        ondelete="cascade",
    )
    feature_id = fields.Many2one(
        string="Feature",
        comodel_name="odoo_feature",
        required=True,
        ondelete="restrict",
    )
    feature_implementation_id = fields.Many2one(
        string="# Feature Implementation",
        comodel_name="odoo_feature_implementation",
        readonly=True,
    )

    def _create_feature_implementation(self):
        self.ensure_one()
        if self.feature_implementation_id:
            return True

        feature_implementation = self.env["odoo_feature_implementation"].create(
            self._prepare_feature_implementation()
        )
        self.write(
            {
                "feature_implementation_id": feature_implementation.id,
            }
        )

    def _prepare_feature_implementation(self):
        self.ensure_one()
        return {
            "implementation_id": self.deployment_id.implementation_id.id,
            "feature_id": self.feature_id.id,
        }

    def _delete_feature_implementation(self):
        if not self.feature_implementation_id:
            return True
        feature_implementation = self.feature_implementation_id
        self.write(
            {
                "feature_implementation_id": False,
            }
        )
        feature_implementation.unlink()
