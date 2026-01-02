# Copyright 2022 - Komun.org Álex Berbel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import content_disposition
import base64

_logger = logging.getLogger(__name__)

class Download_xls(http.Controller):
    
    @http.route('/web/binary/download_demo_importar_ventas', type='http', auth="public")
    def download_document(self, **kw):
        invoice_xls = request.env['ir.attachment'].search([('name','=','sale_order_line.xlsx')])
        _logger.debug(f"invoice_xls: {invoice_xls}")
        filecontent = invoice_xls.datas
        _logger.debug(f"filecontent: {filecontent}")
        filename = 'Demo_importar_ventas.xlsx'
        filecontent = base64.b64decode(filecontent)

        return request.make_response(filecontent,
            [('Content-Type', 'application/octet-stream'),
            ('Content-Disposition', content_disposition(filename))])
