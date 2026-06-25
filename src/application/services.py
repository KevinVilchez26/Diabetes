from typing import List, Tuple, Dict
from src.ports.api import DiabetesApiPort
from src.ports.uow import UnitOfWorkPort
from src.ports.event_publisher import EventPublisherPort
from src.domain.exceptions import ApiCaidaError, DatosNoEncontradosError, ValidationError
from src.domain.entities import Pais, RegistroDiabetes
from src.domain.value_objects import Year, Prevalence, Population, Percentage, CountryCode
from src.domain.events import RegistroCreado, PrevalenciaActualizada

class ObtenerDatosDiabetesUseCase:
    def __init__(self, api: DiabetesApiPort, uow: UnitOfWorkPort, event_publisher: EventPublisherPort):
        self.api = api
        self.uow = uow
        self.event_publisher = event_publisher

    def execute(self) -> Tuple[List[RegistroDiabetes], List[Pais], str]:
        """
        Intenta obtener datos de la API. Si tiene éxito, los persiste en SQLite (caché)
        y los retorna. Si la API falla, carga de forma transparente los datos de SQLite.
        """
        try:
            # 1. Intentar descargar datos en tiempo real de la API
            raw_data = self.api.fetch_data()
            
            # Guardar en SQLite utilizando UOW
            with self.uow:
                # Procesar y guardar los países
                unique_countries = {}
                for item in raw_data:
                    unique_countries[item["pais"]] = item["codigo_pais"]

                paises_mapped = {}
                for name, code in unique_countries.items():
                    country_code = CountryCode(code)
                    pais_entidad = Pais(nombre=name, codigo=country_code)
                    
                    # Buscar en base de datos para no duplicar u obtener ID
                    existing = self.uow.paises.get_by_codigo(country_code)
                    if existing:
                        paises_mapped[name] = existing
                    else:
                        self.uow.paises.save(pais_entidad)
                        paises_mapped[name] = pais_entidad

                # Procesar y guardar los registros anuales
                for item in raw_data:
                    pais_entidad = paises_mapped.get(item["pais"])
                    if not pais_entidad or not pais_entidad.id:
                        continue
                        
                    ano = Year(item["ano"])
                    prevalencia = Prevalence(item["prevalencia"])
                    poblacion = Population(item["poblacion"])
                    gasto = Percentage(item["gasto_salud_pib"])
                    
                    existing_record = self.uow.registros.get_by_pais_y_ano(pais_entidad.id, ano)
                    
                    if existing_record:
                        # Si existe, comprobar si la prevalencia cambió para disparar el evento
                        old_prev = existing_record.prevalencia.value
                        if old_prev != prevalencia.value:
                            existing_record.actualizar_mediciones(prevalencia, poblacion, gasto)
                            self.uow.registros.save(existing_record)
                            # Disparar evento de dominio
                            self.event_publisher.publish(PrevalenciaActualizada(
                                registro_id=existing_record.id,
                                pais_id=pais_entidad.id,
                                ano=ano.value,
                                nueva_prevalencia=prevalencia.value
                            ))
                    else:
                        # Crear nuevo registro usando el factory del dominio (calcula casos estimando)
                        nuevo_registro = RegistroDiabetes.crear_y_calcular(
                            pais_id=pais_entidad.id,
                            ano=ano,
                            prevalencia=prevalencia,
                            poblacion=poblacion,
                            gasto_salud_pib=gasto
                        )
                        self.uow.registros.save(nuevo_registro)
                        # Disparar evento de dominio
                        self.event_publisher.publish(RegistroCreado(
                            registro_id=nuevo_registro.id,
                            pais_id=pais_entidad.id,
                            ano=ano.value,
                            prevalencia=prevalencia.value
                        ))
                
                # Commit de la transacción
                self.uow.commit()

            # Leer la lista completa y limpia de registros de la base de datos para retornar
            with self.uow:
                registros = self.uow.registros.list_active()
                paises = self.uow.paises.list_all()
                
            return registros, paises, "ONLINE"

        except ApiCaidaError as e:
            print(f"Fallback automático activado debido a error de red: {e}")
            # 2. Mecanismo de Fallback automático -> SQLite local
            try:
                with self.uow:
                    registros = self.uow.registros.list_active()
                    paises = self.uow.paises.list_all()

                if not registros:
                    raise DatosNoEncontradosError("La API está caída y la base de datos local está vacía.")
                
                return registros, paises, "OFFLINE_FALLBACK"
            except Exception as db_err:
                if isinstance(db_err, DatosNoEncontradosError):
                    raise db_err
                raise DatosNoEncontradosError(f"Error al leer la base de datos local en fallback: {db_err}")


class ObtenerLogsAuditoriaUseCase:
    def __init__(self, uow: UnitOfWorkPort):
        self.uow = uow

    def execute(self, limit: int = 10) -> Tuple[List[dict], dict]:
        with self.uow:
            logs = self.uow.logs.list_logs(limit)
            stats = {
                "total_paises": self.uow.paises.count(),
                "total_registros": self.uow.registros.count(),
                "total_logs": self.uow.logs.count()
            }
            return logs, stats
