# Modelo de amenazas

| Categoría | Amenaza | Mitigación | Prueba |
|---|---|---|---|
| Autenticación | Una caja sin token (o con uno invalido) consulta afiliaciones de otras cajas | Cada ruta exige `Authorization: Bearer <token>` validado contra el token configurado de cada caja; sin coincidencia, 401 | test_consulta_sin_token_responde_401 |
| Finalidad | Una consulta sin declarar para que se usa el dato, o con una finalidad no reconocida | El parametro purpose es obligatorio y se valida contra la lista cerrada de finalidades permitidas; si falta o no es valida, 400 | test_consulta_sin_purpose_responde_400 |
| Dato mínimo | La respuesta filtra campos personales (nombre, direccion, telefono, correo, salario) que las cajas de origen si devuelven | Los modelos de respuesta se construyen campo por campo (ADR-002): el esquema de salida no tiene atributo para esos campos, asi que no pueden aparecer por accidente | test_consulta_respuesta_no_contiene_campos_prohibidos |
| Secretos | Una URL, token o contraseña de una caja queda escrita en el codigo fuente del equipo | Todas las credenciales y URLs se leen de variables de entorno (.env, nunca versionado); una prueba automatizada escanea src/ en busca de direcciones de caja hardcodeadas | test_no_source_file_hardcodes_a_caja_address_or_port |
| Auditoría | Alguien sin privilegios de administrador lee el historial de consultas de todas las cajas | GET /api/v1/audit exige el ADMIN_TOKEN especificamente (un token de caja valido no alcanza) y cada entrada guarda el documento enmascarado, nunca en claro | test_auditoria_requiere_admin_token |
