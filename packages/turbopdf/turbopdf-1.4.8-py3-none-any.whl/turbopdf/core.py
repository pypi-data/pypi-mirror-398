import subprocess
import sys
import os

import pdfkit

def _check_wkhtmltopdf():
    """Verifica si wkhtmltopdf está disponible en PATH"""
    try:
        # Intenta ejecutar wkhtmltopdf --version
        result = subprocess.run(['wkhtmltopdf', '--version'], capture_output=True, text=True, check=True)
        print("✅ wkhtmltopdf encontrado:", result.stdout.strip())
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ wkhtmltopdf no encontrado. Por favor, instálalo:")
        if sys.platform.startswith('win'):
            print("   Descárgalo desde: https://github.com/wkhtmltopdf/packaging/releases")
            print("   Usa la versión 0.12.6 y asegúrate de que esté en PATH.")
        elif sys.platform.startswith('linux'):
            print("   Instálalo con: sudo apt-get install wkhtmltopdf")
        else:  # macOS
            print("   Instálalo con: brew install wkhtmltopdf")
        return False

def multiply(value, arg):
    """Multiplica dos valores. Devuelve 0 si hay error."""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0

def generate_pdf(template_name, context=None, output_path=None):
    """Genera PDF desde un template Django."""
    if context is None:
        context = {}

    from django.template.loader import render_to_string
    html = render_to_string(f'sistema/{template_name}', context)
    return _generate_pdf_from_html(html, output_path)


def generate_pdf_from_string(html_content, output_path=None):
    """Genera PDF directamente desde un string HTML."""
    return _generate_pdf_from_html(html_content, output_path)


def _generate_pdf_from_html(html, output_path=None):
    """Función interna para generar PDF desde HTML."""
    options = {
        'enable-local-file-access': True,
        'page-size': 'Letter',
        'encoding': 'UTF-8',
        'margin-top': '1.5cm',
        'margin-right': '1cm',
        'margin-left': '1cm',
        'margin-bottom': '15mm',
    }
    
    try:
        pdf = pdfkit.from_string(html, False, options=options)
    except Exception as e:
        raise RuntimeError(f"Error al generar PDF: {e}")

    if output_path:
        with open(output_path, 'wb') as f:
            f.write(pdf)
        return output_path

    return pdf