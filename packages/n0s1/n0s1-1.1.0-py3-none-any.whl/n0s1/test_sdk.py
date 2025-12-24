import n0s1

# jira_scan --email marcelo@spark1.us --server https://spark1us.atlassian.net
jira_scanner = n0s1.Scanner(target="jira", email="marcelo@spark1.us", server="https://spark1us.atlassian.net")
jira_report = jira_scanner.scan()

print(jira_report)

findings = jira_report.get("findings", {})

for id in findings:
    url = findings[id].get("url")
    print(url)


