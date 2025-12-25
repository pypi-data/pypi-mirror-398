import sys
import click

from tai_sql import pm as sqlpm
from tai_api import DatabaseAuthConfig

def rundbconfig() -> DatabaseAuthConfig:
    """
    Configura la autenticación basada en base de datos.
    """
    click.echo("\n🗄️  Configurando autenticación de base de datos...")
    click.echo("-" * 40)
    
    if not sqlpm.db.tables:
        click.echo("❌ No se encontraron tablas en la base de datos.", err=True)
        sys.exit(1)
    
    tables = sqlpm.db.tables
    
    # Mostrar tablas disponibles
    click.echo("\n📊 Tablas disponibles:")
    for i, table in enumerate(tables, 1):
        column_count = len(table.columns)
        click.echo(f"   {i}. {table._name} ({column_count} columnas)")
    
    # Seleccionar tabla de usuarios
    while True:
        choice: int = click.prompt(
            f"\n🔢 Selecciona la tabla de usuarios (1-{len(tables)})", 
            type=int,
            show_default=False
        )
        
        if 1 <= choice <= len(tables):
            selected_table = tables[choice - 1]
            break
        else:
            click.echo(f"❌ Opción no válida. Selecciona un número entre 1 y {len(tables)}.")

    click.echo(f"✅ Tabla seleccionada: {selected_table._name}")

    columns = list(selected_table.columns.values())
    
    # Seleccionar campo de username
    click.echo(f"\n🏷️  Selecciona el campo para 'username':")
    for i, column in enumerate(columns, 1):
        click.echo(f"   {i}. {column.name} ({column.type})")
    
    while True:
        choice: int = click.prompt(
            f"🔢 Selecciona el campo de 'username' (1-{len(columns)})", 
            type=int,
            show_default=False
        )
        
        if 1 <= choice <= len(columns):
            username_field = columns[choice - 1]
            if not username_field.args.primary_key:
                click.echo("❌ El campo de 'username' debe ser una clave primaria.", err=True)
                continue
            break
        else:
            click.echo(f"❌ Opción no válida. Selecciona un número entre 1 y {len(columns)}.")

    click.echo(f"✅ Campo de username: {username_field.name}")
    
    # Seleccionar campo de password
    click.echo(f"\n🏷️  Selecciona el campo para 'password':")
    for i, column in enumerate(columns, 1):
        click.echo(f"   {i}. {column.name} ({column.type})")
    
    while True:
        choice: int = click.prompt(
            f"🔢 Selecciona el campo de 'password' (1-{len(columns)})", 
            type=int,
            show_default=False
        )
        
        if 1 <= choice <= len(columns):
            password_field = columns[choice - 1]
            break
        else:
            click.echo(f"❌ Opción no válida. Selecciona un número entre 1 y {len(columns)}.")

    click.echo(f"✅ Campo de password: {password_field.name}")
    
    # Seleccionar campo de session_id (opcional)
    click.echo(f"\n🔐 ¿Deseas configurar manejo de sesiones concurrentes?")
    click.echo("   Esto permite invalidar sesiones cuando un usuario se loguea desde otro lugar.")
    click.echo("   Si seleccionas 'Sí', debes elegir un campo para almacenar el session_id.")
    
    session_management = click.confirm("\n🔄 ¿Habilitar manejo de sesiones?", default=True)
    session_id_field = None
    
    if session_management:
        click.echo(f"\n🏷️  Selecciona el campo para 'session_id':")
        click.echo("   (Este campo debe poder almacenar texto, como VARCHAR, TEXT, etc.)")
        for i, column in enumerate(columns, 1):
            click.echo(f"   {i}. {column.name} ({column.type})")
        
        while True:
            choice: int = click.prompt(
                f"🔢 Selecciona el campo de 'session_id' (1-{len(columns)})", 
                type=int,
                show_default=False
            )
            
            if 1 <= choice <= len(columns):
                session_id_field = columns[choice - 1]
                break
            else:
                click.echo(f"❌ Opción no válida. Selecciona un número entre 1 y {len(columns)}.")

        click.echo(f"✅ Campo de session_id: {session_id_field.name}")
    
    # Seleccionar campo de password_expiration (opcional)
    click.echo(f"\n🔐 ¿Deseas configurar renovación de contraseñas?")
    click.echo("   Esto obliga al usuario a renovar su contraseña cada cierto tiempo.")
    
    pwd_renewal = click.confirm("\n🔄 ¿Habilitar renovación de contraseñas?", default=True)
    pwd_expiration_field = None
    
    if pwd_renewal:
        click.echo(f"\n🏷️  Selecciona el campo para 'password_expiration':")
        click.echo("   (Este campo debe ser DATE o DATETIME.)")
        for i, column in enumerate(columns, 1):
            click.echo(f"   {i}. {column.name} ({column.type})")
        
        while True:
            choice: int = click.prompt(
                f"🔢 Selecciona el campo de 'session_id' (1-{len(columns)})", 
                type=int,
                show_default=False
            )
            
            if 1 <= choice <= len(columns):
                pwd_expiration_field = columns[choice - 1]
                break
            else:
                click.echo(f"❌ Opción no válida. Selecciona un número entre 1 y {len(columns)}.")

        click.echo(f"✅ Campo de password_expiration: {pwd_expiration_field.name}")
        click.echo("💡 El sistema generará un UUID único para cada sesión y lo almacenará en este campo.")
    else:
        click.echo("✅ Manejo de sesiones deshabilitado (se permitirán múltiples sesiones concurrentes)")

    return DatabaseAuthConfig(
        table_name=selected_table._name,
        username_field=username_field.name,
        password_field=password_field.name,
        session_id_field=session_id_field.name,
        password_expiration_field=pwd_expiration_field.name if pwd_renewal else None,
    )
