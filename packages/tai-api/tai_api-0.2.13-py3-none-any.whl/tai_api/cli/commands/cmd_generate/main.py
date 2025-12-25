import sys
import click

from tai_sql import pm as sqlpm
from tai_api import pm
from .funcs import run_generate

@click.command()
@click.option('--schema', '-s', help='Nombre del esquema')
@click.option('--all', is_flag=True, help='Generar para todos los esquemas')
def generate(schema: str=None, all: bool=False):
    """Genera recursos para la API."""

    if not pm.get_project_config():
        click.echo("❌ No se encontró la configuración del proyecto. Asegúrate de haber inicializado el proyecto con tai-api init.", err=True)
        sys.exit(1)

    if schema and all:
        click.echo("❌ Las opciones --schema y --all no pueden usarse juntas.", err=True)
        sys.exit(1)

    if schema:
        sqlpm.set_current_schema(schema)
        run_generate()

    elif all:
        for schema_name in sqlpm.discover_schemas():
            click.echo(f"\n🔄 Generando para esquema: {schema_name}\n")
            sqlpm.set_current_schema(schema_name)
            run_generate()

    else:
        sqlconfig = sqlpm.get_project_config()
        if sqlconfig:
            sqlpm.set_current_schema(sqlconfig.default_schema)
            

        if not schema and not sqlpm.db:
            click.echo(f"❌ No existe ningún esquema por defecto", err=True)
            click.echo(f"   Puedes definir uno con: tai-sql set-default-schema <nombre>", err=True)
            click.echo(f"   O usar la opción: --schema <nombre_esquema>", err=True)
            sys.exit(1)

        run_generate()
