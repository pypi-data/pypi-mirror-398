from aiogram.filters.callback_data import CallbackData


class NavCallbackData(CallbackData, prefix="nav"):  # navigate menu
    to: str


class BoolCd(CallbackData, prefix="bool"):
    req: str
    res: bool
    xtr: int | str | None = None


flags = {
    "RUB": "🇷🇺",
    "THB": "🇹🇭",
    "IDR": "🇮🇩",
    "TRY": "🇹🇷",
    "GEL": "🇬🇪",
    "VND": "🇻🇳",
    "AED": "🇦🇪",
    "AMD": "🇦🇲",
    "AZN": "🇦🇿",
    "CNY": "🇨🇳",
    "EUR": "🇪🇺",
    "HKD": "🇭🇰",
    "INR": "🇮🇳",
    "PHP": "🇵🇭",
    "USD": "🇺🇸",
}
