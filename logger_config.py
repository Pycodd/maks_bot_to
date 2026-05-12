from imports import logging, json, Callable, Awaitable, BaseMiddleware, Dict, Any, UpdateUnion, time


def logging_conf():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler("bot_updates.log", encoding="utf-8"), logging.StreamHandler()])


def get_chat_id_from_event(event_object: Any) -> str:
    """Универсальная функция получения chat_id из разных типов событий"""
    try:
        if hasattr(event_object, 'message') and hasattr(event_object.message, 'recipient'):
            return str(event_object.message.recipient.chat_id)
        elif hasattr(event_object, 'recipient'):
            return str(event_object.recipient.chat_id)
        elif hasattr(event_object, 'chat_id'):
            return str(event_object.chat_id)
        else:
            return 'unknown'
    except (AttributeError, TypeError, ValueError) as e:
        logging.warning(f"Не удалось получить chat_id: {e}")
        return 'unknown'


def get_user_id_from_event(event_object: Any) -> str:
    """Универсальная функция получения user_id из разных типов событий"""
    try:
        if hasattr(event_object, 'message') and hasattr(event_object.message, 'sender'):
            return str(event_object.message.sender.user_id)
        elif hasattr(event_object, 'sender'):
            return str(event_object.sender.user_id)
        elif hasattr(event_object, 'user_id'):
            return str(event_object.user_id)
        else:
            return 'unknown'
    except (AttributeError, TypeError, ValueError) as e:
        logging.warning(f"Не удалось получить user_id: {e}")
        return 'unknown'


class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования всех событий с замером времени."""

    async def __call__(
            self,
            handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
            event_object: UpdateUnion,
            data: Dict[str, Any],
    ) -> Any:
        event_type = type(event_object).__name__
        chat_id = get_chat_id_from_event(event_object)
        user_id = get_user_id_from_event(event_object)

        start_time = time.perf_counter()

        try:
            if hasattr(event_object, 'model_dump'):
                event_dict = event_object.model_dump()
            elif hasattr(event_object, 'dict'):
                event_dict = event_object.dict()
            else:
                event_dict = {"raw": str(event_object)}

            if isinstance(event_dict, dict) and 'body' in event_dict and 'text' in event_dict.get('body', {}):
                text = event_dict['body']['text']
                if len(text) > 200:
                    event_dict['body']['text'] = text[:200] + '... (обрезано)'

            event_json = json.dumps(event_dict, indent=2, ensure_ascii=False, default=str)
            logging.debug(f"📨 Получено {event_type} | chat: {chat_id} | user: {user_id}\n{event_json}")

        except (TypeError, ValueError, json.JSONDecodeError) as e:
            logging.debug(f"📨 Получено {event_type} | chat: {chat_id} | user: {user_id} | ошибка сериализации: {e}")
        except AttributeError as e:
            logging.debug(
                f"📨 Получено {event_type} | chat: {chat_id} | user: {user_id} | ошибка доступа к атрибуту: {e}")

        try:
            result = await handler(event_object, data)
        except Exception as e:
            logging.error(f"❌ Ошибка в хендлере {event_type}: {e}", exc_info=True)
            raise

        elapsed_time = (time.perf_counter() - start_time) * 1000
        logging.debug(f"✅ Обработка {event_type} завершена | chat: {chat_id} | время: {elapsed_time:.2f} мс")

        return result
