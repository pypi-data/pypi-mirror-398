import sys
import subprocess
import click

from tai_api.generators import MainFileGenerator
from tai_api import pm

from tai_sql import pm as sqlpm

@click.command()
def set_mcp():
    """Configura el servidor para exponer /mcp"""

    config = pm.get_project_config()

    if not config:
        click.echo("❌ No se encontró la configuración del proyecto. Asegúrate de haber inicializado el proyecto con tai-api init.", err=True)
        sys.exit(1)
    
    sqlconfig = sqlpm.get_project_config()
    if sqlconfig:
        sqlpm.set_current_schema(sqlconfig.default_schema)
    else:
        click.echo("❌ No existe ningún esquema por defecto", err=True)
        click.echo("   Puedes definir uno con: tai-sql set-default-schema <nombre>", err=True)
        sys.exit(1)
    
    if config.mcp:
        click.echo("✅ El servidor ya está configurado para exponer /mcp.")
        sys.exit(0)
    else:
        # Instalar fastapi-mcp en el directorio del proyecto
        project_root = pm.find_project_root()
        if not project_root:
            click.echo("❌ No se pudo encontrar el directorio raíz del proyecto", err=True)
            sys.exit(1)
        
        click.echo("📦 Instalando fastapi-mcp...")
        try:
            subprocess.run(['poetry', 'add', 'fastapi-mcp>=0.4.0,<1.0'], 
                        cwd=project_root,
                        check=True, 
                        capture_output=True)
            click.echo("   ✅ fastapi-mcp instalado")
        except subprocess.CalledProcessError as e:
            click.echo(f"   ❌ Error al instalar fastapi-mcp: {e}", err=True)
            sys.exit(1)
        
        pm.update_mcp_config(True)
        main_file_generator = MainFileGenerator(
            output_dir=config.main_namespace.as_posix()
        )
        main_file_generator.generate()
        click.echo("✅ El servidor ha sido configurado para exponer /mcp.")
        sys.exit(0)