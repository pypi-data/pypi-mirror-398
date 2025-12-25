import sys
import subprocess
import click

from tai_sql import pm as sqlpm
from tai_sql.generators import BaseGenerator
from tai_api import pm, AuthConfig, AuthType
from tai_api.generators import AuthDatabaseGenerator, AuthKeycloakGenerator, MainFileGenerator, RoutersGenerator

from .database import rundbconfig
from .keycloak import runkeycloakconfig

@click.command()
def set_auth():
    """Genera recursos para la seguridad de la API"""
    
    click.echo("🔐 Configuración de Autenticación - tai-api")
    click.echo("=" * 50)
    
    # Verificar configuración de tai-api
    config = pm.get_project_config()
    if not config:
        click.echo("❌ No se encontró la configuración del proyecto tai-api.", err=True)
        click.echo("   Asegúrate de haber inicializado el proyecto con tai-api init.", err=True)
        sys.exit(1)
    
    # Seleccionar tipo de autenticación
    click.echo("\n📋 Selecciona el tipo de autenticación:")
    click.echo("   1. Database - Autenticación basada en base de datos")
    click.echo("   2. Keycloak - Autenticación con Keycloak")
    
    while True:
        choice = click.prompt(
            "\n🔢 Selecciona una opción (1 o 2)", 
            type=int,
            show_default=False
        )
        
        if choice == 1:
            click.echo("✅ Has seleccionado: Database")
            click.echo()
            auth_type = "database"
            break
        elif choice == 2:
            click.echo("✅ Has seleccionado: Keycloak")
            click.echo()
            auth_type = "keycloak"
            break
        else:
            click.echo("❌ Opción no válida. Por favor selecciona 1 o 2.")
    
    if auth_type == "database":

        # Verificar configuración de tai-sql
        sqlconfig = sqlpm.get_project_config()
        if not sqlconfig:
            click.echo("❌ No se encontró la configuración de tai-sql.", err=True)
            click.echo("   Asegúrate de haber inicializado el proyecto con tai-sql init.", err=True)
            sys.exit(1)
        
        # Establecer esquema por defecto si existe
        if sqlpm.config.default_schema:
            sqlpm.set_current_schema(sqlconfig.default_schema)
        
        # Verificar que existe información de la base de datos
        if not sqlpm.db or not sqlpm.db.tables:
            click.echo("❌ No se encontró información de tablas en la base de datos.", err=True)
            sys.exit(1)

        # Obtener configuración de la base de datos
        db_auth_config = rundbconfig()
        
        # Crear configuración de autenticación
        auth_config = AuthConfig(
            type=AuthType.DATABASE,
            config=db_auth_config
        )
        
        # Guardar en la configuración del proyecto
        try:
            pm.update_auth_config(auth_config)
        except ValueError as e:
            click.echo(f"❌ Error al guardar la configuración: {e}", err=True)
            sys.exit(1)
        
        # Mostrar mensaje de configuración
        click.echo("\n⚙️  Configuración de autenticación...")
        click.echo("-" * 40)
        click.echo(f"📝 Configuración seleccionada: database")
        click.echo(f"   • Tabla: {db_auth_config.table_name}")
        click.echo(f"   • Campo username: {db_auth_config.username_field}")
        click.echo(f"   • Campo password: {db_auth_config.password_field}")
        
        if db_auth_config.has_session_management:
            click.echo(f"   • Campo session_id: {db_auth_config.session_id_field}")
            click.echo("   • ✅ Manejo de sesiones concurrentes habilitado")
        else:
            click.echo("   • ❌ Manejo de sesiones concurrentes deshabilitado")
            click.echo("")
        
        auth_generator = AuthDatabaseGenerator(output_dir=pm.config.auth_namespace.as_posix())
        main_file_generator = MainFileGenerator(
            output_dir=pm.config.main_namespace.as_posix()
        )

        generators: list[BaseGenerator] = [auth_generator, main_file_generator]

        for generator in generators:

            generator_name = generator.__class__.__name__
            click.echo(f"Ejecutando: {click.style(generator_name, bold=True)}")
                
            # El generador se encargará de descubrir los modelos internamente
            result = generator.generate()
            
            click.echo(f"✅ Generador {generator_name} completado con éxito.")
            if result:
                click.echo(f"   Recursos en: {result}")
            click.echo("")
            
    elif auth_type == "keycloak":
        # Instalar tai-keycloak en el directorio del proyecto
        project_root = pm.find_project_root()
        if not project_root:
            click.echo("❌ No se pudo encontrar el directorio raíz del proyecto", err=True)
            sys.exit(1)
        
        click.echo("📦 Instalando tai-keycloak...")
        try:
            subprocess.run(['poetry', 'add', 'tai-keycloak>=0.1.20,<1.0'], 
                        cwd=project_root,
                        check=True, 
                        capture_output=True)
            click.echo("   ✅ tai-keycloak instalado")
        except subprocess.CalledProcessError as e:
            click.echo(f"   ❌ Error al instalar tai-keycloak: {e}", err=True)
            sys.exit(1)
        
        # Obtener configuración de Keycloak
        kc_auth_config = runkeycloakconfig()
        
        # Crear configuración de autenticación
        auth_config = AuthConfig(
            type=AuthType.KEYCLOAK,
            config=kc_auth_config
        )
        
        # Guardar en la configuración del proyecto
        try:
            pm.update_auth_config(auth_config)
        except ValueError as e:
            click.echo(f"❌ Error al guardar la configuración: {e}", err=True)
            sys.exit(1)

        if pm.config.has_routers:

            # Verificar configuración de tai-sql
            sqlconfig = sqlpm.get_project_config()
            if not sqlconfig:
                click.echo("❌ No se encontró la configuración de tai-sql.", err=True)
                click.echo("   Asegúrate de haber inicializado el proyecto con tai-sql init.", err=True)
                sys.exit(1)

            for schema_name in sqlpm.discover_schemas():
                sqlpm.set_current_schema(schema_name)
                click.echo(f"Ejecutando: {click.style(RoutersGenerator.__name__, bold=True)}")
                click.echo(f"   • Esquema: {schema_name}")
                result = RoutersGenerator(
                    output_dir=(pm.config.routers_namespace / schema_name).as_posix()
                ).generate()
                click.echo(f"✅ Generador {RoutersGenerator.__name__} completado con éxito.")
                if result:
                    click.echo(f"   Recursos en: {result}")
                click.echo("")

        auth_generator = AuthKeycloakGenerator(output_dir=pm.config.auth_namespace.as_posix())
        main_file_generator = MainFileGenerator(
            output_dir=pm.config.main_namespace.as_posix()
        )

        base_generators: list[BaseGenerator] = [auth_generator, main_file_generator]

        for generator in base_generators:

            generator_name = generator.__class__.__name__
            click.echo(f"Ejecutando: {click.style(generator_name, bold=True)}")
                
            # El generador se encargará de descubrir los modelos internamente
            result = generator.generate()
            
            click.echo(f"✅ Generador {generator_name} completado con éxito.")
            if result:
                click.echo(f"   Recursos en: {result}")
            click.echo("")
    else:
        click.echo("❌ Opción no válida.", err=True)
        sys.exit(1)
