# 💱 Banxico SIE

Cliente Python para consultar tipos de cambio del Sistema de Información Económica (SIE) de Banxico.

## 🚀 Instalación

```bash
pip install banxico-sie-xp
```

O desde el source:

```bash
git clone https://github.com/soyrushian/banxico-sie.git
cd banxico-sie
pip install -e .
```

## 🔑 Requisitos

Necesitas un token de la API de Banxico. Lo consigues gratis aquí:
👉 https://www.banxico.org.mx/SieAPIRest/service/v1/token

## 💡 Uso

### Setup básico

```python
from banxico_sie import BanxicoSIEClient, Currency

# Inicializa el cliente con tu token
client = BanxicoSIEClient("tu_token_aqui")
```

### Consultar tipo de cambio actual

```python
# USD FIX (por determinación)
usd = client.get_rate(Currency.USD) # Dólar (FIX - Determinación DOF)
print(f"USD: ${usd['valor']} MXN")

# USD Spot (para liquidación)
usd_spot = client.get_rate(Currency.USD_SPOT) # Dólar (Para liquidación)
print(f"USD SPOT: ${usd_spot['valor']} MXN")

# Otras monedas
eur = client.get_rate(Currency.EUR) # Euro
cad = client.get_rate(Currency.CAD) # Dolar canadiense
gbp = client.get_rate(Currency.GBP) # Libra Esterlina
```

### Consultar fecha específica

```python
from datetime import datetime

# Fecha específica como string
rate = client.get_rate(Currency.USD, fecha="2024-12-01")
print(f"USD el 1 dic 2024: ${rate['valor']}")

# Fecha como datetime
rate = client.get_rate(Currency.EUR, fecha=datetime(2024, 11, 15))
```

### Rango de fechas

```python
# Histórico USD FIX
historico = client.get_rates_range(
    Currency.USD,
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Histórico USD para liquidación
historico_pagos = client.get_rates_range(
    Currency.USD_PAGOS,
    start_date="2024-01-01",
    end_date="2024-12-31"
)

for rate in historico:
    print(f"{rate['fecha']}: ${rate['valor']}")
```

### Obtener el más reciente

```python
# Último USD FIX
latest = client.get_latest(Currency.USD)
print(f"Último USD: ${latest['valor']} ({latest['fecha']})")

# Último USD para liquidación
latest_pagos = client.get_latest(Currency.USD_PAGOS)
print(f"Último USD PAGOS: ${latest_pagos['valor']} ({latest_pagos['fecha']})")
```

## 🌍 Monedas disponibles

```python
Currency.USD # 🇺🇸 Dólar (FIX - Determinación DOF)
Currency.USD_SPOT # 🇺🇸 Dólar (Para liquidación)
Currency.CAD # 🇨🇦 Dólar canadiense (Cotización Cruzada)
Currency.EUR # 🇪🇺 Euro (Cotización Cruzada)
Currency.JPY # 🇯🇵 Yen japonés (Cotización Cruzada)
Currency.GBP # 🇬🇧 Libra Esterlina (Cotización Cruzada)
```

## 📦 Estructura de respuesta

```python
{
    'fecha': '26/12/2024',
    'moneda': 'USD',
    'moneda_nombre': 'Dólar estadounidense',
    'simbolo': '$',
    'valor': 20.3456,
    'tipo': 'FIX - Determinación publicada en DOF'
}
```

Para `Currency.USD_SPOT`:
```python
{
    'fecha': '26/12/2024',
    'moneda': 'USD',
    'moneda_nombre': 'Dólar estadounidense',
    'simbolo': '$',
    'valor': 20.4567,
    'tipo': 'Para liquidación (obligaciones)'
}
```

## 📋 Series de Banxico

| Currency | Serie | Símbolo | Tipo |
|----------|-------|---------|------|
| `Currency.USD` | SF43718 | $ | FIX - Determinación publicada en DOF |
| `Currency.USD_SPOT` | SF60653 | $ | Para liquidación (obligaciones) |
| `Currency.CAD` | SF60632 | C$ | Cotización Cruzada |
| `Currency.EUR` | SF46410 | € | Cotización Cruzada |
| `Currency.JPY` | SF46406 | ¥ | Cotización Cruzada |
| `Currency.GBP` | SF46407 | £ | Cotización Cruzada |

## 🔥 Ejemplos prácticos

### Comparar USD FIX vs SPOT

```python
usd_fix = client.get_rate(Currency.USD)
usd_spot = client.get_rate(Currency.USD_SPOT)

print(f"USD FIX: ${usd_fix['valor']:.4f}")
print(f"USD SPOT: ${usd_spot['valor']:.4f}")
print(f"Diferencia: ${abs(usd_fix['valor'] - usd_spot['valor']):.4f}")
```

### Histórico con análisis

```python
from datetime import datetime, timedelta

hace_mes = datetime.now() - timedelta(days=30)
historico = client.get_rates_range(
Currency.USD,
start_date=hace_mes,
end_date=datetime.now()
)

valores = [r['valor'] for r in historico if r['valor']]
print(f"Mínimo: ${min(valores):.4f}")
print(f"Máximo: ${max(valores):.4f}")
print(f"Promedio: ${sum(valores)/len(valores):.4f}")
```

### Tabla de todas las monedas

```python
monedas = [
Currency.USD,
Currency.USD_SPOT,
Currency.EUR,
Currency.CAD,
Currency.JPY,
Currency.GBP
]

for moneda in monedas:
rate = client.get_rate(moneda)
print(f"{rate['simbolo']} {rate['moneda']}: ${rate['valor']:.4f} MXN")
```

## 📝 Licencia

MIT License - puedes hacer lo que quieras con este código.

## 🤝 Contribuir

Pull requests son bienvenidos. Para cambios grandes, abre un issue primero para discutir qué te gustaría cambiar.

## ⚠️ Disclaimer

Este paquete no está afiliado con el Banco de México. Usa los datos bajo tu propio riesgo y verifica la información crítica directamente con fuentes oficiales.

## 🔗 Links útiles

- [API de Banxico SIE](https://www.banxico.org.mx/SieAPIRest/service/v1/)
- [Documentación oficial](https://www.banxico.org.mx/SieAPIRest/service/swagger-ui.html#/Series)
- [Catálogo de series](https://www.banxico.org.mx/SieAPIRest/service/v1/doc/catalogoSeries)

## 📮 Contacto

Issues: https://github.com/soyrushian/banxico-sie/issues

