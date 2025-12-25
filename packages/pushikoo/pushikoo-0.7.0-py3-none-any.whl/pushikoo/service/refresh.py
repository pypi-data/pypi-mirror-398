import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple
from uuid import UUID

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from pushikoo_interface import (
    Detail,
    Getter,
    Processer,
    Pusher,
    Struct,
    StructImage,
    StructText,
    TerminateFlowException,
)
from sqlmodel import func, select

from pushikoo.db import AdapterInstance as AdapterInstanceDB
from pushikoo.db import Flow as FlowDB
from pushikoo.db import FlowCron as FlowCronDB
from pushikoo.db import FlowInstance as FlowInstanceDB
from pushikoo.db import get_session
from pushikoo.model.config import SystemConfig
from pushikoo.model.cron import Cron, CronCreate, CronListFilter, CronUpdate
from pushikoo.model.flow import (
    Flow,
    FlowCreate,
    FlowInstanceListFilter,
    FlowInstanceOrder,
    FlowInstanceStatus,
    FlowListFilter,
    FlowUpdate,
)
from pushikoo.model.flow import (
    FlowInstance as FlowInstanceModel,
)
from pushikoo.model.message import MessageCreate, MessageListFilter
from pushikoo.model.pagination import Page, apply_page_limit
from pushikoo.service.adapter import AdapterInstanceService
from pushikoo.service.config import ConfigService
from pushikoo.service.image import ImageService
from pushikoo.service.message import MessageService
from pushikoo.service.warning import WarningService
from pushikoo.util.setting import CRON_SCHEDULER_MAX_WORKERS

getter_get_timeline_continuous_failed_times: dict[tuple[str, str], int] = {}


class FlowService:
    @staticmethod
    def _to_model(session, flow_db: FlowDB) -> Flow:
        return Flow(
            id=flow_db.id,
            name=flow_db.name,
            nodes=list(flow_db.nodes or []),
        )

    @staticmethod
    def create(flow_create: FlowCreate) -> Flow:
        with get_session() as session:
            if not flow_create.nodes:
                raise ValueError("Flow must have at least one node")

            # Validate all nodes exist
            for adapter_instance_id in flow_create.nodes:
                adapter_db = session.exec(
                    select(AdapterInstanceDB).where(
                        AdapterInstanceDB.id == adapter_instance_id
                    )
                ).first()
                if not adapter_db:
                    raise ValueError(
                        f"Flow node adapter instance not found: {adapter_instance_id}"
                    )

            flow_db = FlowDB(name=flow_create.name, nodes=list(flow_create.nodes))
            session.add(flow_db)
            session.flush()

            session.commit()
            logger.info(f"Created flow {flow_db.id}")
            return FlowService._to_model(session, flow_db)

    @staticmethod
    def list_(filter: FlowListFilter) -> Page[Flow]:
        with get_session() as session:
            # When filtering by getter_instance_id we must filter in Python,
            # because getter is encoded as the first node in the JSON list.
            if filter and filter.getter_instance_id is not None:
                all_rows = session.exec(select(FlowDB).order_by(FlowDB.id)).all()
                filtered_rows = [
                    f
                    for f in all_rows
                    if f.nodes and f.nodes[0] == filter.getter_instance_id
                ]
                total = len(filtered_rows)
                if filter.offset is not None:
                    filtered_rows = filtered_rows[filter.offset :]
                if filter.limit is not None:
                    filtered_rows = filtered_rows[: filter.limit]
                rows = filtered_rows
            else:
                # Get total count
                count_q = select(func.count()).select_from(FlowDB)
                total = session.exec(count_q).one()

                q = select(FlowDB).order_by(FlowDB.id)
                if filter and filter.offset is not None:
                    q = q.offset(filter.offset)
                if filter and filter.limit is not None:
                    q = q.limit(apply_page_limit(filter.limit))
                rows = session.exec(q).all()

            items = [FlowService._to_model(session, f) for f in rows]
            return Page(
                items=items,
                total=total,
                limit=filter.limit if filter else None,
                offset=filter.offset if filter else None,
            )

    @staticmethod
    def get(flow_id: UUID) -> Flow:
        with get_session() as session:
            flow_db = session.exec(select(FlowDB).where(FlowDB.id == flow_id)).first()

            if not flow_db:
                raise KeyError("Not found")

            return FlowService._to_model(session, flow_db)

    @staticmethod
    def update(flow_id: UUID, flow_update: FlowUpdate) -> Flow:
        with get_session() as session:
            flow_db = session.exec(select(FlowDB).where(FlowDB.id == flow_id)).first()
            if not flow_db:
                raise ValueError("Not found")

            if flow_update.name is not None:
                flow_db.name = flow_update.name

            if flow_update.nodes is not None:
                if not flow_update.nodes:
                    raise ValueError("Flow must have at least one node")

                # Validate all nodes exist
                for adapter_instance_id in flow_update.nodes:
                    adapter_db = session.exec(
                        select(AdapterInstanceDB).where(
                            AdapterInstanceDB.id == adapter_instance_id
                        )
                    ).first()
                    if not adapter_db:
                        raise ValueError(
                            f"Flow node adapter instance not found: {adapter_instance_id}"
                        )

                flow_db.nodes = list(flow_update.nodes)

            session.commit()
            logger.info(f"Updated flow {flow_id}")
            return FlowService._to_model(session, flow_db)

    @staticmethod
    def delete(flow_id: UUID) -> None:
        with get_session() as session:
            flow_db = session.exec(select(FlowDB).where(FlowDB.id == flow_id)).first()
            if not flow_db:
                raise ValueError("Not found")

            # remove related crons for this flow
            flow_crons = session.exec(
                select(FlowCronDB).where(FlowCronDB.flow_id == flow_id)
            ).all()
            for cron in flow_crons:
                session.delete(cron)

            session.delete(flow_db)
            session.commit()

        # reload scheduler to drop any jobs bound to this flow
        CronService._reload()

        logger.info(f"Deleted flow {flow_id}")


