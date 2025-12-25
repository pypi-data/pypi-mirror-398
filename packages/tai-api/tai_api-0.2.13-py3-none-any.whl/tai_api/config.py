"""
Manejo de configuración de proyecto TAI-API
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

from tai_sql import pm as sqlpm

class RuntimeMode(str, Enum):
    """Modos de ejecución del proyecto TAI-API"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class AuthType(str, Enum):
    """Tipos de autenticación soportados"""
    DATABASE = "database"
    KEYCLOAK = "keycloak"


@dataclass
class DatabaseAuthConfig:
    """Configuración de autenticación basada en base de datos"""
    table_name: str
    username_field: str
    password_field: str
    session_id_field: Optional[str] = None  # Campo opcional para manejar sesiones
    password_expiration_field: Optional[str] = None
    expiration: Optional[int] = 30  # Tiempo de expiración del token en minutos
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatabaseAuthConfig':
        """Crea DatabaseAuthConfig desde diccionario"""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte DatabaseAuthConfig a diccionario"""
        return asdict(self)
    
    @property
    def has_session_management(self) -> bool:
        """Verifica si se configuró manejo de sesiones"""
        return self.session_id_field is not None
    
    @property
    def has_password_expiration(self) -> bool:
        """Verifica si se configuró expiración de contraseñas"""
        return self.password_expiration_field is not None


@dataclass
class KeycloakAuthConfig:
    """Configuración de autenticación con Keycloak"""
    realm_name: str = 'main_realm'
    client_name: str = 'api'
    audience: Optional[str] = 'api'
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeycloakAuthConfig':
        """Crea KeycloakAuthConfig desde diccionario"""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte KeycloakAuthConfig a diccionario"""
        return asdict(self)


@dataclass
class AuthConfig:
    """Configuración general de autenticación"""
    type: AuthType
    config: Union[DatabaseAuthConfig, KeycloakAuthConfig]
    enabled: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuthConfig':
        """Crea AuthConfig desde diccionario"""
        auth_type = AuthType(data['type'])
        
        if auth_type == AuthType.DATABASE:
            config = DatabaseAuthConfig.from_dict(data['config'])
        elif auth_type == AuthType.KEYCLOAK:
            config = KeycloakAuthConfig.from_dict(data['config'])
        else:
            raise ValueError(f"Tipo de autenticación no soportado: {auth_type}")
        
        return cls(type=auth_type, config=config)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte AuthConfig a diccionario"""
        return {
            'type': self.type.value,
            'config': self.config.to_dict()
        }


@dataclass
class ProjectConfig:
    """Configuración del proyecto TAI-API"""
    name: str
    namespace: str
    current_version: str = "0.1.0"
    mode: RuntimeMode = RuntimeMode.DEVELOPMENT
    auth: Optional[AuthConfig] = None
    mcp: Optional[bool] = False
    secret_key_name: Optional[str] = 'SECRET_KEY'
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectConfig':
        """Crea ProjectConfig desde diccionario"""
        # Manejar auth como opcional
        auth_data = data.pop('auth', None)
        auth_config = None
        
        if auth_data:
            auth_config = AuthConfig.from_dict(auth_data)
        
        return cls(auth=auth_config, **data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte ProjectConfig a diccionario"""
        result = asdict(self)
        
        # Convertir auth si existe
        if self.auth:
            result['auth'] = self.auth.to_dict()
        
        return result
    
    @property
    def subnamespace(self) -> str:
        """Retorna el namespace del proyecto"""
        return self.namespace.replace('-', '_')

    @property
    def main_namespace(self) -> Path:
        """Retorna el namespace principal del proyecto"""
        return Path(self.namespace) / self.subnamespace

    @property
    def database_namespace(self) -> Path:
        """Retorna el namespace para la base de datos"""
        return Path(self.namespace) / self.subnamespace / "database"
    
    @property
    def diagrams_namespace(self) -> Path:
        """Retorna el namespace para diagramas"""
        return Path(self.namespace) / self.subnamespace / "diagrams"
    
    @property
    def routers_namespace(self) -> Path:
        """Retorna el namespace para routers"""
        return Path(self.namespace) / self.subnamespace / "routers" / "database"

    @property
    def auth_namespace(self) -> Path:
        """Retorna el namespace para autenticación"""
        return Path(self.namespace) / self.subnamespace / "auth"
    
    @property
    def resources_namespace(self) -> Path:
        """Retorna el namespace para respuestas"""
        return Path(self.namespace) / self.subnamespace / "resources"
    
    @property
    def models_import_path(self) -> str:
        """Retorna la ruta de importación para modelos"""
        return f"{self.subnamespace}.database.{sqlpm.db.schema_name}.models"
    
    @property
    def crud_import_path(self) -> str:
        """Retorna la ruta de importación para CRUD"""
        return f"{self.subnamespace}.database.{sqlpm.db.schema_name}.crud.asyn"
    
    @property
    def routers_import_path(self) -> str:
        """Retorna la ruta de importación para routers"""
        return f"{self.subnamespace}.routers.database"
    
    @property
    def resources_import_path(self) -> str:
        """Retorna la ruta de importación para respuestas"""
        return f"{self.subnamespace}.resources"
    
    @property
    def auth_import_path(self) -> str:
        """Retorna la ruta de importación para autenticación"""
        return f"{self.subnamespace}.auth"
    
    @property
    def has_auth(self) -> bool:
        """Verifica si el proyecto tiene configuración de autenticación"""
        return self.auth is not None
    
    @property
    def auth_type(self) -> Optional[AuthType]:
        """Retorna el tipo de autenticación configurado"""
        return self.auth.type if self.auth else None
    
    @property
    def has_routers(self) -> bool:
        """Verifica si existen routers generados en el proyecto"""
        for schema_name in sqlpm.discover_schemas():
            location = self.routers_namespace / schema_name
            if location.exists() and location.is_dir() and any(location.glob("*.py")):
                return True
        return False
    
    @property
    def database_auth_config(self) -> Optional[DatabaseAuthConfig]:
        """Retorna la configuración de autenticación de base de datos si existe"""
        if self.auth and self.auth.type == AuthType.DATABASE:
            return self.auth.config
        return None
    
    @property
    def keycloak_auth_config(self) -> Optional[KeycloakAuthConfig]:
        """Retorna la configuración de autenticación de Keycloak si existe"""
        if self.auth and self.auth.type == AuthType.KEYCLOAK:
            return self.auth.config
        return None

    