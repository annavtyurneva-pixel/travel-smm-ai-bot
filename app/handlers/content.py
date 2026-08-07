from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.keyboards import actions_keyboard, confirm_keyboard, main_keyboard
from app.services.llm_service import AIServiceError, ContentBrief, LLMService
from app.services.publisher import PublishError, TelegramPublisher
from app.services.storage import Draft, DraftStorage
from app.states import ContentStates

router = Router(name="content")

HELP = (
    "Я помогу подготовить публикацию для тревел-канала.\n\n"
    "💡 Идеи постов — получить пять тем.\n"
    "✍️ Создать пост — пройти короткий бриф.\n"
    "🖼 Создать изображение — добавить картинку к черновику.\n"
    "👀 Предпросмотр — проверить материал перед публикацией.\n"
    "❌ Отменить — удалить текущий черновик.\n\n"
    "Публикация выполняется только после отдельного подтверждения."
)


def _valid(text: str | None, max_length: int = 200) -> str | None:
    value = (text or "").strip()
    return value if 2 <= len(value) <= max_length else None


def _brief(draft: Draft) -> ContentBrief:
    return ContentBrief(
        destination=draft.destination,
        audience=draft.audience,
        post_format=draft.post_format,
        tone=draft.tone,
        goal=draft.goal,
        topic=draft.topic,
    )


async def _load_or_explain(message: Message, storage: DraftStorage) -> Draft | None:
    draft = await storage.get(message.from_user.id)
    if not draft:
        await message.answer("Черновика пока нет. Нажмите «✍️ Создать пост».")
    return draft


async def _show_preview(message: Message, draft: Draft) -> None:
    if draft.image:
        await message.answer_photo(
            BufferedInputFile(draft.image, filename="preview.png"),
            caption="🖼 Изображение текущего черновика",
        )
    await message.answer(
        "👀 ПРЕДПРОСМОТР\n\n" + (draft.text or "Текст ещё не создан."),
        reply_markup=actions_keyboard(),
    )


@router.message(CommandStart())
async def start(message: Message, storage: DraftStorage) -> None:
    draft = await storage.get(message.from_user.id)
    suffix = "\n\nСохранённый черновик доступен через «👀 Предпросмотр»." if draft else ""
    await message.answer("Добро пожаловать в Travel SMM AI Assistant!\n\n" + HELP + suffix,
                         reply_markup=main_keyboard())


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(HELP, reply_markup=main_keyboard())


@router.message(F.text == "💡 Идеи постов")
async def ideas(message: Message, llm: LLMService) -> None:
    brief = ContentBrief(
        destination="популярные и небанальные направления",
        audience="самостоятельные путешественники",
        post_format="полезный пост",
        tone="дружелюбный и профессиональный",
        goal="вовлечение и сохранения",
    )
    await message.answer("Готовлю пять идей…")
    try:
        result = await llm.generate_ideas(brief)
        await message.answer("💡 Идеи для тревел-блога\n\n" + result)
    except AIServiceError as error:
        await message.answer(f"⚠️ {error}")


@router.message(F.text == "✍️ Создать пост")
async def create_post(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ContentStates.destination)
    await message.answer("Шаг 1 из 6. Укажите страну, город или направление:")


async def _accept(message: Message, state: FSMContext, field: str, next_state, question: str) -> None:
    value = _valid(message.text)
    if not value:
        await message.answer("Введите от 2 до 200 символов. Попробуйте ещё раз:")
        return
    await state.update_data(**{field: value})
    await state.set_state(next_state)
    await message.answer(question)


@router.message(ContentStates.destination)
async def destination(message: Message, state: FSMContext) -> None:
    await _accept(message, state, "destination", ContentStates.audience,
                  "Шаг 2 из 6. Кто целевая аудитория?")


@router.message(ContentStates.audience)
async def audience(message: Message, state: FSMContext) -> None:
    await _accept(message, state, "audience", ContentStates.post_format,
                  "Шаг 3 из 6. Укажите формат: гид, подборка, история, чек-лист…")


@router.message(ContentStates.post_format)
async def post_format(message: Message, state: FSMContext) -> None:
    await _accept(message, state, "post_format", ContentStates.tone,
                  "Шаг 4 из 6. Какой нужен тон: дружелюбный, экспертный, вдохновляющий…?")


@router.message(ContentStates.tone)
async def tone(message: Message, state: FSMContext) -> None:
    await _accept(message, state, "tone", ContentStates.goal,
                  "Шаг 5 из 6. Цель поста: вовлечение, сохранения, обсуждение…?")


@router.message(ContentStates.goal)
async def goal(message: Message, state: FSMContext) -> None:
    await _accept(message, state, "goal", ContentStates.topic,
                  "Шаг 6 из 6. Уточните тему поста:")


