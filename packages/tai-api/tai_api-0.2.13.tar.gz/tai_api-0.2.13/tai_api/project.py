"""
Manejo de configuración de proyecto TAI-API
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict, Any

from .config import ProjectConfig, AuthConfig


class ProjectManager:
    """
    Gestor central de proyectos TAI-API con soporte para múltiples SchemaManager
    """
    
    PROJECT_FILE = '.taiapiproject'

    config: Optional[ProjectConfig] = None
    
    _project_root_cache: Optional[Path] = None

    @classmethod
    def find_project_root(cls, start_path: str = '.') -> Optional[Path]:
        """Busca el directorio raíz del proyecto TAI-API"""
        if cls._project_root_cache is not None:
            return cls._project_root_cache
            
        current_path = Path(start_path).resolve()

        # Buscar en el directorio actual y subcarpetas
        for dir_path in [current_path] + [p for p in current_path.rglob("*") if p.is_dir()]:
            project_file = dir_path / cls.PROJECT_FILE
            if project_file.exists():
                cls._project_root_cache = dir_path
                return dir_path
        
        return None
    
    @classmethod
    def clear_cache(cls) -> None:
        """Limpia toda la caché del ProjectManager"""
        cls._project_root_cache = None
        cls.config = None

    @classmethod
    def get_project_config(cls) -> Optional[ProjectConfig]:
        """Obtiene la configuración del proyecto con caché"""
        if cls.config is None:
            cls.load_config()
        return cls.config

    @classmethod
    def create_config(cls, name: str, namespace: str, current_version: str = '0.1.0') -> ProjectConfig:
        """Crea un nuevo proyecto con configuración inicial"""
        config = ProjectConfig(
            name=name,
            namespace=namespace,
            current_version=current_version,
        )
        
        cls.save_config(config, Path(namespace))
        return config
    
    @classmethod
    def load_config(cls, project_root: Optional[Path] = None) -> Optional[ProjectConfig]:
        """Carga la configuración del proyecto"""

        if cls.config is not None:
            return cls.config
        
        if project_root is None:
            project_root = cls.find_project_root()
        
        if not project_root:
            return None
        
        project_file = project_root / cls.PROJECT_FILE
        
        if not project_file.exists():
            return None
        
        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                config = ProjectConfig.from_dict(data)

            cls.config = config  # Guardar en caché
            
            return config
        
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            raise ValueError(f"Error al leer {cls.PROJECT_FILE}: {e}")
    
    @classmethod
    def save_config(cls, config: ProjectConfig, project_root: Path) -> None:
        """Guarda la configuración del proyecto"""
        project_file = project_root / cls.PROJECT_FILE
        
        try:
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
            
            cls.config = config  # Actualizar caché
        
        except Exception as e:
            raise ValueError(f"Error al escribir {cls.PROJECT_FILE}: {e}")
    
    @classmethod
    def update_config(cls, project_root: Path, **updates) -> ProjectConfig:
        """Actualiza la configuración del proyecto"""
        config = cls.load_config(project_root)
        
        if not config:
            raise ValueError("No se encontró configuración de proyecto")
        
        # Actualizar campos
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        cls.save_config(config, project_root)

        return config
    
    @classmethod
    def update_auth_config(cls, auth_config: AuthConfig, project_root: Optional[Path] = None) -> ProjectConfig:
        """Actualiza específicamente la configuración de autenticación"""
        if project_root is None:
            project_root = cls.find_project_root()
        
        if not project_root:
            raise ValueError("No se encontró la raíz del proyecto")
        
        config = cls.load_config(project_root)
        
        if not config:
            raise ValueError("No se encontró configuración de proyecto")
        
        config.auth = auth_config
        cls.save_config(config, project_root)
        
        return config
    
    @classmethod
    def update_mcp_config(cls, mcp: bool, project_root: Optional[Path] = None) -> ProjectConfig:
        """Actualiza específicamente la configuración de /mcp"""
        if project_root is None:
            project_root = cls.find_project_root()
        
        if not project_root:
            raise ValueError("No se encontró la raíz del proyecto")
        
        config = cls.load_config(project_root)
        
        if not config:
            raise ValueError("No se encontró configuración de proyecto")
        
        config.mcp = mcp
        cls.save_config(config, project_root)
        
        return config
    
    @classmethod
    def get_project_info(cls) -> Dict[str, Any]:
        """Obtiene información completa del proyecto"""
        config = cls.get_project_config()
        project_root = cls.find_project_root()
        
        info = {
            'project_root': str(project_root) if project_root else None,
            'config': config.to_dict() if config else None
        }
        
        return info
    