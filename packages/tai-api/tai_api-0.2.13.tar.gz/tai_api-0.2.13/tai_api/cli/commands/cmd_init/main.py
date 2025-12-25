import sys
import click
from .model import InitCommand

@click.command()
@click.argument('project', type=str)
@click.option('--namespace', '-n', default='api', help='Nombre del proyecto a crear')
def init(project: str, namespace: str):
    """Inicializa un nuevo proyecto tai-api"""
    command = InitCommand(project=project, namespace=namespace)
    try:
        command.check_poetry()
        command.check_directory_is_avaliable()
        command.check_virtualenv()
        command.create_project()
        command.create_project_config()
        command.add_dependencies()
        command.add_folders()
        command.msg()
    except Exception as e:
        click.echo(f"❌ Error al inicializar el proyecto: {str(e)}", err=True)
        sys.exit(1)