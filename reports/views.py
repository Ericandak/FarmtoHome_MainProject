from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.utils import timezone
from datetime import timedelta
import csv
from django.conf import settings
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter,inch
from orders.models import Order, OrderItem
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
import os


@login_required
def generate_sales_report(request):
    start_date = parse_date(request.GET.get('start_date')) or timezone.now().date() - timedelta(days=30)
    end_date = parse_date(request.GET.get('end_date')) or timezone.now().date()
    report_type = request.GET.get('report_type', 'csv')

    orders = Order.objects.filter(
        items__product__seller=request.user,
        order_date__range=(start_date, end_date)
    ).distinct()

    if report_type == 'csv':
        return generate_csv_report(request, orders, start_date, end_date)
    elif report_type == 'pdf':
        return generate_pdf_report(request, orders, start_date, end_date)
    else:
        return HttpResponse("Invalid report type", status=400)

def generate_csv_report(request, orders, start_date, end_date):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date}_to_{end_date}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Date', 'Product', 'Quantity', 'Total Price'])

    for order in orders:
        for item in order.items.filter(product__seller=request.user):
            writer.writerow([order.id, order.order_date, item.product.name, item.quantity, item.total_price])

    return response

def generate_pdf_report(request, orders, start_date, end_date):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    try:
        logo_path = os.path.join(settings.STATIC_ROOT, 'assets', 'img', 'file.png')
        if not os.path.exists(logo_path):
            raise FileNotFoundError
    except (AttributeError, FileNotFoundError):
        # Use a default image or skip adding the logo
        logo_path = None

    if logo_path:
        logo = Image(logo_path, width=2*inch, height=1*inch)
        elements.append(logo)
        elements.append(Spacer(1, 0.5*inch))

    # Add title
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"Hey {request.user.username} ",styles['Title']))
    elements.append(Paragraph(f"your sales report from the date {start_date} to {end_date} is ready", styles['Title']))
    elements.append(Spacer(1, 0.25*inch))

    # Prepare data for the table
    data = [['Order ID', 'Date', 'Product', 'Quantity', 'Total Price']]
    for order in orders:
        for item in order.items.filter(product__seller=request.user):
            data.append([
                str(order.id),
                order.order_date.strftime('%d-%m-%Y'),
                item.product.name,
                str(item.quantity),
                f"{item.total_price:.2f}",
            ])

    # Create the table
    table = Table(data, repeatRows=1)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),  # Reduced font size to fit new column
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),  # Reduced font size to fit new column
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    table.setStyle(style)

    elements.append(table)

    # Build the PDF
    def add_background(canvas, doc):
        canvas.saveState()
        canvas.setFillColorRGB(0.9, 0.9, 0.9)  # Light grey color
        canvas.setFont('Helvetica', 50)
        canvas.rotate(45)
        canvas.drawCentredString(450, 0, "Farm To Home")
        canvas.restoreState()

    doc.build(elements, onFirstPage=add_background, onLaterPages=add_background)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="sales_report_{request.user.username}_{start_date}_to_{end_date}.pdf"'

    return response