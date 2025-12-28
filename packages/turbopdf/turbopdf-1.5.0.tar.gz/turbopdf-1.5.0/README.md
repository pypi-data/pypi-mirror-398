# 🚀 TurboPDF — Generador de PDFs Profesionales y Modulares para Django

[![PyPI version](https://img.shields.io/pypi/v/turbopdf.svg?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/turbopdf/)
[![Python versions](https://img.shields.io/pypi/pyversions/turbopdf.svg?style=for-the-badge&logo=python&logoColor=white)](https://pypi.org/project/turbopdf/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](https://github.com/EcosistemaUNP/python-ecosistema-turbopdf/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/EcosistemaUNP/python-ecosistema-turbopdf?style=for-the-badge&logo=github)](https://github.com/EcosistemaUNP/python-ecosistema-turbopdf/stargazers)

> ✨ **Crea formularios oficiales, informes y documentos institucionales en minutos — con componentes HTML reutilizables y una estructura base profesional.**

TurboPDF te permite ensamblar PDFs complejos (como formularios de la UNP) usando **componentes modulares** (`fila_dos.html`, `firma.html`, etc.) y una **estructura base reutilizable** que incluye:
- Logos institucionales
- Márgenes y estilos oficiales
- Paginación automática
- Bloque "Archívese en:"

Ideal para entornos gubernamentales, educativos o empresariales que requieren documentos estandarizados.

---

## 🎯 ¿Por qué TurboPDF?

✅ **Modular** — Reutiliza componentes HTML en múltiples formularios  
✅ **Flexible** — Construye cualquier formulario directamente desde tu vista  
✅ **Profesional** — Estilos y estructura listos para documentos oficiales  
✅ **Django-Friendly** — Integración directa con tus vistas y modelos  
✅ **Mantenible** — La lógica del formulario vive en tu proyecto, no en la librería

---

## ⚡ Instalación

```bash
pip install turbopdf

```

---
## 📌 Requisitos: 

---
Python ≥ 3.8
Django ≥ 3.2
wkhtmltopdf instalado en el sistema (guía de instalación )


---
## 🧩 Componentes incluidos
TurboPDF incluye componentes HTML listos para usar:

titulo_logo.html — Encabezado con logos y títulos
fila_dos.html, fila_tres.html, fila_cuatro.html — Filas de datos
tipo_identificacion.html — Selector de tipo de documento
firma.html, firmaop2.html — Firmas del solicitante
oficializacion.html — Pie de página con código y paginación
archivese.html — Bloque "Archívese en:"
pregunta_si_no.html, tipos_checkbox.html — Controles de selección
texarea.html — Áreas de texto grandes
anexos_limpio.html, manifiesto.html, leyenda_autoriza_correo.html — Componentes legales

---

---

## 🛠️ Cómo usar TurboPDF
Ejemplo 1: Formulario básico con encabezado y firma
from django.http import HttpResponse
from turbopdf.assemblers import BaseFormAssembler

```def mi_vista_pdf(request):
    context = {'nombreCompleto': 'Ana López'}
    
    assembler = BaseFormAssembler(context)
    assembler.add_raw_html('<div style="border:1px solid #303d50; padding:20px;">')
    assembler.add_component('titulo_logo.html', {
        'titulo1': "MI FORMULARIO OFICIAL",
        'titulo2': "SUBTÍTULO",
        'titulo3': "INSTITUCIÓN"
    })
    assembler.add_component('firmaop2.html', {'nombre_completo': context['nombreCompleto']})
    assembler.add_raw_html('</div>')
    assembler.add_component('archivese.html', {})
    assembler.add_component('oficializacion.html', {
        'codigo': "MIF-FT-01",
        'fecha': "Oficialización: 01/01/2025",
        'pagina': "Pág. 1 de 1"
    })

    response = HttpResponse(assembler.build(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="documento.pdf"'
    return response
```
Ejemplo 2: Fila de datos + selección

```
assembler.add_component('fila_dos.html', {
    'label1': "Nombre", 'valor1': "Juan Pérez",
    'label2': "Correo", 'valor2': "juan@example.com"
})

assembler.add_component('pregunta_si_no.html', {
    'pregunta': "¿Autoriza notificaciones por correo?",
    'valor': "Sí"
})
```

Ejemplo 3: Tipo de identificación
```
assembler.add_component('tipo_identificacion.html', {
    'numeracion1': 1,
    'numeracion2': "2. Número de identificación *",
    'numeroIdentificacion': "123456789",
    'numeracion3': "3. Fecha de expedición *",
    'fechaExpedicion': "01/01/2020",
    'tipoIdentificacion': "Cédula de ciudadanía"
})
```

---

## 📜 Licencia
UNP - EcosistemaUNP ©

---