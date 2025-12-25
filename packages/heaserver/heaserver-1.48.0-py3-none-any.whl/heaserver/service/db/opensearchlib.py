import logging
from typing import AsyncGenerator

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from heaobject.folder import Item

import re

from heaserver.service import response
from heaserver.service.appproperty import HEA_DB
from heaserver.service.db.database import DatabaseContextManager
from heaobject.root import DesktopObjectDict, to_dict
from heaserver.service.db.opensearch import OpenSearch, ItemTypeVar, OpenSearchContext


def build_query(request: Request, permission_context: dict[str, list[str]], regexp_type: str, search_term: str):
    # Placeholder for the must array in the query
    # Handle multiple `regexp` query params
    santize_search_term = re.escape(search_term).lower()
    if not search_term:
        raise ValueError("search text is required and cannot be empty")

    # Build the final query object
    search_path = None
    if regexp_type == 'contains':
        search_path= {
            "match": {
                "path.contains": santize_search_term
            }
        }
    elif regexp_type == 'starts_with':
        search_path= {
            "prefix": {
                "path.starts_with": santize_search_term
            }
        }
    elif regexp_type == 'ends_with':
        search_path= {
            "prefix": {
                "path.ends_with": santize_search_term[::-1]
            }
        }
    else:
        raise ValueError("Invalid query type. Must be one of: 'contains', 'starts_with', 'ends_with'.")

    query = {
        "query": {
            "bool": {
                "must": [
                    search_path,
                    {"terms": permission_context}
                ]
            }
        }
    }
    if regexp_type == 'contains':
        query["query"]["bool"]["filter"] = [
            {
                "regexp": {
                    "path.keyword": f".*{santize_search_term}.*"
                }
            }
        ]

    return query



async def insert (request: Request,
                  doc: Item,
                  index: str | None = None) -> Response:
    """
    Executes a dynamic search query in OpenSearch and returns the result. The request can provide a volume_id
    as a route param instead of using the volume_id parameter.

    :param doc:
    :param request: the HTTP request.
    :param index: (Optional) the OpenSearch index name, if not present it will default to db config for it.
    :return: The OpenSearch query result or None if no result is found.
    """
    logger = logging.getLogger(__name__)
    if not doc:
        return response.status_bad_request('The item is required to insert')
    doc_volume_id =  doc.volume_id if doc.volume_id else None
    volume_id_ = request.match_info.get('volume_id') if request.match_info.get('volume_id') else doc_volume_id

    # Build the query dynamically based on the input parameters
    async with OpenSearchContext(request=request, volume_id= volume_id_) as opensearch:
        result = await opensearch.insert(doc=doc.to_dict() , index=index)
        if not result:
            return response.status_bad_request("Invalid search results")
        logger.debug(f"opensearch result id: {result}")
    return await response.put(True if result else False)


async def batch_insert(request: Request,
                       doc_gen: AsyncGenerator[ItemTypeVar, None],
                       volume_id: str | None = None) -> Response:
    """
    Executes a dynamic search query in OpenSearch and returns the result. The request can provide a volume_id
    as a route param instead of using the volume_id parameter.

    :param doc_gen: a generator that yields ItemTypeVar
    :param volume_id: (Optional) the volume if for associating the volume.
    :return: The OpenSearch query result or None if no result is found.
    """
    logger = logging.getLogger(__name__)

    volume_id_ = request.match_info.get('volume_id') if request.match_info.get('volume_id') else volume_id

    # Build the query dynamically based on the input parameters
    async with OpenSearchContext(request=request, volume_id= volume_id_) as opensearch:
        result = await opensearch.batch_insert(bulk_doc_gen=doc_gen)
        if not result:
            return response.status_bad_request("Invalid search results")
        logger.debug(f"opensearch result id: {result}")
    return await response.put(True if result else False)


async def get(request: Request,
              item_id: str,
              search_item_type: type[ItemTypeVar],
              index: str | None = None,
              volume_id: str | None = None) -> ItemTypeVar | None:
    """
    Retrieves a single item from OpenSearch using its document ID. The request can provide a volume_id
    as a route param instead of using the volume_id parameter.

    :param request: the HTTP request.
    :param item_id: the ID of the item to retrieve.
    :param search_item_type: the class type to deserialize the result into.
    :param index: (Optional) the index to retrieve from.
    :param volume_id: (Optional) the volume ID, used in OpenSearch context.
    :return: The item instance or None.
    """
    volume_id_ = request.match_info.get('volume_id') if request.match_info.get('volume_id') else volume_id

    async with OpenSearchContext(request=request, volume_id=volume_id_) as opensearch:
        return await opensearch.get_doc(item_id=item_id, search_item_type=search_item_type, index=index)


