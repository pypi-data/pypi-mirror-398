import os
from importlib import resources
from jinja2 import Environment, FileSystemLoader, select_autoescape
from core import multiply

def get_template_env():
    """Obtiene un entorno de Jinja2 que carga templates desde el paquete turbopdf."""
    # Usa importlib.resources para acceder a la carpeta templates incluso en .whl
    with resources.path('turbopdf', '__init__.py') as p:
        templates_dir = p.parent / 'templates'
        if templates_dir.exists():
            env = Environment(
                loader=FileSystemLoader(str(templates_dir)),
                autoescape=select_autoescape()
            )
            env.filters['multiply'] = multiply
            return env
    
    # Fallback: modo desarrollo
    turbopdf_path = os.path.dirname(os.path.dirname(__file__))
    templates_dir = os.path.join(turbopdf_path, 'templates')
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape()
    )
    env.filters['multiply'] = multiply
    return env

def render_template(template_name, context):
    """Renderiza un template sin depender de Django."""
    env = get_template_env()
    template = env.get_template(template_name)
    return template.render(**context)