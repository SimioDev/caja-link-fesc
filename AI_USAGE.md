# Uso de inteligencia artificial

## Uso 1
- Herramienta: Claude Code
- Para qué se usó: diseñar la arquitectura del servicio (patrón hub central) y armar el plan de implementación completo, tarea por tarea con TDD
- Prompt principal (resumido): "arma el plan de implementacion completo para Caja Link, con tests y calidad de codigo senior"
- Qué produjo: un plan de 16 tareas con código propuesto por archivo (adaptadores, orquestador, seguridad, lote, documentación), siguiendo TDD
- Qué modificó o corrigió el equipo: el Dockerfile de pruebas no copiaba requirements.txt ni .env.example, agregamos esas líneas para que el build no fallara

## Uso 2
- Herramienta: Claude Code
- Para qué se usó: implementar el adaptador de Caja Centro (lectura del archivo plano diario) siguiendo TDD
- Prompt principal (resumido): escribir el test del adaptador de Centro y luego el código que lo hace pasar
- Qué produjo: un parser que asumía el mismo formato de fecha (YYYYMMDD) para el encabezado FECHA_CORTE y para las fechas de cada fila
- Qué modificó o corrigió el equipo: el test falló contra el archivo real porque FECHA_CORTE usa formato ISO con guiones y las fechas de fila no; separamos en dos funciones de parseo distintas

## Uso 3
- Herramienta: Claude Code
- Para qué se usó: revisión de seguridad del código ya implementado (autenticación, manejo de secretos, posibles fugas)
- Prompt principal (resumido): "haz las validaciones de seguridad, revisa que no tenga fugas"
- Qué produjo: detectó que la comparación de tokens Bearer usaba `==` simple, vulnerable en teoría a un ataque de temporización
- Qué modificó o corrigió el equipo: cambiamos la comparación a `hmac.compare_digest` en `requester_from_token` y `require_admin`, y revalidamos que la autenticación siguiera pasando