async def search(request: Request,
                 search_item_type: type[ItemTypeVar],
                 perm_context: dict[str, list[str]],
                 index: str | None = None,
                 volume_id: str | None = None) -> Response:
    """
    Executes a dynamic search query in OpenSearch and returns the result. The request can provide a volume_id
    as a route param instead of using the volume_id parameter.

    :param request: the HTTP request.
    :param search_item_type:
    :param perm_context: The permission context provides list of strings where at least one needs match
    :param index: (Optional) the OpenSearch index name, if not present it will default to db config for it.
    :param volume_id: (Optional) the id of the volume
    :return: The OpenSearch query result or None if no result is found.
    """
    logger = logging.getLogger(__name__)
    volume_id_ = request.match_info.get('volume_id') if request.match_info.get('volume_id', None) else volume_id
    regexp_type = request.query.get('regexp_type', 'contains')
    search_term = request.query.get('text', '')

    # Build the query dynamically based on the input parameters
    query = build_query(request, perm_context,regexp_type, search_term )
    async with OpenSearchContext(request=request, volume_id=volume_id_) as opensearch:
        results = await opensearch.search(query=query, search_item_type=search_item_type, index=index)
        if not results:
            return response.status_bad_request("Invalid search results")
        logger.debug(f"opensearch result: {results}")
    return await response.get_all(request, [to_dict(sr) for sr in results])


async def search_dict(request: Request,
                      search_item_type: type[ItemTypeVar],
                      perm_context: dict[str, list[str]],
                      index: str | None = None,
                      volume_id: str | None = None)  -> list[DesktopObjectDict]:
    """
    Executes a dynamic search query in OpenSearch and returns the results as a list of dictionaries. The request can provide a volume_id
    as a route param instead of using the volume_id parameter.

    :param request: The HTTP request containing headers and query parameters.
    :param search_item_type: The type of items to search for, used for deserializing the results.
    :param perm_context: A dictionary of permission context specifying lists of strings where at least one needs to match.
    :param index: (Optional) The OpenSearch index name. Defaults to the configured database index if not specified.
    :param volume_id: (Optional) The ID of the volume to filter the search query.
    :return: A list of search results as dictionaries. Returns an empty list if no results are found.
    """
    logger = logging.getLogger(__name__)
    volume_id_ = request.match_info.get('volume_id') if request.match_info.get('volume_id', None) else volume_id
    regexp_type = request.query.get('regexp_type', 'contains')
    search_term = request.query.get('text', '')

    # Build the query dynamically based on the input parameters
    query = build_query(request, perm_context, regexp_type, search_term)
    async with OpenSearchContext(request=request, volume_id=volume_id_) as opensearch:
        results = await opensearch.search(query=query, search_item_type=search_item_type, index=index)
        if not results:
            return []
        logger.debug(f"opensearch result: {results}")
    return [to_dict(sr) for sr in results]


async def batch_delete(request: Request,
                       doc_ids_gen: AsyncGenerator[str, None],
                       volume_id: str | None = None) -> Response:
    """
    Deletes multiple documents from OpenSearch using their document IDs.The request can provide a volume_id
    as a route param instead of using the volume_id parameter.


    :param request: The HTTP request.
    :param doc_ids_gen: An async generator yielding document IDs to delete.
    :param volume_id: (Optional) Volume ID to determine OpenSearch context.
    :return: Response indicating success or failure.
    """
    logger = logging.getLogger(__name__)
    volume_id_ = request.match_info.get('volume_id') if request.match_info.get('volume_id') else volume_id

    async with OpenSearchContext(request=request, volume_id=volume_id_) as opensearch:
        result = await opensearch.batch_delete(bulk_doc_ids=doc_ids_gen)
        if not result:
            return response.status_bad_request("Batch delete failed")
        logger.debug("Batch delete completed successfully.")

    return await response.put(True)


async def delete(request: Request,
                 item_id: str,
                 index: str | None = None,
                 volume_id: str | None = None) -> bool:
    """
    Deletes a single document from OpenSearch using its document ID. The request can provide a volume_id
    as a route param instead of using the volume_id parameter.

    :param request: the HTTP request.
    :param item_id: the ID of the item to delete.
    :param index: (Optional) the index to delete from.
    :param volume_id: (Optional) the volume ID, used in OpenSearch context.
    :return: True if deleted, False if not found.
    """
    volume_id_ = request.match_info.get('volume_id') if request.match_info.get('volume_id') else volume_id

    async with OpenSearchContext(request=request, volume_id=volume_id_) as opensearch:
        return await opensearch.delete_doc(item_id=item_id, index=index)
