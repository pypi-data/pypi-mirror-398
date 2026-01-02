"""Memory persistence for agent context continuity."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import httpx

from glaium.exceptions import APIError, ConnectionError, TimeoutError

# Environment variable for memory service URL
MEMORY_SERVICE_URL_ENV = "GLAIUM_MEMORY_URL"


@dataclass
class MemoryEntry:
    """A single memory entry."""

    id: str | None = None
    memory_type: str = "general"
    """Type: 'decision', 'outcome', 'pattern', 'constraint_learned', 'user_feedback'."""
    content: str = ""
    summary: str | None = None
    importance: float = 0.5
    """Importance score 0.0-1.0. Higher = more likely to be recalled."""
    tags: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    valid_until: datetime | None = None


class Memory:
    """
    Memory service for agent context persistence.

    Enables agents to remember past decisions, outcomes, and learned patterns.

    Example:
        ```python
        from glaium.extras import Memory

        memory = Memory(agent_id="my-agent", organization_id=123)

        # Store a memory
        await memory.store(
            memory_type="decision",
            content="Increased bid on campaign X by 15% due to high ROAS",
            importance=0.8,
            tags=["bid", "campaign_x"],
        )

        # Recall memories
        past = await memory.recall(
            types=["decision", "outcome"],
            limit=10,
            min_importance=0.5,
        )

        # Build context string for LLM
        context = await memory.build_context()
        ```
    """

    def __init__(
        self,
        agent_id: str,
        organization_id: int,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
    ):
        """
        Initialize memory service.

        Args:
            agent_id: Agent identifier.
            organization_id: Organization ID.
            base_url: Memory service URL. Falls back to GLAIUM_MEMORY_URL env var.
            api_key: API key for authentication.
            timeout: Request timeout in seconds.
        """
        self.agent_id = agent_id
        self.organization_id = organization_id
        self._base_url = (base_url or os.environ.get(MEMORY_SERVICE_URL_ENV, "")).rstrip("/")
        self._api_key = api_key or os.environ.get("GLAIUM_API_KEY")
        self._timeout = timeout

        # Local cache for when no service is available
        self._local_cache: list[MemoryEntry] = []
        self._use_local = not self._base_url

        self._async_client: httpx.AsyncClient | None = None

    @property
    def _async(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._async_client is None and self._base_url:
            self._async_client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
            )
        return self._async_client  # type: ignore

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        return headers

    # =========================================================================
    # Store
    # =========================================================================

    async def store(
        self,
        memory_type: str,
        content: str,
        summary: str | None = None,
        importance: float = 0.5,
        tags: list[str] | None = None,
        valid_days: int | None = None,
    ) -> MemoryEntry:
        """
        Store a new memory.

        Args:
            memory_type: Type of memory ('decision', 'outcome', 'pattern', etc.).
            content: Full memory content.
            summary: Short summary (auto-generated if not provided).
            importance: Importance score 0.0-1.0.
            tags: Tags for filtering.
            valid_days: Days until memory expires (None = no expiry).

        Returns:
            The stored MemoryEntry.
        """
        entry = MemoryEntry(
            memory_type=memory_type,
            content=content,
            summary=summary or content[:200],
            importance=importance,
            tags=tags or [],
            created_at=datetime.utcnow(),
            valid_until=(
                datetime.utcnow() + timedelta(days=valid_days)
                if valid_days
                else None
            ),
        )

        if self._use_local:
            entry.id = f"local_{len(self._local_cache)}"
            self._local_cache.append(entry)
            return entry

        try:
            payload = {
                "agent_id": self.agent_id,
                "organization_id": self.organization_id,
                "memory_type": entry.memory_type,
                "content": entry.content,
                "summary": entry.summary,
                "importance": entry.importance,
                "tags": entry.tags,
                "valid_days": valid_days,
            }
            response = await self._async.post(
                "/memory/store",
                json=payload,
                headers=self._get_headers(),
            )
            if response.status_code == 200:
                data = response.json()
                entry.id = str(data.get("id"))
            return entry
        except Exception:
            # Fall back to local storage
            entry.id = f"local_{len(self._local_cache)}"
            self._local_cache.append(entry)
            return entry

    def store_sync(
        self,
        memory_type: str,
        content: str,
        summary: str | None = None,
        importance: float = 0.5,
        tags: list[str] | None = None,
        valid_days: int | None = None,
    ) -> MemoryEntry:
        """Sync version of store()."""
        import asyncio

        return asyncio.run(
            self.store(memory_type, content, summary, importance, tags, valid_days)
        )

    # =========================================================================
    # Recall
    # =========================================================================

    async def recall(
        self,
        types: list[str] | None = None,
        limit: int = 10,
        min_importance: float = 0.0,
        days_back: int = 30,
        tags: list[str] | None = None,
    ) -> list[MemoryEntry]:
        """
        Recall relevant memories.

        Args:
            types: Filter by memory types.
            limit: Maximum memories to return.
            min_importance: Minimum importance score.
            days_back: How far back to look.
            tags: Filter by tags.

        Returns:
            List of MemoryEntry objects.
        """
        if self._use_local:
            # Filter local cache
            cutoff = datetime.utcnow() - timedelta(days=days_back)
            results = [
                m
                for m in self._local_cache
                if (m.importance >= min_importance)
                and (not types or m.memory_type in types)
                and (not tags or any(t in m.tags for t in tags))
                and (m.created_at is None or m.created_at >= cutoff)
                and (m.valid_until is None or m.valid_until > datetime.utcnow())
            ]
            # Sort by importance and recency
            results.sort(
                key=lambda x: (x.importance, x.created_at or datetime.min),
                reverse=True,
            )
            return results[:limit]

        try:
            params: dict[str, Any] = {
                "agent_id": self.agent_id,
                "organization_id": self.organization_id,
                "limit": limit,
                "min_importance": min_importance,
                "days_back": days_back,
            }
            if types:
                params["types"] = ",".join(types)
            if tags:
                params["tags"] = ",".join(tags)

            response = await self._async.get(
                "/memory/recall",
                params=params,
                headers=self._get_headers(),
            )
            if response.status_code == 200:
                data = response.json()
                return [
                    MemoryEntry(
                        id=str(m.get("id")),
                        memory_type=m.get("type", ""),
                        content=m.get("content", ""),
                        summary=m.get("summary"),
                        importance=m.get("importance", 0.5),
                        tags=m.get("tags", []),
                        created_at=datetime.fromisoformat(m["date"])
                        if m.get("date")
                        else None,
                    )
                    for m in data.get("memories", [])
                ]
            return []
        except Exception:
            # Fall back to local
            return await self.recall(types, limit, min_importance, days_back, tags)

    def recall_sync(
        self,
        types: list[str] | None = None,
        limit: int = 10,
        min_importance: float = 0.0,
        days_back: int = 30,
        tags: list[str] | None = None,
    ) -> list[MemoryEntry]:
        """Sync version of recall()."""
        import asyncio

        return asyncio.run(self.recall(types, limit, min_importance, days_back, tags))

    # =========================================================================
    # Context Building
    # =========================================================================

    async def build_context(
        self,
        limit: int = 15,
        min_importance: float = 0.3,
    ) -> str:
        """
        Build memory context string for LLM prompts.

        Args:
            limit: Maximum memories to include.
            min_importance: Minimum importance score.

        Returns:
            Formatted string with relevant memories.
        """
        memories = await self.recall(limit=limit, min_importance=min_importance)

        if not memories:
            return "No relevant past memories."

        context = "RELEVANT MEMORIES FROM PAST EXECUTIONS:\n\n"

        # Group by type
        by_type: dict[str, list[MemoryEntry]] = {}
        for m in memories:
            by_type.setdefault(m.memory_type, []).append(m)

        for memory_type, type_memories in by_type.items():
            context += f"[{memory_type.upper()}]\n"
            for m in type_memories[:5]:  # Max 5 per type
                date_str = (
                    m.created_at.strftime("%Y-%m-%d") if m.created_at else "unknown"
                )
                context += f"  - ({date_str}) {m.summary or m.content[:100]}\n"
            context += "\n"

        return context

    def build_context_sync(
        self,
        limit: int = 15,
        min_importance: float = 0.3,
    ) -> str:
        """Sync version of build_context()."""
        import asyncio

        return asyncio.run(self.build_context(limit, min_importance))

    # =========================================================================
    # Decision Outcome Storage
    # =========================================================================

    async def store_decision_outcome(
        self,
        decision: str,
        outcome: str,
        success: bool,
        lesson_learned: str | None = None,
    ) -> MemoryEntry:
        """
        Store the outcome of a decision for learning.

        Args:
            decision: What decision was made.
            outcome: What was the result.
            success: Whether it was successful.
            lesson_learned: Optional lesson to remember.

        Returns:
            The stored MemoryEntry.
        """
        importance = 0.6 if success else 0.8  # Failures more important to remember

        content = f"Decision: {decision}\nOutcome: {outcome}"
        if lesson_learned:
            content += f"\nLesson: {lesson_learned}"

        return await self.store(
            memory_type="outcome" if success else "constraint_learned",
            content=content,
            summary=f"{'Success' if success else 'Failure'}: {decision[:100]}",
            importance=importance,
            tags=["decision_outcome", "success" if success else "failure"],
        )

    # =========================================================================
    # Cleanup
    # =========================================================================

    async def aclose(self) -> None:
        """Close async client."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

    async def __aenter__(self) -> "Memory":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
