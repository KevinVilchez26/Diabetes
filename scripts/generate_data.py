import os
import sys
import pandas as pd

# Añadir el directorio raíz al path de Python para poder importar 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.composer import get_obtener_datos_diabetes_use_case
from src.adapters.persistence.migration_runner import MigrationRunner
from src.domain.exceptions import DomainError

def format_large_number(num):
    if pd.isnull(num): return "0"
    try:
        num = float(num)
    except:
        return str(num)
        
    if num >= 1_000_000:
        return f"{num/1_000_000:.2f} M"
    elif num >= 1_000:
        return f"{num/1_000:.1f} K"
    return str(int(num))

def generate_diabetes_data():
    # Resolver la ruta de la base de datos a la raíz del proyecto
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "diabetes.db"))
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "diabetes_data.csv"))
    
    print(f"Inicializando la base de datos en {db_path} y ejecutando migraciones...")
    try:
        runner = MigrationRunner(db_path)
        runner.run()
    except Exception as e:
        print(f"Error crítico al ejecutar migraciones: {e}")
        return

    print("Obteniendo datos de diabetes del Banco Mundial a través del Caso de Uso del Dominio...")
    try:
        use_case = get_obtener_datos_diabetes_use_case(db_path)
        registros, paises, status = use_case.execute()
        print(f"Sincronización finalizada con estado: {status}")
        
        if not registros:
            print("No se obtuvieron registros de la API ni de la base de datos local.")
            return

        # Mapeamos los datos de las entidades de dominio a un pandas DataFrame
        paises_dict = {p.id: (p.nombre, p.codigo.value) for p in paises}
        data = []
        for r in registros:
            pais_nombre, pais_codigo = paises_dict.get(r.pais_id, (None, None))
            if pais_nombre is None:
                continue
            data.append({
                "pais": pais_nombre,
                "codigo_pais": pais_codigo,
                "ano": r.ano.value,
                "prevalencia": r.prevalencia.value,
                "poblacion": r.poblacion.value,
                "gasto_salud_pib": r.gasto_salud_pib.value,
                "casos_estimados": r.casos_estimados
            })

        df_final = pd.DataFrame(data)
        if not df_final.empty:
            df_final = df_final.sort_values(by=["pais", "ano"])
            
            # Formatear las columnas para hacerlas super legibles en el CSV legacy
            df_final['poblacion'] = df_final['poblacion'].apply(format_large_number)
            df_final['gasto_salud_pib'] = df_final['gasto_salud_pib'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "0.00%")
            df_final['casos_estimados'] = df_final['casos_estimados'].apply(format_large_number)
            
            # Omitir la columna interna de codigo_pais para mantener el CSV exactamente idéntico al original
            df_csv = df_final.drop(columns=["codigo_pais"])
            df_csv.to_csv(csv_path, index=False)
            print(f"¡Archivo '{csv_path}' generado con formato ultra-legible con éxito!")
        else:
            print("El DataFrame de salida está vacío.")
    except DomainError as de:
        print(f"Error de reglas de negocio / dominio: {de}")
    except Exception as e:
        print(f"Error inesperado durante la generación de datos: {e}")

if __name__ == "__main__":
    generate_diabetes_data()
