from typing import Any, Optional, Dict, List, Union, Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from .exceptions import ErrorCode

T = TypeVar('T')

class ResponseStatus(str, Enum):
    """Estados posibles de una respuesta de la API."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"

class APIError(BaseModel):
    """Modelo para representar errores en la API."""
    code: ErrorCode = Field(..., description="Código de error específico")
    message: str = Field(..., description="Mensaje descriptivo del error")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales del error")
    field: Optional[str] = Field(None, description="Campo específico que causó el error")

class PaginationMeta(BaseModel):
    """Metadatos de paginación para respuestas que contienen listas de datos."""
    total: Optional[int] = Field(None, description="Total de registros disponibles")
    limit: Optional[int] = Field(None, description="Número máximo de elementos por página")
    offset: Optional[int] = Field(None, description="Número de elementos omitidos desde el inicio")
    has_next: Optional[bool] = Field(None, description="Indica si hay más páginas disponibles")
    has_prev: Optional[bool] = Field(None, description="Indica si hay páginas anteriores")

class APIResponse(BaseModel, Generic[T]):
    """
    Respuesta estandarizada de la API que envuelve todos los datos retornados.
    
    Esta clase proporciona un formato consistente para todas las respuestas de la API,
    incluyendo el estado de la operación, los datos solicitados, mensajes informativos
    y manejo de errores. El campo 'data' contiene el tipo específico solicitado (T)
    que puede ser cualquier modelo de Pydantic, permitiendo que la documentación
    refleje correctamente la estructura de los datos retornados.
    
    Attributes:
        status: Estado de la respuesta (success, error, warning)
        data: Datos de la respuesta del tipo especificado
        message: Mensaje descriptivo sobre el resultado de la operación
        errors: Lista de errores si la operación no fue exitosa
        meta: Metadatos adicionales como información de paginación
    """
    status: ResponseStatus = Field(
        ..., 
        description="Estado de la respuesta que indica el resultado de la operación"
    )
    data: Optional[T] = Field(
        None, 
        description="Datos de la respuesta del tipo especificado. La estructura exacta depende del endpoint consultado y se documenta en cada endpoint específico."
    )
    message: Optional[str] = Field(
        None, 
        description="Mensaje descriptivo sobre el resultado de la operación realizada"
    )
    errors: Optional[List[APIError]] = Field(
        None, 
        description="Lista de errores detallados si la operación no fue exitosa. Solo presente cuando status es 'error'."
    )
    meta: Optional[Dict[str, Any]] = Field(
        None, 
        description="Metadatos adicionales como información de paginación, contadores, etc."
    )

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
    )

    @classmethod
    def success(
        cls, 
        data: T, 
        message: Optional[str] = None, 
        meta: Optional[Dict[str, Any]] = None
    ) -> 'APIResponse[T]':
        """Crea una respuesta exitosa."""
        return cls(
            status=ResponseStatus.SUCCESS,
            data=data,
            message=message,
            meta=meta
        )

    @classmethod
    def error(
        cls, 
        errors: Union[APIError, List[APIError]], 
        message: Optional[str] = None
    ) -> 'APIResponse[None]':
        """Crea una respuesta de error."""
        if isinstance(errors, APIError):
            errors = [errors]
        
        return cls(
            status=ResponseStatus.ERROR,
            data=None,
            message=message or "Se ha producido un error",
            errors=errors
        )

    @classmethod
    def not_found(cls, resource: str = "Registro") -> 'APIResponse[None]':
        """Crea una respuesta para recurso no encontrado."""
        return cls.error(
            APIError(
                code=ErrorCode.RECORD_NOT_FOUND,
                message=f"{resource} no encontrado"
            ),
            message=f"{resource} no encontrado"
        )

    @classmethod
    def validation_error(cls, field: str, message: str) -> 'APIResponse[None]':
        """Crea una respuesta de error de validación."""
        return cls.error(
            APIError(
                code=ErrorCode.VALIDATION_ERROR,
                message=message,
                field=field
            ),
            message="Error de validación"
        )

    @classmethod
    def database_error(cls, message: Optional[str] = None) -> 'APIResponse[None]':
        """Crea una respuesta de error de base de datos."""
        return cls.error(
            APIError(
                code=ErrorCode.DATABASE_ERROR,
                message=message or "Error en la base de datos"
            ),
            message="Error interno del servidor"
        )

class PaginatedResponse(APIResponse[List[T]]):
    """
    Respuesta paginada que extiende APIResponse para incluir metadatos de paginación.
    
    Esta clase se utiliza específicamente para endpoints que retornan listas de datos
    con soporte para paginación, incluyendo información sobre el total de registros,
    límites, navegación y metadatos útiles para implementar paginación en clientes.
    
    La información de paginación se incluye en el campo 'meta' bajo la clave 'pagination'
    y contiene detalles como el total de registros, límites aplicados y flags de navegación.
    
    Attributes:
        status: Siempre 'success' para respuestas paginadas exitosas
        data: Lista de elementos del tipo especificado
        message: Mensaje descriptivo de la operación
        meta: Contiene información de paginación en meta.pagination
    """
    
    @classmethod
    def success_paginated(
        cls,
        data: List[T],
        total: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        message: Optional[str] = None
    ) -> 'PaginatedResponse[T]':
        """Crea una respuesta exitosa paginada."""
        pagination_meta = PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            has_next=None if total is None or limit is None or offset is None 
                     else (offset + limit) < total,
            has_prev=None if offset is None else offset > 0
        )
        
        return cls(
            status=ResponseStatus.SUCCESS,
            data=data,
            message=message,
            meta={"pagination": pagination_meta.model_dump()}
        )