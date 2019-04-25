# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2013 Savoir-faire Linux
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

from openerp.tests.common import TransactionCase
from openerp import exceptions
import time
import copy

YEAR = str(time.localtime(time.time())[0])
TRAVEL_VALS = {
    'name': 'This is a test travel name',
    'date_start': YEAR + '-01-01',
    'date_stop': YEAR + '-01-14',
}


class TestTravel(TransactionCase):

    def setUp(self):
        """Create values for test, travel and partner also created"""
        super(TestTravel, self).setUp()
        self.year = copy.copy(YEAR)
        self.vals = copy.copy(TRAVEL_VALS)
        self.travel = self.env['travel.travel'].create(self.vals)

    def test_write_travel(self):
        """Test basic write of date_stop on travel.travel"""
        self.travel.write({'date_stop': self.year + '-01-21'})

    def test_unlink_travel(self):
        """Test basic unlink of travel.travel"""
        self.travel.unlink()

    def test_change_state_travel(self):
        """Test workflow of travel.travel"""
        states = {
            'open': 'travel_open',
            'booking': 'travel_book',
            'reserved': 'travel_reserve',
            'confirmed': 'travel_confirm',
            'done': 'travel_close',
        }
        for state, func in states.iteritems():
            self.assertTrue(
                getattr(self.travel, func)(),
                "Failure while calling %s" % func
            )
            self.assertEqual(
                self.travel.state,
                state,
                "Travel state did not properly update to %s after calling %s"
                % (state, func)
            )
