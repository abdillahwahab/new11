from odoo import api, fields, models, exceptions, _
from datetime import datetime

class abd_res_config_settings(models.TransientModel):
	_inherit = 'res.config.settings'

	@api.model
	def default_get(self, fields):
		res = super(abd_res_config_settings, self).default_get(fields)
		company = self.env.user.company_id
		limit_list = []
		for ls in company.limit_list:
			src = {
				'name': ls.name.id if ls.name else False,
				'limit': ls.limit,
				'company_currency_id': ls.company_currency_id.id,
			}
			limit_list.append((0,0,src))
		res['limit_list'] = limit_list
		return res

	limit_list = fields.One2many('abd.list.approval.group.temp','config_id','Limit List')

	@api.model
	def create(self, vals):
		res = super(abd_res_config_settings, self).create(vals)
		company = self.env.user.company_id
		if res:
			company.limit_list.unlink()
			limit_list = []
			for ls in res.limit_list:
				src = {
					'name': ls.name.id if ls.name else False,
					'limit': ls.limit,
				}
				limit_list.append((0,0,src))
			company.limit_list = limit_list
		return res

class abd_list_approval_temp(models.TransientModel):
	_name = 'abd.list.approval.group.temp'

	@api.model
	def _get_domain(self):
		app = self.env.ref('base.module_category_purchase_management')
		return [('category_id','=',app.id)]

	name = fields.Many2one('res.groups','Groups', required=True , domain=_get_domain )
	config_id = fields.Many2one('res.config.settings','Config ID')
	#limit = fields.Float('Limit Purchase', required=True) #using negatif for Unlimited
	limit = fields.Monetary(string="Purchase Limit", currency_field='company_currency_id')
	company_currency_id = fields.Many2one('res.currency', related='config_id.company_id.currency_id', readonly=True, help='Utility field to express amount currency')


class abd_res_company(models.Model):
	_inherit = 'res.company'

	limit_list = fields.One2many('abd.list.approval.group','config_id','Limit List')

class abd_list_approval(models.Model):
	_name = 'abd.list.approval.group'

	name = fields.Many2one('res.groups','Groups')
	config_id = fields.Many2one('res.company','Config ID')
	#limit = fields.Float('Limit Purchase') #using negatif for for Unlimited
	limit = fields.Monetary(string="Purchase Limit", currency_field='company_currency_id')
	company_currency_id = fields.Many2one('res.currency', related='config_id.currency_id', readonly=True, help='Utility field to express amount currency')
