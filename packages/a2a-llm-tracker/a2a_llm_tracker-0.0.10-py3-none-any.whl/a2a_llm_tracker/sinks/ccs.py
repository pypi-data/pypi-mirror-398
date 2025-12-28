from __future__ import annotations

import asyncio
import json
import threading
from .base import Sink
from ..events import UsageEvent


class CCSSink(Sink):
    """Sink that sends usage events to mftsccs using LocalTransaction."""

    def __init__(
        self,
        application_name: str = "",
        user_id: int = 101,
        entity_id: int = 0,
    ) -> None:
        """
        Initialize the CCS sink.

        Args:
            application_name: Name of the application (used as parent concept)
            user_id: User ID for creating concepts
            entity_id: Entity ID to connect the tracker to (from client_id)
        """
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self.application_name = application_name
        self.user_id = user_id
        self.entity_id = entity_id

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def write(self, event: UsageEvent) -> None:
        fut = asyncio.run_coroutine_threadsafe(
            self._write_async(event),
            self._loop
        )
        fut.result() 

    # def write(self, event: UsageEvent) -> None:
    #     """
    #     Send a usage event to mftsccs using LocalTransaction.

    #     This is a sync wrapper that runs the async _write_async method.

    #     Args:
    #         event: The usage event to send
    #     """
    #     async def _write_with_error_handling():
    #         try:
    #             await self._write_async(event)
    #         except Exception as e:
    #             import traceback
    #             print("Error in CCS sink write:", e)
    #             traceback.print_exc()

    #     try:
    #         loop = asyncio.get_running_loop()
    #         # Already in an async context - schedule task in current loop
    #         # Use create_task and keep reference to prevent garbage collection
    #         task = loop.create_task(_write_with_error_handling())

    #         # Store task reference to prevent cancellation
    #     except RuntimeError:
    #         # No running loop, create a new one and run synchronously
    #         asyncio.run(_write_with_error_handling())

    async def awrite(self, event: UsageEvent) -> None:
        """
        Async version of write - use this when calling from async code.

        Args:
            event: The usage event to send
        """
        try:
            await self._write_async(event)
        except Exception as e:
            import traceback
            print("Error in CCS sink write:", e)
            traceback.print_exc()

    async def _write_async(self, event: UsageEvent) -> None:
        """
        Async implementation of write using LocalTransaction.

        Creates:
        - A "the_llm_tracker" concept for the app (upserted via isLocal=True)
        - A "the_llm_usage" concept for each usage event
        - A "the_llm_provider" concept (upserted)
        - A "the_llm_model" concept (upserted)
        - Connections between them
        - If entity_id is provided, connects the tracker to that entity

        Args:
            event: The usage event to send
        """
        from ccs import LocalTransaction, GetTheConcept

        tx = LocalTransaction()
        await tx.initialize()

        try:
            # Create/upsert the application concept (isLocal=True for upsert behavior)
            app_concept = await tx.MakeTheInstanceConceptLocal(
                "the_llm_tracker",  # concept type
                self.application_name or "llm-tracker",  # concept value
                True,  # isLocal - upsert if exists
                userId=self.user_id,
            )
            # If entity_id provided, connect tracker to that entity
            if self.entity_id:
                try:
                    print("this is the app concept", app_concept, self.entity_id)
                    entityId = self.entity_id
                    entity = await GetTheConcept(entityId)
                    print("this is the entity", entity)
                    if entity and entity.id != 0:
                        await tx.CreateConnection(
                            entity,
                            app_concept,
                            "the_entity_s_llm_tracker",
                        )
                        print("Entity connection created successfully")
                except BaseException as e:
                    # Continue without entity connection if it fails
                    import traceback
                    import sys
                    print("Exception error in entity connection:", e, file=sys.stderr)
                    traceback.print_exc()
                    # Explicitly continue - don't re-raise
                print("Continuing after entity connection attempt...")

            # Create the usage concept with all event data as value (isLocal=False - always create new)
            # Build properties JSON for the usage event
            properties = {
                "ts": event.ts.isoformat(),
                "provider": event.provider,
                "model": event.model,
                "status": event.status,
            }

            if event.total_tokens is not None:
                properties["total_tokens"] = event.total_tokens
            if event.cost_usd is not None:
                properties["cost_usd"] = event.cost_usd
            if event.accuracy:
                properties["accuracy"] = event.accuracy
            if event.latency_ms is not None:
                properties["latency_ms"] = event.latency_ms
            if event.error_type:
                properties["error_type"] = event.error_type
            if event.error_message:
                properties["error_message"] = event.error_message
            if event.token_breakdown:
                properties["token_breakdown"] = [b.to_dict() for b in event.token_breakdown]
            if event.metadata:
                properties["metadata"] = event.metadata

            properties_json = json.dumps(properties)

            usage_concept = await tx.MakeTheInstanceConceptLocal(
                "the_llm_usage",  # concept type
                properties_json,  # concept value (JSON string with all data)
                False,  # isLocal=False - always create new
                userId=self.user_id,
            )

            # Connect application -> usage
            await tx.CreateConnection(
                app_concept,
                usage_concept,
                "the_llm_tracker_usage",
            )

            # Create/upsert provider concept and connect
            if event.provider:
                provider_concept = await tx.MakeTheInstanceConceptLocal(
                    "the_llm_provider",
                    event.provider,
                    True,  # isLocal=True - upsert
                    userId=self.user_id,
                )
                await tx.CreateConnection(
                    app_concept,
                    provider_concept,
                    "the_llm_tracker_provider",
                )

            # Create/upsert model concept and connect
            if event.model:
                model_concept = await tx.MakeTheInstanceConceptLocal(
                    "the_llm_model",
                    event.model,
                    True,  # isLocal=True - upsert
                    userId=self.user_id,
                )
                await tx.CreateConnection(
                    app_concept,
                    model_concept,
                    "the_llm_tracker_model",
                )

            # Add individual property concepts for easier querying
            if event.cost_usd is not None:
                cost_concept = await tx.MakeTheInstanceConceptLocal(
                    "the_cost",
                    str(event.cost_usd),
                    False,
                    userId=self.user_id,
                )
                await tx.CreateConnection(
                    app_concept,
                    cost_concept,
                    "the_llm_tracker_cost",
                )

            if event.total_tokens is not None:
                tokens_concept = await tx.MakeTheInstanceConceptLocal(
                    "the_token_count",
                    str(event.total_tokens),
                    False,
                    userId=self.user_id,
                )
                await tx.CreateConnection(
                    app_concept,
                    tokens_concept,
                    "the_llm_tracker_tokens",
                )

            # Commit the transaction
            await tx.commitTransaction()

        except Exception as e:
            # Rollback on error
            print("Exception error outside:", e)
            await tx.rollbackTransaction()
            raise
