import sys
import click
import subprocess

from tai_api import pm

@click.command()
@click.option('--auth', '-w', is_flag=True, help='Activar autenticación')
def dev(auth: bool = False):
    """Inicia el servidor en modo desarrollo."""

    config = pm.get_project_config()

    if not config:
        click.echo("❌ No se encontró la configuración del proyecto. Asegúrate de haber inicializado el proyecto con tai-api init.", err=True)
        sys.exit(1)
    
    if auth:
        if pm.config.auth is None:
            click.echo("⚠️  Advertencia: Se ejecutará sin autenticación porque no ha sido configurada.", err=True)
        file_name = '__main__.py'
    else:
        file_name = '__dev__.py'
    
    main_file = pm.config.main_namespace / file_name

    sys.exit(subprocess.call(["fastapi", "dev", main_file.as_posix()]))