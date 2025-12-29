"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Lifespan management utilities for MCP Proxy Adapter API.
"""

import asyncio
import signal
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from fastapi import FastAPI

from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.core.path_utils import (
    ensure_application_path,
    ensure_registered_modules_paths,
)
from .registration_manager import RegistrationManager, set_stop_flag_sync


class LifespanManager:
    """Manager for application lifespan events."""

    def __init__(self):
        """Initialize lifespan manager."""
        self.logger = get_global_logger()
        self.registration_manager = RegistrationManager()

    def create_lifespan(
        self,
        config_path: Optional[str] = None,
        current_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Create lifespan manager for the FastAPI application.

        Args:
            config_path: Path to configuration file (optional)
            current_config: Current configuration data (optional)

        Returns:
            Lifespan context manager
        """

        def signal_handler(signum, frame):  # type: ignore[no-redef]
            """Handle interrupt signals (SIGINT, SIGTERM) by setting stop flag."""
            logger = get_global_logger()
            logger.info(f"🛑 Received signal {signum}, setting stop flag...")
            set_stop_flag_sync(True)

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Lifespan context manager."""
            # Startup
            logger = get_global_logger()
            try:
                logger.info("=" * 80)
                logger.info("🚀 LIFESPAN STARTUP CALLED")
                logger.info("=" * 80)
                logger.info("Starting MCP Proxy Adapter")

                # CRITICAL: Ensure application path is in PYTHONPATH for spawn mode
                # This ensures that custom modules are importable in child processes
                try:
                    added_paths = ensure_application_path(config_path)
                    if added_paths:
                        logger.info(
                            f"✅ Added application paths to PYTHONPATH for spawn mode: {added_paths}"
                        )

                    # Also ensure registered modules' paths are available
                    registered_paths = ensure_registered_modules_paths()
                    if registered_paths:
                        logger.info(
                            f"✅ Added registered module paths to PYTHONPATH: {registered_paths}"
                        )
                except Exception as path_error:
                    logger.warning(
                        f"⚠️ Failed to ensure application paths for spawn mode: {path_error}"
                    )

                logger.info(
                    f"🔍 lifespan function: current_config parameter value: {current_config}"
                )
                logger.info(
                    f"🔍 lifespan function: current_config is None: {current_config is None}"
                )

                # Start heartbeat task only if registration is enabled
                # Check if registration is enabled before calling start_heartbeat
                logger = get_global_logger()
                logger.info(
                    f"🔍 Lifespan: current_config is {'None' if current_config is None else 'not None'}"
                )
                if current_config:
                    logger.info(
                        f"🔍 Lifespan: current_config type: {type(current_config)}"
                    )
                    logger.info(
                        f"🔍 Lifespan: current_config keys: {list(current_config.keys()) if hasattr(current_config, 'keys') else 'no keys'}"
                    )
                    if hasattr(current_config, "keys"):
                        logger.info(
                            f"🔍 Lifespan: current_config['registration'] exists: {'registration' in current_config}"
                        )
                        if "registration" in current_config:
                            reg_section = current_config.get("registration")
                            logger.info(
                                f"🔍 Lifespan: registration section type: {type(reg_section)}"
                            )
                            logger.info(
                                f"🔍 Lifespan: registration section: {reg_section}"
                            )

                    registration_enabled = False
                    # Check SimpleConfigModel first
                    try:
                        from mcp_proxy_adapter.config import get_config

                        cfg = get_config()
                        logger.info(f"🔍 SimpleConfigModel: cfg type: {type(cfg)}")
                        logger.info(
                            f"🔍 SimpleConfigModel: hasattr(cfg, 'model'): {hasattr(cfg, 'model')}"
                        )
                        if hasattr(cfg, "model"):
                            logger.info(
                                f"🔍 SimpleConfigModel: cfg.model type: {type(cfg.model)}"
                            )
                            logger.info(
                                f"🔍 SimpleConfigModel: hasattr(cfg.model, 'registration'): {hasattr(cfg.model, 'registration')}"
                            )
                            if hasattr(cfg.model, "registration"):
                                reg_model = cfg.model.registration
                                logger.info(
                                    f"🔍 SimpleConfigModel: reg_model type: {type(reg_model)}"
                                )
                                logger.info(
                                    f"🔍 SimpleConfigModel: reg_model.enabled: {reg_model.enabled}, reg_model.auto_on_startup: {reg_model.auto_on_startup}"
                                )
                                registration_enabled = (
                                    reg_model.enabled and reg_model.auto_on_startup
                                )
                                logger.info(
                                    f"🔍 Registration enabled check (SimpleConfigModel): {registration_enabled}"
                                )
                    except Exception as e:
                        logger.info(f"🔍 SimpleConfigModel check failed: {e}")
                        import traceback

                        logger.info(
                            f"🔍 SimpleConfigModel check traceback: {traceback.format_exc()}"
                        )

                    # Check registration section
                    if not registration_enabled:
                        registration_config = current_config.get("registration") or {}
                        if registration_config:
                            reg_enabled = registration_config.get("enabled", False)
                            reg_auto_startup = registration_config.get(
                                "auto_on_startup", True
                            )
                            registration_enabled = reg_enabled and reg_auto_startup

                    logger.info(
                        f"🔍 FINAL registration_enabled: {registration_enabled}"
                    )
                    if registration_enabled:
                        logger.info("✅ Registration enabled, starting heartbeat task")
                        try:
                            await self.registration_manager.start_heartbeat(
                                current_config
                            )
                        except Exception as e:
                            logger.error(
                                f"❌ Failed to start heartbeat task: {e}", exc_info=True
                            )
                            # Don't fail startup if heartbeat fails - server should still work
                    else:
                        logger.info(
                            "⚠️ Registration is disabled, skipping heartbeat task"
                        )
                else:
                    logger.info("⚠️ current_config is None, skipping heartbeat task")

                # Initialize queue manager if queuemgr is available
                try:
                    from mcp_proxy_adapter.integrations.queuemgr_integration import (
                        init_global_queue_manager,
                    )

                    # Read queue manager config from current_config or global config
                    queue_config = None
                    if current_config and "queue_manager" in current_config:
                        queue_config = current_config.get("queue_manager", {})
                    else:
                        # Try to get from global config
                        try:
                            from mcp_proxy_adapter.config import get_config

                            cfg = get_config()
                            if hasattr(cfg, "model") and hasattr(
                                cfg.model, "queue_manager"
                            ):
                                queue_config = {
                                    "enabled": cfg.model.queue_manager.enabled,
                                    "in_memory": cfg.model.queue_manager.in_memory,
                                    "registry_path": cfg.model.queue_manager.registry_path,
                                    "shutdown_timeout": cfg.model.queue_manager.shutdown_timeout,
                                    "max_concurrent_jobs": cfg.model.queue_manager.max_concurrent_jobs,
                                    "max_queue_size": cfg.model.queue_manager.max_queue_size,
                                    "per_job_type_limits": cfg.model.queue_manager.per_job_type_limits,
                                    "completed_job_retention_seconds": cfg.model.queue_manager.completed_job_retention_seconds,
                                }
                        except Exception as e:
                            logger.debug(
                                f"Could not read queue config from global config: {e}"
                            )

                    # Use defaults if config not found
                    if queue_config is None:
                        queue_config = {}

                    # Only initialize if enabled (default: True)
                    if queue_config.get("enabled", True):
                        await init_global_queue_manager(
                            registry_path=queue_config.get("registry_path"),
                            shutdown_timeout=queue_config.get("shutdown_timeout", 30.0),
                            max_concurrent_jobs=queue_config.get(
                                "max_concurrent_jobs", 10
                            ),
                            in_memory=queue_config.get("in_memory", True),
                            max_queue_size=queue_config.get("max_queue_size"),
                            per_job_type_limits=queue_config.get("per_job_type_limits"),
                            completed_job_retention_seconds=queue_config.get(
                                "completed_job_retention_seconds", 21600
                            ),
                        )
                        logger.info("✅ Queue manager initialized")
                    else:
                        logger.info("⚠️ Queue manager is disabled in configuration")
                except ImportError:
                    logger.debug("Queue manager not available (queuemgr not installed)")
                except Exception as e:
                    logger.warning(f"⚠️ Queue manager initialization failed: {e}")
                    # Don't fail startup if queue manager fails - server should still work
            except Exception as e:
                logger.error(f"❌ Lifespan startup failed: {e}", exc_info=True)
                # Don't fail startup - let the server start anyway
                # The error is logged, but the server should still be able to handle requests

            yield

            # Shutdown
            get_global_logger().info("Shutting down MCP Proxy Adapter")
            await self.registration_manager.stop()

            # Shutdown queue manager if initialized
            try:
                from mcp_proxy_adapter.integrations.queuemgr_integration import (
                    shutdown_global_queue_manager,
                )

                await shutdown_global_queue_manager()
                get_global_logger().info("✅ Queue manager stopped")
            except ImportError:
                pass  # Queue manager not available
            except Exception as e:
                get_global_logger().warning(f"⚠️ Queue manager shutdown failed: {e}")

        return lifespan
