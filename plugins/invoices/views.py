# encoding: UTF-8
# browsershots.org - Test your web design in different browsers
# Copyright (C) 2007 Johann C. Rocholl <johann@browsershots.org>
#
# Browsershots is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Browsershots is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""
Priority views.
"""

__revision__ = "$Rev: 2744 $"
__date__ = "$Date: 2008-03-30 17:56:40 -0700 (Sun, 30 Mar 2008) $"
__author__ = "$Author: johann $"

import os
from decimal import Decimal, getcontext
import reportlab.pdfgen.canvas
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import letter, A4
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from shotserver04.priority.models import UserPriority
from shotserver04.common.templatetags.human import human_date
from shotserver04.common.templatetags.countries import country_name


@login_required
def overview(http_request):
    priorities_list = UserPriority.objects.filter(
	user=http_request.user).order_by('-activated')
    return render_to_response('invoices/overview.html', locals(),
        context_instance=RequestContext(http_request))


@login_required
def details(http_request, id):
    id = int(id)
    priority = get_object_or_404(UserPriority, id=id)
    if http_request.user != priority.user:
        return error_page(http_request, _("Access Denied"),
            _("This invoice is for a different user."))
    return render_to_response('invoices/details.html', locals(),
        context_instance=RequestContext(http_request))


def drawStrings(canvas, x, y, *lines):
    step = 0.5*cm
    for line in lines:
        if isinstance(line, int):
            if line < 0:
                canvas.setFont('Helvetica-Bold', abs(line))
            else:
                canvas.setFont('Helvetica', abs(line))
            step = abs(line) / 24.0 * cm
            continue
        canvas.drawString(x, y, line)
        y -= step


@login_required
def pdf(http_request, id):
    id = int(id)
    priority = get_object_or_404(UserPriority, id=id)
    if http_request.user != priority.user and http_request.user.id != 1:
        return error_page(http_request, _("Access Denied"),
            _("This invoice is for a different user."))
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%d.pdf' % id

    if priority.country.upper() == 'US':
        pagesize = letter
    else:
        pagesize = A4
    width, height = pagesize
    canvas = reportlab.pdfgen.canvas.Canvas(response, pagesize=pagesize)

    left = 4*cm
    middle = 6*cm
    right = 13*cm

    german = priority.country.upper() == 'DE'
    if german:
        getcontext().prec = 3
        payment = Decimal('%.2f' % (float(priority.payment) / 1.19))
        tax = priority.payment - payment
    else:
        payment = priority.payment
        tax = Decimal('0.00')

    dir = os.path.dirname(__file__)
    logo = os.path.join(dir, 'logo.jpg')
    canvas.drawInlineImage(logo, right, 23.7*cm,
                           width=1*cm, height=1*cm)
    canvas.setFont('Helvetica', 16)
    canvas.drawString(right + 1.2*cm, 24*cm, u"Browsershots")

    drawStrings(canvas, right, 23*cm, 12,
                u"Johann C. Rocholl",
                u"johann@browsershots.org",
                u"Pütnitzer Str. 12",
                u"18311 Ribnitz-Damgarten")

    # canvas.drawString(left, 25*cm, u"Customer:")
    drawStrings(canvas, left, 23*cm,
                u"%s %s" % (priority.user.first_name.title(),
                            priority.user.last_name.title()),
                priority.user.email)
    if german:
        canvas.drawString(left, 22*cm, u"Deutschland")
        canvas.drawString(right, 21*cm, u"Deutschland")
    else:
        canvas.drawString(left, 22*cm, country_name(priority.country))
        canvas.drawString(right, 21*cm, u"Germany")

    table = 14*cm
    if german:
        drawStrings(canvas, left, 17*cm,
                    -12, u"Rechnung Nummer %d" % id,
                    12, u"Datum: %s" % human_date(priority.activated))
        drawStrings(canvas, left, table,
                    -12, u"Menge", '',
                    12, u"1", '', '',
                    u"19%")
        drawStrings(canvas, middle, table,
                    -12, u"Beschreibung", '',
                    12, u"Priority processing für %s" % priority.user.username,
                    u"von %s bis %s" % (human_date(priority.activated),
                                        human_date(priority.expire)), '',
                    u"Mehrwertsteuer", '',
                    u"Rechnungsbetrag (Brutto)")
        drawStrings(canvas, right, table,
                    -12, u"Preis", '',
                    12, u"%s %.2f" % (priority.currency, payment), '', '',
                    u"%s %.2f" % (priority.currency, tax), '',
                    u"%s %.2f" % (priority.currency, priority.payment))
        drawStrings(canvas, left, 8*cm,
                    u"Vielen Dank für Ihren Auftrag.", '',
                    u"Mit freundlichen Grüßen,",
                    u"Johann C. Rocholl")
    else:
        drawStrings(canvas, left, 17*cm,
                    -12, u"Invoice Number %d" % id,
                    12, u"Date: %s" % human_date(priority.activated))
        drawStrings(canvas, left, table,
                    -12, u"Qty", '',
                    12, u"1")
        drawStrings(canvas, middle, table,
                    -12, u"Description", '',
                    12, u"Priority processing for %s" % priority.user.username,
                    u"from %s to %s" % (human_date(priority.activated),
                                       human_date(priority.expire)))
        drawStrings(canvas, right, table,
                    -12, u"Price", '',
                    12, u"%s %.2f" % (priority.currency, priority.payment))
        drawStrings(canvas, left, 10*cm,
u"For customers outside Germany, this invoice does not include",
u"sales tax, value added tax (VAT) or goods and services tax (GST).",
u"You may have to pay use tax or reverse charge VAT, according",
u"to the tax laws in your country or state.", '',
                    u"Thank you for your business.", '',
                    u"Kind regards,",
                    u"Johann C. Rocholl")

    canvas.line(left, 3.5*cm, width - left, 3.5*cm)
    if german:
        drawStrings(canvas, left, 3*cm, 8,
                    u"Inhaber: Johann C. Rocholl",
                    u"PayPal: johann@browsershots.org")
        drawStrings(canvas, right, 3*cm, 8,
                    u"Konto: 3415213",
                    u"BLZ: 38070724")
    else:
        drawStrings(canvas, left, 3*cm, 8,
                    u"Sole proprietor: Johann C. Rocholl",
                    u"PayPal: johann@browsershots.org")
        drawStrings(canvas, right, 3*cm, 8,
                    u"IBAN: DE63380707240341521300",
                    u"BIC / SWIFT: DEUTDEDBXXX")

    canvas.showPage()
    canvas.save()
    return response
