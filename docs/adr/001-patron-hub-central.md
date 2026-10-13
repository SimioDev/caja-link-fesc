# ADR 001: Patron de integracion hub central

## Contexto

El reto exige integrar cuatro cajas heterogeneas (REST, SOAP, archivo plano, y una
cuarta activable por configuracion) detras de un unico contrato ya fijado por los
organizadores. El equipo es de dos personas con tiempo acotado y el contrato no
deja margen para negociar el formato de respuesta entre cajas.

## Decision

Usamos un hub central: un unico servicio (`caja-link`) que mantiene un adaptador
por caja detras de una interfaz comun (`CajaAdapter.lookup`) y un orquestador que
llama a todos los adaptadores relevantes en paralelo, agregando el resultado.

## Alternativas

- Federado: cada caja resuelve su parte de la consulta y las respuestas se
  combinan en el cliente o en un bus de eventos; descartado por requerir que las
  cajas (que son mocks fijos del kit) cooperen en un protocolo que no existe.
- Hibrido: hub central para consulta en linea, cola de eventos para el lote;
  descartado por complejidad operativa (una pieza de infraestructura mas) sin
  beneficio medible a la escala de 4 cajas y 10.000 documentos del reto.

## Consecuencias

Toda la logica de negocio (exclusion de la caja consultante, calculo de vigencia,
tolerancia a fallas) vive en un solo lugar (`src/orchestrator.py`), facil de
probar con adaptadores falsos sin red. El costo es que el hub es un punto unico
de fallo del lado de caja-link mismo, aceptable porque el propio contrato del
reto ya asume un unico servicio en el puerto 8083.
