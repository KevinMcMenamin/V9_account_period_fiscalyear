# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011- Solnet Solutions (<http://www.solnetsolutions.co.nz>).
#    Copyright (C) 2010 OpenERP S.A. http://www.openerp.com
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv
from openerp.tools.translate import _


class account_fiscalyear(osv.osv):
    _name = "account.fiscalyear"
    _description = "Fiscal Year"
    _columns = {
        'name': fields.char('Fiscal Year', required=True),
        'code': fields.char('Code', size=6, required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'date_start': fields.date('Start Date', required=True),
        'date_stop': fields.date('End Date', required=True),
        'period_ids': fields.one2many('account.period', 'fiscalyear_id', 'Periods'),
    }
    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }
    _order = "date_start, id"

    def create_period(self, cr, uid, ids, context=None, interval=1):
        period_obj = self.pool.get('account.period')
        for fy in self.browse(cr, uid, ids, context=context):
            ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
            period_obj.create(cr, uid, {
                'name': "%s %s" % (_('Opening Period'), ds.strftime('%Y')),
                'code': ds.strftime('00/%Y'),
                'date_start': ds,
                'date_stop': ds,
                'special': True,
                'fiscalyear_id': fy.id,
            })
            while ds.strftime('%Y-%m-%d') < fy.date_stop:
                de = ds + relativedelta(months=interval, days=-1)

                if de.strftime('%Y-%m-%d') > fy.date_stop:
                    de = datetime.strptime(fy.date_stop, '%Y-%m-%d')

                period_obj.create(cr, uid, {
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'fiscalyear_id': fy.id,
                })
                ds = ds + relativedelta(months=interval)
        return True


class AccountPeriod(osv.Model):

    _name = 'account.period'

    _description = "Account period"
    _columns = {
        'name': fields.char('Period Name', required=True),
        'code': fields.char('Code', size=12),
        'date_start': fields.date('Start of Period', required=True),
        'date_stop': fields.date('End of Period', required=True),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year', required=True, select=True),
        'company_id': fields.related('fiscalyear_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True)
    }
    _order = "date_start"
    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)', 'The name of the period must be unique per company!'),
    ]


class AccountMoveLine(osv.Model):

    def _period_get(self, cr, uid, ids, name, arg, context=None):

        result = {}
        if ids:
            for move in self.browse(cr, uid, ids, context=context):
                period_id = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', move.date),
                                                                             ('date_stop', '>=', move.date),
                                                                             ('company_id', '=', move.company_id.id)],
                                                                   context=context)
                if period_id:
                    result[move.id] = period_id[0]
        return result

    def _fiscalyear_get(self, cr, uid, ids, name, arg, context=None):

        result = {}
        if ids:
            for move in self.browse(cr, uid, ids, context=context):
                fiscalyear_id = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start', '<=', move.date),
                                                                                     ('date_stop', '>=', move.date),
                                                                                     ('company_id', '=', move.company_id.id)],
                                                                           context=context)
                if fiscalyear_id:
                    result[move.id] = fiscalyear_id[0]
        return result

    _inherit = 'account.move.line'

    _columns = {
        'period_id': fields.function(_period_get, type='many2one', relation='account.period', method=True, store=True, string='Period'),
        'fiscalyear_id': fields.function(_fiscalyear_get, type='many2one', relation='account.fiscalyear', method=True, store=True, string='Fiscal Year')
    }


class AccountInvoice(osv.Model):

    def _period_get(self, cr, uid, ids, name, arg, context=None):

        result = {}
        if ids:
            for invoice in self.browse(cr, uid, ids, context=context):
                period_id = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', invoice.date),
                                                                             ('date_stop', '>=', invoice.date),
                                                                             ('company_id', '=', invoice.company_id.id)],
                                                                   context=context)
                if period_id:
                    result[invoice.id] = period_id[0]
        return result

    _inherit = 'account.invoice'

    _columns = {
        'period_id': fields.function(_period_get, type='many2one', relation='account.period', method=True, store=True, string='Period'),
    }
