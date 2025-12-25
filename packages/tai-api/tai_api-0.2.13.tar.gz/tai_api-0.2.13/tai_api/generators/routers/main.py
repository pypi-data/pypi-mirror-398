import os
from pathlib import Path
from typing import ClassVar
import jinja2
from tai_sql.generators import BaseGenerator
from tai_sql import pm as sqlpm
from tai_api import pm, AuthType


class RoutersGenerator(BaseGenerator):
    """
    Generador de endpoints para FastAPI.
    
    Este generador crea los endpoints necesarios para interactuar con los modelos
    definidos en tai_sql, utilizando la configuración proporcionada.
    
    Genera automáticamente:
    - Endpoints CRUD completos para cada tabla
    - Archivos router_{table_name}.py en routers/generated/
    - Importaciones automáticas de DTOs y DAOs
    
    Atributos:
        output_dir (str): Directorio donde se generarán los routers
        template_dir (str): Directorio donde están los templates Jinja2
    """

    _jinja_env: ClassVar[jinja2.Environment] = None

    def __init__(self, output_dir: str = "api/api/routers/generated"):
        """
        Inicializa el generador de endpoints.
        
        Args:
            output_dir: Directorio donde se generarán los archivos router
            template_dir: Directorio donde están los templates Jinja2
        """
        super().__init__(output_dir)

    @property
    def jinja_env(self) -> jinja2.Environment:
        """Retorna el entorno Jinja2 configurado"""
        if self._jinja_env is None:
            templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
            self._jinja_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(templates_dir),
                trim_blocks=True,
                lstrip_blocks=True
            )
            self._jinja_env.filters['zip'] = zip
            self._jinja_env.globals["zip"] = zip
        return self._jinja_env
    
    @property
    def crud_class(self) -> str:
        """Retorna el nombre de la clase CRUD para el esquema actual"""
        return f"{sqlpm.db.schema_name.title()}AsyncDBAPI"
    
    def generate(self):
        """
        Genera todos los archivos router para las tablas definidas en models.
        """
        # Crear directorio de salida si no existe
        os.makedirs(self.config.output_dir, exist_ok=True)
        try:
            # Generar routers para cada modelo
            self._generate_routers()
            # Generar router para enumeraciones
            self._generate_enumerations_router()
            # Generar archivo __init__.py para importar todos los routers
            self._generate_init_file()
            # Generar archivo __init__.py exterior para importar todos los routers de cada schema
            self._generate_outer_init_file()
        except Exception as e:
            import logging
            logging.exception(f"Error generating routers: {e}")
    
    def _generate_routers(self):
        """
        Genera los routers para cada modelo definido en models.
        """
        # Cargar el template Jinja2
        template = self.jinja_env.get_template("router_template.py.j2")

        imports = [
            "from fastapi import APIRouter, Depends, Query, Path, Body",
            f"from {pm.config.crud_import_path} import *",
            f"from {pm.config.resources_import_path} import (",
            "    APIResponse, PaginatedResponse, RecordNotFoundException,",
            "    ValidationException",
            ")",
            "from typing import Optional, List, Literal",
            "from tai_alphi import Alphi"
        ]

        if pm.config.has_auth and pm.config.auth_type == AuthType.KEYCLOAK:
            imports.append(f"from {pm.config.auth_import_path} import AccessToken, requires_permissions")

        # Generar router para cada modelo
        for model in self.models:
            model_imports = imports.copy()
            has_datetime = any(col.type == 'datetime' or col.type == 'date' or col.type == 'time' for col in model.columns.values())
            if has_datetime:
                model_imports.append('from datetime import datetime, date, time')
            content = template.render(
                imports=model_imports,
                model=model.info(),
                crud_class=self.crud_class,
                with_keycloak=pm.config.has_auth and pm.config.auth_type == AuthType.KEYCLOAK,
            )
            # Escribir archivo
            output_file = Path(self.config.output_dir) / f"router_{model.tablename}.py"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

    def _generate_enumerations_router(self):
        """
        Genera el router para todas las enumeraciones del sistema.
        """
        # Cargar el template Jinja2 para enumeraciones
        template = self.jinja_env.get_template("enums_template.py.j2")
        
        # Preparar las importaciones necesarias
        imports = [
            "from fastapi import APIRouter, Depends",
            "from typing import List, Dict, Optional",
            f"from {pm.config.crud_import_path} import *",
            "from api.resources import APIResponse"
        ]

        if pm.config.has_auth and pm.config.auth_type == AuthType.KEYCLOAK:
            imports.append(f"from {pm.config.auth_import_path} import AccessToken, requires_permissions")
        
        # Renderizar el template
        rendered_code = template.render(
            imports=imports,
            crud_class=self.crud_class,
            enumerations=[enum.info() for enum in sqlpm.db.enums],
            with_keycloak=pm.config.has_auth and pm.config.auth_type == AuthType.KEYCLOAK,
        )
        
        # Escribir el archivo
        output_file = Path(self.config.output_dir) / "router_enums.py"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(rendered_code)

    def _generate_init_file(self):
        """
        Genera el archivo __init__.py para importar todos los routers generados.
        """
        # Cargar el template Jinja2 para enumeraciones
        template = self.jinja_env.get_template("__init__.py.j2")
        
        # Importar todos los routers
        imports = ["from fastapi import APIRouter"]
        routers = {}
        for model in self.models:
            routers[f"router_{model.tablename}"] = f"{model.tablename}_router"
        
        routers["router_enums"] = "enumerations_router"

        imports.extend([f"from .{router_file} import {router_var}" for router_file, router_var in routers.items()])

        rendered_code = template.render(
            imports=imports,
            routers=routers,
            schema_name=sqlpm.db.schema_name
        )

        # Escribir archivo
        init_file = os.path.join(self.config.output_dir, "__init__.py")
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(rendered_code)

    def _generate_outer_init_file(self):
        """
        Genera el archivo __init__.py para importar todos los routers generados, de cada schema.
        """
        # Cargar el template Jinja2 para enumeraciones
        template = self.jinja_env.get_template("__outerinit__.py.j2")
        
        # Importar todos los routers
        imports = ["from fastapi import APIRouter"]
        routers = {}
        for schema_name in sqlpm.discover_schemas():
            routers[f"{schema_name}_router"] = f"{schema_name}_router"
            imports.extend([f"from .{schema_name} import {schema_name}_router"])

        rendered_code = template.render(
            imports=imports,
            routers=routers
        )

        # Escribir archivo
        init_file = os.path.join(Path(self.config.output_dir).parent, "__init__.py")
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(rendered_code)
