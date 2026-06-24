from imports import (MessageCallback, MemoryContext, TextFormat, RegistrationStates, Keyboards, MessageCreated)
from utils import EventContext, log_response_detailed
from responses import BotResponses
from message_handlers import MessageHandlers


class CallbackHandlers:
    """
    Класс для обработки всех callback-запросов от кнопок.
    ВСЯ логика регистрации здесь.
    """
    async def handle(self, callback: MessageCallback, context: MemoryContext = None):
        ctx = await EventContext.from_event(callback)
        data = callback.callback.payload
        ctx.log_info(f"нажал кнопку: {data}")

        # ===== СОГЛАШЕНИЕ =====
        if data == "agreement_accept":
            await self.agreement_accept(callback, ctx, context)
            return
        elif data == "agreement_decline":
            await self.agreement_decline(callback, ctx, context)
            return

        # # ===== ВЫБОР РАЙОНА =====
        # if data.startswith("district_"):
        #     await self.district_selection(callback, ctx, context)
        #     return

    # ========== НАЧАЛО РЕГИСТРАЦИИ (из /start) ==========

    @staticmethod
    async def handle_start(event: MessageCreated, context: MemoryContext, user_name: str):
        """
        Обрабатывает команду /start.
        Устанавливает состояние, получает клавиатуру, отправляет соглашение.
        """
        ctx = await EventContext.from_event(event)
        ctx.log_info(f"📋 Начало регистрации для {user_name}")

        # 1. Устанавливаем состояние
        ctx.log_info(f"🔍 Устанавливаю состояние: {RegistrationStates.waiting_for_agreement}")
        await context.set_state(RegistrationStates.waiting_for_agreement)

        current_state = await context.get_state()
        ctx.log_info(f"🔍 Состояние после установки: {current_state}")

        await context.set_data({"user_name": user_name})

        # 2. Получаем клавиатуру из модуля Keyboards
        keyboard = Keyboards.agreement_keyboard()

        # 3. Отправляем сообщение
        await MessageHandlers.format_received_message(
            event=event,
            response=BotResponses.user_agreement(),
            bot=None,
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

    # ========== РЕГИСТРАЦИЯ: СОГЛАШЕНИЕ ==========

    @staticmethod
    async def agreement_accept(callback: MessageCallback, ctx: EventContext, context: MemoryContext):
        """Обработчик кнопки 'Принять и продолжить'"""
        ctx.log_info("✅ Пользователь принял соглашение")

        # Проверяем состояние
        current_state = await context.get_state()
        ctx.log_info(f"🔍 ТЕКУЩЕЕ СОСТОЯНИЕ: {current_state}")
        ctx.log_info(f"🔍 ОЖИДАЕМОЕ СОСТОЯНИЕ: {RegistrationStates.waiting_for_agreement}")

        if current_state != RegistrationStates.waiting_for_agreement:
            ctx.log_info("❌ СОСТОЯНИЕ НЕ СОВПАДАЕТ!")
            await callback.message.answer("⚠️ Пожалуйста, начните с /start")
            return

        # Получаем данные
        data = await context.get_data()
        user_name = data.get("user_name", "Пользователь")

        # 1. Устанавливаем новое состояние
        await context.set_state(RegistrationStates.waiting_for_district)

        # 2. Получаем клавиатуру из модуля Keyboards
        keyboard, district_names = Keyboards.create_user_keyboard_district_and_map()
        data["district_names"] = district_names
        await context.set_data(data)

        # 3. Отправляем сообщение с районами
        registration_text = BotResponses.registration_start(user_name)

        await MessageHandlers.format_received_message(
            event=callback,
            response=registration_text,
            bot=None,
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
    async def agreement_decline(callback: MessageCallback, ctx: EventContext, context: MemoryContext):
        """Обработчик кнопки 'Отказаться'"""
        ctx.log_info("❌ Пользователь отказался от соглашения")

        # Сбрасываем состояние
        await context.set_state(None)
        await context.set_data({})

        await callback.message.answer(
            "❌ Вы отказались от пользовательского соглашения.\n\n"
            "Без принятия соглашения использование бота невозможно."
        )
