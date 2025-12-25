"""
Manejadores de excepciones para tai-api.

Este módulo contiene los manejadores que convierten excepciones en respuestas HTTP apropiadas.
"""
from fastapi import Request, HTTPException, status, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, NoResultFound
from pydantic import ValidationError
from tai_alphi import Alphi

from .exceptions import APIException, ErrorCode, UnAuthorizedException, InvalidTokenException
from .responses import APIResponse, APIError

bot = Alphi()

logger = bot.get_logger(__name__)

async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """
    Manejador para excepciones específicas de tai-api.
    """
    logger.warning(f"APIException: {exc.message}", exc_info=exc)
    
    api_error = APIError(
        code=exc.error_code,
        message=exc.message,
        details=exc.details,
        field=exc.field
    )
    
    response = APIResponse.error(api_error)
    
    # Mapear códigos de error a códigos HTTP
    status_code_map = {
        ErrorCode.VALIDATION_ERROR: status.HTTP_422_UNPROCESSABLE_CONTENT,
        ErrorCode.INVALID_INPUT: status.HTTP_400_BAD_REQUEST,
        ErrorCode.MISSING_REQUIRED_FIELD: status.HTTP_400_BAD_REQUEST,
        ErrorCode.RECORD_NOT_FOUND: status.HTTP_404_NOT_FOUND,
        ErrorCode.DUPLICATE_RECORD: status.HTTP_409_CONFLICT,
        ErrorCode.FOREIGN_KEY_VIOLATION: status.HTTP_409_CONFLICT,
        ErrorCode.BUSINESS_RULE_VIOLATION: status.HTTP_422_UNPROCESSABLE_CONTENT,
        ErrorCode.UNAUTHORIZED_ACCESS: status.HTTP_401_UNAUTHORIZED,
        ErrorCode.INSUFFICIENT_PERMISSIONS: status.HTTP_403_FORBIDDEN,
        
        # Códigos específicos de autenticación y sesiones
        ErrorCode.INVALID_CREDENTIALS: status.HTTP_401_UNAUTHORIZED,
        ErrorCode.INVALID_TOKEN: status.HTTP_401_UNAUTHORIZED,
        ErrorCode.TOKEN_EXPIRED: status.HTTP_401_UNAUTHORIZED,
        ErrorCode.SESSION_INVALIDATED: status.HTTP_401_UNAUTHORIZED,
        ErrorCode.SESSION_EXPIRED: status.HTTP_401_UNAUTHORIZED,
        ErrorCode.CONCURRENT_SESSION_DETECTED: status.HTTP_409_CONFLICT,
        
        ErrorCode.DATABASE_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCode.INTERNAL_SERVER_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCode.SERVICE_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
        ErrorCode.TIMEOUT_ERROR: status.HTTP_504_GATEWAY_TIMEOUT,
    }
    
    status_code = status_code_map.get(exc.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump()
    )

async def insufficient_permissions_handler(request: Request, exc: UnAuthorizedException) -> JSONResponse:
    """
    Manejador para excepciones de permisos insuficientes.
    """
    logger.warning(f"Insufficient permissions: {exc.details}", exc_info=exc)

    api_error = APIError(
        code=ErrorCode.INSUFFICIENT_PERMISSIONS,
        message=exc.message,
        details=exc.details
    )
    
    response = APIResponse.error(api_error)
    
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=response.model_dump()
    )

async def invalid_token_handler(request: Request, exc: InvalidTokenException) -> JSONResponse:
    """
    Manejador para excepciones de token inválido.
    """
    logger.warning(f"Invalid token: {exc.message}", exc_info=exc)
    
    api_error = APIError(
        code=ErrorCode.INVALID_TOKEN,
        message=exc.message
    )
    
    response = APIResponse.error(api_error)
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=response.model_dump()
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Manejador para excepciones de SQLAlchemy.
    """
    logger.error(f"SQLAlchemy error: {str(exc)}", exc_info=exc)
    
    api_error = APIError(
        code=ErrorCode.DATABASE_ERROR,
        message="Error en la base de datos"
    )
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    response = APIResponse.error(api_error)
    
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump()
    )

async def sqlalchemy_integrity_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """
    Manejador para excepciones de SQLAlchemy.
    """
    logger.error(f"Integrity error: {str(exc)}", exc_info=exc)

    error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
    
    if "UNIQUE constraint failed" in error_msg or "duplicate key" in error_msg.lower():
        api_error = APIError(
            code=ErrorCode.DUPLICATE_RECORD,
            message="El registro ya existe"
        )
        status_code = status.HTTP_409_CONFLICT
    elif "FOREIGN KEY constraint failed" in error_msg or "foreign key" in error_msg.lower():
        api_error = APIError(
            code=ErrorCode.FOREIGN_KEY_VIOLATION,
            message="Violación de clave foránea"
        )
        status_code = status.HTTP_409_CONFLICT
    else:
        api_error = APIError(
            code=ErrorCode.DATABASE_ERROR,
            message="Error de integridad en la base de datos"
        )
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    response = APIResponse.error(api_error)
    
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump()
    )

async def sqlalchemy_notfound_handler(request: Request, exc: NoResultFound) -> JSONResponse:
    """
    Manejador para excepciones de SQLAlchemy.
    """
    logger.error(f"No result found error: {str(exc)}", exc_info=exc)
    
    api_error = APIError(
        code=ErrorCode.RECORD_NOT_FOUND,
        message="Registro no encontrado"
    )
    status_code = status.HTTP_404_NOT_FOUND
    
    response = APIResponse.error(api_error)
    
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump()
    )

async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Manejador para errores de validación de Pydantic.
    """
    logger.warning(f"Validation error: {str(exc)}")
    
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append(APIError(
            code=ErrorCode.VALIDATION_ERROR,
            message=error["msg"],
            field=field,
            details={"input": error.get("input")}
        ))
    
    response = APIResponse.error(errors, message="Errores de validación")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=response.model_dump()
    )

