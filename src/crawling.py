from datetime import datetime
from typing import List, Dict, Any

from tqdm import tqdm

from config import get_token
from src.notion_api import get_databases, get_database_contents, get_page_properties, get_page_contents
from src.db import session
from src.models import Database, Page, Mention

__all__ = [
    'update',
]

token = get_token()


def get_database_ids() -> List[str]:
    """Get a list of database ids.

    Also deletes all the local databases that are not present in Notion.

    :return: list of database ids
    """

    databases = {database.id: database for database in session.query(Database).all()}

    database_ids = set()

    for item in get_databases(token):
        database_id = item['id']
        database = databases.get(database_id, Database(id=database_id))

        database.title = ''.join(part['plain_text'] for part in item['title'])

        session.add(database)
        session.commit()

        database_ids.add(database_id)

    for database_id in set(databases.keys()) - database_ids:
        database = databases[database_id]
        session.delete(database)
        session.commit()

    return list(database_ids)


def get_edited_database_page_ids(database_id: str) -> List[str]:
    """Get a list of ids of edited database pages.

    Also deletes all the pages in the local database
    that are not present in Notion.

    :return: list of edited database page ids
    """

    database = session.query(Database).filter(Database.id == database_id).first()

    database_pages = {page.id: page for page in database.pages}
    database_page_edit_times = {page.id: page.last_edited for page in database_pages.values()}

    page_ids = set()
    edited_page_ids = set()

    for item in get_database_contents(database_id=database_id, token=token):
        if item['object'] != 'page':
            continue

        page_id = item['id']
        page_ids.add(page_id)

        last_edited = item['last_edited_time']

        if page_id not in database_page_edit_times or last_edited != database_page_edit_times[page_id]:
            edited_page_ids.add(page_id)

    for page_id in set(database_page_edit_times.keys()) - page_ids:
        page = database_pages[page_id]
        session.delete(page)
        session.commit()

    return list(edited_page_ids)


def get_child_pages() -> List[str]:
    query = session.query(Page).filter(Page.parent_id.isnot(None))

    return [page.id for page in query.all()]


def get_page_title(page_properties: dict) -> str:
    for prop in page_properties['properties'].values():
        if prop['type'] == 'title':
            return ''.join(part['plain_text'] for part in prop['title'])


def get_mentioned_page_ids(page_properties: dict, page_contents: List[dict]) -> List[str]:
    def find_mentions(block_text: List[Dict[str, Any]]) -> List[str]:
        block_mentions = []

        for block_text_part in block_text:
            if block_text_part['type'] == 'mention' and block_text_part['mention']['type'] == 'page':
                block_mentions.append(block_text_part['mention']['page']['id'])

        return block_mentions

    mentions = []

    for prop in page_properties['properties'].values():
        if prop['type'] in {'title', 'rich_text'}:
            text = prop[prop['type']]

            mentions.extend(find_mentions(text))

    for block in page_contents:
        text = block[block['type']].get('text', [])

        mentions.extend(find_mentions(text))

    return mentions


def update_page(page_id: str, force: bool = False):
    """Updates the given page and its child pages.

    Does not update if page's `last_edited` property has not
    changed since the last crawling process.

    Set force=True to override the above and force-update.

    :param page_id: page id
    :param force: force update page
    """

    page = session.query(Page).filter(Page.id == page_id).first() or Page(id=page_id)
    properties = get_page_properties(page_id=page_id, token=token)

    if properties is None:  # page does not exist anymore
        session.delete(page)
        session.commit()
        return

    last_edited = properties['last_edited_time']

    if not force and page.last_edited == last_edited:
        return

    page.url = properties.get('url')

    session.query(Mention).filter(Mention.page_id == page_id).delete()
    session.commit()

    blocks, child_pages = get_page_contents(page_id=page_id, token=token)
    page.crawling_time = datetime.now()

    page.title = get_page_title(properties)
    page.last_edited = last_edited

    parent = properties['parent']
    parent_type = parent['type']

    if parent_type == 'page_id':
        page.parent_id = parent[parent_type]
        page.database_id = None

        mention = Mention(page_id=page_id, mentioned_id=page.parent_id)
        session.add(mention)
        session.commit()

    elif parent_type == 'database_id':
        page.database_id = parent[parent_type]
        page.parent_id = None

    else:
        raise ValueError(f'parent type {parent_type} not understood')

    session.add(page)
    session.commit()

    mentioned_page_ids = get_mentioned_page_ids(page_properties=properties, page_contents=blocks)

    for mentioned_id in mentioned_page_ids:
        mention = Mention(page_id=page_id, mentioned_id=mentioned_id)
        session.add(mention)
        session.commit()

    for page_id in child_pages:
        update_page(page_id=page_id, force=force)


def update(force: bool = False, progress_bar: bool = False):
    page_ids = []

    for database_id in get_database_ids():
        page_ids.extend(get_edited_database_page_ids(database_id))

    page_ids.extend(get_child_pages())

    for page_id in tqdm(page_ids, disable=not progress_bar):
        update_page(page_id=page_id, force=force)

    for mention in session.query(Mention).all():
        if mention.mentioned is None:  # mention of a non-existent page
            session.delete(mention)
            session.commit()
