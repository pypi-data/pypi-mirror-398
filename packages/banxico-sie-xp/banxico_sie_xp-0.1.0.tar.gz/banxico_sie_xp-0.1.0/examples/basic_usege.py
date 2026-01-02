"""
Ejemplos básicos de uso del cliente banxico-sie

Antes de ejecutar:
1. Obtén tu token: https://www.banxico.org.mx/SieAPIRest/service/v1/
2. Instala el paquete: pip install banxico-sie
3. Configura tu token en variable de ambiente o en el código
"""

import os
from datetime import datetime, timedelta
from banxico_sie import BanxicoSIEClient, Currency


def main():
    # Obtén tu token de Banxico
    token = os.getenv("BANXICO_TOKEN", "tu_token_aqui")
    
    # Inicializa el cliente
    client = BanxicoSIEClient(token)
    
    print("=" * 60)
    print("EJEMPLOS DE USO - BANXICO SIE")
    print("=" * 60)
    
    # Ejemplo 1: USD FIX vs USD PAGOS
    print("\n1. USD - FIX vs Para liquidación:")
    try:
        usd = client.get_rate(Currency.USD)
        print(f"   USD (FIX): ${usd['valor']:.4f} MXN")
        print(f"   - {usd['tipo']}")
        print(f"   - Fecha: {usd['fecha']}")
        
        usd_pagos = client.get_rate(Currency.USD_PAGOS)
        print(f"\n   USD (Liquidación): ${usd_pagos['valor']:.4f} MXN")
        print(f"   - {usd_pagos['tipo']}")
        print(f"   - Fecha: {usd_pagos['fecha']}")
        
        diff = abs(usd['valor'] - usd_pagos['valor'])
        print(f"\n   Diferencia: ${diff:.4f} MXN")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Ejemplo 2: Todas las monedas
    print("\n2. Tipos de cambio actuales:")
    monedas = [Currency.USD, Currency.USD_PAGOS, Currency.EUR, Currency.CAD, Currency.JPY]
    
    print("   Moneda       | Valor      | Tipo")
    print("   " + "-" * 50)
    for moneda in monedas:
        try:
            rate = client.get_rate(moneda)
            tipo_corto = "FIX" if "FIX" in rate['tipo'] else "Liquidación"
            print(f"   {rate['simbolo']} {rate['moneda']:<10} | ${rate['valor']:>9.4f} | {tipo_corto}")
        except Exception as e:
            print(f"   {moneda.name}: Error - {e}")
    
    # Ejemplo 3: Fecha específica
    print("\n3. USD en fecha específica (1 dic 2024):")
    try:
        usd_hist = client.get_rate(Currency.USD, fecha="2024-12-01")
        print(f"   USD FIX: ${usd_hist['valor']:.4f} MXN")
        
        usd_pagos_hist = client.get_rate(Currency.USD_PAGOS, fecha="2024-12-01")
        print(f"   USD Liquidación: ${usd_pagos_hist['valor']:.4f} MXN")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Ejemplo 4: Histórico última semana
    print("\n4. USD última semana (ambos tipos):")
    try:
        hoy = datetime.now()
        hace_semana = hoy - timedelta(days=7)
        
        hist_fix = client.get_rates_range(
            Currency.USD,
            start_date=hace_semana,
            end_date=hoy
        )
        
        hist_pagos = client.get_rates_range(
            Currency.USD_PAGOS,
            start_date=hace_semana,
            end_date=hoy
        )
        
        print(f"   Datos FIX: {len(hist_fix)} días")
        print(f"   Datos Liquidación: {len(hist_pagos)} días")
        
        if hist_fix and hist_pagos:
            print("\n   Últimos 3 días:")
            print("   Fecha         | FIX      | Liquidación | Dif")
            print("   " + "-" * 53)
            
            for i in range(min(3, len(hist_fix), len(hist_pagos))):
                fix = hist_fix[-(i+1)]
                pagos = hist_pagos[-(i+1)]
                diff = abs(fix['valor'] - pagos['valor'])
                print(f"   {fix['fecha']} | ${fix['valor']:.4f} | ${pagos['valor']:.4f}      | ${diff:.4f}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Ejemplo 5: Análisis estadístico USD FIX
    print("\n5. Análisis estadístico USD FIX (último mes):")
    try:
        hoy = datetime.now()
        hace_mes = hoy - timedelta(days=30)
        
        historico = client.get_rates_range(
            Currency.USD,
            start_date=hace_mes,
            end_date=hoy
        )
        
        valores = [r['valor'] for r in historico if r['valor']]
        
        if valores:
            minimo = min(valores)
            maximo = max(valores)
            promedio = sum(valores) / len(valores)
            variacion_pct = ((maximo / minimo) - 1) * 100
            
            print(f"   Datos: {len(valores)} registros")
            print(f"   Mínimo: ${minimo:.4f}")
            print(f"   Máximo: ${maximo:.4f}")
            print(f"   Promedio: ${promedio:.4f}")
            print(f"   Rango: ${maximo - minimo:.4f} ({variacion_pct:.2f}%)")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Ejemplo 6: Análisis estadístico USD PAGOS
    print("\n6. Análisis estadístico USD Liquidación (último mes):")
    try:
        hoy = datetime.now()
        hace_mes = hoy - timedelta(days=30)
        
        historico = client.get_rates_range(
            Currency.USD_PAGOS,
            start_date=hace_mes,
            end_date=hoy
        )
        
        valores = [r['valor'] for r in historico if r['valor']]
        
        if valores:
            minimo = min(valores)
            maximo = max(valores)
            promedio = sum(valores) / len(valores)
            variacion_pct = ((maximo / minimo) - 1) * 100
            
            print(f"   Datos: {len(valores)} registros")
            print(f"   Mínimo: ${minimo:.4f}")
            print(f"   Máximo: ${maximo:.4f}")
            print(f"   Promedio: ${promedio:.4f}")
            print(f"   Rango: ${maximo - minimo:.4f} ({variacion_pct:.2f}%)")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Ejemplo 7: Comparativa internacional
    print("\n7. Tabla comparativa internacional:")
    try:
        print("   Moneda       | MXN        | Tipo")
        print("   " + "-" * 50)
        
        # Dólares
        usd = client.get_rate(Currency.USD)
        print(f"   {usd['simbolo']} USD (FIX)  | ${usd['valor']:>9.4f} | FIX")
        
        usd_p = client.get_rate(Currency.USD_PAGOS)
        print(f"   {usd_p['simbolo']} USD (Liq) | ${usd_p['valor']:>9.4f} | Liquidación")
        
        # Otras monedas
        cad = client.get_rate(Currency.CAD)
        print(f"   {cad['simbolo']} CAD       | ${cad['valor']:>9.4f} | FIX")
        
        eur = client.get_rate(Currency.EUR)
        print(f"   {eur['simbolo']} EUR       | ${eur['valor']:>9.4f} | FIX")
        
        jpy = client.get_rate(Currency.JPY)
        print(f"   {jpy['simbolo']} JPY       | ${jpy['valor']:>9.4f} | FIX")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # Ejemplo 8: get_latest
    print("\n8. Últimos tipos de cambio disponibles:")
    try:
        latest_usd = client.get_latest(Currency.USD)
        latest_pagos = client.get_latest(Currency.USD_PAGOS)
        
        print(f"   USD FIX: ${latest_usd['valor']:.4f} ({latest_usd['fecha']})")
        print(f"   USD Liquidación: ${latest_pagos['valor']:.4f} ({latest_pagos['fecha']})")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Ejemplo 9: Conversión práctica
    print("\n9. Ejemplo de conversión:")
    try:
        mxn_cantidad = 10000  # 10,000 pesos
        
        usd = client.get_rate(Currency.USD)
        usd_pagos = client.get_rate(Currency.USD_PAGOS)
        
        usd_fix_convertido = mxn_cantidad / usd['valor']
        usd_pagos_convertido = mxn_cantidad / usd_pagos['valor']
        
        print(f"   ${mxn_cantidad:,.2f} MXN equivalen a:")
        print(f"   - ${usd_fix_convertido:,.2f} USD (tipo FIX)")
        print(f"   - ${usd_pagos_convertido:,.2f} USD (tipo Liquidación)")
        print(f"   - Diferencia: ${abs(usd_fix_convertido - usd_pagos_convertido):.2f} USD")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("Ejemplos completados!")
    print("=" * 60)


if __name__ == "__main__":
    main()
