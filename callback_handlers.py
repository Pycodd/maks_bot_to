from imports import (MessageCallback, MemoryContext, TextFormat, RegistrationStates, Keyboards, MessageCreated)
from utils import EventContext, log_response_detailed
from responses import BotResponses
from message_handlers import MessageHandlers


class CallbackHandlers:
    """
    Класс для обработки всех callback-запросов от кнопок.
    ВСЯ логика регистрации здесь.
    """
    async def handle(self, callback: MessageCallback, context: MemoryContext = None, bot=None):
        ctx = await EventContext.from_event(callback)
        data = callback.callback.payload
        ctx.log_info(f"нажал кнопку: {data}")

        if data == "agreement_accept":
            await self.agreement_accept(callback, ctx, context, bot)
            return

        elif data == "agreement_decline":
            await self.agreement_decline(callback, ctx, context, bot)
            return

        # # ===== ВЫБОР РАЙОНА =====
        # if data.startswith("district_"):
        #     await self.district_selection(callback, ctx, context)
        #     return

    # ========== НАЧАЛО РЕГИСТРАЦИИ (из /start) ==========

    @staticmethod
    async def handle_start(event: MessageCreated, context: MemoryContext, user_name: str, bot):
        """
        Обрабатывает команду /start.
        Устанавливает состояние, получает клавиатуру, отправляет соглашение.
        """
        ctx = await EventContext.from_event(event)
        await context.set_state(RegistrationStates.waiting_for_agreement)
        await context.set_data({
            "user_name": user_name,
            "user_id": ctx.user_id,
            "chat_id": ctx.chat_id,
        })

        keyboard = Keyboards.agreement_keyboard()
        await MessageHandlers.format_received_message(
            response=BotResponses.user_agreement(),
            bot=bot,
            user_id=ctx.user_id,
            chat_id=ctx.chat_id,
            chat_type="dialog",
            keyboard=keyboard,
            text_format=TextFormat.HTML
        )

        log_response_detailed(
            chat_id=ctx.chat_id,
            response_text=BotResponses.user_agreement(),
            attachments=[keyboard]
        )

    @staticmethod
    async def agreement_accept(callback: MessageCallback, ctx: EventContext, context: MemoryContext, bot):
        """Обработчик кнопки 'Принять и продолжить'"""
        current_state = await context.get_state()
        if current_state != RegistrationStates.waiting_for_agreement:
            await callback.message.answer("⚠️ Пожалуйста, начните с /start")
            return

        data = await context.get_data()
        user_name = data.get("user_name", "Пользователь")

        await context.set_state(RegistrationStates.waiting_for_district)

        keyboard, district_names = Keyboards.create_user_keyboard_district_and_map()
        data["district_names"] = district_names
        await context.set_data(data)
        registration_text = BotResponses.registration_start(user_name)

        await MessageHandlers.format_received_message(
            response=registration_text,
            bot=bot,
            user_id=ctx.user_id,
            chat_id=ctx.chat_id,
            chat_type="dialog",
            keyboard=keyboard,
            text_format=TextFormat.MARKDOWN
        )

        log_response_detailed(
            chat_id=ctx.chat_id,
            response_text=registration_text,
            attachments=[keyboard]
        )

    @staticmethod
    async def agreement_decline(callback: MessageCallback, ctx: EventContext, context: MemoryContext, bot):
        """Обработчик кнопки 'Отказаться'"""
        ctx.log_info("❌ Пользователь отказался от соглашения")

        # Сбрасываем состояние
        await context.set_state(None)
        await context.set_data({})

        await callback.message.answer(
            "❌ Вы отказались от пользовательского соглашения.\n\n"
            "Без принятия соглашения использование бота невозможно."
        )
