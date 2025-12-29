from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import asyncio
import logging

from xync_bot.loader import TOKEN

# Пример списка из 200 вариантов (замените на ваши данные)
OPTIONS = (
    [
        f"Apple {i}"
        for i in range(50)  # 50 вариантов на A
    ]
    + [
        "Banana"  # 1 вариант на B
    ]
    + [
        f"Dog {i}"
        for i in range(30)  # 30 вариантов на D
    ]
    + [
        f"Elephant {i}"
        for i in range(20)  # 20 вариантов на E
    ]
    + [
        f"Fish {i}"
        for i in range(40)  # 40 вариантов на F
    ]
    + [
        f"Zebra {i}"
        for i in range(59)  # 59 вариантов на Z
    ]
)


class SmartAlphaPager:
    def __init__(self, options, items_per_page=15):
        self.options = sorted(options)  # Сортируем по алфавиту
        self.items_per_page = items_per_page
        self.pages = self._create_balanced_pages()

    def _create_balanced_pages(self):
        """Создаем страницы с примерно равным количеством элементов"""
        pages = []
        current_page = []

        for option in self.options:
            current_page.append(option)

            # Если страница заполнена, создаем новую
            if len(current_page) >= self.items_per_page:
                pages.append(current_page)
                current_page = []

        # Добавляем последнюю страницу, если есть остатки
        if current_page:
            pages.append(current_page)

        return pages

    def _get_page_title(self, page_items):
        """Создает заголовок страницы на основе диапазона букв"""
        if not page_items:
            return "Пустая страница"

        first_letter = page_items[0][0].upper()
        last_letter = page_items[-1][0].upper()

        if first_letter == last_letter:
            return f"📋 Буква '{first_letter}'"
        else:
            return f"📋 Буквы '{first_letter}' - '{last_letter}'"

    def get_overview_menu(self):
        """Возвращает обзорное меню со всеми страницами"""
        if not self.pages:
            return InlineKeyboardMarkup(inline_keyboard=[])

        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        # Создаем кнопки для каждой страницы
        for i, page_items in enumerate(self.pages):
            first_letter = page_items[0][0].upper()
            last_letter = page_items[-1][0].upper()
            count = len(page_items)

            if first_letter == last_letter:
                button_text = f"{first_letter} ({count})"
            else:
                button_text = f"{first_letter}-{last_letter} ({count})"

            # Группируем по 3 кнопки в ряд
            if i % 3 == 0:
                keyboard.inline_keyboard.append([])

            keyboard.inline_keyboard[-1].append(InlineKeyboardButton(text=button_text, callback_data=f"page_{i}"))

        return keyboard

    def get_page_keyboard(self, page_num):
        """Возвращает клавиатуру для конкретной страницы"""
        if page_num < 0 or page_num >= len(self.pages):
            return None, None

        page_items = self.pages[page_num]
        title = self._get_page_title(page_items)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        # Добавляем кнопки с вариантами
        for option in page_items:
            keyboard.inline_keyboard.append([InlineKeyboardButton(text=option, callback_data=f"select_{option}")])

        # Навигационные кнопки
        nav_row = []

        # Кнопка "К обзору"
        nav_row.append(InlineKeyboardButton(text="📖 Обзор", callback_data="back_to_overview"))

        # Кнопки навигации между страницами
        if len(self.pages) > 1:
            if page_num > 0:
                nav_row.append(InlineKeyboardButton(text="⬅️ Пред", callback_data=f"nav_page_{page_num - 1}"))

            nav_row.append(
                InlineKeyboardButton(text=f"{page_num + 1}/{len(self.pages)}", callback_data="current_page_info")
            )

            if page_num < len(self.pages) - 1:
                nav_row.append(InlineKeyboardButton(text="След ➡️", callback_data=f"nav_page_{page_num + 1}"))

        keyboard.inline_keyboard.append(nav_row)

        # Дополнительная информация в заголовке
        items_count = len(page_items)
        total_items = sum(len(page) for page in self.pages)
        full_title = f"{title}\nСтраница {page_num + 1}/{len(self.pages)} • {items_count} из {total_items} вариантов"

        return keyboard, full_title

    def get_stats(self):
        """Возвращает статистику распределения"""
        stats = {}
        for page_num, page_items in enumerate(self.pages):
            first_letter = page_items[0][0].upper()
            last_letter = page_items[-1][0].upper()

            if first_letter == last_letter:
                range_text = f"'{first_letter}'"
            else:
                range_text = f"'{first_letter}'-'{last_letter}'"

            stats[f"Страница {page_num + 1}"] = {"range": range_text, "count": len(page_items)}

        return stats


# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

pager = SmartAlphaPager(OPTIONS)


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    """Стартовая команда - показываем обзор страниц"""
    keyboard = pager.get_overview_menu()
    total_options = len(pager.options)
    total_pages = len(pager.pages)

    text = (
        f"🔍 Выберите диапазон для просмотра:\n\n"
        f"📊 Всего вариантов: {total_options}\n"
        f"📄 Всего страниц: {total_pages}"
    )

    await message.answer(text, reply_markup=keyboard)


@dp.message(Command("stats"))
async def stats_handler(message: types.Message):
    """Показать статистику распределения"""
    stats = pager.get_stats()

    text = "📊 Статистика распределения по страницам:\n\n"
    for page_name, info in stats.items():
        text += f"{page_name}: {info['range']} — {info['count']} вариантов\n"

    await message.answer(text)


@dp.callback_query(lambda c: c.data == "back_to_overview")
async def back_to_overview(callback: types.CallbackQuery):
    """Возврат к обзору страниц"""
    keyboard = pager.get_overview_menu()
    total_options = len(pager.options)
    total_pages = len(pager.pages)

    text = (
        f"🔍 Выберите диапазон для просмотра:\n\n"
        f"📊 Всего вариантов: {total_options}\n"
        f"📄 Всего страниц: {total_pages}"
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("page_"))
async def show_page(callback: types.CallbackQuery):
    """Показываем конкретную страницу"""
    page_num = int(callback.data.split("_")[1])
    keyboard, text = pager.get_page_keyboard(page_num)

    if keyboard:
        await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback.answer("Ошибка: страница не найдена")

    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("nav_page_"))
async def navigate_pages(callback: types.CallbackQuery):
    """Навигация между страницами"""
    page_num = int(callback.data.split("_")[2])
    keyboard, text = pager.get_page_keyboard(page_num)

    if keyboard:
        await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback.answer("Ошибка навигации")

    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("select_"))
async def option_selected(callback: types.CallbackQuery):
    """Обработка выбора варианта"""
    selected = callback.data.replace("select_", "")

    await callback.message.edit_text(
        f"✅ Вы выбрали: {selected}\n\n"
        f"Используйте /start для нового выбора\n"
        f"Используйте /stats для просмотра статистики"
    )
    await callback.answer(f"Выбран: {selected}")


@dp.callback_query(lambda c: c.data == "current_page_info")
async def current_page_info(callback: types.CallbackQuery):
    """Информация о текущей странице"""
    await callback.answer("Информация о текущей странице")


async def main():
    """Запуск бота"""
    logging.basicConfig(level=logging.INFO)
    print("Бот запущен...")

    # Выводим статистику при запуске
    stats = pager.get_stats()
    print("\n📊 Статистика распределения:")
    for page_name, info in stats.items():
        print(f"{page_name}: {info['range']} — {info['count']} вариантов")
    print()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
