import base64
from django.template.loader import render_to_string
from turbopdf.core import generate_pdf_from_string
import os
import turbopdf

class BaseFormAssembler:
    def __init__(self, context=None):
        self.context = context or {}
        self.components = []
        self.img_base = self._get_img_base()

    def _get_img_base(self):
        turbopdf_path = os.path.dirname(turbopdf.__file__)
        img_dir = os.path.join(turbopdf_path, 'img')
        img_dir = img_dir.replace('\\', '/')
        return f'file:///{img_dir}'
    
    def add_component(self, template_name, extra_context=None, wrapper_html=None):
        """
        Agrega un componente al ensamblador.
        
        Args:
            template_name (str): Nombre del template (ej: 'fila_dos.html')
            extra_context (dict): Contexto adicional para el template
            wrapper_html (str): HTML envolvente (ej: '<div style="...">...</div>')
        """
        full_context = {
            **self.context,
            'img_base': self.img_base,
            **(extra_context or {})
        }
        
        rendered = render_to_string(f'sistema/{template_name}', full_context)
        
        if wrapper_html:
            # Si hay wrapper, insertar el componente dentro
            rendered = wrapper_html.replace('{{component}}', rendered)
        
        self.components.append(rendered)
        return self  # Para encadenamiento

    def add_raw_html(self, html):
        """Agrega HTML crudo (útil para divs de página, saltos, etc.)"""
        self.components.append(html)
        return self

    def build(self):
        html_completo = "\n".join(self.components)
        
        # ✅ Construir contexto para style.html
        head_context = {
            **self.context,
            'img_base': self._get_img_base(),
        }
        
        head = render_to_string('sistema/style.html', head_context)

        html_final = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Documento PDF</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
            {head}
        </head>
        <body>
            {html_completo}
        </body>
        </html>
        """
        return generate_pdf_from_string(html_final)