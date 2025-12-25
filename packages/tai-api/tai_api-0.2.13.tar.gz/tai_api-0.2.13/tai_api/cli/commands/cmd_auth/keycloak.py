import click
from tai_api import KeycloakAuthConfig

def runkeycloakconfig() -> KeycloakAuthConfig:
    click.echo(click.style("🚀 Running Keycloak configuration...", fg='cyan', bold=True))
    click.echo("")
    click.echo(click.style("📋 Para que la API funcione correctamente con Keycloak, necesitas provisionar las siguientes variables de entorno:", fg='yellow', bold=True))
    click.echo("")
    click.echo(click.style("1️⃣  MAIN_KEYCLOAK_URL", fg='blue', bold=True))
    click.echo(click.style("   Formato: ", fg='white') + click.style("MAIN_KEYCLOAK_URL=<protocol>://<user>:<pwd>@<host>:<port>", fg='magenta'))
    click.echo(click.style("   Ejemplo: ", fg='white') + click.style("MAIN_KEYCLOAK_URL=http://admin:admin@localhost:8090", fg='green'))
    click.echo("")
    click.echo(click.style("2️⃣  KEYCLOAK_API_CLIENT_SECRET", fg='blue', bold=True))
    click.echo(click.style("   Formato: ", fg='white') + click.style("KEYCLOAK_API_CLIENT_SECRET='secreto_del_cliente_api'", fg='magenta'))
    click.echo("")
    click.echo(click.style("🔍 Para encontrar el KEYCLOAK_API_CLIENT_SECRET:", fg='yellow', bold=True))
    click.echo(click.style("   1. Accede a ", fg='white') + click.style("<host>:<port>", fg='cyan') + click.style(" (ej: ", fg='white') + click.style("localhost:8090", fg='green') + click.style(")", fg='white'))
    click.echo(click.style("   2. Ve a ", fg='white') + click.style("Main Realm > Clients > \"api\" > Credentials", fg='cyan'))
    click.echo(click.style("   3. Copia el Client Secret que aparece ahí", fg='white'))
    click.echo("")
    click.echo(click.style("✅ Una vez configuradas estas variables, la API podrá autenticarse con Keycloak", fg='green', bold=True))
    click.echo("")
    
    return KeycloakAuthConfig(realm_name="main-realm", client_name="api", audience="api")