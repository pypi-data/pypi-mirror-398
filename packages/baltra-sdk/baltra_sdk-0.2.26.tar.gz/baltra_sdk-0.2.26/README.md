# Baltra SDK — Arquitectura centralizada y desacoplada

## Objetivo
Consolidar en un único paquete reutilizable la lógica de negocio, los contratos de dominio y las integraciones comunes (bases de datos, Meta, Step Functions, proveedores externos), evitando duplicación en microservicios y reduciendo el tiempo de mantenimiento frente a cambios en modelos o esquemas.

## Alcance
- SDK empaquetado como librería Python (`baltra-sdk`) distribuida vía PyPI privado o repositorio Git.
- Exporta servicios, modelos, repositorios y clientes externos usados hoy por los microservicios Baltra.
- Incluye utilidades compartidas (logging, configuración, validaciones, unit of work).
- Define contratos explícitos entre el dominio y las capas de infraestructura para preservar compatibilidad hacia atrás.

## Principios de diseño
- **Dominio independiente de infraestructura**: los servicios consumen puertos (interfaces) sin conocer implementaciones concretas.
- **Sin efectos secundarios al importar**: inicializaciones (sesiones, clientes) se ejecutan bajo factories o context managers.
- **Idempotencia y backwards compatibility**: cambios de esquema deben exponerse sin romper versiones existentes.
- **Versionado semántico**: cualquier ruptura debe incrementar el major version y disparar migraciones coordinadas.
- **Observabilidad incluida**: el SDK expone hooks para métricas, logging y tracing sin acoplarse a un proveedor particular.

## Arquitectura propuesta

```
baltra/
├─ baltra_sdk/
│  ├─ domain/
│  │  ├─ models/        # DTOs de entrada/salida y entidades de dominio
│  │  ├─ services/      # Casos de uso orquestando lógica
│  │  └─ ports/         # Protocolos (interfaces) de repositorios y gateways
│  ├─ infra/
│  │  ├─ db/            # Repositorios SQLAlchemy, factories de sesión
│  │  ├─ meta/          # Integraciones Facebook/Meta
│  │  ├─ sfn/           # Clientes para Step Functions
│  │  └─ messaging/     # Ej. SQS, SNS, Kafka
│  ├─ shared/
│  │  ├─ config.py      # Helpers para leer variables de entorno
│  │  ├─ logging.py     # Inicialización de logging estructurado
│  │  └─ utils/         # Helpers comunes
│  ├─ __init__.py       # Puntos de entrada públicos
│  └─ pyproject.toml
└─ services/
   ├─ worker_a/
   ├─ worker_b/
   └─ api_x/
```

Cada servicio importa solo los contratos necesarios y decide cómo construir las dependencias concretas (inyección manual o factory). Las capas de presentación (por ejemplo, blueprints HTTP) permanecen en cada microservicio; el SDK solo entrega middleware reutilizable cuando aplica.

### Ejemplo de consumo
```python
from baltra_sdk.domain.services.funnel import FunnelService
from baltra_sdk.infra.db.repositories import SqlAlchemyAdminDashboardRepository
from baltra_sdk.infra.db.session import SessionLocal

def handler(job):
    with SessionLocal() as session:
        repo = SqlAlchemyAdminDashboardRepository(session)
        service = FunnelService(repo)
        return service.buckets(company_id=job["company_id"])
```

## Contratos y dependencias

| Capa | Responsabilidad | Paquetes clave |
|------|-----------------|----------------|
| `domain.models` | DTOs Pydantic, validaciones y defaults | `pydantic` |
| `domain.services` | Casos de uso, reglas de negocio | `dataclasses`, `typing` |
| `domain.ports` | Protocolos para repositorios y APIs externas | `typing.Protocol` |
| `infra.db` | Repositorios SQLAlchemy y factories de sesión | `sqlalchemy`, `alembic` |
| `infra.meta` | Cliente Meta Marketing API | `facebook-business`, `requests` |
| `infra.sfn` | Cliente Step Functions | `boto3` |
| `shared` | Configuración, logging, observabilidad | `structlog`, `tenacity` |

Dependencias externas se definen dentro del SDK; los servicios consumidores no deben instanciarlas directamente.

### Dependencias y extras opcionales
- Instalación base: `pip install baltra-sdk`
- Funcionalidades de reportes (Playwright, pandas, numpy, matplotlib, Pillow): `pip install baltra-sdk[reporting]`
- Integraciones de IA (OpenAI, aiohttp): `pip install baltra-sdk[ai]`
- Paquete completo: `pip install baltra-sdk[all]`
- En desarrollo local basta con `pip install -e ./baltra_sdk` (o bind-mount `/sdk` en contenedores) para usar el código en vivo.

