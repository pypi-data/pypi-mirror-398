"""
Telegram bot handlers for commands and messages.

Handles:
- /start, /mode, /reload_faq commands
- Text message processing through RAG
- Session management
- Error handling
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction

from telegram_rag_bot.langchain_adapter.rag_chains import RAGChainFactory
from telegram_rag_bot.utils.session_manager import SessionManager
from telegram_rag_bot.utils.metrics import QUERY_LATENCY, ERROR_COUNT

logger = logging.getLogger(__name__)


class TelegramHandlers:
    """
    Telegram bot handlers for commands and messages.
    
    Handles:
    - /start, /mode, /reload_faq commands
    - Text message processing through RAG
    - Session management
    - Error handling
    """
    
    # Constants
    DEFAULT_MODE = "it_support"
    MAX_MESSAGE_LENGTH = 4096
    
    def __init__(
        self,
        rag_factory: RAGChainFactory,
        session_manager: SessionManager,
        config: Dict[str, Any]
    ):
        """
        Initialize handlers.
        
        Args:
            rag_factory: RAGChainFactory instance for creating RAG chains
            session_manager: SessionManager instance for user sessions
            config: Full configuration dictionary from ConfigLoader
        """
        self.rag_factory = rag_factory
        self.session_manager = session_manager
        self.config = config
        
        # Mode display names mapping
        self.mode_display_names = {
            "it_support": "IT Support"
        }
    
    def _is_admin(self, user_id: int) -> bool:
        """
        Check if user is admin.
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            True if user is in admin_ids list
        """
        admin_ids = self.config["telegram"].get("admin_ids", [])
        return user_id in admin_ids
    
    def _escape_markdown_v2(self, text: str) -> str:
        """
        Escape special characters for Telegram MarkdownV2.
        
        Characters to escape: _ * [ ] ( ) ~ ` > # + - = | { } . !
        
        Args:
            text: Text to escape
        
        Returns:
            Escaped text
        """
        escape_chars = '_*[]()~`>#+-=|{}.!'
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    def _get_mode_display(self, mode: str) -> str:
        """
        Get human-readable mode name.
        
        Args:
            mode: Mode key (e.g., "it_support")
        
        Returns:
            Human-readable name (e.g., "IT Support")
        """
        display = self.mode_display_names.get(mode)
        if display is None:
            # Fallback: capitalize snake_case
            display = mode.replace("_", " ").title()
        return display
    
    async def cmd_start(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle /start command.
        
        Shows welcome message and available commands.
        Does NOT create session (created on first message).
        
        Args:
            update: Telegram Update object
            context: Callback context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or "User"
        
        # Critical: Get session with fallback to default if not found or error
        # This ensures bot works even if Redis/SessionManager fails
        try:
            session = await self.session_manager.get_session(user_id)
            if session is None:
                session = {}  # Empty session → will use DEFAULT_MODE
        except Exception as e:
            logger.warning(f"Session manager error in /start: {e}")
            session = {}  # Fallback to empty session (in-memory)
        
        current_mode = session.get("mode", self.DEFAULT_MODE)
        mode_display = self._get_mode_display(current_mode)
        
        # Form welcome message (without markdown - too complex to escape)
        welcome_text = (
            "👋 Привет! Я FAQ бот компании.\n\n"
            "Я помогу ответить на ваши вопросы по IT поддержке.\n\n"
            "📝 Доступные команды:\n"
            "/start — показать это сообщение\n"
            "/mode <режим> — сменить режим работы\n\n"
            f"📌 Текущий режим: {mode_display}\n\n"
            "Задайте мне вопрос!"
        )
        
        # Send message (no parse_mode for commands)
        await update.message.reply_text(welcome_text)
        
        logger.info(f"User {user_id} ({username}) started bot")
    
    async def cmd_set_mode(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle /mode command.
        
        Usage: /mode <mode_name>
        Without argument: shows current mode + available modes
        
        Args:
            update: Telegram Update object
            context: Callback context
        """
        user_id = update.effective_user.id
        
        # Critical: Get session once (used in both branches)
        # This optimizes session loading (not twice)
        try:
            session = await self.session_manager.get_session(user_id)
            if session is None:
                session = {"mode": self.DEFAULT_MODE}
        except Exception as e:
            logger.warning(f"Session error in /mode: {e}")
            session = {"mode": self.DEFAULT_MODE}
        
        current_mode = session.get("mode", self.DEFAULT_MODE)
        
        # No argument → show current + available modes
        if not context.args:
            current_mode_display = self._get_mode_display(current_mode)
            available_modes = ", ".join(self.config["modes"].keys())
            
            await update.message.reply_text(
                f"📌 Текущий режим: {current_mode_display}\n\n"
                f"📋 Доступные режимы: {available_modes}\n\n"
                f"Используйте: /mode <режим>"
            )
            return
        
        # With argument → switch mode
        new_mode = context.args[0].lower().strip()
        
        # Validate mode exists
        if new_mode not in self.config["modes"]:
            available_modes = ", ".join(self.config["modes"].keys())
            await update.message.reply_text(
                f"❌ Неизвестный режим: {new_mode}\n\n"
                f"Доступные режимы: {available_modes}"
            )
            return
        
        # Check if mode changed
        if new_mode == current_mode:
            # Already in this mode → no message
            return
        
        # Update session
        session["mode"] = new_mode
        session["last_active"] = datetime.now().isoformat()
        
        # Critical: Save session with error handling (consistency with other methods)
        try:
            await self.session_manager.set_session(user_id, session)
        except Exception as e:
            logger.warning(f"Failed to update session in /mode: {e}")
            # Continue anyway → user sees confirmation even if session save fails
        
        # Send confirmation
        mode_display = self._get_mode_display(new_mode)
        await update.message.reply_text(
            f"✅ Режим изменён на: {mode_display}"
        )
        
        logger.info(f"User {user_id} switched to mode: {new_mode}")
    
    async def cmd_reload_faq(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle /reload_faq command (admin only).
        
        Rebuilds FAISS index for specified mode.
        Usage: /reload_faq [mode_name]
        Without argument: rebuilds current mode
        
        Args:
            update: Telegram Update object
            context: Callback context
        """
        user_id = update.effective_user.id
        
        # Admin check
        if not self._is_admin(user_id):
            await update.message.reply_text(
                "❌ Нет доступа. Команда только для администраторов."
            )
            return
        
        # Determine mode to rebuild
        if context.args:
            mode = context.args[0].lower().strip()
        else:
            # No argument → use current mode from session
            try:
                session = await self.session_manager.get_session(user_id)
                if session is None:
                    session = {"mode": self.DEFAULT_MODE}
            except Exception as e:
                logger.warning(f"Session error in /reload_faq: {e}")
                session = {"mode": self.DEFAULT_MODE}
            
            mode = session.get("mode", self.DEFAULT_MODE)
        
        # Validate mode
        if mode not in self.config["modes"]:
            available_modes = ", ".join(self.config["modes"].keys())
            await update.message.reply_text(
                f"❌ Неизвестный режим: {mode}\n\n"
                f"Доступные режимы: {available_modes}"
            )
            return
        
        # Show progress message
        mode_display = self._get_mode_display(mode)
        await update.message.reply_text(
            f"🔨 Пересобираю индекс для режима {mode_display}..."
        )
        
        # Get FAQ file path
        faq_file = self.config["modes"][mode]["faq_file"]
        
        # Rebuild index (sync operation in async thread)
        try:
            await asyncio.to_thread(
                self.rag_factory.rebuild_index,
                mode,
                faq_file
            )
        except FileNotFoundError as e:
            await update.message.reply_text(
                f"❌ Ошибка: FAQ файл не найден\n{faq_file}"
            )
            logger.error(f"FAQ file not found: {faq_file}", exc_info=True)
            return
        except Exception as e:
            logger.error(f"Failed to rebuild index for {mode}: {e}", exc_info=True)
            await update.message.reply_text(
                f"❌ Ошибка при пересборке индекса\n{str(e)}"
            )
            return
        
        # Send success message
        await update.message.reply_text(
            f"✅ Индекс обновлён для режима {mode_display}"
        )
        
        logger.info(f"Admin {user_id} reloaded FAQ index for mode: {mode}")
    
    async def handle_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle text messages.
        
        Processes user questions through RAG chain and returns answers.
        Shows typing indicator during processing.
        
        Args:
            update: Telegram Update object
            context: Callback context
        
        Flow:
            1. Get user_id and session
            2. Show typing indicator
            3. Create/get RAG chain for mode
            4. Invoke chain with timeout
            5. Format answer (escape markdown)
            6. Send response (with fallback)
            7. Update session
        
        Error Handling:
            - Empty messages → ignored
            - Session errors → fallback to default
            - Chain errors → user-friendly messages
            - Timeout → "Запрос занял слишком много времени"
            - Send errors → fallback to raw text
        """
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        # Ignore empty messages
        if not text:
            return
        
        # Critical: Засечь время для метрики latency
        start_time = time.time()
        
        # Critical: Get session with fallback to default if not found or error
        # This ensures bot works even if Redis/SessionManager fails
        try:
            session = await self.session_manager.get_session(user_id)
            if session is None:
                # First message from user → create new session
                session = {
                    "mode": self.DEFAULT_MODE,
                    "last_active": datetime.now().isoformat()
                }
                # Critical: Save new session to SessionManager for persistence
                # Without this, session will be recreated on every request
                try:
                    await self.session_manager.set_session(user_id, session)
                    logger.info(f"Created new session for user {user_id}")
                except Exception as e:
                    logger.warning(f"Failed to create session: {e}")
                    # Continue with in-memory session (fallback)
        except Exception as e:
            logger.warning(f"Session manager error: {e}")
            # Fallback to default session (in-memory)
            session = {
                "mode": self.DEFAULT_MODE,
                "last_active": datetime.now().isoformat()
            }
        
        mode = session.get("mode", self.DEFAULT_MODE)
        
        # Validate mode
        if mode not in self.config["modes"]:
            logger.warning(f"Invalid mode {mode} for user {user_id}, using default")
            mode = self.DEFAULT_MODE
            session["mode"] = mode
        
        # Show typing indicator
        await update.message.chat.send_action(ChatAction.TYPING)
        
        # Get timeout from config
        timeout = self.config["modes"][mode]["timeout_seconds"]  # 30
        
        # Create/get chain (with error handling)
        try:
            chain = self.rag_factory.create_chain(mode)
        except ValueError as e:
            # Mode not found
            available_modes = ", ".join(self.config["modes"].keys())
            await update.message.reply_text(
                f"❌ Неизвестный режим: {mode}\n\n"
                f"Доступные режимы: {available_modes}"
            )
            return
        except FileNotFoundError as e:
            # FAQ file not found (critical error)
            logger.error(f"FAQ file not found for mode {mode}: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Ошибка конфигурации. Обратитесь к администратору."
            )
            return
        except Exception as e:
            logger.error(f"Failed to create chain for mode {mode}: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Ошибка загрузки модели. Обратитесь к администратору."
            )
            return
        
        # Critical: Invoke chain with timeout (sync operation in async thread)
        # asyncio.to_thread() ensures non-blocking execution
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    chain.invoke,
                    {"input": text}
                ),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            latency = time.time() - start_time
            ERROR_COUNT.labels(error_type="timeout").inc()
            await update.message.reply_text(
                "⏱️ Запрос занял слишком много времени. Попробуйте упростить вопрос."
            )
            logger.warning(
                f"Query timeout for user {user_id} (mode={mode})",
                extra={"user_id": user_id, "mode": mode, "latency": latency}
            )
            return
        except ValueError as e:
            latency = time.time() - start_time
            # Check if it's dimension mismatch error
            if "dimension" in str(e).lower():
                ERROR_COUNT.labels(error_type="dimension_mismatch").inc()
            else:
                ERROR_COUNT.labels(error_type="unknown").inc()
            logger.error(f"Error invoking chain: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Произошла ошибка. Попробуйте позже."
            )
            return
        except Exception as e:
            latency = time.time() - start_time
            # Check if it's rate limit error
            error_str = str(e).lower()
            if "rate" in error_str and "limit" in error_str:
                ERROR_COUNT.labels(error_type="rate_limit").inc()
            else:
                ERROR_COUNT.labels(error_type="unknown").inc()
            logger.error(f"Error invoking chain: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Произошла ошибка. Попробуйте позже."
            )
            return
        
        # Extract answer
        answer = response.get("answer", "Не удалось получить ответ")
        
        # Critical: Escape markdown for Telegram MarkdownV2
        # LLM output may contain special chars: _ * [ ] ( ) ~ ` > # + - = | { } . !
        formatted_answer = self._escape_markdown_v2(answer)
        
        # Check length (safe truncation)
        if len(formatted_answer) > self.MAX_MESSAGE_LENGTH:
            truncated = formatted_answer[:self.MAX_MESSAGE_LENGTH - 100]
            formatted_answer = truncated + "\n\n\\.\\.\\.  \\(сообщение обрезано\\)"
        
        # Critical: Fallback if markdown parsing fails
        # Send raw answer without markdown to ensure user gets response
        message_sent = False  # Track if message was successfully sent
        try:
            await update.message.reply_text(
                formatted_answer,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            message_sent = True
        except Exception as e:
            logger.error(f"Failed to send with markdown: {e}", exc_info=True)
            # Fallback: send raw answer without markdown
            try:
                await update.message.reply_text(answer)  # Raw text fallback
                message_sent = True  # Mark as sent if fallback succeeded
            except Exception as e2:
                logger.error(f"Failed to send fallback message: {e2}")
                # Both attempts failed → do not update session or log success
        
        # Update session only if message was sent
        if message_sent:
            session["last_active"] = datetime.now().isoformat()
            try:
                await self.session_manager.set_session(user_id, session)
            except Exception as e:
                logger.warning(f"Failed to update session: {e}")
            
            # Log success only if message was sent
            latency = time.time() - start_time
            # Record query latency metric
            QUERY_LATENCY.labels(mode=mode).observe(latency)
            logger.info(
                f"User {user_id} (mode={mode}) query: '{text[:50]}...' | "
                f"Answer length: {len(answer)} chars",
                extra={"user_id": user_id, "mode": mode, "latency": latency}
            )
        else:
            # Message failed to send → log error
            latency = time.time() - start_time
            logger.error(
                f"Failed to send answer to user {user_id} (mode={mode}) | "
                f"Query: '{text[:50]}...'",
                extra={"user_id": user_id, "mode": mode, "latency": latency}
            )

