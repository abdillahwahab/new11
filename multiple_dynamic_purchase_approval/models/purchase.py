from odoo import api, fields, models, exceptions, _
from datetime import datetime

class abd_confirmed(models.Model):
    _name = 'purchase.order.confirmed'

    name = fields.Many2one('res.users', 'Confirmed By')
    order_id = fields.Many2one('purchase.order', 'Purchase')

class abd_purchase(models.Model):
    _inherit = 'purchase.order'

    can_approve = fields.Boolean('Can Approve', compute='_can_approve')
    can_confirm = fields.Boolean('Can Approve', compute='_can_confirm')
    confirmed_ids = fields.One2many('purchase.order.confirmed', 'order_id', 'Confirmed By', domain=[('name','!=',False)])

    @api.multi
    def button_confirmby(self):
        for rec in self:
            rec.confirmed_ids = (0, 0,  {'name': self.env.user.id})
        return True

    @api.multi
    def _can_confirm(self):
        for rec in self:
            rec.can_confirm = False
            if rec.state not in ['to approve']:
                continue
            ada = False
            for conf in rec.confirmed_ids:
                if conf.name.id == self.env.user.id:
                    ada = True
            if rec.company_id.po_double_validation == 'two_step' and not ada:
                for limit in self.env.user.company_id.limit_list:
                    self._cr.execute("""SELECT 1 FROM res_groups_users_rel WHERE uid=%s AND gid = %s """, (self._uid, (limit.name.id)))
                    if bool(self._cr.fetchone()):
                        rec.can_confirm = True

    @api.multi
    def _can_approve(self):
        for rec in self:
            rec.can_approve = False
            if rec.state not in ['to approve']:
                continue
            if rec.company_id.po_double_validation == 'two_step':
                for limit in self.env.user.company_id.limit_list:
                    self._cr.execute("""SELECT 1 FROM res_groups_users_rel WHERE uid=%s AND gid = %s """, (self._uid, (limit.name.id)))
                    if bool(self._cr.fetchone()):
                        if limit.limit < 0:
                            rec.can_approve = True
                        if rec.amount_total < self.env.user.company_id.currency_id.compute(limit.limit, rec.currency_id):
                            rec.can_approve = True

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            deal = False
            two_step = False
            if order.company_id.po_double_validation == 'one_step':
                deal = True
            elif order.company_id.po_double_validation == 'two_step':
                for limit in self.env.user.company_id.limit_list:
                    self._cr.execute("""SELECT 1 FROM res_groups_users_rel WHERE uid=%s AND gid = %s """, (self._uid, (limit.name.id)))
                    if bool(self._cr.fetchone()):
                        if limit.limit < 0:
                            deal = True
                            two_step = True
                            continue
                        if order.amount_total < self.env.user.company_id.currency_id.compute(limit.limit, order.currency_id):
                            deal = True
                            two_step = True

            if order.user_has_groups('base.group_system'):
                deal = True

            if deal:
                order.button_approve()
            else:
                if not two_step:
                    #order.company_id.po_double_validation_amount = 0
                    res = super(abd_purchase, self).button_confirm()
                    order.button_confirmby()
                order.write({'state': 'to approve'})
        return True
