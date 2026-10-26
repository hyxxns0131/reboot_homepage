import csv
import io
from decimal import Decimal
from flask import Response


def safe_cell(value):
    if isinstance(value, Decimal):
        return format(value, '.2f')
    if isinstance(value, float):
        return format(value, '.4f')
    text = str(value if value is not None else '')
    return "'" + text if text.lstrip().startswith(('=', '+', '-', '@', '\t', '\r', '\n')) or text.startswith(('\t', '\r', '\n')) else text


def csv_response(rows, fields, filename):
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(fields)
    for row in rows:
        writer.writerow([safe_cell(row.get(field, '')) for field in fields])
    return Response(output.getvalue().encode('utf-8-sig'), content_type='text/csv; charset=utf-8', headers={'Content-Disposition': f'attachment; filename="{filename}"', 'Cache-Control': 'no-store'})

