Feature: Prueba de aceptación del MCP

Background:
  * def auth = call read('../auth/auth.feature')
  * def token = auth.token
  * configure headers = { Authorization: '#("Bearer " + token)' }
  * def baseUrl = karate.get('baseUrl')
  * def fullUrl = baseUrl + '/api/health'

Scenario: Obtener estado del microservicio
  Given url fullUrl
  When method GET
  Then status 200
  And match response == { "status": "ok" }