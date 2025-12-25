import os
from pathlib import Path
from typing import Dict, ClassVar
import jinja2

from tai_sql import pm as sqlpm
from tai_api import pm, AuthType


class AuthDatabaseGenerator:
    """
    Generador de autenticación para FastAPI.
    
    Este generador crea un sistema de autenticación JWT completo con soporte 
    para manejo de sesiones y validación de usuarios usando plantillas Jinja2.
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
            templates_dir = Path(__file__).parent / "templates" / "db"
            self._jinja_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(templates_dir.as_posix()),
                trim_blocks=True,
                lstrip_blocks=True
            )
        return self._jinja_env

    @property
    def crud_class(self) -> str:
        """Retorna el nombre de la clase CRUD para el esquema actual"""
        return f"{sqlpm.db.schema_name.title()}AsyncDBAPI"
    
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
        self._generate_router()
        self._generate_jwt()
        self._generate_dependencies()
        self._generate_init()
    
    def _validate_config(self) -> None:
        """
        Valida que la configuración de autenticación esté completa.
        
        Raises:
            ValueError: Si falta alguna configuración requerida
        """
        if not pm.config.auth:
            raise ValueError("No se ha configurado la autenticación en el proyecto")

        if not pm.config.auth.type == AuthType.DATABASE:
            raise ValueError("El tipo de autenticación debe ser DATABASE")
        
        if not os.getenv(pm.config.secret_key_name, None):
            raise ValueError(f"Variable de entorno '{pm.config.secret_key_name}' no configurada")
        
        required_fields = [
            'table_name',
            'username_field', 
            'password_field'
        ]
        
        for field in required_fields:
            if not getattr(pm.config.auth.config, field, None):
                raise ValueError(f"Campo requerido '{field}' no configurado en auth_config")
    
    def _generate_router(self):
        """
        Genera el router de auth
        """
        # Cargar el template Jinja2
        template = self.jinja_env.get_template("auth_router.py.j2")

        context = {
            'project_name': pm.config.name,
            'crud_import_path': pm.config.crud_import_path,
            'crud_class': self.crud_class,
            'auth_table_name': pm.config.auth.config.table_name,
            'resources_import_path': pm.config.resources_import_path,
            'has_session_management': pm.config.auth.config.has_session_management,
            'auth_table_name': pm.config.auth.config.table_name,
            'username_field': pm.config.auth.config.username_field,
            'password_field': pm.config.auth.config.password_field,
            'session_id_field': pm.config.auth.config.session_id_field,
            'has_password_expiration': pm.config.auth.config.has_password_expiration,
            'password_expiration_field': pm.config.auth.config.password_expiration_field
        }
        content = template.render(**context)

        # Escribir archivo
        output_file = os.path.join(self.output_dir, "auth_router.py")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_jwt(self):
        """
        Genera el manejador de JWT
        """
        # Cargar el template Jinja2
        template = self.jinja_env.get_template("jwt.py.j2")

        context = {
            'project_name': pm.config.name,
            'resources_import_path': pm.config.resources_import_path,
            'secret_key_name': pm.config.secret_key_name,
            'jwt_expiration': pm.config.auth.config.expiration,
        }
        content = template.render(**context)

        # Escribir archivo
        output_file = os.path.join(self.output_dir, "jwt.py")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_dependencies(self):
        """
        Genera el archivo de dependencias para auth
        """
        # Cargar el template Jinja2
        template = self.jinja_env.get_template("dependencies.py.j2")

        context = {
            'project_name': pm.config.name,
            'crud_import_path': pm.config.crud_import_path,
            'crud_class': self.crud_class,
            'auth_table_name': pm.config.auth.config.table_name,
            'resources_import_path': pm.config.resources_import_path,
            'has_session_management': pm.config.auth.config.has_session_management,
            'auth_table_name': pm.config.auth.config.table_name,
            'username_field': pm.config.auth.config.username_field,
            'session_id_field': pm.config.auth.config.session_id_field
        }
        content = template.render(**context)

        # Escribir archivo
        output_file = os.path.join(self.output_dir, "dependencies.py")
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