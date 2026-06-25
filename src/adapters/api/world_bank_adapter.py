import requests
from typing import List
from src.ports.api import DiabetesApiPort
from src.domain.exceptions import ApiCaidaError

class WorldBankApiAdapter(DiabetesApiPort):
    def __init__(self, base_url: str = "http://api.worldbank.org/v2", countries: str = "NIC;CRI;HND;GTM;SLV;PAN"):
        self.base_url = base_url
        self.countries = countries

    def fetch_data(self) -> List[dict]:
        try:
            print("Consultando API del Banco Mundial...")
            prevalencia = self._fetch_indicator("SH.STA.DIAB.ZS")
            poblacion = self._fetch_indicator("SP.POP.TOTL")
            gasto = self._fetch_indicator("SH.XPD.CHEX.GD.ZS")
            
            # Combinar datos en un diccionario unificado por (país, año)
            data_dict = {}
            
            for item in prevalencia:
                key = (item["pais"], item["codigo_pais"], item["ano"])
                data_dict[key] = {
                    "pais": item["pais"],
                    "codigo_pais": item["codigo_pais"],
                    "ano": item["ano"],
                    "prevalencia": item["valor"],
                    "poblacion": None,
                    "gasto_salud_pib": None
                }
                
            for item in poblacion:
                key = (item["pais"], item["codigo_pais"], item["ano"])
                if key in data_dict:
                    data_dict[key]["poblacion"] = int(item["valor"])
                else:
                    data_dict[key] = {
                        "pais": item["pais"],
                        "codigo_pais": item["codigo_pais"],
                        "ano": item["ano"],
                        "prevalencia": None,
                        "poblacion": int(item["valor"]),
                        "gasto_salud_pib": None
                    }
                    
            for item in gasto:
                key = (item["pais"], item["codigo_pais"], item["ano"])
                if key in data_dict:
                    data_dict[key]["gasto_salud_pib"] = float(item["valor"])
                else:
                    data_dict[key] = {
                        "pais": item["pais"],
                        "codigo_pais": item["codigo_pais"],
                        "ano": item["ano"],
                        "prevalencia": None,
                        "poblacion": None,
                        "gasto_salud_pib": float(item["valor"])
                    }
            
            # Filtrar y asegurar tipos NOT NULL
            filtered_results = []
            for val in data_dict.values():
                # Los campos prevalencia y población son esenciales
                if val["prevalencia"] is None or val["poblacion"] is None:
                    continue
                # Si el gasto en salud es nulo (ej: año 2024), asignamos un valor por defecto
                # de 0.0 para cumplir con la restricción NOT NULL de la base de datos.
                if val["gasto_salud_pib"] is None:
                    val["gasto_salud_pib"] = 0.0
                    
                filtered_results.append(val)
                
            return filtered_results
            
        except requests.RequestException as e:
            # Traducir excepciones de red a una excepción del dominio
            raise ApiCaidaError(f"Error al conectarse a la API del Banco Mundial: {e}")
        except Exception as e:
            raise ApiCaidaError(f"Error al procesar la respuesta de la API: {e}")

    def _fetch_indicator(self, indicator_code: str) -> List[dict]:
        url = f"{self.base_url}/country/{self.countries}/indicator/{indicator_code}?format=json&per_page=1000"
        response = requests.get(url, timeout=15)
        
        if response.status_code != 200:
            raise ApiCaidaError(f"La API respondió con código de estado HTTP {response.status_code}")
            
        data = response.json()
        if len(data) <= 1:
            return []
            
        records = data[1]
        extracted = []
        for item in records:
            if item.get("value") is not None:
                extracted.append({
                    "pais": item["country"]["value"],
                    "codigo_pais": item.get("countryiso3code", ""),
                    "ano": int(item["date"]),
                    "valor": float(item["value"])
                })
        return extracted
