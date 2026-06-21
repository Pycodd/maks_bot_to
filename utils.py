from imports import (logging, json, time, List, Optional, Any, Callable, asyncio)
from dataclasses import dataclass

def _get_chat_id(event) -> int:
    """
    Универсальная функция получения chat_id из события.

    Поддерживает:
    - MessageCreated
    - MessageCallback
    - И другие типы событий MaxAPI
    """
    try:
        if hasattr(event, 'message') and hasattr(event.message, 'recipient'):
            return event.message.recipient.chat_id
        elif hasattr(event, 'recipient'):
            return event.recipient.chat_id
        else:
            raise AttributeError(f"No chat_id found in {type(event)}")
    except (AttributeError, TypeError) as e:
        raise AttributeError(f"Cannot get chat_id from {type(event)}: {e}")


def _get_user_id(event) -> int:
    """
    Универсальная функция получения user_id из события.

    Поддерживает:
    - MessageCreated
    - MessageCallback
    - И другие типы событий MaxAPI
    """
    try:
        if hasattr(event, 'message') and hasattr(event.message, 'sender'):
            return event.message.sender.user_id
        elif hasattr(event, 'sender'):
            return event.sender.user_id
        else:
            raise AttributeError(f"No user_id found in {type(event)}")
    except (AttributeError, TypeError) as e:
        raise AttributeError(f"Cannot get user_id from {type(event)}: {e}")


def _serialize_attachments(attachments) -> List[dict]:
    """
    Сериализует вложения (клавиатуры, кнопки)

    в JSON-совместимый формат
    """
    serialized = []

    if not attachments:
        return serialized

    for att in attachments:
        try:
            if hasattr(att, 'model_dump'):
                serialized.append(att.model_dump())
            elif hasattr(att, 'dict'):
                serialized.append(att.dict())
            elif isinstance(att, dict):
                serialized.append(att)
            else:
                serialized.append({"raw": str(att)})
        except (AttributeError, TypeError, ValueError) as e:
            serialized.append({"error": f"Failed to serialize: {e}"})

    return serialized


def log_response_detailed(
        chat_id: int,
        response_text: str = None,
        attachments: list = None,
        reply_to: int = None,
        parse_mode: str = None,
        duration_ms: float = None,
        **kwargs
) -> None:
    """
    Подробное логирование ответа бота в JSON-формате.

    В конце блока
    """
    try:
        response_log = {
            "direction": "outgoing",
            "timestamp": int(time.time() * 1000),
            "chat_id": chat_id,
            "response": {
                "text": response_text if response_text else "",
                "attachments": _serialize_attachments(attachments) if attachments else [],
                "reply_to": reply_to,
                "parse_mode": parse_mode
            }
        }

        if duration_ms is not None:
            response_log["processing_time_ms"] = round(duration_ms, 2)

        if kwargs:
            response_log["extra"] = kwargs

        if response_log["response"]["text"] and len(response_log["response"]["text"]) > 500:
            response_log["response"]["text"] = response_log["response"]["text"][:500] + "... (обрезано)"

        logging.info(f"🤖 Бот ответил:\n{json.dumps(response_log, indent=2, ensure_ascii=False)}")

    except (TypeError, ValueError, json.JSONDecodeError) as e:
        logging.error(f"Ошибка при логировании ответа: {e}")
        logging.info(f"🤖 Бот ответил | chat: {chat_id} | текст: {response_text[:200] if response_text else ''}")


def log_response_simple(chat_id: int, response_text: str, max_length: int = 500) -> None:
    """ Упрощённое логирование ответа бота (одной строкой). """
    try:
        if len(response_text) > max_length:
            response_text = response_text[:max_length] + "... (обрезано)"
        logging.info(f"🤖 Бот ответил | chat: {chat_id} | текст: {response_text}")
    except (TypeError, AttributeError) as e:
        logging.error(f"Ошибка при простом логировании ответа: {e}")


@dataclass
class EventContext:
    """Контекст события с основными данными."""
    event: Any
    chat_id: int
    user_id: int
    message_text: str = ""
    message_mid: str = ""
    raw_event: Any = None

    @classmethod
    async def from_event(cls, event_obj: Any, extractors: Optional[List[Callable]] = None) -> "EventContext":
        """
        Создаёт контекст из события.

        Аргументы:
            event_obj: Событие от MaxAPI (переименовал, чтобы не было конфликта)
            extractors: Список дополнительных функций-экстракторов
        """
        chat_id = _get_chat_id(event_obj)
        user_id = _get_user_id(event_obj)

        message_text = ""
        message_mid = ""

        if hasattr(event_obj, 'message') and hasattr(event_obj.message, 'body'):
            message_text = getattr(event_obj.message.body, 'text', "")
            message_mid = getattr(event_obj.message.body, 'mid', "")

        context = cls(
            event=event_obj,
            chat_id=chat_id,
            user_id=user_id,
            message_text=message_text,
            message_mid=message_mid,
            raw_event=event_obj
        )

        if extractors:
            for extractor in extractors:
                try:
                    if asyncio.iscoroutinefunction(extractor):
                        extra_data = await extractor(event_obj)
                    else:
                        extra_data = extractor(event_obj)
                    if isinstance(extra_data, dict):
                        for key, value in extra_data.items():
                            setattr(context, key, value)
                except Exception as e:
                    logging.warning(f"Ошибка в экстракторе {extractor.__name__}: {e}")

        return context

    def log_info(self, message: str):
        """Логирует информационное сообщение с контекстом."""
        logging.info(f"👤 Пользователь {self.user_id} (chat: {self.chat_id}) | {message}")

    def log_debug(self, message: str):
        """Логирует отладочное сообщение с контекстом."""
        logging.debug(f"🔍 {message} | chat: {self.chat_id} | user: {self.user_id}")