class FlowInstanceService:
    @staticmethod
    def _to_model(instance_db: FlowInstanceDB) -> FlowInstanceModel:
        return FlowInstanceModel(
            id=instance_db.id,
            flow_id=instance_db.flow_id,
            status=FlowInstanceStatus(instance_db.status),
            created_at=instance_db.created_at,
        )

    @staticmethod
    def create(
        flow_id: UUID, status: FlowInstanceStatus = FlowInstanceStatus.WAITING
    ) -> FlowInstanceModel:
        with get_session() as session:
            instance_db = FlowInstanceDB(flow_id=flow_id, status=status.value)
            session.add(instance_db)
            session.commit()
            session.refresh(instance_db)
            logger.info(f"Created flow instance {instance_db.id} for flow {flow_id}")
            return FlowInstanceService._to_model(instance_db)

    @staticmethod
    def update_status(
        instance_id: UUID, status: FlowInstanceStatus
    ) -> FlowInstanceModel:
        with get_session() as session:
            instance_db = session.exec(
                select(FlowInstanceDB).where(FlowInstanceDB.id == instance_id)
            ).first()

            if not instance_db:
                raise KeyError("Not found")

            instance_db.status = status.value
            session.add(instance_db)
            session.commit()
            session.refresh(instance_db)
            logger.info(f"Updated flow instance {instance_id} status to {status.value}")
            return FlowInstanceService._to_model(instance_db)

    @staticmethod
    def get(instance_id: UUID) -> FlowInstanceModel:
        with get_session() as session:
            instance_db = session.exec(
                select(FlowInstanceDB).where(FlowInstanceDB.id == instance_id)
            ).first()

            if not instance_db:
                raise KeyError("Not found")

            return FlowInstanceService._to_model(instance_db)

    @staticmethod
    def list_(filter: FlowInstanceListFilter) -> Page[FlowInstanceModel]:
        with get_session() as session:
            q = select(FlowInstanceDB)
            if filter:
                if filter.flow_id is not None:
                    q = q.where(FlowInstanceDB.flow_id == filter.flow_id)
                if filter.status is not None:
                    q = q.where(FlowInstanceDB.status == filter.status.value)

            # Get total count before pagination
            count_q = select(func.count()).select_from(q.subquery())
            total = session.exec(count_q).one()

            # Apply ordering
            if filter and filter.order == FlowInstanceOrder.CREATED_AT_ASC:
                q = q.order_by(FlowInstanceDB.created_at.asc())
            else:
                q = q.order_by(FlowInstanceDB.created_at.desc())

            # Apply pagination
            if filter:
                if filter.offset is not None:
                    q = q.offset(filter.offset)
                if filter.limit is not None:
                    q = q.limit(apply_page_limit(filter.limit))
            rows = session.exec(q).all()
            items = [FlowInstanceService._to_model(row) for row in rows]

            return Page(
                items=items,
                total=total,
                limit=filter.limit if filter else None,
                offset=filter.offset if filter else None,
            )


