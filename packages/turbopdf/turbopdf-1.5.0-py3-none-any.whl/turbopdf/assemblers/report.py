# src/turbopdf/assemblers/report.py
from django.template.loader import render_to_string
from turbopdf.core import generate_pdf_from_string
import turbopdf
import os

class TwoColumnReportAssembler:
    def __init__(self, context=None):
        self.context = context or {}
        self.components = []
        self.img_base = self._get_img_base()

    def _get_img_base(self):
        turbopdf_path = os.path.dirname(turbopdf.__file__)
        img_dir = os.path.join(turbopdf_path, 'img')
        img_dir = img_dir.replace('\\', '/')
        return f'file:///{img_dir}'

    def add_section(self, title, content_html):
        """Agrega una sección con título y contenido en dos columnas."""
        section_html = f"""
        <div style="margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
            <h3 style="color: #2c3e50; margin-bottom: 10px;">{title}</h3>
            <div style="display: flex; gap: 20px;">
                {content_html}
            </div>
        </div>
        """
        self.components.append(section_html)
        return self

    def add_raw_html(self, html):
        """Agrega HTML crudo (útil para encabezados, saltos, etc.)"""
        self.components.append(html)
        return self

    def build(self):
        # Renderizar head global
        head_context = {**self.context, 'img_base': self.img_base}
        head = render_to_string('sistema/style.html', head_context)

        # Combinar todos los componentes
        html_completo = "\n".join(self.components)

        # Plantilla base del informe
        html_final = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Informe</title>
            <link href="https://fonts.googleapis.com/css?family=Roboto" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
            {head}
        </head>
        <body style="font-family: 'Roboto', sans-serif; padding: 30px; background-color: #f9f9f9;">
            <h1 style="color: #2c3e50; text-align: center; margin-bottom: 20px;">Informe</h1>
            {html_completo}
        </body>
        </html>
        """
        return generate_pdf_from_string(html_final)