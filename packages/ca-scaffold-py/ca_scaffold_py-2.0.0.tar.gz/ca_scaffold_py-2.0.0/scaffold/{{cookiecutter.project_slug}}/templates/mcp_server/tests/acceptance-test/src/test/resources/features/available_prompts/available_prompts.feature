Feature: MCP Prompts Listing

Background:
  * def auth = call read('../auth/auth.feature')
  * def token = auth.token
  * configure headers = { Authorization: '#("Bearer " + token)' }

  Scenario: Complete MCP flow - List prompts
    * def baseUrl = karate.get('baseUrl')
    * def mcpUrl = baseUrl + '/mcp/?transportType=streamable-http'
    * def protocolVersion = '2025-06-18'
        
    Given url mcpUrl
    And header accept = 'application/json, text/event-stream'
    And header content-type = 'application/json'
    And header mcp-protocol-version = protocolVersion
    And request
      """
      {
        "method": "prompts/list",
        "params": {
          "_meta": {
            "progressToken": 1
          }
        },
        "jsonrpc": "2.0",
        "id": 1
      }
      """
    When method POST
    Then status 200
    And match header Content-Type == 'text/event-stream'

    * def rawDataLine = response.split('\n').find(x => x.startsWith('data:'))
    * def rawJson = rawDataLine.replace('data: ', '')
    * def promptsResponseData = karate.jsonPath(rawJson, '$')

    And match promptsResponseData.result.prompts[0].name == "generate_search_prompt"
