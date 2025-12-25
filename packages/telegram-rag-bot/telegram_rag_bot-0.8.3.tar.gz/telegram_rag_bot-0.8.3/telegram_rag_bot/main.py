"""
Main entry point for Telegram bot with Multi-LLM-Orchestrator integration.

This module initializes all components (Router, RAG chains, session manager, 
handlers) and runs the Telegram bot application.
"""

import asyncio
import logging
import signal
from typing import Dict, Any

from aiohttp import web
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from prometheus_client import generate_latest

from telegram_rag_bot.config_loader import ConfigLoader
from telegram_rag_bot.langchain_adapter.rag_chains import RAGChainFactory
from telegram_rag_bot.utils.session_manager import SessionManager
from telegram_rag_bot.handlers import TelegramHandlers

from orchestrator import Router
from orchestrator.providers import GigaChatProvider, YandexGPTProvider, ProviderConfig
from orchestrator.langchain import MultiLLMOrchestrator

logger = logging.getLogger(__name__)


def setup_logging(config: Dict[str, Any]) -> None:
    """
    Setup structured logging from configuration.
    
    Configures root logger with format and level from config.yaml.
    Supports both JSON (production) and text (development) formats.
    
    Args:
        config: Full configuration dictionary from ConfigLoader
    """
    from telegram_rag_bot.utils.logger import setup_structured_logging
    
    log_config = config.get("logging", {})
    log_format = log_config.get("format", "text")
    log_level_str = log_config.get("level", "INFO").upper()
    
    # Safe conversion: getattr(logging, "INFO", logging.INFO)
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    setup_structured_logging(log_format=log_format, level=log_level)


def create_router(orchestrator_config: Dict[str, Any]) -> Router:
    """
    Create and configure Multi-LLM-Orchestrator Router.
    
    Args:
        orchestrator_config: Configuration dict with strategy and providers.
    
    Returns:
        Configured Router instance with enabled providers.
    
    Raises:
        ValueError: If no enabled providers are configured.
    """
    router = Router(strategy=orchestrator_config["strategy"])
    
    for provider_cfg in orchestrator_config["providers"]:
        # Skip disabled providers
        if not provider_cfg.get("enabled", True):
            logger.info(f"Skipping disabled provider: {provider_cfg['name']}")
            continue
        
        # Create GigaChat provider
        if provider_cfg["type"] == "GigaChatProvider":
            config = ProviderConfig(
                name=provider_cfg["name"],
                api_key=provider_cfg["config"]["api_key"],
                model=provider_cfg["config"]["model"],
                scope=provider_cfg["config"]["scope"]
            )
            router.add_provider(GigaChatProvider(config))
            logger.info(f"Added provider: {provider_cfg['name']} (GigaChat)")
        
        # Create YandexGPT provider
        elif provider_cfg["type"] == "YandexGPTProvider":
            config = ProviderConfig(
                name=provider_cfg["name"],
                api_key=provider_cfg["config"]["api_key"],
                folder_id=provider_cfg["config"]["folder_id"],
                model=provider_cfg["config"]["model"]
            )
            router.add_provider(YandexGPTProvider(config))
            logger.info(f"Added provider: {provider_cfg['name']} (YandexGPT)")
    
    # Bug #3: router.providers всегда список (не генератор) в Multi-LLM-Orchestrator v0.7.0
    # Ensure at least one provider is enabled
    provider_count = len(router.providers)
    
    if provider_count == 0:
        raise ValueError("No enabled providers configured in config.yaml")
    
    return router


async def health_handler(request: web.Request) -> web.Response:
    """
    Health check endpoint for Docker/Kubernetes.
    
    Checks:
    - Telegram bot application.running
    - Redis connection (if used)
    - Embeddings provider initialized
    - VectorStore provider initialized
    
    Returns:
        HTTP 200 if all checks pass, HTTP 503 if any check fails.
    """
    app = request.app
    application = app.get('application')
    session_manager = app.get('session_manager')
    rag_factory = app.get('rag_factory')
    
    checks = {}
    all_healthy = True
    
    # Check Telegram bot
    telegram_running = application.running if application else False
    checks['telegram'] = {
        'status': 'ok' if telegram_running else 'unhealthy',
        'running': telegram_running
    }
    if not telegram_running:
        all_healthy = False
    
    # Check Redis (only if using Redis mode)
    # Critical: Health check должен проверять только наличие клиента, НЕ делать реальный ping
    # Реальный ping может быть медленным (>100ms) и блокировать health check
    redis_healthy = True  # Default: healthy (memory mode)
    if hasattr(session_manager, 'use_redis'):
        if session_manager.use_redis:
            # Redis mode: проверить наличие клиента
            redis_healthy = session_manager.redis_client is not None
        # Else: memory mode — всегда healthy
    
    checks['redis'] = {
        'status': 'ok' if redis_healthy else 'unhealthy',
        'mode': 'redis' if hasattr(session_manager, 'use_redis') and session_manager.use_redis else 'memory'
    }
    if not redis_healthy:
        all_healthy = False
    
    # Check Embeddings provider
    embeddings_initialized = rag_factory.embeddings_provider is not None if rag_factory else False
    checks['embeddings'] = {
        'status': 'ok' if embeddings_initialized else 'unhealthy',
        'initialized': embeddings_initialized
    }
    if not embeddings_initialized:
        all_healthy = False
    
    # Check VectorStore provider
    vectorstore_initialized = rag_factory.vectorstore_provider is not None if rag_factory else False
    checks['vectorstore'] = {
        'status': 'ok' if vectorstore_initialized else 'unhealthy',
        'initialized': vectorstore_initialized
    }
    if not vectorstore_initialized:
        all_healthy = False
    
    status_code = 200 if all_healthy else 503
    response_data = {
        'status': 'ok' if all_healthy else 'unhealthy',
        'checks': checks
    }
    
    return web.json_response(response_data, status=status_code)