class FlowInstanceRunner:
    """Pipeline-based flow runner that executes nodes sequentially.

    Nodes can be Getter, Processer, or Pusher in any order.
    Data flows through content_list which is modified by each node type:
    - Getter: appends new content to content_list
    - Processer: processes each item in content_list and replaces
    - Pusher: pushes each item in content_list and clears it
    """

    ATTEMPT_COUNT = 3

    def __init__(self, flow_id: UUID, include_nodes: list[UUID] | None = None):
        self.flow_id = flow_id
        self.include_nodes = (
            set(str(n) for n in include_nodes) if include_nodes is not None else None
        )

        with get_session() as session:
            flow_db = session.exec(select(FlowDB).where(FlowDB.id == flow_id)).first()
            if not flow_db:
                raise ValueError(f"Flow not found: {flow_id}")
            if not flow_db.nodes:
                raise ValueError(f"Flow has no nodes: {flow_id}")

            # Filter to only included nodes (None = include all)
            all_nodes = list(flow_db.nodes or [])
            if self.include_nodes is not None:
                self.flow_nodes = [n for n in all_nodes if n in self.include_nodes]
            else:
                self.flow_nodes = all_nodes

            if self.include_nodes is not None:
                logger.info(
                    f"Flow {flow_id} executing with {len(self.include_nodes)} included nodes"
                )

        self.id = uuid.uuid4()
        self.flow_instance_id: UUID | None = None
        self.current_processing_adapter_inst: str | None = None
        self._thread: threading.Thread | None = None

    def _issue_warning(self, warning_text: str):
        WarningService.issue(Struct(content=[StructText(text=warning_text)]))

    def _execute_getter(self, getter: Getter) -> list[Struct]:
        """Execute Getter: timeline → filter existing → detail(s) → create messages → return content list."""
        getter_full_name = f"{getter.adapter_name}.{getter.identifier}"
        result: list[Struct] = []

        # Get timeline with continuous failure tracking
        try:
            newest_list = getter.timeline()
        except Exception as ex:
            self._track_getter_timeline_failure(getter, ex)
            raise

        # Reset failure counter on success
        key = (getter.adapter_name, getter.identifier)
        getter_get_timeline_continuous_failed_times[key] = 0

        # Filter out already existing messages
        for message_id in newest_list.copy():
            if MessageService.list(
                MessageListFilter(
                    message_identifier=message_id,
                    getter_name=getter.adapter_name,
                )
            ).items:
                newest_list.remove(message_id)

        if not newest_list:
            logger.debug(f"No new messages for {getter_full_name}")
            return result

        logger.info(f"New messages for {getter_full_name}: {newest_list}")

        if ConfigService("system", SystemConfig).get().policy.perf_merged_details:
            # Try batch details() first
            try:
                detail = getter.details(newest_list)
                for message_id in newest_list:
                    content = self._create_and_save_message(getter, detail, message_id)
                result.append(content)  # details() only appends one Struct
                return result
            except NotImplementedError:
                pass
            except Exception as e:
                logger.warning(
                    f"Getter {getter_full_name} details() failed, falling back to detail(): {e}"
                )

        # Fall back to individual detail() calls using thread pool for concurrency
        def fetch_detail_with_retry(message_id: str) -> Struct | None:
            """Fetch detail for a single message with retry logic."""
            for attempt in range(1, self.ATTEMPT_COUNT + 1):
                try:
                    detail = getter.detail(message_id)
                    content = self._create_and_save_message(getter, detail, message_id)
                    return content
                except Exception as e:
                    if attempt == self.ATTEMPT_COUNT:
                        warning_text = (
                            f"Getter '{getter_full_name}' failed to fetch details for "
                            f"identifier {message_id} after {self.ATTEMPT_COUNT} attempts."
                        )
                        self._issue_warning(warning_text)
                        logger.error(f"Failed to get detail for {message_id}: {e}")
                    else:
                        logger.warning(f"Getter detail() attempt {attempt} failed: {e}")
            return None

        # Use thread pool with max 5 workers for concurrent detail fetching
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(fetch_detail_with_retry, msg_id): msg_id
                for msg_id in newest_list
            }
            for future in as_completed(futures):
                content = future.result()
                if content is not None:
                    result.append(content)

        return result

    def _create_and_save_message(
        self, getter: Getter, detail: Detail, message_identifier: str
    ) -> Struct:
        """Create message content from detail and save to database."""
        message_content = MessageService.Template.v1(detail)
        # Process all images through ImageService
        self._process_struct_images(message_content)
        MessageService.create(
            MessageCreate(
                message_identifier=message_identifier,
                getter_name=getter.adapter_name,
                ts=detail.ts,
                content=message_content,
            )
        )
        return message_content

    def _process_struct_images(self, struct: Struct) -> None:
        """Process all StructImage items in a Struct, replacing their source with ImageService URLs."""
        if not struct or not struct.content:
            return
        for item in struct.content:
            if isinstance(item, StructImage) and item.source:
                item.source = ImageService.create(item.source)

    def _track_getter_timeline_failure(self, getter: Getter, ex: Exception):
        """Track consecutive timeline failures and issue warnings at thresholds."""
        key = (getter.adapter_name, getter.identifier)
        if key not in getter_get_timeline_continuous_failed_times:
            getter_get_timeline_continuous_failed_times[key] = 0
        getter_get_timeline_continuous_failed_times[key] += 1

        warning_attempt_count = (
            ConfigService("system", SystemConfig).get().policy.attempt.getter_timeline
        )
        attempt_count = getter_get_timeline_continuous_failed_times[key]

        if attempt_count in warning_attempt_count:
            getter_full_name = f"{getter.adapter_name}.{getter.identifier}"
            warning_text = (
                f"Getter '{getter_full_name}' failed to fetch timeline as its "
                f"consecutive failures exceeded {attempt_count} times. "
                f"Latest exception: {str(ex)}"
            )
            self._issue_warning(warning_text)

        logger.warning(
            f"Failed to get timeline for {getter.adapter_name}.{getter.identifier}: {ex}"
        )

    def _execute_processer(
        self, processer: Processer, content_list: list[Struct]
    ) -> list[Struct]:
        """Process each item in content_list and return processed list."""
        processer_full_name = f"{processer.adapter_name}.{processer.identifier}"
        result: list[Struct] = []

        for content in content_list:
            for attempt in range(1, self.ATTEMPT_COUNT + 1):
                try:
                    logger.debug(
                        f"Processing with {processer_full_name} (attempt {attempt}/{self.ATTEMPT_COUNT})"
                    )
                    processed = processer.process(content.model_copy(deep=True))
                    result.append(processed)
                    logger.debug(f"Successfully processed with {processer_full_name}")
                    break
                except TerminateFlowException:
                    # TerminateFlowException signals skipping this specific content
                    logger.info(
                        f"Processer {processer_full_name} raised TerminateFlowException, "
                        f"skipping current content"
                    )
                    break
                except Exception as e:
                    if attempt == self.ATTEMPT_COUNT:
                        warning_text = (
                            f"Processer '{processer_full_name}' failed to process message "
                            f"after {self.ATTEMPT_COUNT} attempts. Error: {str(e)}"
                        )
                        self._issue_warning(warning_text)
                        raise
                    else:
                        logger.warning(f"Processer attempt {attempt} failed: {e}")

        return result

    def _execute_pusher(self, pusher: Pusher, content_list: list[Struct]) -> None:
        """Push each item in content_list."""
        pusher_full_name = f"{pusher.adapter_name}.{pusher.identifier}"

        for content in content_list:
            for attempt in range(1, self.ATTEMPT_COUNT + 1):
                try:
                    logger.debug(
                        f"Pushing with {pusher_full_name} (attempt {attempt}/{self.ATTEMPT_COUNT})"
                    )
                    pusher.push(content.model_copy(deep=True))
                    logger.info(f"Successfully pushed to {pusher_full_name}")
                    break
                except Exception as e:
                    if attempt == self.ATTEMPT_COUNT:
                        warning_text = (
                            f"Pusher '{pusher_full_name}' failed to push message "
                            f"after {self.ATTEMPT_COUNT} attempts. Error: {str(e)}"
                        )
                        self._issue_warning(warning_text)
                        logger.error(
                            f"Pusher {pusher_full_name} failed, skipping to next message: {e}"
                        )
                        break  # Skip to next message instead of raising
                    else:
                        logger.warning(f"Pusher attempt {attempt} failed: {e}")

    def _refresh_worker(self) -> None:
        """Main pipeline worker: iterates through nodes and executes each."""
        logger.debug(f"Starting refresh for flow: {self.flow_id}")

        # Create FlowInstance record
        try:
            instance = FlowInstanceService.create(flow_id=self.flow_id)
            flow_instance_id = instance.id
            self.flow_instance_id = flow_instance_id
        except Exception as e:
            logger.error(f"Failed to create flow instance for flow {self.flow_id}: {e}")
            return

        # Initialize content_list for pipeline data flow
        content_list: list[Struct] = []

        # Update status to RUNNING
        try:
            FlowInstanceService.update_status(
                flow_instance_id, FlowInstanceStatus.RUNNING
            )
        except Exception as e:
            logger.warning(
                f"Failed to update flow instance {flow_instance_id} to running: {e}"
            )

        def _failed(adapter_instance_id, e):
            logger.error(f"Failed to process node {adapter_instance_id}: {e}")
            self._issue_warning(
                f"Flow {self.flow_id} failed at node {adapter_instance_id}: {str(e)}"
            )
            try:
                FlowInstanceService.update_status(
                    flow_instance_id, FlowInstanceStatus.FAILED
                )
            except Exception:
                pass

        # Execute each node in order
        for adapter_instance_id in self.flow_nodes:
            try:
                node_obj = AdapterInstanceService.get_object_by_id(
                    UUID(adapter_instance_id)
                )
            except Exception as e:
                _failed(adapter_instance_id, e)
                return

            try:
                self.current_processing_adapter_inst = (
                    f"{node_obj.adapter_name}.{node_obj.identifier}"
                )

                if isinstance(node_obj, Getter):
                    new_contents = self._execute_getter(node_obj)
                    content_list.extend(new_contents)
                    logger.info(
                        f"Getter {node_obj.adapter_name}.{node_obj.identifier} "
                        f"added {len(new_contents)} items, total: {len(content_list)}"
                    )

                elif isinstance(node_obj, Processer):
                    content_list = self._execute_processer(node_obj, content_list)
                    logger.info(
                        f"Processer {node_obj.adapter_name}.{node_obj.identifier} "
                        f"processed {len(content_list)} items"
                    )

                elif isinstance(node_obj, Pusher):
                    self._execute_pusher(node_obj, content_list)
                    logger.info(
                        f"Pusher {node_obj.adapter_name}.{node_obj.identifier} "
                        f"pushed {len(content_list)} items, clearing content_list"
                    )
                    content_list.clear()

                else:
                    logger.warning(
                        f"Unknown node type for {adapter_instance_id}: {type(node_obj)}"
                    )

            except Exception as e:
                # Check if the failing node is a Getter - if so, continue with other nodes
                if isinstance(node_obj, Getter):
                    logger.warning(
                        f"Getter {adapter_instance_id} failed, continuing with next node: {e}"
                    )
                    continue

                # For non-Getter nodes (or if we can't determine type), fail the flow
                _failed(adapter_instance_id, e)
                return

        # Update final status
        try:
            FlowInstanceService.update_status(
                flow_instance_id, FlowInstanceStatus.COMPLETED
            )
        except Exception as e:
            logger.warning(
                f"Failed to update flow instance {flow_instance_id} to {FlowInstanceStatus.COMPLETED}: {e}"
            )

        logger.debug(f"Completed refresh for flow: {self.flow_id}")

    def do(self):
        self._thread = threading.Thread(target=self._refresh_worker)
        self._thread.start()


