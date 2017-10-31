# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################
{
    "name": "Stock Inventory Import from CSV file",
    "version": "9.0.1.0.0",
    "category": "Warehouse",
    "author": "Jakc Labs",
    "website": "http://www.jakc-labs.com",
    "depends": [
        "stock",
        "jakc_stock",
        "jakc_product",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/import_inventory_view.xml",
        "views/inventory_view.xml",
    ],
    "installable": True,
}