async def metrics_handler(request: web.Request) -> web.Response:
    """
    Prometheus metrics endpoint.
    
    Returns:
        HTTP 200 with Prometheus metrics in text/plain format.
    """
    metrics_data = generate_latest()
    return web.Response(body=metrics_data, content_type="text/plain")


async def update_active_users_metric(session_manager: SessionManager) -> None:
    """
    Background task to update ACTIVE_USERS metric periodically.
    
    Updates Prometheus gauge every 60 seconds with current active user count.
    
    Args:
        session_manager: SessionManager instance for getting active users count
    """
    from telegram_rag_bot.utils.metrics import ACTIVE_USERS
    
    while True:
        try:
            active_count = session_manager.get_active_users_count()
            ACTIVE_USERS.set(active_count)
            await asyncio.sleep(60)  # Update every 60 seconds
        except asyncio.CancelledError:
            logger.info("Background metrics task cancelled")
            break
        except Exception as e:
            logger.warning(f"Error updating active users metric: {e}")
            await asyncio.sleep(60)


async def main() -> None:
    """
    Main entry point for Telegram bot.
    
    Initializes all components in the correct order:
    1. ConfigLoader - Load config.yaml
    2. Router - Create Multi-LLM-Orchestrator with providers
    3. MultiLLMOrchestrator - LangChain LLM wrapper
    4. RAGChainFactory - Initialize RAG chains
    5. SessionManager - Redis/in-memory sessions
    6. TelegramHandlers - Bot command/message handlers
    7. Application - Telegram bot application
    8. Run - Start polling and idle loop
    
    Raises:
        Exception: Any fatal error during initialization or runtime.
    """
    # Initialize basic logging first (before config load)
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )
    logger.info("Starting Telegram bot...")
    
    application = None  # Initialize for finally block
    
    try:
        # 1. Load config
        config = ConfigLoader.load_config("config/config.yaml")
        logger.info("✅ Config loaded successfully")
        
        # 1.5. Setup structured logging from config
        setup_logging(config)
        
        # Bug #2: Validate critical environment variables
        telegram_token = config["telegram"]["token"]
        if not telegram_token or telegram_token.startswith("${"):
            logger.error("TELEGRAM_TOKEN environment variable not set")
            logger.error("Create .env file with: TELEGRAM_TOKEN=your_token_here")
            raise SystemExit(1)
        
        # Validate at least one provider has valid API key
        has_valid_provider = False
        for provider_cfg in config["orchestrator"]["providers"]:
            if not provider_cfg.get("enabled", True):
                continue
            api_key = provider_cfg["config"].get("api_key", "")
            if api_key and not api_key.startswith("${"):
                has_valid_provider = True
                break
        
        if not has_valid_provider:
            logger.error("No enabled provider has valid API key set")
            logger.error("Set environment variables: GIGACHAT_KEY, YANDEX_API_KEY")
            raise SystemExit(1)
        
        # Bug #2: Validate embeddings/vectorstore environment variables
        # Validate embeddings config (if using cloud providers)
        if config["embeddings"]["type"] == "gigachat":
            gigachat_api_key = config["embeddings"]["gigachat"].get("api_key", "")
            if not gigachat_api_key or gigachat_api_key.startswith("${"):
                logger.error("GIGACHAT_EMBEDDINGS_KEY not set (required for gigachat embeddings)")
                logger.error("Set environment variable: GIGACHAT_EMBEDDINGS_KEY=your_key_here")
                raise SystemExit(1)
        
        # Validate vectorstore config (if using OpenSearch)
        if config["vectorstore"]["type"] == "opensearch":
            opensearch_host = config["vectorstore"]["opensearch"].get("host", "")
            if not opensearch_host or opensearch_host.startswith("${"):
                logger.error("OPENSEARCH_HOST not set (required for opensearch vectorstore)")
                logger.error("Set environment variable: OPENSEARCH_HOST=your_host_here")
                raise SystemExit(1)
        
        # 2. Create Router with providers
        router = create_router(config["orchestrator"])
        provider_count = len(router.providers)
        logger.info(f"✅ Router created with {provider_count} providers")
        
        # 3. Create LangChain LLM
        llm = MultiLLMOrchestrator(router=router)
        logger.info("✅ LangChain LLM created (MultiLLMOrchestrator)")
        
        # 4. Create RAG factory
        rag_factory = RAGChainFactory(
            llm=llm,
            embeddings_config=config["embeddings"],
            vectorstore_config=config["vectorstore"],
            chunk_config=config["langchain"],
            modes=config["modes"]
        )
        logger.info("✅ RAG factory initialized")
        
        # 5. Create session manager
        session_manager = SessionManager(
            redis_url=config["storage"]["sessions"].get("url"),
            ttl_seconds=config["storage"]["sessions"]["ttl_seconds"]
        )
        logger.info("✅ Session manager initialized")
        
        # 5.5. Start background task for metrics
        metrics_task = asyncio.create_task(
            update_active_users_metric(session_manager)
        )
        logger.info("✅ Background metrics task started")
        
        # 6. Create handlers
        handlers = TelegramHandlers(
            rag_factory=rag_factory,
            session_manager=session_manager,
            config=config
        )
        logger.info("✅ Telegram handlers created")
        
        # 7. Create application
        application = Application.builder().token(config["telegram"]["token"]).build()
        
        # 8. Register handlers
        application.add_handler(CommandHandler("start", handlers.cmd_start))
        application.add_handler(CommandHandler("mode", handlers.cmd_set_mode))
        application.add_handler(CommandHandler("reload_faq", handlers.cmd_reload_faq))
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            handlers.handle_message
        ))
        logger.info("✅ Handlers registered")
        
        # 8.5. Create HTTP server for health check and metrics
        # Critical: HTTP сервер должен запускаться параллельно с Telegram bot (не блокировать)
        app = web.Application()
        app['application'] = application
        app['session_manager'] = session_manager
        app['rag_factory'] = rag_factory
        
        app.router.add_get("/health", health_handler)
        app.router.add_get("/metrics", metrics_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8000)
        await site.start()
        logger.info("✅ Health check server started on port 8000")
        
        # 9. Run
        logger.info("🚀 Starting polling...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        # Setup signal handlers for graceful shutdown in Docker (SIGTERM) and local (SIGINT)
        stop_event = asyncio.Event()

        def signal_handler(signum, frame):
            """Handle SIGTERM/SIGINT signals for graceful shutdown."""
            logger.info(f"Received signal {signum}, initiating shutdown...")
            stop_event.set()

        signal.signal(signal.SIGTERM, signal_handler)  # Docker stop
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C

        logger.info("🚀 Bot is running. Press Ctrl+C to stop.")
        await stop_event.wait()
        logger.info("Stop event triggered, shutting down...")
        
    except ImportError as e:
        logger.error("Multi-LLM-Orchestrator v0.7.0 not installed")
        logger.error("Install with: pip install multi-llm-orchestrator[langchain]==0.7.0")
        raise SystemExit(1) from e
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
    
    finally:
        # Cancel background metrics task
        if 'metrics_task' in locals() and not metrics_task.done():
            metrics_task.cancel()
            try:
                await metrics_task
            except asyncio.CancelledError:
                pass  # Expected
            logger.info("✅ Background metrics task cancelled")
        
        # Close HTTP server (if exists)
        if 'runner' in locals() and runner:
            await runner.cleanup()
            logger.info("✅ HTTP server stopped")
        
        # Close OpenSearch connection (if using OpenSearch)
        if 'rag_factory' in locals() and hasattr(rag_factory, 'vectorstore_provider'):
            vectorstore = rag_factory.vectorstore_provider
            if hasattr(vectorstore, 'close') and callable(vectorstore.close):
                try:
                    await vectorstore.close()
                    logger.info("✅ OpenSearch connection closed")
                except Exception as e:
                    logger.warning(f"Failed to close OpenSearch: {e}")
        
        # Note: Redis connection НЕ закрываем (синхронный клиент закроется автоматически при завершении процесса)
        
        # Shutdown Telegram application (correct order: updater -> application -> shutdown)
        if application:
            logger.info("Shutting down gracefully...")
            
            try:
                # 1. Stop updater first (critical: must be stopped before application.shutdown())
                if application.updater and application.updater.running:
                    await application.updater.stop()
                    logger.info("✅ Telegram updater stopped")
                
                # 2. Stop application
                if application.running:
                    await application.stop()
                    logger.info("✅ Telegram application stopped")
                
                # 3. Shutdown (cleanup resources)
                await application.shutdown()
                logger.info("✅ Telegram application shutdown complete")
            
            except RuntimeError as e:
                # Gracefully handle "still running" errors (shouldn't happen with correct order)
                if "still running" in str(e).lower():
                    logger.warning(f"⚠️ Shutdown warning (non-critical): {e}")
                else:
                    logger.error(f"❌ Unexpected error during shutdown: {e}")
                    raise
            
            logger.info("👋 Shutdown complete. Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())