class CronService:
    _scheduler = BackgroundScheduler(
        executors={
            "default": {"type": "threadpool", "max_workers": CRON_SCHEDULER_MAX_WORKERS}
        }
    )
    _lock = threading.Lock()

    @staticmethod
    def _parse_cron_to_trigger(expr: str) -> CronTrigger:
        expr = expr.strip()
        parts = expr.split()

        if len(parts) == 5:
            minute, hour, day, month, day_of_week = parts
            return CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
            )

        elif len(parts) == 6:
            second, minute, hour, day, month, day_of_week = parts
            return CronTrigger(
                second=second,
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
            )

        elif len(parts) == 7:
            second, minute, hour, day, month, day_of_week, year = parts
            return CronTrigger(
                second=second,
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                year=year,
            )

        else:
            raise ValueError(f"Invalid cron expression: '{expr}'")

    @staticmethod
    def _job_id(flow_id: UUID, cron_expr: str) -> str:
        return str(flow_id) + cron_expr

    @staticmethod
    def _load_all_from_db() -> List[Tuple[UUID, UUID, str, bool]]:
        with get_session() as session:
            rows = session.exec(select(FlowCronDB)).all()
            result: List[Tuple[UUID, UUID, str, bool]] = []
            for c in rows:
                result.append((c.id, c.flow_id, c.cron, c.enabled))
            return result

    @classmethod
    def _reload(cls):
        with cls._lock:
            logger.info("CronService reloading scheduler...")

            db_crons = cls._load_all_from_db()
            # Only schedule enabled crons
            enabled_crons = [
                (cron_id, flow_id, cron_expr)
                for cron_id, flow_id, cron_expr, enabled in db_crons
                if enabled
            ]
            db_ids = {
                cls._job_id(flow_id, cron_expr)
                for cron_id, flow_id, cron_expr in enabled_crons
            }

            job_ids = {job.id for job in cls._scheduler.get_jobs()}

            to_add = db_ids - job_ids
            to_remove = job_ids - db_ids

            cron_map = {
                cls._job_id(flow_id, cron_expr): (cron_id, flow_id, cron_expr)
                for cron_id, flow_id, cron_expr in enabled_crons
            }

            for job_id in to_add:
                cron_id, flow_id, cron = cron_map[job_id]
                cls._scheduler.add_job(
                    func=lambda flow_id=flow_id: FlowInstanceRunner(flow_id).do(),
                    trigger=CronService._parse_cron_to_trigger(cron),
                    id=job_id,
                    replace_existing=True,
                )
                logger.info(f"Added {job_id}")

            for job_id in to_remove:
                try:
                    cls._scheduler.remove_job(job_id)
                    logger.info(f"Removed {job_id}")
                except Exception:
                    logger.warning(f"Job {job_id} does not exist")

    @classmethod
    def init(cls):
        cls._reload()
        if not cls._scheduler.running:
            cls._scheduler.start()

    @classmethod
    def create(cls, cron_create: CronCreate) -> Cron:
        with get_session() as session:
            flow_db = session.exec(
                select(FlowDB).where(FlowDB.id == cron_create.flow_id)
            ).first()
            if not flow_db:
                raise ValueError("Flow not found")

            flow_id = flow_db.id

            cron_db = FlowCronDB(
                flow_id=flow_id,
                cron=cron_create.cron,
                enabled=cron_create.enabled,
            )
            session.add(cron_db)
            session.commit()
            session.refresh(cron_db)

        cls._reload()
        logger.info(
            f"Created cron: {cron_db.id} for flow {flow_id} with schedule '{cron_create.cron}' enabled={cron_db.enabled}"
        )

        return Cron(
            id=cron_db.id,
            flow_id=flow_id,
            cron=cron_db.cron,
            enabled=cron_db.enabled,
        )

    @classmethod
    def update(cls, cron_id: UUID, cron_update: CronUpdate) -> Cron:
        with get_session() as session:
            cron_record = session.exec(
                select(FlowCronDB).where(FlowCronDB.id == cron_id)
            ).first()

            if not cron_record:
                raise ValueError("Not found")

            if cron_update.cron is not None:
                cron_record.cron = cron_update.cron
            if cron_update.enabled is not None:
                cron_record.enabled = cron_update.enabled

            session.add(cron_record)
            session.commit()
            session.refresh(cron_record)

        cls._reload()
        logger.info(
            f"Updated cron: {cron_id} cron='{cron_record.cron}' enabled={cron_record.enabled}"
        )

        return Cron(
            id=cron_record.id,
            flow_id=cron_record.flow_id,
            cron=cron_record.cron,
            enabled=cron_record.enabled,
        )

    @staticmethod
    def list(filter: CronListFilter) -> Page[Cron]:
        with get_session() as session:
            q = select(FlowCronDB)
            if filter:
                if filter.flow_id is not None:
                    q = q.where(FlowCronDB.flow_id == filter.flow_id)
                if filter.cron is not None:
                    q = q.where(FlowCronDB.cron == filter.cron)
                if filter.enabled is not None:
                    q = q.where(FlowCronDB.enabled == filter.enabled)

            # Get total count before pagination
            count_q = select(func.count()).select_from(q.subquery())
            total = session.exec(count_q).one()

            q = q.order_by(FlowCronDB.id)
            if filter and filter.offset is not None:
                q = q.offset(filter.offset)
            if filter and filter.limit is not None:
                q = q.limit(apply_page_limit(filter.limit))
            rows = session.exec(q).all()
            items: list[Cron] = []
            for c in rows:
                items.append(
                    Cron(
                        id=c.id,
                        flow_id=c.flow_id,
                        cron=c.cron,
                        enabled=c.enabled,
                    )
                )

            return Page(
                items=items,
                total=total,
                limit=filter.limit if filter else None,
                offset=filter.offset if filter else None,
            )

    @classmethod
    def delete(cls, cron_id: UUID) -> None:
        with get_session() as session:
            cron_record = session.exec(
                select(FlowCronDB).where(FlowCronDB.id == cron_id)
            ).first()

            if not cron_record:
                raise ValueError("Not found")

            session.delete(cron_record)
            session.commit()

        cls._reload()
        logger.info(
            f"Deleted cron: {cron_id} for flow {cron_record.flow_id} with schedule '{cron_record.cron}'"
        )

    @classmethod
    def close(cls):
        with cls._lock:
            if cls._scheduler.running:
                cls._scheduler.shutdown(wait=False)
                logger.info("CronService scheduler shutdown complete")