async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Manejador para errores de validación de request de FastAPI.
    Maneja errores en body, query parameters, path parameters, etc.
    """
    logger.warning(f"Request validation error: {str(exc)}")
    
    errors = []
    for error in exc.errors():
        # Determinar el tipo de error basado en la ubicación
        location = error["loc"]
        if location and location[0] == "body":
            error_type = "Cuerpo de la petición"
            field_path = ".".join(str(loc) for loc in location[1:]) if len(location) > 1 else "body"
        elif location and location[0] == "query":
            error_type = "Parámetro de consulta"
            field_path = ".".join(str(loc) for loc in location[1:]) if len(location) > 1 else "query"
        elif location and location[0] == "path":
            error_type = "Parámetro de ruta"
            field_path = ".".join(str(loc) for loc in location[1:]) if len(location) > 1 else "path"
        elif location and location[0] == "header":
            error_type = "Cabecera"
            field_path = ".".join(str(loc) for loc in location[1:]) if len(location) > 1 else "header"
        else:
            error_type = "Campo"
            field_path = ".".join(str(loc) for loc in location)
        
        # Personalizar mensaje según el tipo de error
        error_msg = error.get("msg", "Error de validación")
        if error["type"] == "missing":
            custom_message = f"{error_type} requerido: '{field_path}'"
        elif error["type"] == "type_error":
            custom_message = f"Tipo incorrecto en {error_type.lower()}: '{field_path}' - {error_msg}"
        elif error["type"] == "value_error":
            custom_message = f"Valor inválido en {error_type.lower()}: '{field_path}' - {error_msg}"
        else:
            custom_message = f"Error en {error_type.lower()}: '{field_path}' - {error_msg}"
        
        errors.append(APIError(
            code=ErrorCode.VALIDATION_ERROR,
            message=custom_message,
            field=field_path,
            details={
                "input": error.get("input"),
                "error_type": error["type"],
                "location_type": location[0] if location else "unknown"
            }
        ))
    
    response = APIResponse.error(
        errors, 
        message=f"Se encontraron {len(errors)} error(es) de validación"
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=response.model_dump()
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Manejador para HTTPExceptions de FastAPI.
    """
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    
    # Mapear códigos HTTP a códigos de error internos
    error_code_map = {
        400: ErrorCode.INVALID_INPUT,
        401: ErrorCode.UNAUTHORIZED_ACCESS,
        403: ErrorCode.INSUFFICIENT_PERMISSIONS,
        404: ErrorCode.RECORD_NOT_FOUND,
        409: ErrorCode.DUPLICATE_RECORD,
        422: ErrorCode.VALIDATION_ERROR,
        500: ErrorCode.INTERNAL_SERVER_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }
    
    api_error = APIError(
        code=error_code_map.get(exc.status_code, ErrorCode.INTERNAL_SERVER_ERROR),
        message=exc.detail
    )
    
    response = APIResponse.error(api_error)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump()
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Manejador general para excepciones no controladas.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=exc)
    
    api_error = APIError(
        code=ErrorCode.INTERNAL_SERVER_ERROR,
        message="Error interno del servidor"
    )
    
    response = APIResponse.error(api_error, message="Ha ocurrido un error inesperado")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump()
    )

def setup_exception_handlers(app: FastAPI):
    """
    Configura todos los manejadores de excepciones en la aplicación FastAPI.
    
    Args:
        app: Instancia de la aplicación FastAPI
    """
    # Manejadores específicos de tai-api
    app.add_exception_handler(APIException, api_exception_handler)
    
    # Manejadores de FastAPI (más específicos primero)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    
    # Manejadores de SQLAlchemy
    app.add_exception_handler(IntegrityError, sqlalchemy_integrity_handler)
    app.add_exception_handler(NoResultFound, sqlalchemy_notfound_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    
    # Manejadores de Pydantic (para casos no cubiertos por RequestValidationError)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # Auth
    app.add_exception_handler(UnAuthorizedException, insufficient_permissions_handler)
    app.add_exception_handler(InvalidTokenException, invalid_token_handler)

    # Manejadores generales
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
