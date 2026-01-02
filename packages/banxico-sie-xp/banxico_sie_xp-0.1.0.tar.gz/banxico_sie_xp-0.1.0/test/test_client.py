"""Tests para el cliente principal de Banxico SIE"""

import pytest
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock

from banxico_sie import BanxicoSIEClient, Currency, RateType
from banxico_sie.exceptions import (
    BanxicoAPIError,
    BanxicoAuthError,
    BanxicoRateLimitError,
    BanxicoDataNotFoundError,
)


@pytest.fixture
def client():
    """Fixture que retorna un cliente de prueba"""
    return BanxicoSIEClient("test_token_123")


@pytest.fixture
def mock_response():
    """Fixture que retorna una respuesta mock de la API"""
    return {
        "bmx": {
            "series": [
                {
                    "idSerie": "SF43718",
                    "titulo": "Tipo de cambio",
                    "datos": [
                        {"fecha": "26/12/2024", "dato": "20.3456"},
                        {"fecha": "27/12/2024", "dato": "20.4567"},
                    ]
                }
            ]
        }
    }


class TestBanxicoSIEClient:
    """Suite de tests para BanxicoSIEClient"""
    
    def test_init_without_token(self):
        """Test que valida que se requiere un token"""
        with pytest.raises(ValueError, match="Se requiere un token de API válido"):
            BanxicoSIEClient("")
    
    def test_init_with_token(self):
        """Test de inicialización correcta del cliente"""
        client = BanxicoSIEClient("test_token")
        assert client.api_token == "test_token"
        assert client.session.headers["Bmx-Token"] == "test_token"
        assert client.timeout == 30
    
    def test_format_date_string(self, client):
        """Test de formateo de fecha desde string"""
        result = client._format_date("2024-12-26")
        assert result == "2024-12-26"
    
    def test_format_date_datetime(self, client):
        """Test de formateo de fecha desde datetime"""
        dt = datetime(2024, 12, 26)
        result = client._format_date(dt)
        assert result == "2024-12-26"
    
    def test_format_date_date(self, client):
        """Test de formateo de fecha desde date"""
        d = date(2024, 12, 26)
        result = client._format_date(d)
        assert result == "2024-12-26"
    
    @patch('banxico_sie.client.requests.Session.get')
    def test_make_request_success(self, mock_get, client, mock_response):
        """Test de petición exitosa a la API"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response
        
        result = client._make_request(["SF43718"], "2024-12-26", "2024-12-27")
        
        assert result == mock_response
        mock_get.assert_called_once()
    
    @patch('banxico_sie.client.requests.Session.get')
    def test_make_request_auth_error(self, mock_get, client):
        """Test de error de autenticación"""
        mock_get.return_value.status_code = 401
        mock_get.return_value.content = b'{"error": "Invalid token"}'
        mock_get.return_value.json.return_value = {"error": "Invalid token"}
        
        with pytest.raises(BanxicoAuthError):
            client._make_request(["SF43718"], "2024-12-26", "2024-12-27")
    
    @patch('banxico_sie.client.requests.Session.get')
    def test_make_request_rate_limit_error(self, mock_get, client):
        """Test de error de límite de peticiones"""
        mock_get.return_value.status_code = 429
        mock_get.return_value.content = b'{"error": "Rate limit"}'
        mock_get.return_value.json.return_value = {"error": "Rate limit"}
        
        with pytest.raises(BanxicoRateLimitError):
            client._make_request(["SF43718"], "2024-12-26", "2024-12-27")
    
    def test_parse_response_success(self, client, mock_response):
        """Test de parseo exitoso de respuesta"""
        results = client._parse_response(mock_response, Currency.USD)
        
        assert len(results) == 2
        assert results[0]["fecha"] == "26/12/2024"
        assert results[0]["moneda"] == "USD"
        assert results[0]["moneda_nombre"] == "Dólar estadounidense"
        assert results[0]["valor"] == 20.3456
    
    def test_parse_response_empty_data(self, client):
        """Test de parseo con datos vacíos"""
        empty_response = {
            "bmx": {
                "series": [
                    {
                        "idSerie": "SF43718",
                        "datos": []
                    }
                ]
            }
        }
        
        with pytest.raises(BanxicoDataNotFoundError):
            client._parse_response(empty_response, Currency.USD)
    
    def test_parse_response_invalid_structure(self, client):
        """Test de parseo con estructura inválida"""
        invalid_response = {"invalid": "structure"}
        
        with pytest.raises(BanxicoAPIError):
            client._parse_response(invalid_response, Currency.USD)
    
    @patch.object(BanxicoSIEClient, '_make_request')
    @patch.object(BanxicoSIEClient, '_parse_response')
    def test_get_rate_default_date(self, mock_parse, mock_request, client, mock_response):
        """Test de obtener tipo de cambio con fecha por defecto"""
        mock_request.return_value = mock_response
        mock_parse.return_value = [
            {
                "fecha": "26/12/2024",
                "moneda": "USD",
                "moneda_nombre": "Dólar estadounidense",
                "simbolo": "$",
                "valor": 20.3456
            }
        ]
        
        result = client.get_rate(Currency.USD)
        
        assert result["moneda"] == "USD"
        assert result["valor"] == 20.3456
        assert result["tipo"] == "fix"
        assert "tipo_descripcion" in result
    
    @patch.object(BanxicoSIEClient, '_make_request')
    @patch.object(BanxicoSIEClient, '_parse_response')
    def test_get_rate_specific_date(self, mock_parse, mock_request, client, mock_response):
        """Test de obtener tipo de cambio para fecha específica"""
        mock_request.return_value = mock_response
        mock_parse.return_value = [
            {
                "fecha": "01/12/2024",
                "moneda": "EUR",
                "moneda_nombre": "Euro",
                "simbolo": "€",
                "valor": 22.5678
            }
        ]
        
        result = client.get_rate(Currency.EUR, fecha="2024-12-01")
        
        assert result["moneda"] == "EUR"
        assert result["valor"] == 22.5678
    
    @patch.object(BanxicoSIEClient, '_make_request')
    @patch.object(BanxicoSIEClient, '_parse_response')
    def test_get_rate_with_pagos_type(self, mock_parse, mock_request, client, mock_response):
        """Test de obtener tipo de cambio tipo PAGOS"""
        mock_request.return_value = mock_response
        mock_parse.return_value = [
            {
                "fecha": "26/12/2024",
                "moneda": "USD",
                "moneda_nombre": "Dólar estadounidense",
                "simbolo": "$",
                "valor": 20.3456
            }
        ]
        
        result = client.get_rate(Currency.USD, rate_type=RateType.PAGOS)
        
        assert result["tipo"] == "pagos"
        assert result["tipo_descripcion"] == "Tipo de cambio para pagos"
    
    @patch.object(BanxicoSIEClient, '_make_request')
    @patch.object(BanxicoSIEClient, '_parse_response')
    def test_get_rates_range(self, mock_parse, mock_request, client, mock_response):
        """Test de obtener rango de tipos de cambio"""
        mock_request.return_value = mock_response
        mock_parse.return_value = [
            {
                "fecha": "26/12/2024",
                "moneda": "USD",
                "moneda_nombre": "Dólar estadounidense",
                "simbolo": "$",
                "valor": 20.3456
            },
            {
                "fecha": "27/12/2024",
                "moneda": "USD",
                "moneda_nombre": "Dólar estadounidense",
                "simbolo": "$",
                "valor": 20.4567
            }
        ]
        
        results = client.get_rates_range(
            Currency.USD,
            start_date="2024-12-26",
            end_date="2024-12-27"
        )
        
        assert len(results) == 2
        assert all(r["tipo"] == "fix" for r in results)
        assert results[0]["valor"] == 20.3456
        assert results[1]["valor"] == 20.4567
    
    @patch.object(BanxicoSIEClient, 'get_rate')
    def test_get_latest(self, mock_get_rate, client):
        """Test de obtener último tipo de cambio"""
        mock_get_rate.return_value = {
            "fecha": "26/12/2024",
            "moneda": "JPY",
            "valor": 0.1234
        }
        
        result = client.get_latest(Currency.JPY)
        
        assert result["moneda"] == "JPY"
        mock_get_rate.assert_called_once_with(Currency.JPY, rate_type=RateType.FIX)


class TestCurrencyEnum:
    """Tests para el enum Currency"""
    
    def test_currency_values(self):
        """Test de valores de series de Banxico"""
        assert Currency.USD.value == "SF43718"
        assert Currency.CAD.value == "SF43687"
        assert Currency.EUR.value == "SF46410"
        assert Currency.JPY.value == "SF46406"
    
    def test_currency_names_es(self):
        """Test de nombres en español"""
        assert Currency.USD.name_es == "Dólar estadounidense"
        assert Currency.EUR.name_es == "Euro"
    
    def test_currency_symbols(self):
        """Test de símbolos de monedas"""
        assert Currency.USD.symbol == "$"
        assert Currency.EUR.symbol == "€"
        assert Currency.JPY.symbol == "¥"


class TestRateTypeEnum:
    """Tests para el enum RateType"""
    
    def test_rate_type_values(self):
        """Test de valores de tipos de cambio"""
        assert RateType.FIX.value == "fix"
        assert RateType.PAGOS.value == "pagos"
    
    def test_rate_type_descriptions(self):
        """Test de descripciones de tipos de cambio"""
        assert "FIX" in RateType.FIX.description
        assert "pagos" in RateType.PAGOS.description