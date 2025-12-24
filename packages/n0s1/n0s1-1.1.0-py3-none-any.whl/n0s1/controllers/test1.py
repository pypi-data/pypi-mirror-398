# def callback(a, b):
#     print('Sum = {0}'.format(a+b))
#
# def main(a,b,f=None):
#     print('Add any two digits.')
#     if f is not None:
#         f(a,b)
#
# main(1, 2, callback)

# def is_connected(self):
#     try:
#         if self._client:
#             if user := self._client.myself():
#                 self.log_message(f"Logged to {self.get_name()} as {user}")
#             else:
#                 self.log_message(f"Unable to connect to {self.get_name()} instance. Check your credentials.", logging.ERROR)
#                 return False
#
#         if projects := self._client.projects():
#             project_found = False
#             issue_found = False
#             for key in projects:
#                 project_found = True
#                 ql = f"project = '{key}'"
#                 try:
#                     for issue in self._client.search_issues(ql):
#                         if issue:
#                             issue_found = True
#                             return True
#                 except JIRAError as e:
#                     if e.status_code == 400:
#                         self.log_message(f"Skipping project '{key}' due to JIRAError 400: {e.text}", logging.WARNING)
#                         continue
#                     else:
#                         self.log_message(f"JIRAError: {e.status_code} {e.text}", logging.ERROR)
#                         continue
#                 if project_found:
#                     if issue_found: return True
#                     else: self.log_message(f"Unable to list {self.get_name()} issues. Check your permissions.", logging.ERROR)
#                 else:
#                     self.log_message(f"Unable to list {self.get_name()} projects. Check your permissions.", logging.ERROR)
#             else:
#                 self.log_message(f"Unable to connect to {self.get_name()} instance. Check your credentials.", logging.ERROR)
#                 return False
#     except JIRAError as e:
#         self.log_message(f"JIRAError: {e.status_code} {e.text}", logging.ERROR)
#         self.log_message("Failed to retrieve user information. Check your credentials and permissions.", logging.ERROR)
#     return False
#
# Console Output INFO:root:Logged to Jira as {'self': 'https://<JIRA_INSTANCE>/rest/api/2/user?accountId=<ACCOUNT_ID>', 'accountId': '<ACCOUNT_ID>', 'accountType': 'atlassian', 'emailAddress': '<EMAIL_ADDRESS>', 'avatarUrls': {'48x48': '<AVATAR_URL_48>', '24x24': '<AVATAR_URL_24>', '16x16': '<AVATAR_URL_16>', '32x32': '<AVATAR_URL_32>'}, 'displayName': '<DISPLAY_NAME>', 'active': True, 'timeZone': '<TIME_ZONE>', 'locale': '<LOCALE>', 'groups': {'size': 5, 'items': []}, 'applicationRoles': {'size': 1, 'items': []}, 'expand': 'groups,applicationRoles'} WARNING:root:Skipping project '<PROJECT_KEY_1>' due to JIRAError 400: The value '<PROJECT_KEY_1>' does not exist for the field 'project'. WARNING:root:Skipping project '<PROJECT_KEY_2>' due to JIRAError 400: The value '<PROJECT_KEY_2>' does not exist for the field 'project'. INFO:root:Starting scan in community mode... INFO:root:Scanning Jira project: [TEST]...
#

from langchain_text_splitters import RecursiveJsonSplitter

json_data = {
    "complex_key": {
        "nested_key": [
            {"item1": "value1"},
            {"item2": "value2"},
            {"item3": "value3"}
        ]
    },
    "another_key": "some_value"
}

splitter = RecursiveJsonSplitter(max_chunk_size=5)
json_chunks = splitter.split_json(json_data)

print(json_chunks)