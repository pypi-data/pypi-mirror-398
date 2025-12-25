from pathlib import Path
from typing import ClassVar
import jinja2
from tai_sql.generators import BaseGenerator
from tai_api import pm, AuthType
from tai_sql import pm as sqlpm

class MainFileGenerator(BaseGenerator):
    """
    Generador del archivo __main__.py principal.
    
    Este generador crea el archivo __main__.py basándose en el estado actual
    del proyecto, incluyendo automáticamente las funcionalidades disponibles.
    """

    _jinja_env: ClassVar[jinja2.Environment] = None
    
    def __init__(self, output_dir: str = 'api/api'):
        """
        Inicializa el generador del archivo principal.
        
        Args:
            project_config: Configuración del proyecto
        """
        super().__init__(output_dir)

    @property
    def jinja_env(self) -> jinja2.Environment:
        """Retorna el entorno Jinja2 configurado"""
        if self._jinja_env is None:
            templates_dir = Path(__file__).parent / "templates"
            self._jinja_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(templates_dir.as_posix()),
                trim_blocks=True,
                lstrip_blocks=True
            )
        return self._jinja_env
    
    def generate(self) -> str:
        """
        Genera el archivo __main__.py basándose en la configuración del proyecto.
            
        Returns:
            str: Ruta del archivo generado
        """
        
        # Renderizar template
        prod_template = self.jinja_env.get_template("__main__.py.j2")
        dev_template = self.jinja_env.get_template("__dev__.py.j2")
        
        operations = []
        if pm.config.mcp:
            for model in self.models:
                operations.extend([f"{ model.tablename }_find_many", f"{ model.tablename }_find"])

        context = {
            "project_name": pm.config.name if pm.config else "TAI API",
            "version": pm.config.current_version if pm.config else "0.1.0",
            "routers_import_path": pm.config.routers_import_path,
            "resources_import_path": pm.config.resources_import_path,
            "auth_import_path": pm.config.auth_import_path if pm.config.auth else None,
            "operations": operations,
            "with_mcp": pm.config.mcp,
            "has_auth": pm.config.has_auth,
            "auth_type": pm.config.auth_type,
            "has_routers": pm.config.has_routers,
            "schemas": sqlpm.discover_schemas()
        }
        prod_content = prod_template.render(**context)
        dev_content = dev_template.render(**context)
        
        # Escribir archivo
        prod_output_path = Path(self.config.output_dir) / "__main__.py"
        prod_output_path.parent.mkdir(parents=True, exist_ok=True)

        dev_output_path = Path(self.config.output_dir) / "__dev__.py"
        dev_output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(prod_output_path, "w", encoding="utf-8") as f:
            f.write(prod_content)
        
        with open(dev_output_path, "w", encoding="utf-8") as f:
            f.write(dev_content)
        
        return str(prod_output_path)
    