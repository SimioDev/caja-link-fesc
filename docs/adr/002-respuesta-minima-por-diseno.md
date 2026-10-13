# ADR 002: Respuesta minima por diseño, no por filtro

## Contexto

El dato minimo (Ley 1581) exige que la respuesta de afiliacion nunca incluya
nombre, direccion, telefono, correo, salario ni beneficiarios, aunque las cajas
de origen si devuelven esos campos en sus respuestas crudas (Norte y Oriente en
particular). Un error de implementacion tipico es "pasar" el JSON de la caja y
olvidar filtrar un campo nuevo que se agregue despues.

## Decision

Los modelos de respuesta (`src/schemas.py`) se construyen campo por campo a
partir del resultado interno del adaptador (`CajaLookup`/`Membership`), nunca
por "spread" o reenvio del diccionario crudo de una caja.

## Alternativas

- Lista negra de campos a remover antes de responder: descartada porque un
  campo nuevo que una caja agregue en el futuro pasaria por defecto, al reves
  de lo que exige la ley (solo se comparte lo explicitamente necesario).
- Serializacion automatica del modelo interno de cada caja con un decorador
  de "campos publicos": descartada por ser mas compleja que simplemente no
  tener esos campos en el modelo de respuesta.

## Consecuencias

Es estructuralmente imposible filtrar un campo prohibido por error: el modelo
de respuesta no tiene atributo para ponerlo. El costo es que agregar un campo
legitimo al contrato (por ejemplo affiliateType en v2) requiere tocar el modelo
de respuesta explicitamente, lo cual es deseable para este caso.