### Compatibilidad con código legacy
- `baltra_sdk.legacy` reexporta módulos antiguos (por ejemplo `dashboards_folder`) para evitar cortes inmediatos.
- Cada import desde `baltra_sdk.legacy` emite `DeprecationWarning`; la meta es migrar esas piezas a `domain` o `infra` antes de la versión `1.0`.
- Los módulos originales bajo `app/` actúan como _wrappers_ que importan desde `baltra_sdk`, así se mantiene compatibilidad sin duplicar lógica. Puedes migrar cada servicio a los nuevos paths a su propio ritmo.

## Desarrollo local
- Montar el SDK como volumen editable para hot-reload o instalar en modo editable.
- Recomendado envolver la instalación en `entrypoint.sh` del contenedor:

```bash
set -euo pipefail
if [ -d "/sdk" ]; then
  pip install -e /sdk
else
  pip install --no-cache-dir --upgrade "baltra-sdk==${SDK_VERSION:-1.*}" \
    --extra-index-url "${PIP_EXTRA_INDEX_URL}"
fi
exec "$@"
```

## Estrategia de release
1. Merge a `main` ejecuta pipeline de empaquetado (`python -m build`).
2. Publicación a PyPI privado / release Git junto con changelog generado (`towncrier` o `cz`).
3. Tag semántico (`v1.7.0`) y artefacto `.whl` firmado.
4. Renovate o pipeline aguas abajo actualiza las imágenes que dependen del SDK.

### Versionado
- `MAJOR`: ruptura en contratos (`domain.models`, `domain.services`).
- `MINOR`: nuevas funcionalidades compatibles.
- `PATCH`: bugfix sin cambios de API.

## Buena prácticas de implementación
- Factories de sesión (`SessionLocal`, `unit_of_work`) devuelven context managers reutilizables.
- No leer variables de entorno en import time; usar funciones `get_settings()` cacheadas.
- DTOs Pydantic con `ConfigDict(from_attributes=True)` para mapear ORM.
- Repositorios deben exponer métodos idempotentes y transaccionales.
- Usar adaptadores por servicio para escenarios complejos (ej. Meta > Step Functions).

## Calidad y observabilidad
- Tests unitarios por módulo (`domain` aislado con stubs, `infra` con fixtures de base de datos en Docker).
- Contratos validados con `pydantic` y `beartype` opcional.
- Integrar `pytest` con `Coverage.py` para `>=85%` en `domain` y `shared`.
- Hooks para métricas (ej. `baltra_sdk.shared.metrics.emit`) que puedan conectarse a Datadog/NewRelic.

## Roadmap de implementación
1. **Fase 0 — Inventario**: catalogar servicios, modelos y repositorios duplicados; definir owners.
2. **Fase 1 — Bootstrap**: crear repositorio SDK, linting, CI básico, plantillas de módulo.
3. **Fase 2 — Migración de dominio**: mover servicios de funil, onboarding y admin dashboard.
4. **Fase 3 — Integraciones externas**: encapsular clientes Meta y Step Functions.
5. **Fase 4 — Adopción gradual**: actualizar microservicios prioritarios, publicar guías de adopción.
6. **Fase 5 — Endgame**: deprecación de código duplicado, monitoreo post-migración.

## Plan de migración y compatibilidad
- Mantener ambos caminos (legacy y SDK) durante un ciclo de release.
- Publicar facades que actúen como shim para consumidores antiguos.
- Documentar en cada release los cambios de campos y migraciones requeridas.
- Ejecutar pruebas contractuales (ej. `pact`) para asegurar que los contratos HTTP sigan vigentes.

## Checklist de adopción
- [ ] Caso de uso migrado a `domain/services`.
- [ ] Repositorio o cliente implementado bajo `infra`.
- [ ] Pruebas unitarias y de integración ejecutadas en CI.
- [ ] Documentación actualizada (`README`, guías específicas).
- [ ] Publicada versión del SDK en PyPI privado.
- [ ] Servicios consumidores actualizados y redeployados.

## Conclusión
Un SDK centralizado convierte al repositorio Baltra en un núcleo extensible: los microservicios pasan a ser finos consumidores que importan contratos estables, las integraciones se mantienen en un único punto y los despliegues se vuelven reproducibles. Esta estrategia permite evolucionar el dominio con menos fricción y acelerar la entrega de nuevas funcionalidades.
