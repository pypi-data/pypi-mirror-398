import secret_scan
import os

debug=False
email="marcelo@spark1.us"
api_key = os.getenv("JIRA_TOKEN")
server="https://spark1us.atlassian.net"
scope = {"cql": "space=IS and type=page"}
scope=None

# result = secret_scan.confluence_scan(debug=debug, email=email, server=server, api_key=api_key, scan_scope=scope)
# print(result)

result = secret_scan.jira_scan(debug=debug, email=email, server=server, api_key=api_key)
print(result)