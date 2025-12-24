import requests
import json
import os

# Your integration token
NOTION_API_TOKEN = os.getenv("NOTION_TOKEN")
# Your database ID
DATABASE_ID = '591db2acac96450fafdb2112352d3d2d'


def query_database():
    url = f'https://api.notion.com/v1/databases/{DATABASE_ID}/query'
    headers = {
        'Authorization': f'Bearer {NOTION_API_TOKEN}',
        'Content-Type': 'application/json',
        'Notion-Version': '2022-06-28'
    }

    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def list_tasks():
    data = query_database()
    if not data:
        return

    tasks = data.get('results', [])
    for task in tasks:
        properties = task.get('properties', {})
        name_property = properties.get('Name', {})
        name_text = name_property.get('title', [{}])[0].get('text', {}).get('content', 'No Title')
        status_property = properties.get('Status', {})
        status_text = status_property.get('select', {}).get('name', 'No Status')

        print(f"Task: {name_text} | Status: {status_text}")


if __name__ == "__main__":
    list_tasks()