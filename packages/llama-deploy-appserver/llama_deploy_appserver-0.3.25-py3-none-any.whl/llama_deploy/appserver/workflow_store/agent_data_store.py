import asyncio
import logging
import os
import sys
from typing import Any, List, cast

from llama_cloud.client import AsyncLlamaCloud, httpx
from llama_cloud_services.beta.agent_data import AsyncAgentDataClient
from llama_deploy.appserver.settings import ApiserverSettings
from llama_deploy.core.client.ssl_util import get_httpx_verify_param
from llama_deploy.core.deployment_config import DeploymentConfig
from workflows.server import AbstractWorkflowStore, HandlerQuery, PersistentHandler

from .keyed_lock import AsyncKeyedLock
from .lru_cache import LRUCache

if sys.version_info <= (3, 11):
    from typing_extensions import override
else:
    from typing import override

logger = logging.getLogger(__name__)


class AgentDataStore(AbstractWorkflowStore):
    def __init__(
        self, settings: DeploymentConfig, server_settings: ApiserverSettings
    ) -> None:
        agent_url_id: str | None = server_settings.cloud_persistence_name
        collection = "workflow_contexts"
        if agent_url_id is not None:
            parts = agent_url_id.split(":")
            if len(parts) > 1:
                collection = parts[1]
            agent_url_id = parts[0]
        else:
            agent_url_id = settings.name

        self.settings = settings
        project_id = os.getenv("LLAMA_DEPLOY_PROJECT_ID")
        self.client = AsyncAgentDataClient(
            type=PersistentHandler,
            collection=collection,
            agent_url_id=agent_url_id,
            client=AsyncLlamaCloud(
                base_url=os.getenv("LLAMA_CLOUD_BASE_URL"),
                token=os.getenv("LLAMA_CLOUD_API_KEY"),
                httpx_client=httpx.AsyncClient(
                    headers={"Project-Id": project_id} if project_id else None,
                    verify=get_httpx_verify_param(),
                ),
            ),
        )
        self.lock = AsyncKeyedLock()
        # workflow id -> agent data id
        self.cache = LRUCache[str, str](maxsize=1024)

    @override
    async def query(self, query: HandlerQuery) -> List[PersistentHandler]:
        filters = self._build_filters(query)
        results = await self.client.search(
            filter=filters,
            page_size=1000,
        )
        return [x.data for x in results.items]

    @override
    async def update(self, handler: PersistentHandler) -> None:
        async with self.lock.acquire(handler.handler_id):
            id = await self._get_item_id(handler)
            if id is None:
                item = await self.client.create_item(
                    data=handler,
                )
                if item.id is None:
                    raise ValueError(f"Failed to create handler {handler.handler_id}")
                self.cache.set(handler.handler_id, item.id)
            else:
                await self.client.update_item(
                    item_id=id,
                    data=handler,
                )

    @override
    async def delete(self, query: HandlerQuery) -> int:
        filters = self._build_filters(query)
        results = await self.client.search(filter=filters, page_size=1000)
        await asyncio.gather(
            *[self.client.delete_item(item_id=x.id) for x in results.items if x.id]
        )
        return len(results.items)

    async def _get_item_id(self, handler: PersistentHandler) -> str | None:
        cached_id = self.cache.get(handler.handler_id)
        if cached_id is not None:
            return cached_id
        search_filter = {"handler_id": {"eq": handler.handler_id}}
        results = await self.client.search(
            filter=cast(Any, search_filter),
            page_size=1,
        )
        if not results.items:
            return None
        id = results.items[0].id
        if id is None:
            return None
        self.cache.set(handler.handler_id, id)
        return id

    def _build_filters(self, query: HandlerQuery) -> dict[str, Any]:
        filters: dict[str, Any] = {}
        if query.handler_id_in is not None:
            filters["handler_id"] = {
                "includes": query.handler_id_in,
            }
        if query.workflow_name_in is not None:
            filters["workflow_name"] = {
                "includes": query.workflow_name_in,
            }
        if query.status_in is not None:
            filters["status"] = {
                "includes": query.status_in,
            }
        return filters
