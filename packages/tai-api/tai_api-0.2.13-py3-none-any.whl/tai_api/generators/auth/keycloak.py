import os
from pathlib import Path
from typing import Dict, ClassVar
import jinja2

from tai_api import pm, AuthType


class AuthKeycloakGenerator:
    """
    Generador de autenticación para FastAPI-Keycloak.
    Este generador crea un sistema de autenticación completo usando Keycloak.
    """

    _jinja_env: ClassVar[jinja2.Environment] = None
    
    def __init__(self, output_dir: str='api/api/auth'):
        """
        Inicializa el generador de autenticación.
        
        Args:
            project_config: Configuración del proyecto con datos de autenticación
        """
        self.output_dir = output_dir
    
    @property
    def jinja_env(self) -> jinja2.Environment:
        """Retorna el entorno Jinja2 configurado"""
        if self._jinja_env is None:
            templates_dir = Path(__file__).parent / "templates" / "kc"
            self._jinja_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(templates_dir.as_posix()),
                trim_blocks=True,
                lstrip_blocks=True
            )
        return self._jinja_env
    
    def generate(self) -> Dict[str, str]:
        """
        Genera todos los archivos de autenticación en el directorio especificado.
        
        Args:
            output_dir: Directorio donde generar los archivos de autenticación
            
        Returns:
            Dict[str, str]: Mapeo de nombre de archivo -> ruta completa generada
            
        Raises:
            ValueError: Si la configuración de autenticación no está completa
            FileNotFoundError: Si las plantillas no existen
        """
        
        # Validar configuración
        self._validate_config()
        
        # Crear directorio de salida
        output_path = Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generar todos los archivos
        self._generate_routers()
        self._generate_dependencies()
        self._generate_utils()
        self._generate_init()
    
    def _validate_config(self) -> None:
        """
        Valida que la configuración de autenticación esté completa.
        
        Raises:
            ValueError: Si falta alguna configuración requerida
        """
        if not pm.config.auth:
            raise ValueError("No se ha configurado la autenticación en el proyecto")

        if not pm.config.auth.type == AuthType.KEYCLOAK:
            raise ValueError("El tipo de autenticación debe ser KEYCLOAK para este generador")

    def _generate_routers(self):
        """
        Genera el router de auth
        """
        # Cargar el template Jinja2
        login_template = self.jinja_env.get_template("login_router.py.j2")
        keycloak_template = self.jinja_env.get_template("keycloak_router.py.j2")

        context = {
            'project_name': pm.config.name,
            'resources_import_path': pm.config.resources_import_path,
        }
        
        login_content = login_template.render(**context)
        keycloak_content = keycloak_template.render(**context)

        # Escribir archivos
        output_file = os.path.join(self.output_dir, "login_router.py")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(login_content)

        output_file = os.path.join(self.output_dir, "keycloak_router.py")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(keycloak_content)
    
    def _generate_dependencies(self):
        """
        Genera el archivo de dependencias para auth
        """
        # Cargar el template Jinja2
        template = self.jinja_env.get_template("dependencies.py.j2")

        context = {
            'project_name': pm.config.name,
            'resources_import_path': pm.config.resources_import_path,
        }
        content = template.render(**context)

        # Escribir archivo
        output_file = os.path.join(self.output_dir, "dependencies.py")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_utils(self):
        """
        Genera el archivo de utilidades para auth
        """
        # Cargar el template Jinja2
        template = self.jinja_env.get_template("utils.py.j2")

        context = {
            'project_name': pm.config.name,
        }
        content = template.render(**context)

        # Escribir archivo
        output_file = os.path.join(self.output_dir, "utils.py")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_init(self):
        """
        Genera el archivo __init__.py para el namespace de auth
        """
        # Cargar el template Jinja2
        template = self.jinja_env.get_template("__init__.py.j2")

        content = template.render(project_name=pm.config.name)

        # Escribir archivo
        output_file = os.path.join(self.output_dir, "__init__.py")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)