"""Excepciones personalizadas para el cliente de Banxico SIE"""


class BanxicoAPIError(Exception):
    """Excepción base para errores de la API de Banxico"""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class BanxicoAuthError(BanxicoAPIError):
    """Error de autenticación con la API de Banxico (token inválido o expirado)"""
    
    def __init__(self, message: str = "Token de API inválido o expirado", **kwargs):
        super().__init__(message, **kwargs)


class BanxicoRateLimitError(BanxicoAPIError):
    """Se excedió el límite de peticiones a la API de Banxico"""
    
    def __init__(self, message: str = "Límite de peticiones excedido", **kwargs):
        super().__init__(message, **kwargs)


class BanxicoDataNotFoundError(BanxicoAPIError):
    """No se encontraron datos para la consulta especificada"""
    
    def __init__(self, message: str = "No se encontraron datos", **kwargs):
        super().__init__(message, **kwargs)