from typing import List, Dict, Any, Tuple, Optional

import requests

__all__ = [
    'get_headers',
    'get_databases',
    'get_database_properties',
    'get_database_contents',
    'get_page_properties',
    'get_page_contents',
]


def get_headers(token: str) -> dict:
    return {
        'Authorization': f'Bearer {token}',
        'Notion-Version': '2021-05-13',
        'Content-Type': 'application/json',
    }


def _paginate_through(url: str, token: str, post: bool = False, page_size: int = 100) -> List[Dict[str, Any]]:
    has_more = True
    data = {'page_size': page_size}
    headers = get_headers(token)

    results = []

    while has_more:
        if post:
            r = requests.post(url, json=data, headers=headers)
        else:
            r = requests.get(url, params=data, headers=headers)

        if r.status_code != 200:
            raise RuntimeError(f'request for "{url}" returned status code {r.status_code}')

        jn = r.json()
        has_more = jn['has_more']
        start_cursor = jn['next_cursor']

        data['start_cursor'] = start_cursor

        results.extend(jn['results'])

    return results


def get_databases(token: str) -> List[Dict[str, Any]]:
    url = 'https://api.notion.com/v1/databases'

    return _paginate_through(url, token=token)


def get_database_properties(database_id: str, token: str) -> Optional[Dict[str, Any]]:
    url = f'https://api.notion.com/v1/databases/{database_id}'

    r = requests.get(url, headers=get_headers(token))

    if r.status_code == 404:
        return None

    elif r.status_code != 200:
        raise RuntimeError(f'request for "{url}" returned status code {r.status_code}')

    return r.json()


def get_database_contents(database_id: str, token: str) -> List[Dict[str, Any]]:
    url = f'https://api.notion.com/v1/databases/{database_id}/query'

    return _paginate_through(url, token=token, post=True)


def get_page_properties(page_id: str, token: str) -> Optional[Dict[str, Any]]:
    url = f'https://api.notion.com/v1/pages/{page_id}'
    
    r = requests.get(url, headers=get_headers(token))

    if r.status_code == 404:
        return None

    elif r.status_code != 200:
        raise RuntimeError(f'request for "{url}" returned status code {r.status_code}')

    return r.json()


def get_block_children(block_id: str, token: str) -> List[Dict[str, Any]]:
    url = f'https://api.notion.com/v1/blocks/{block_id}/children'
    
    return _paginate_through(url, token=token)


def _get_recursive_children(block_id: str, token: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    child_blocks = []
    child_pages = []
    
    for obj in get_block_children(block_id=block_id, token=token):
        child_blocks.append(obj)

        if obj['type'] == 'child_page':
            child_pages.append(obj['id'])
        
        elif obj['has_children']:
            blocks, pages = _get_recursive_children(block_id=obj['id'], token=token)
            child_blocks.extend(blocks)
            child_pages.extend(pages)

    return child_blocks, child_pages


def get_page_contents(page_id: str, token: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    return _get_recursive_children(page_id, token)
