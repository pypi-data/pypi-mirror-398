Feature: MCP Tool Listing

Background:
  * def auth = call read('../auth/auth.feature')
  * def token = auth.token
  * configure headers = { Authorization: '#("Bearer " + token)' }

  Scenario: Complete MCP flow - List tools
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
        "method": "tools/list",
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
    * def toolsResponseData = karate.jsonPath(rawJson, '$')

    And match toolsResponseData.result.tools[0].name == "search_papers"
    And match toolsResponseData.result.tools[1].name == "extract_info"
    And match toolsResponseData.result.tools[2].name == "sum_numbers"
