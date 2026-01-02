from enum import Enum

class Currency(Enum):
    """
    Monedas soportadas por el SIE de Banxico.
    Formato de definición: (ID_SERIE, NOMBRE, SIMBOLO, DESCRIPCION_TIPO)
    """
    # Single Source of Truth
    USD = ("SF43718", "Dólar estadounidense", "$",  "FIX - Determinación publicada en DOF")
    USD_SPOT = ("SF60653", "Dólar estadounidense", "$",  "Para liquidación (obligaciones)")
    CAD = ("SF60632", "Dólar canadiense",     "C$", "Cotización Cruzada")
    EUR = ("SF46410", "Euro",                 "€",  "Cotización Cruzada")
    JPY = ("SF46406", "Yen japonés",          "¥",  "Cotización Cruzada")
    GBP = ("SF46407", "Libra Esterlina",      "£",  "Cotización cruzada")

    def __new__(cls, series_id, name_es, symbol, tipo_desc):
        """
        Constructor que distribuye la tupla a las propiedades.
        El primer valor (series_id) se convierte automáticamente en el .value
        """
        obj = object.__new__(cls)
        obj._value_ = series_id  # El valor nativo del Enum será el ID de Banxico
        
        # Asignación a atributos internos (protected)
        obj._name_es = name_es
        obj._symbol = symbol
        obj._tipo = tipo_desc
        return obj

    @property
    def name_es(self) -> str:
        """Retorna el nombre en español de la moneda"""
        return self._name_es

    @property
    def symbol(self) -> str:
        """Retorna el símbolo de la moneda"""
        return self._symbol

    @property
    def tipo(self) -> str:
        """Retorna el tipo de cambio de la serie"""
        return self._tipo

