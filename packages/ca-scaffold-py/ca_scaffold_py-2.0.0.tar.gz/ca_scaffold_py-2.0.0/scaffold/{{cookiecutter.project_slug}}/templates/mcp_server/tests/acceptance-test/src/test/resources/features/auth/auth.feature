Feature: Obtener token JWT desde Cognito con client_credentials

Scenario: Solicitar token
  * def fullUrl = karate.get('cognitoUrl')
  * def clientId = karate.get('clientId')
  * def clientSecret = karate.get('clientSecret')

  Given url fullUrl
  And header Content-Type = 'application/x-www-form-urlencoded'
  And request 'grant_type=client_credentials&client_id=' + clientId + '&client_secret=' + clientSecret
  When method POST
  Then status 200
  * def token = response.access_token