Feature: Consume a tool MCP

Background:
  * def auth = call read('../auth/auth.feature')
  * def token = auth.token
  * configure headers = { Authorization: '#("Bearer " + token)' }

  Scenario: Complete MCP flow - Consume tools
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
        "method":"tools/call",
        "params":{
            "name":"extract_info",
            "arguments":
                {"paper_id":"search"},
                "_meta":{
                  "progressToken":1
                }
        },
        "jsonrpc":"2.0",
        "id":5
        }
        """
      When method POST
      Then status 200

      