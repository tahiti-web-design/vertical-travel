# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2010 - 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import fields, models, api, exceptions, _
import logging

_logger = logging.getLogger(__name__)


class Travel(models.Model):
    """Travel"""

    _description = _(__doc__)
    _name = 'travel.travel'
    _inherit = ['mail.thread']

    name = fields.Char('Name of travel', required=True)
    step_ids = fields.One2many(
        'travel.step',
        'travel_id',
        string='Etapes',
        help='Etapes du voyage.'
    )
    date_start = fields.Date('Start Date', required=True)
    date_stop = fields.Date('End Date', required=True)
    passenger_ids = fields.Many2many(
        'res.partner',
        id1='travel_id',
        id2='partner_id',
        string='Travel_Passengers',
    )
    manager_only = fields.Boolean(
        'Manager',
        function="is_manager_only",
        help='Can only be edited by a manager',
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('open', 'Saved'),
            ('booking', 'In Reservation'),
            ('reserved', 'Reserved'),
            ('confirmed', 'Confirmed'),
            ('done', 'Closed'),
        ],
        'Status',
        readonly=True,
        default='draft',
    )
    responsable = fields.Many2one(
        'res.users',
        string='Vendeur',
        required=False,
        ondelete='cascade',
        help="Responsable Agence",
    )
    contact_principal = fields.Many2one(
        'res.partner',
        'Customer',
        required=False,
    )
    devis_id = fields.Many2one(
        'sale.order',
        string='Devis',
        ondelete='cascade',
        help="Devis associé",
    )
    note = fields.Text('Note')

    @api.constrains('date_start', 'date_stop')
    def check_date(self):
        if self.date_start > self.date_stop:
            raise exceptions.Warning(
                _('Start date cannot be after departure date.')
            )

    @api.model
    def create(self, vals):
        """
        Warn if user tried to create travel with too many passengers for
        according to his security role.
        """
        return super(Travel, self).create(vals)

    @api.multi
    def write(self, vals):
        """
        Warn if user does not have rights to modify travel with current number
        of  passengers or to add more than the limit.
        """
        return super(Travel, self).write(vals)

    @api.multi
    def unlink(self):
        """Prevent deletion if travel isn't in draft

        Warn if ids being deleted contain a travel which has too many
        passengers for the current user to delete.
        """
        return super(Travel, self).unlink()

    @api.multi
    def travel_open(self):
        """Put the state of the travel into open"""
        return self.write({'state': 'open'})

    @api.multi
    def travel_book(self):
        """Put the state of the travel into booking"""
        return self.write({'state': 'booking'})

    @api.multi
    def travel_reserve(self):
        """Put the state of the travel into reserved"""
        return self.write({'state': 'reserved'})

    @api.multi
    def travel_confirm(self):
        """Put the state of the travel into confirmed"""
        return self.write({'state': 'confirmed'})

    @api.multi
    def travel_close(self):
        """Put the state of the travel into done"""
        return self.write({'state': 'done'})

    @api.multi
    def travel_print_vouchers(self):
        """Imprime les vouchers pour les étapes sélectionnées"""
        for step in self.step_ids.filtered(lambda s: s.print_voucher):
            self.note = self.note + ' ' + step.prestataire

    def get_print_vouchers(self):
        return self.step_ids.filtered(lambda s: s.print_voucher).sorted(key=lambda r: r.date_start)

    @api.onchange('devis_id')
    def on_change_devis_id(self):
        if self.devis_id:
            devis = self.env['sale.order'].browse([self.devis_id.id])
            if not self.date_start:
                if devis.date_start:
                    self.date_start = devis.date_start;
                if devis.date_end:
                    self.date_stop = devis.date_end
                if devis.note:
                    self.note = devis.note
                if devis.partner_id:
                    self.contact_principal = devis.partner_id
                    self.passenger_ids = [(4, devis.partner_id.id)]
                    self.name = devis.partner_id.name
                if devis.user_id:
                    self.responsable = devis.user_id
                lines = devis.order_line
                # _logger.info(lines)
                if lines:
                    tab_step = []
                    for line in lines:
                        # _logger.info(line)
                        # _logger.info(line.line_date_start)
                        step_dict = {
                            'date_start': line.line_date_start,
                            'date_end': line.line_date_end,
                            'description': line.name,
                            'print_voucher': True,
                            'nb_adult': devis.nb_adult,
                            'nb_child': devis.nb_child,
                            'nb_baby': devis.nb_baby
                        }
                        step = self.env['travel.step'].create(step_dict)
                        tab_step.append(step.id)
                    _logger.info(tab_step)
                    self.step_ids = [(6, 0, tab_step)]


class Etapes(models.Model):
    """Etapes du voyage"""
    _name = "travel.step"
    date_start = fields.Datetime(string='Du')
    date_end = fields.Datetime(string='Au')
    prestataire = fields.Char(string='Prestataire')
    description = fields.Char(string='Description')
    ile = fields.Char(string='Ile')
    travel_id = fields.Many2one(
        'travel.travel',
        'Travel',
        help='Travel for which the passenger is participating.'
    )
    print_voucher = fields.Boolean(string="V")
    nb_adult = fields.Integer(string="Adultes", required=True)
    nb_child = fields.Integer(string="Enfants", required=True)
    nb_baby = fields.Integer(string="Bébés", required=True)

    _defaults = {
        'nb_adult': 0,
        'nb_child': 0,
        'nb_baby': 0,
    }

    manager_only = fields.Boolean(
        'Manager',
        function="is_manager_only",
        help='Can only be edited by a manager',
    )

    @api.multi
    def is_manager_only(self):
        return False

    def action_voucher_send(self, cr, uid, ids, context=None):
        """
        This function opens a window to compose an email, with the edi sale template message loaded by default
        """
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'travel', 'email_template_edi_travel')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[
                1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'travel.step',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


class InfosVoyageurs(models.Model):
    _inherit = 'res.partner'

    passport_num = fields.Char(string="Passeport", help="Numéro de passeport")
    passport_date = fields.Date(
        string="Validité passeport"
    )
    visa_num = fields.Char(
        string="Visa",
        help="Numéro de Visa"
    )
    visa_date = fields.Date(
        string="Validité Visa"
    )
    esta_num = fields.Char(
        string="ESTA",
        help="Numéro ESTA"
    )
    esta_date = fields.Date(
        string="Validité ESTA"
    )
    carte_atn = fields.Char(
        string="Carte Air Tahiti/Nui",
        help="Numéro de carte de réduction"
    )
    carte_atn_date = fields.Date(
        string="Validité Carte"
    )
    travel_ids = fields.Many2many(
        'travel.travel',
        id2='travel_id',
        id1='partner_id',
        string='Travel_Passengers',
    )
    origine = fields.Selection(
        [
            ('website', 'Site internet'),
            ('facebook', 'Facebook'),
            ('phone', 'Téléphone'),
            ('email', 'Email'),
            ('agence', 'Agence'),
            ('other', 'Autre'),
        ],
        'Provenance',
        default='other',
    )