@router.message(ContentStates.topic)
async def topic(message: Message, state: FSMContext, storage: DraftStorage, llm: LLMService) -> None:
    value = _valid(message.text)
    if not value:
        await message.answer("Введите тему от 2 до 200 символов:")
        return
    data = await state.get_data()
    draft = Draft(user_id=message.from_user.id, topic=value, **data)
    await message.answer("Генерирую текст поста…")
    try:
        draft.text = await llm.generate_post(_brief(draft))
        await storage.save(draft)
        await state.clear()
        await message.answer("✅ Текст создан и сохранён. Теперь можно создать изображение или открыть предпросмотр.",
                             reply_markup=main_keyboard())
        await _show_preview(message, draft)
    except AIServiceError as error:
        await message.answer(f"⚠️ {error}\nБриф сохранён в текущем диалоге — можно повторить тему.")


@router.message(F.text == "🖼 Создать изображение")
async def create_image(message: Message, storage: DraftStorage, llm: LLMService, image_service) -> None:
    draft = await _load_or_explain(message, storage)
    if not draft:
        return
    if not draft.text:
        await message.answer("Сначала создайте текст поста.")
        return
    await message.answer("Создаю изображение для текущего черновика…")
    try:
        draft.image_prompt = await llm.generate_image_prompt(_brief(draft), draft.text)
        draft.image = await image_service.generate(draft.image_prompt)
        await storage.save(draft)
        await message.answer("✅ Изображение создано и привязано к черновику.")
        await _show_preview(message, draft)
    except AIServiceError as error:
        await message.answer(f"⚠️ {error}")


@router.message(F.text == "👀 Предпросмотр")
async def preview(message: Message, storage: DraftStorage) -> None:
    draft = await _load_or_explain(message, storage)
    if draft:
        await _show_preview(message, draft)


@router.callback_query(F.data == "regen_text")
async def regenerate_text(callback: CallbackQuery, storage: DraftStorage, llm: LLMService) -> None:
    draft = await storage.get(callback.from_user.id)
    if not draft:
        await callback.answer("Черновик не найден", show_alert=True)
        return
    await callback.answer("Генерирую новый текст")
    try:
        draft.text = await llm.generate_post(_brief(draft))
        await storage.save(draft)  # image намеренно сохраняется
        await _show_preview(callback.message, draft)
    except AIServiceError as error:
        await callback.message.answer(f"⚠️ {error}")


@router.callback_query(F.data == "regen_image")
async def regenerate_image(callback: CallbackQuery, storage: DraftStorage, llm: LLMService, image_service) -> None:
    draft = await storage.get(callback.from_user.id)
    if not draft or not draft.text:
        await callback.answer("Сначала создайте текст", show_alert=True)
        return
    await callback.answer("Генерирую новое изображение")
    try:
        draft.image_prompt = await llm.generate_image_prompt(_brief(draft), draft.text)
        draft.image = await image_service.generate(draft.image_prompt)
        await storage.save(draft)  # text намеренно сохраняется
        await _show_preview(callback.message, draft)
    except AIServiceError as error:
        await callback.message.answer(f"⚠️ {error}")


@router.callback_query(F.data == "publish_request")
async def publish_request(callback: CallbackQuery, state: FSMContext, storage: DraftStorage) -> None:
    draft = await storage.get(callback.from_user.id)
    if not draft or not draft.text:
        await callback.answer("Нет готового текста", show_alert=True)
        return
    await state.set_state(ContentStates.confirm_publish)
    await callback.answer()
    await callback.message.answer(
        "Материал будет опубликован в заданном канале. Подтверждаете публикацию?",
        reply_markup=confirm_keyboard(),
    )


@router.callback_query(ContentStates.confirm_publish, F.data == "publish_confirm")
async def publish_confirm(callback: CallbackQuery, state: FSMContext, storage: DraftStorage,
                          publisher: TelegramPublisher) -> None:
    draft = await storage.get(callback.from_user.id)
    if not draft:
        await callback.answer("Черновик не найден", show_alert=True)
        return
    await callback.answer("Публикую…")
    try:
        await publisher.publish(draft.text, draft.image)
        await storage.delete(callback.from_user.id)
        await state.clear()
        await callback.message.answer("✅ Материал опубликован, черновик очищен.", reply_markup=main_keyboard())
    except PublishError as error:
        await callback.message.answer(f"⚠️ {error}\nЧерновик сохранён.")


@router.callback_query(ContentStates.confirm_publish, F.data == "publish_abort")
async def publish_abort(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Публикация отменена")
    await callback.message.answer("Публикация не выполнялась. Черновик сохранён.")


@router.message(F.text == "❌ Отменить")
@router.callback_query(F.data == "cancel")
async def cancel(event: Message | CallbackQuery, state: FSMContext, storage: DraftStorage) -> None:
    user_id = event.from_user.id
    await state.clear()
    await storage.delete(user_id)
    if isinstance(event, CallbackQuery):
        await event.answer("Черновик удалён")
        message = event.message
    else:
        message = event
    await message.answer("❌ Действие отменено, текущий черновик очищен.", reply_markup=main_keyboard())


@router.message()
async def fallback(message: Message) -> None:
    await message.answer("Не понял команду. Используйте кнопки меню или /help.", reply_markup=main_keyboard())

