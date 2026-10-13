# Caja Link - Cabrera & Peñaranda

<!--
Documentación del software de la pareja (entregable «README: documentación del software», 2 puntos).
Llenen cada sección; conserven los títulos ## tal como están. Los comentarios como este no cuentan
y una sección vacía no suma. La guía del kit está en KIT.md.
-->

## Descripción

Caja Link es el servicio de interoperabilidad entre cuatro cajas de compensación familiar
(Norte, Oriente, Centro y Sur) que permite a cualquiera de ellas validar, antes de otorgar una
tarifa subsidiada o un subsidio, si una persona ya tiene afiliación vigente en otra caja,
sin compartir bases de datos entre sí, sin exponer más datos personales de los estrictamente
necesarios, y sin dar nunca una respuesta falsa cuando alguna caja no responde a tiempo.

## Integrantes

- Nestor Fabian Cabrera Carreño
- William Alexsi Peñaranda Castro

## Requisitos

Docker y el plugin `docker compose` (no se usa `docker-compose` standalone), Git, y acceso a
internet solo para construir las imágenes la primera vez. No hace falta tener Python instalado
en el equipo: todo corre dentro de contenedores.

## Instalación y ejecución

<!-- Los comandos, en orden, para levantarlo desde una copia limpia (al menos 15 palabras). Deben aparecer `docker compose` con `up`. -->

## Configuración

<!-- Expliquen cada variable de .env.example: nombre, para qué sirve y un valor de ejemplo. El sistema verifica que estén todas. -->

## Arquitectura

<!-- Componentes y cómo se comunican (al menos 30 palabras). Nombren cada servicio de docker-compose.yml; el sistema verifica que estén todos. -->

## Uso

<!-- Las rutas del servicio con un ejemplo de cada una: /api/v1/affiliations/{document}, /api/v2/affiliations/{document}, /api/v1/batch-checks, /api/v1/batch-checks/{jobId} y /api/v1/audit. El sistema verifica que aparezcan las cinco. -->

## Pruebas

<!-- Qué prueban sus pruebas automatizadas y cómo se ejecutan con docker compose --profile test run --rm tests (al menos 15 palabras). -->

## Documentación

<!-- Enlaces a los demás documentos del repositorio: docs/architecture.md, docs/adr/, docs/threat-model.md, docs/load-test.md, openapi.yaml, config/cajas.yaml y AI_USAGE.md. -->

## Qué resolvimos

<!-- Qué problemas encontraron, cómo los resolvieron y qué quedó funcionando (al menos 30 palabras). -->

## Limitaciones y pendientes

<!-- Qué no alcanzaron a hacer o qué falla todavía (al menos 10 palabras). -->
