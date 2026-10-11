# ============================================================
# bot.py - МЕГА-БОТ EXTRA DM
# Промокоды + Рассылки + Баны + Тикеты + Всё
# ============================================================

import telebot
from telebot import types
import os
import sys
import bcrypt
import asyncio
import aiohttp
import time
from datetime import datetime
from dotenv import load_dotenv
from db import (
    get_shop_items, get_account, get_account_by_static, get_top_players,
    add_money, add_dp,
    save_link, get_link, delete_link,
    is_admin, add_admin, remove_admin,
    add_shop_item, delete_shop_item, update_shop_item_price,
    get_purchases, create_purchase, give_item_to_player,
    update_purchase_status, get_bot_stats,
    log_admin_action, get_admin_logs,
    is_banned, ban_user_and_account, unban_user_and_account,
    unban_by_tg_id, unban_all, get_ban_by_tg_id, get_banned_users,
    is_muted, mute_user, unmute_user,
    warn_user, get_user_warns, clear_warns,
    create_ticket, add_ticket_message, get_ticket, get_open_tickets,
    get_user_tickets, get_ticket_messages, close_ticket,
    create_promo, use_promo, get_all_promos, delete_promo,
    claim_daily_bonus,
    save_user_ip,
    get_connection,
    register_user, update_user_link, clear_user_link,
    get_all_users_info, find_user_by_login, find_user_by_tg_id
)

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
SERVER_IP = os.getenv('SERVER_IP', '127.0.0.1:22005')
SUPPORT_CONTACT = os.getenv('SUPPORT_CONTACT', '@dadaka200')
RAGE_SERVER_IP = os.getenv('RAGE_SERVER_IP', '69.197.191.214')
RAGE_SERVER_PORT = int(os.getenv('RAGE_SERVER_PORT', 22005))
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'EXTRABE')

bot = telebot.TeleBot(BOT_TOKEN)

# === ХРАНИЛИЩА ОЖИДАНИЙ ===
authorized_admins = {}
ban_pending = {}
mute_pending = {}
warn_pending = {}
broadcast_pending = {}
broadcast_photo_pending = {}
promo_pending = {}
promo_delete_pending = {}
ticket_reply = {}
admin_add_pending = {}

print('🤖 Мега-бот TERYRP запущен!')
print(f'🔐 Пароль админки: "{ADMIN_PASSWORD}"')


# ============================================================
# ОНЛАЙН
# ============================================================
async def get_server_online():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://cdn.rage.mp/master/", timeout=5) as r:
                data = await r.json()
                for s in data.values():
                    if s.get('ip') == RAGE_SERVER_IP and s.get('port') == RAGE_SERVER_PORT:
                        return {
                            'players': s.get('players', 0),
                            'maxplayers': s.get('maxplayers', 0),
                            'peak': s.get('peak', 0),
                            'gamemode': s.get('gamemode')
                        }
                return None
    except Exception as e:
        print(f'❌ Ошибка онлайна: {e}')
        return None


def get_server_online_sync():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        r = loop.run_until_complete(get_server_online())
        loop.close()
        return r
    except Exception as e:
        return None


# ============================================================
# МЕНЮ
# ============================================================
def get_main_menu(is_admin_user=False):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('📡 IP', callback_data='ip'),
        types.InlineKeyboardButton('📊 Онлайн', callback_data='online'),
        types.InlineKeyboardButton('🛒 Магазин', callback_data='shop'),
        types.InlineKeyboardButton('👤 Профиль', callback_data='profile'),
        types.InlineKeyboardButton('📈 Статистика', callback_data='stats'),
        types.InlineKeyboardButton('🏆 Топ', callback_data='top'),
        types.InlineKeyboardButton('🎁 Бонус', callback_data='bonus'),
        types.InlineKeyboardButton('🎫 Промокод', callback_data='promo'),
        types.InlineKeyboardButton('🆘 Тикет', callback_data='ticket'),
        types.InlineKeyboardButton('ℹ️ Помощь', callback_data='help')
    )
    if is_admin_user:
        markup.add(types.InlineKeyboardButton('⚙️ Админ-панель', callback_data='admin_auth'))
    return markup


def get_admin_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton('📊 Статистика', callback_data='admin_stats'),
        types.InlineKeyboardButton('📦 Заявки', callback_data='admin_orders'),
        types.InlineKeyboardButton('🛒 Товары', callback_data='admin_items'),
        types.InlineKeyboardButton('👥 Пользователи', callback_data='admin_users'),
        types.InlineKeyboardButton('🔍 Поиск игрока', callback_data='admin_find'),
        types.InlineKeyboardButton('🚫 Баны', callback_data='admin_bans'),
        types.InlineKeyboardButton('🔇 Муты', callback_data='admin_mutes'),
        types.InlineKeyboardButton('⚠️ Варны', callback_data='admin_warns'),
        types.InlineKeyboardButton('🎫 Тикеты', callback_data='admin_tickets'),
        types.InlineKeyboardButton('🎟 Промокоды', callback_data='admin_promos'),
        types.InlineKeyboardButton('📢 Рассылка текста', callback_data='admin_broadcast'),
        types.InlineKeyboardButton('📸 Рассылка фото', callback_data='admin_broadcast_photo'),
        types.InlineKeyboardButton('➕ Админ', callback_data='admin_add'),
        types.InlineKeyboardButton('📜 Логи', callback_data='admin_logs'),
        types.InlineKeyboardButton('🚪 Выход', callback_data='admin_logout')
    )
    return markup


def get_promo_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton('➕ Создать промокод', callback_data='admin_promo_create'),
        types.InlineKeyboardButton('📋 Список промокодов', callback_data='admin_promo_list'),
        types.InlineKeyboardButton('🗑 Удалить промокод', callback_data='admin_promo_delete'),
        types.InlineKeyboardButton('⬅️ Назад', callback_data='admin_back')
    )
    return markup


# ============================================================
# ПРОВЕРКА ПАРОЛЯ
# ============================================================
def check_password(input_password, hashed_password):
    try:
        if hashed_password.startswith('$2'):
            return bcrypt.checkpw(input_password.encode('utf-8'), hashed_password.encode('utf-8'))
        return input_password == hashed_password
    except:
        return False


# ============================================================
# ПАРОЛЬ АДМИНКИ (ПЕРВЫЙ!)
# ============================================================
@bot.message_handler(
    func=lambda m: m.text and m.text.strip() == ADMIN_PASSWORD,
    content_types=['text']
)
def admin_password_handler(message):
    tg_id = message.from_user.id
    tg_username = message.from_user.username or message.from_user.first_name
    print(f'🔐 Получен пароль от {tg_username} ({tg_id})')
    if not is_admin(tg_id):
        bot.send_message(message.chat.id, '❌ Нет прав администратора.')
        return
    authorized_admins[tg_id] = True
    log_admin_action(tg_id, tg_username, 'admin_login', 'OK')
    print(f'✅ {tg_username} авторизован')
    bot.send_message(message.chat.id, '✅ *Доступ разрешён!*',
        parse_mode='Markdown', reply_markup=get_admin_menu())


# ============================================================
# ОБРАБОТЧИКИ ОЖИДАНИЙ
# ============================================================
@bot.message_handler(func=lambda m: m.from_user.id in ban_pending)
def ban_reason_handler(message):
    tg_id = message.from_user.id
    target = ban_pending.pop(tg_id, None)
    if not target: return
    reason = message.text.strip()
    tg_username = message.from_user.username or message.from_user.first_name
    target_info = find_user_by_tg_id(target)
    target_login = target_info['login'] if target_info else None
    target_static = target_info['static'] if target_info else None
    target_username = target_info['tg_username'] if target_info else None
    success, err = ban_user_and_account(target, target_username, target_static,
                                        target_login, reason, tg_id, tg_username)
    if success:
        log_admin_action(tg_id, tg_username, 'ban', f'tg={target}')
        bot.send_message(message.chat.id,
            f'✅ *Забанен!*\n👤 `{target_login or "-"}`\n📱 `{target}`\n📝 {reason}',
            parse_mode='Markdown', reply_markup=get_admin_menu())
    else:
        bot.send_message(message.chat.id, f'❌ {err}', reply_markup=get_admin_menu())


@bot.message_handler(func=lambda m: m.from_user.id in mute_pending)
def mute_reason_handler(message):
    tg_id = message.from_user.id
    data = mute_pending.pop(tg_id, None)
    if not data: return
    target, hours = data
    reason = message.text.strip()
    tg_username = message.from_user.username or message.from_user.first_name
    if mute_user(target, reason, tg_id, tg_username, hours):
        log_admin_action(tg_id, tg_username, 'mute', f'tg={target}, hours={hours}')
        bot.send_message(message.chat.id,
            f'✅ `{target}` замучен на {hours}ч.\n📝 {reason}',
            parse_mode='Markdown', reply_markup=get_admin_menu())
    else:
        bot.send_message(message.chat.id, '❌ Ошибка', reply_markup=get_admin_menu())


@bot.message_handler(func=lambda m: m.from_user.id in warn_pending)
def warn_reason_handler(message):
    tg_id = message.from_user.id
    target = warn_pending.pop(tg_id, None)
    if not target: return
    reason = message.text.strip()
    tg_username = message.from_user.username or message.from_user.first_name
    if warn_user(target, reason, tg_id, tg_username):
        log_admin_action(tg_id, tg_username, 'warn', f'tg={target}')
        bot.send_message(message.chat.id,
            f'⚠️ `{target}` получил варн.\n📝 {reason}',
            parse_mode='Markdown', reply_markup=get_admin_menu())
    else:
        bot.send_message(message.chat.id, '❌ Ошибка', reply_markup=get_admin_menu())


# ============================================================
# РАССЫЛКА ТЕКСТА
# ============================================================
@bot.message_handler(func=lambda m: m.from_user.id in broadcast_pending)
def broadcast_text_handler(message):
    tg_id = message.from_user.id
    broadcast_pending.pop(tg_id, None)
    text = message.text.strip()
    tg_username = message.from_user.username or message.from_user.first_name

    users = get_all_users_info(limit=10000)
    sent = 0
    failed = 0

    bot.send_message(message.chat.id,
        f'📤 Начинаю рассылку для {len(users)} пользователей...')

    for u in users:
        try:
            bot.send_message(u['tg_id'],
                f'📢 *Объявление:*\n\n{text}', parse_mode='Markdown')
            sent += 1
            time.sleep(0.05)
        except:
            failed += 1

    log_admin_action(tg_id, tg_username, 'broadcast_text',
                     f'sent={sent}, failed={failed}')

    bot.send_message(message.chat.id,
        f'✅ *Рассылка завершена!*\n\n📤 Отправлено: *{sent}*\n❌ Ошибок: *{failed}*',
        parse_mode='Markdown', reply_markup=get_admin_menu())


# ============================================================
# РАССЫЛКА ФОТО / ВИДЕО
# ============================================================
@bot.message_handler(
    func=lambda m: m.from_user.id in broadcast_photo_pending,
    content_types=['photo', 'video', 'document']
)
def broadcast_photo_handler(message):
    tg_id = message.from_user.id
    broadcast_photo_pending.pop(tg_id, None)
    tg_username = message.from_user.username or message.from_user.first_name

    file_id = None
    file_type = None
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = 'photo'
    elif message.video:
        file_id = message.video.file_id
        file_type = 'video'
    elif message.document:
        file_id = message.document.file_id
        file_type = 'document'

    if not file_id:
        bot.send_message(message.chat.id, '❌ Не удалось получить файл.')
        return

    caption = message.caption or ''
    users = get_all_users_info(limit=10000)
    sent = 0
    failed = 0

    bot.send_message(message.chat.id,
        f'📤 Начинаю рассылку для {len(users)} пользователей...')

    for u in users:
        try:
            if file_type == 'photo':
                bot.send_photo(u['tg_id'], file_id,
                    caption=caption if caption else None)
            elif file_type == 'video':
                bot.send_video(u['tg_id'], file_id,
                    caption=caption if caption else None)
            elif file_type == 'document':
                bot.send_document(u['tg_id'], file_id,
                    caption=caption if caption else None)
            sent += 1
            time.sleep(0.05)
        except:
            failed += 1

    log_admin_action(tg_id, tg_username, 'broadcast_photo',
                     f'sent={sent}, failed={failed}')

    bot.send_message(message.chat.id,
        f'✅ *Рассылка завершена!*\n\n📤 Отправлено: *{sent}*\n❌ Ошибок: *{failed}*',
        parse_mode='Markdown', reply_markup=get_admin_menu())


# ============================================================
# СОЗДАНИЕ ПРОМОКОДА
# ============================================================
@bot.message_handler(func=lambda m: m.from_user.id in promo_pending)
def promo_create_handler(message):
    tg_id = message.from_user.id
    promo_pending.pop(tg_id, None)
    tg_username = message.from_user.username or message.from_user.first_name

    parts = message.text.strip().split()
    if len(parts) < 3:
        bot.send_message(message.chat.id,
            '❌ *Формат:* `КОД ТИП СУММА [МАКС]`\n\n'
            'Пример: `WELCOME money 50000 100`',
            parse_mode='Markdown', reply_markup=get_promo_menu())
        return

    code = parts[0].strip().upper()
    rtype = parts[1].strip().lower()

    if rtype not in ['money', 'dp', 'vehicle']:
        bot.send_message(message.chat.id,
            '❌ Тип должен быть: `money`, `dp` или `vehicle`',
            parse_mode='Markdown', reply_markup=get_promo_menu())
        return

    try:
        rvalue = int(parts[2])
    except:
        bot.send_message(message.chat.id, '❌ Сумма должна быть числом.',
            reply_markup=get_promo_menu())
        return

    max_uses = 1
    if len(parts) >= 4:
        try:
            max_uses = int(parts[3])
        except:
            max_uses = 1

    if create_promo(code, rtype, rvalue, max_uses):
        log_admin_action(tg_id, tg_username, 'create_promo',
                         f'code={code}, type={rtype}, value={rvalue}, max={max_uses}')
        bot.send_message(message.chat.id,
            f'✅ *Промокод создан!*\n\n🎟 Код: `{code}`\n🎁 Тип: {rtype}\n'
            f'💰 Сумма: {rvalue:,}\n👥 Макс: {max_uses}',
            parse_mode='Markdown', reply_markup=get_promo_menu())
    else:
        bot.send_message(message.chat.id, '❌ Ошибка создания.',
            reply_markup=get_promo_menu())


# ============================================================
# УДАЛЕНИЕ ПРОМОКОДА
# ============================================================
@bot.message_handler(func=lambda m: m.from_user.id in promo_delete_pending)
def promo_delete_handler(message):
    tg_id = message.from_user.id
    promo_delete_pending.pop(tg_id, None)
    code = message.text.strip().upper()
    tg_username = message.from_user.username or message.from_user.first_name

    if delete_promo(code):
        log_admin_action(tg_id, tg_username, 'delete_promo', f'code={code}')
        bot.send_message(message.chat.id, f'✅ Промокод `{code}` удалён.',
            parse_mode='Markdown', reply_markup=get_promo_menu())
    else:
        bot.send_message(message.chat.id, '❌ Промокод не найден.',
            reply_markup=get_promo_menu())


# ============================================================
# ОТВЕТ НА ТИКЕТ
# ============================================================
@bot.message_handler(func=lambda m: m.from_user.id in ticket_reply)
def ticket_reply_handler(message):
    tg_id = message.from_user.id
    ticket_id = ticket_reply.pop(tg_id, None)
    if not ticket_id: return
    text = message.text.strip()
    tg_username = message.from_user.username or message.from_user.first_name
    add_ticket_message(ticket_id, tg_id, text, is_admin=1)
    ticket = get_ticket(ticket_id)
    if ticket:
        try:
            bot.send_message(ticket['tg_id'],
                f'💬 *Ответ по тикету #{ticket_id}:*\n\n{text}',
                parse_mode='Markdown')
        except: pass
    bot.send_message(message.chat.id, f'✅ Ответ отправлен.',
        reply_markup=get_admin_menu())


# ============================================================
# ДОБАВЛЕНИЕ АДМИНА
# ============================================================
@bot.message_handler(func=lambda m: m.from_user.id in admin_add_pending)
def admin_add_handler(message):
    tg_id = message.from_user.id
    admin_add_pending.pop(tg_id, None)
    parts = message.text.strip().split(maxsplit=1)
    if not parts: return
    try:
        new_id = int(parts[0])
        name = parts[1] if len(parts) > 1 else 'Админ'
        if add_admin(new_id, None, name, 5):
            bot.send_message(message.chat.id, f'✅ Админ `{new_id}` добавлен!',
                parse_mode='Markdown', reply_markup=get_admin_menu())
        else:
            bot.send_message(message.chat.id, '❌ Ошибка', reply_markup=get_admin_menu())
    except:
        bot.send_message(message.chat.id, '❌ TG ID должен быть числом',
            reply_markup=get_admin_menu())


# ============================================================
# /START
# ============================================================
@bot.message_handler(commands=['start'])
def start_command(message):
    tg_id = message.from_user.id
    tg_username = message.from_user.username or message.from_user.first_name
    if is_banned(tg_id):
        bot.send_message(message.chat.id, '🚫 Вы заблокированы.')
        return
    if is_muted(tg_id):
        bot.send_message(message.chat.id, '🔇 Вы в муте.')
        return
    register_user(tg_id, message.from_user.username, message.from_user.first_name,
                  message.from_user.last_name, message.from_user.language_code,
                  bool(getattr(message.from_user, 'is_premium', False)))
    print(f'👤 /start: {tg_username} ({tg_id})')
    is_admin_user = is_admin(tg_id)
    bot.send_message(message.chat.id,
        '👋 *TERY RP* — добро пожаловать!\n\n'
        'Используй кнопки ниже для навигации.',
        parse_mode='Markdown', reply_markup=get_main_menu(is_admin_user))


# ============================================================
# /BIND
# ============================================================
@bot.message_handler(commands=['bind'])
def bind_command(message):
    if is_banned(message.from_user.id) or is_muted(message.from_user.id):
        bot.send_message(message.chat.id, '🚫/🔇 Нет доступа.')
        return
    parts = message.text.split()
    if len(parts) < 3:
        bot.send_message(message.chat.id, '❌ `/bind ЛОГИН ПАРОЛЬ`', parse_mode='Markdown')
        return
    login, password = parts[1].strip(), parts[2].strip()
    if get_link(message.from_user.id):
        bot.send_message(message.chat.id, '⚠️ Уже привязан. `/unlink`', parse_mode='Markdown')
        return
    account = get_account(login)
    if not account:
        bot.send_message(message.chat.id, '❌ Аккаунт не найден.', parse_mode='Markdown')
        return
    if not check_password(password, account['password']):
        bot.send_message(message.chat.id, '❌ Неверный пароль.', parse_mode='Markdown')
        return
    tg_username = message.from_user.username or message.from_user.first_name
    if save_link(message.from_user.id, tg_username, account['static'], account['login']):
        bot.send_message(message.chat.id,
            f'✅ Привязан: `{account["login"]}`\n💰 {account["money"]:,} $\n💎 {account["dp"]} DP',
            parse_mode='Markdown', reply_markup=get_main_menu(is_admin(message.from_user.id)))


# ============================================================
# /UNLINK
# ============================================================
@bot.message_handler(commands=['unlink'])
def unlink_command(message):
    if not get_link(message.from_user.id):
        bot.send_message(message.chat.id, '⚠️ Нет привязки.')
        return
    delete_link(message.from_user.id)
    bot.send_message(message.chat.id, '✅ Отвязано.')


# ============================================================
# /ONLINE
# ============================================================
@bot.message_handler(commands=['online'])
def online_command(message):
    s = get_server_online_sync()
    if s:
        bot.send_message(message.chat.id,
            f'📡 *EXTRA DM*\n👥 {s["players"]}/{s["maxplayers"]}\n🏆 {s["peak"]}\n🕐 {datetime.now().strftime("%H:%M:%S")}',
            parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, '⚠️ Сервер не в мастер-листе.')


# ============================================================
# /STATS, /TOP, /BONUS, /PROMO, /TICKET, /HELP
# ============================================================
@bot.message_handler(commands=['stats'])
def stats_command(message):
    link = get_link(message.from_user.id)
    if not link:
        bot.send_message(message.chat.id, '❌ Сначала `/bind`.', parse_mode='Markdown')
        return
    acc = get_account(link['login'])
    if not acc:
        bot.send_message(message.chat.id, '❌ Ошибка.')
        return
    kd = round(acc['kills'] / max(acc['deaths'], 1), 2)
    bot.send_message(message.chat.id,
        f'📈 *{acc["login"]}*\n💰 {acc["money"]:,} $\n💎 {acc["dp"]} DP\n'
        f'⚔️ {acc["kills"]} | 💀 {acc["deaths"]} | 📊 K/D: {kd}\n🎯 Ур. {acc["glvl"]}',
        parse_mode='Markdown')


@bot.message_handler(commands=['top'])
def top_command(message):
    top = get_top_players('kills', 10)
    text = '🏆 *ТОП-10 по убийствам:*\n\n'
    for i, p in enumerate(top, 1):
        text += f'{i}. `{p["login"]}` — {p["kills"]} убийств\n'
    bot.send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(commands=['bonus'])
def bonus_command(message):
    success, reward, streak = claim_daily_bonus(message.from_user.id)
    if success:
        bot.send_message(message.chat.id,
            f'🎁 *Бонус получен!*\n💰 +{reward:,} $\n🔥 Серия: {streak}',
            parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, f'⏳ Через {reward} ч.')


@bot.message_handler(commands=['promo'])
def promo_command(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, '❌ `/promo КОД`', parse_mode='Markdown')
        return
    code = parts[1].strip().upper()
    success, result = use_promo(message.from_user.id, code)
    if success:
        bot.send_message(message.chat.id,
            f'✅ Промокод активирован!\n🎁 {result["reward_value"]:,} {result["reward_type"]}',
            parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, f'❌ {result}')


@bot.message_handler(commands=['ticket'])
def ticket_command(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id, '❌ `/ticket ТЕМА`', parse_mode='Markdown')
        return
    subject = parts[1].strip()
    tg_username = message.from_user.username or message.from_user.first_name
    link = get_link(message.from_user.id)
    login = link['login'] if link else None
    ticket_id = create_ticket(message.from_user.id, tg_username, login, subject)
    if ticket_id:
        bot.send_message(message.chat.id, f'✅ Тикет #{ticket_id} создан!', parse_mode='Markdown')


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id,
        '📋 *Команды:*\n\n'
        '/start — меню\n'
        '/bind ЛОГИН ПАРОЛЬ — привязать\n'
        '/unlink — отвязать\n'
        '/online — онлайн\n'
        '/stats — статистика\n'
        '/top — топ\n'
        '/bonus — бонус\n'
        '/promo КОД — промокод\n'
        '/ticket ТЕМА — тикет\n'
        '/help — помощь',
        parse_mode='Markdown')


# ============================================================
# АДМИН-КОМАНДЫ
# ============================================================
@bot.message_handler(commands=['unban'])
def unban_cmd(message):
    if not is_admin(message.from_user.id) or not authorized_admins.get(message.from_user.id):
        bot.send_message(message.chat.id, '❌')
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, '❌ `/unban TG_ID`', parse_mode='Markdown')
        return
    try:
        target = int(parts[1])
    except:
        bot.send_message(message.chat.id, '❌ TG ID числом.')
        return
    info = get_ban_by_tg_id(target)
    if not info:
        bot.send_message(message.chat.id, '⚠️ Не забанен.')
        return
    if unban_by_tg_id(target):
        bot.send_message(message.chat.id, f'✅ `{target}` разбанен.',
            parse_mode='Markdown', reply_markup=get_admin_menu())


@bot.message_handler(commands=['unbanall'])
def unbanall_cmd(message):
    if not is_admin(message.from_user.id) or not authorized_admins.get(message.from_user.id):
        bot.send_message(message.chat.id, '❌')
        return
    count = unban_all()
    bot.send_message(message.chat.id, f'✅ Снято: {count}', reply_markup=get_admin_menu())


@bot.message_handler(commands=['banlist'])
def banlist_cmd(message):
    if not is_admin(message.from_user.id) or not authorized_admins.get(message.from_user.id):
        bot.send_message(message.chat.id, '❌')
        return
    bans = get_banned_users(50)
    if not bans:
        bot.send_message(message.chat.id, '📭 Пусто.')
        return
    text = f'🚫 *Баны ({len(bans)}):*\n\n'
    for b in bans:
        text += f'• `{b["tg_id"]}` — {b["login"] or "-"}\n'
    if len(text) > 4000:
        text = text[:4000] + '...'
    bot.send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(commands=['find'])
def find_cmd(message):
    if not is_admin(message.from_user.id) or not authorized_admins.get(message.from_user.id):
        bot.send_message(message.chat.id, '❌')
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, '❌ `/find ЛОГИН`', parse_mode='Markdown')
        return
    login = parts[1].strip()
    u = find_user_by_login(login)
    if not u:
        bot.send_message(message.chat.id, '❌ Не найден.')
        return
    bot.send_message(message.chat.id,
        f'🔍 *{u["login"]}*\n📱 `{u["tg_id"]}`\n👤 @{u["tg_username"] or "-"}\n'
        f'📅 Зашёл: {u["first_seen"]}\n🕐 Был: {u["last_seen"]}',
        parse_mode='Markdown')


# ============================================================
# АКТИВНОСТЬ (ПОСЛЕДНИЙ!)
# ============================================================
@bot.message_handler(func=lambda m: True, content_types=['text'])
def update_activity(message):
    tg_id = message.from_user.id
    if message.text and message.text.startswith('/'):
        return
    register_user(tg_id, message.from_user.username, message.from_user.first_name,
                  message.from_user.last_name, message.from_user.language_code,
                  bool(getattr(message.from_user, 'is_premium', False)))


# ============================================================
# CALLBACK
# ============================================================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    tg_id = call.from_user.id
    tg_username = call.from_user.username or call.from_user.first_name

    if is_banned(tg_id):
        bot.answer_callback_query(call.id, '🚫 Забанены')
        return

    # === ГЛАВНОЕ МЕНЮ ===
    if call.data == 'ip':
        bot.send_message(chat_id, f'📡 `{SERVER_IP}`', parse_mode='Markdown',
            reply_markup=get_main_menu(is_admin(tg_id)))
        bot.answer_callback_query(call.id)

    elif call.data == 'online':
        s = get_server_online_sync()
        if s:
            bot.send_message(chat_id,
                f'📡 *EXTRA DM*\n👥 {s["players"]}/{s["maxplayers"]}\n🏆 {s["peak"]}\n🕐 {datetime.now().strftime("%H:%M:%S")}',
                parse_mode='Markdown', reply_markup=get_main_menu(is_admin(tg_id)))
        else:
            bot.send_message(chat_id, '⚠️ Не в мастер-листе.',
                reply_markup=get_main_menu(is_admin(tg_id)))
        bot.answer_callback_query(call.id)

    elif call.data == 'shop':
        show_shop(chat_id, tg_id)
        bot.answer_callback_query(call.id)

    elif call.data == 'profile':
        show_profile(chat_id, tg_id)
        bot.answer_callback_query(call.id)

    elif call.data == 'stats':
        link = get_link(tg_id)
        if not link:
            bot.send_message(chat_id, '❌ Сначала `/bind`.', parse_mode='Markdown',
                reply_markup=get_main_menu(is_admin(tg_id)))
        else:
            acc = get_account(link['login'])
            if acc:
                kd = round(acc['kills'] / max(acc['deaths'], 1), 2)
                bot.send_message(chat_id,
                    f'📈 *{acc["login"]}*\n💰 {acc["money"]:,} $\n💎 {acc["dp"]} DP\n'
                    f'⚔️ {acc["kills"]} | 💀 {acc["deaths"]} | 📊 K/D: {kd}\n🎯 Ур. {acc["glvl"]}',
                    parse_mode='Markdown', reply_markup=get_main_menu(is_admin(tg_id)))
        bot.answer_callback_query(call.id)

    elif call.data == 'top':
        top = get_top_players('kills', 10)
        text = '🏆 *ТОП-10 по убийствам:*\n\n'
        for i, p in enumerate(top, 1):
            text += f'{i}. `{p["login"]}` — {p["kills"]}\n'
        bot.send_message(chat_id, text, parse_mode='Markdown',
            reply_markup=get_main_menu(is_admin(tg_id)))
        bot.answer_callback_query(call.id)

    elif call.data == 'bonus':
        success, reward, streak = claim_daily_bonus(tg_id)
        if success:
            bot.send_message(chat_id, f'🎁 +{reward:,} $\n🔥 Серия: {streak}',
                parse_mode='Markdown', reply_markup=get_main_menu(is_admin(tg_id)))
        else:
            bot.send_message(chat_id, f'⏳ Через {reward} ч.',
                reply_markup=get_main_menu(is_admin(tg_id)))
        bot.answer_callback_query(call.id)

    elif call.data == 'promo':
        bot.send_message(chat_id, '🎫 Отправь: `/promo КОД`', parse_mode='Markdown',
            reply_markup=get_main_menu(is_admin(tg_id)))
        bot.answer_callback_query(call.id)

    elif call.data == 'ticket':
        bot.send_message(chat_id, '🆘 Отправь: `/ticket ТЕМА`', parse_mode='Markdown',
            reply_markup=get_main_menu(is_admin(tg_id)))
        bot.answer_callback_query(call.id)

    elif call.data == 'help':
        bot.send_message(chat_id,
            '📋 /start /bind /unlink /online /stats /top /bonus /promo /ticket /help',
            parse_mode='Markdown', reply_markup=get_main_menu(is_admin(tg_id)))
        bot.answer_callback_query(call.id)

    elif call.data == 'back_main':
        bot.send_message(chat_id, '🏠 Меню', reply_markup=get_main_menu(is_admin(tg_id)))
        bot.answer_callback_query(call.id)

    elif call.data.startswith('buy_'):
        buy_handler(call)

    # === АДМИН ===
    elif call.data == 'admin_auth':
        if not is_admin(tg_id):
            bot.answer_callback_query(call.id, '❌')
            return
        if authorized_admins.get(tg_id):
            bot.send_message(chat_id, '⚙️ *Админ-панель*',
                parse_mode='Markdown', reply_markup=get_admin_menu())
        else:
            bot.send_message(chat_id, '🔐 Отправь пароль.', parse_mode='Markdown')
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_logout':
        authorized_admins.pop(tg_id, None)
        bot.send_message(chat_id, '🚪 Вышли.', reply_markup=get_main_menu(is_admin(tg_id)))
        bot.answer_callback_query(call.id)

    elif call.data in ['admin_stats', 'admin_orders', 'admin_items', 'admin_users',
                       'admin_find', 'admin_bans', 'admin_mutes', 'admin_warns',
                       'admin_tickets', 'admin_promos', 'admin_promo_create',
                       'admin_promo_list', 'admin_promo_delete',
                       'admin_broadcast', 'admin_broadcast_photo', 'admin_add',
                       'admin_logs', 'admin_back', 'admin_unbanall', 'admin_unbanall_confirm'] \
         or call.data.startswith(('give_', 'reject_', 'admin_del_', 'askban_', 'askmute_',
                                   'askwarn_', 'unban_', 'unmute_', 'clearwarns_',
                                   'viewticket_', 'closeticket_', 'replyticket_')):

        if not is_admin(tg_id):
            bot.answer_callback_query(call.id, '❌')
            return
        if not authorized_admins.get(tg_id):
            bot.answer_callback_query(call.id, '🔐 Пароль!')
            return

        handle_admin_callback(call, chat_id, tg_id, tg_username)


# ============================================================
# ФУНКЦИИ
# ============================================================
def show_shop(chat_id, tg_id):
    items = get_shop_items()
    if not items:
        bot.send_message(chat_id, '🛒 Магазин пуст.')
        return
    cats = {}
    for it in items:
        cats.setdefault(it['category'], []).append(it)
    names = {'money': '💰 Валюта', 'vehicle': '🚗 Транспорт', 'donate': '💎 Донат'}
    text = '🛒 *Магазин*\n\n'
    markup = types.InlineKeyboardMarkup(row_width=1)
    for cat, its in cats.items():
        text += f'*{names.get(cat, cat)}:*\n'
        for it in its:
            text += f'• {it["name"]} — {it["price"]} ₽\n'
            markup.add(types.InlineKeyboardButton(f'{it["name"]} ({it["price"]}₽)',
                callback_data=f'buy_{it["id"]}'))
    markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='back_main'))
    bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)


def show_profile(chat_id, tg_id):
    link = get_link(tg_id)
    if not link:
        bot.send_message(chat_id, '👤 Нет привязки. `/bind`', parse_mode='Markdown')
        return
    acc = get_account(link['login'])
    if acc:
        bot.send_message(chat_id,
            f'👤 *{acc["login"]}*\n💰 {acc["money"]:,} $\n💎 {acc["dp"]} DP\n📅 {link["linked_at"]}',
            parse_mode='Markdown')


def buy_handler(call):
    chat_id = call.message.chat.id
    tg_id = call.from_user.id
    item_id = int(call.data.replace('buy_', ''))
    link = get_link(tg_id)
    if not link:
        bot.send_message(chat_id, '❌ Сначала `/bind`.', parse_mode='Markdown')
        bot.answer_callback_query(call.id)
        return
    items = get_shop_items()
    item = next((i for i in items if i['id'] == item_id), None)
    if not item:
        bot.answer_callback_query(call.id, 'Нет товара')
        return
    pid = create_purchase(tg_id, link['static'], link['login'], item['id'],
                          item['name'], item['price'])
    if pid:
        bot.send_message(chat_id,
            f'✅ Заявка #{pid}\n🛒 {item["name"]}\n💰 {item["price"]} ₽',
            parse_mode='Markdown', reply_markup=get_main_menu(is_admin(tg_id)))
        bot.answer_callback_query(call.id, '✅')
    else:
        bot.answer_callback_query(call.id, '❌')


def handle_admin_callback(call, chat_id, tg_id, tg_username):
    if call.data == 'admin_stats':
        s = get_bot_stats()
        bot.send_message(chat_id,
            f'📊 *Статистика:*\n\n👥 Юзеров: {s.get("users",0)}\n🔗 Привязано: {s.get("links",0)}\n'
            f'🛒 Товаров: {s.get("items",0)}\n📦 Покупок: {s.get("purchases",0)}\n'
            f'⏳ Ожидают: {s.get("pending",0)}\n👑 Админов: {s.get("admins",0)}\n'
            f'🚫 Банов: {s.get("bans",0)}\n🔇 Мутов: {s.get("mutes",0)}\n🎫 Тикетов: {s.get("tickets",0)}',
            parse_mode='Markdown', reply_markup=get_admin_menu())
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_orders':
        orders = get_purchases('pending', 20)
        if not orders:
            bot.send_message(chat_id, '📭 Нет заявок.', reply_markup=get_admin_menu())
        else:
            for o in orders:
                m = types.InlineKeyboardMarkup(row_width=2)
                m.add(
                    types.InlineKeyboardButton('✅', callback_data=f'give_{o["id"]}'),
                    types.InlineKeyboardButton('❌', callback_data=f'reject_{o["id"]}')
                )
                bot.send_message(chat_id,
                    f'📦 #{o["id"]}\n👤 `{o["login"]}`\n🛒 {o["item_name"]}\n💰 {o["price"]} ₽',
                    parse_mode='Markdown', reply_markup=m)
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_items':
        items = get_shop_items()
        text = '🛒 *Товары:*\n\n'
        m = types.InlineKeyboardMarkup(row_width=1)
        for it in items:
            text += f'• #{it["id"]} {it["name"]} — {it["price"]}₽\n'
            m.add(types.InlineKeyboardButton(f'❌ {it["name"]}',
                callback_data=f'admin_del_{it["id"]}'))
        m.add(types.InlineKeyboardButton('⬅️', callback_data='admin_back'))
        bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=m)
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_users':
        users = get_all_users_info(30)
        if not users:
            bot.send_message(chat_id, '📭 Пусто.', reply_markup=get_admin_menu())
            bot.answer_callback_query(call.id)
            return
        text = '👥 *Юзеры:*\n\n'
        m = types.InlineKeyboardMarkup(row_width=1)
        for u in users:
            b = []
            if u['is_admin']: b.append('👑')
            if u['is_banned']: b.append('🚫')
            if u['is_muted']: b.append('🔇')
            if u['has_warn']: b.append('⚠️')
            st = ' '.join(b) or '✅'
            name = u['login'] or u['tg_username'] or 'без имени'
            text += f'{st} *{name}* | `{u["tg_id"]}`\n'
            if u['is_banned']:
                m.add(types.InlineKeyboardButton(f'✅ Разбанить {name}',
                    callback_data=f'unban_{u["tg_id"]}'))
            else:
                m.add(types.InlineKeyboardButton(f'🚫 Забанить {name}',
                    callback_data=f'askban_{u["tg_id"]}'))
            if u['is_muted']:
                m.add(types.InlineKeyboardButton(f'🔊 Размутить {name}',
                    callback_data=f'unmute_{u["tg_id"]}'))
            else:
                m.add(types.InlineKeyboardButton(f'🔇 Замутить {name}',
                    callback_data=f'askmute_{u["tg_id"]}'))
            m.add(types.InlineKeyboardButton(f'⚠️ Варн {name}',
                callback_data=f'askwarn_{u["tg_id"]}'))
        m.add(types.InlineKeyboardButton('⬅️', callback_data='admin_back'))
        if len(text) > 4000:
            text = text[:4000] + '...'
        bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=m)
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_find':
        bot.send_message(chat_id, '🔍 Отправь: `/find ЛОГИН`',
            parse_mode='Markdown', reply_markup=get_admin_menu())
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_bans':
        bans = get_banned_users(30)
        if not bans:
            bot.send_message(chat_id, '📭 Нет банов.', reply_markup=get_admin_menu())
        else:
            text = '🚫 *Баны:*\n\n'
            m = types.InlineKeyboardMarkup(row_width=1)
            for b in bans:
                text += f'👤 `{b["login"] or "-"}` | `{b["tg_id"]}`\n📝 {b["reason"] or "-"}\n\n'
                m.add(types.InlineKeyboardButton(f'✅ Разбанить',
                    callback_data=f'unban_{b["tg_id"]}'))
            m.add(types.InlineKeyboardButton('🔓 Снять ВСЕ', callback_data='admin_unbanall'))
            m.add(types.InlineKeyboardButton('⬅️', callback_data='admin_back'))
            if len(text) > 4000:
                text = text[:4000] + '...'
            bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=m)
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_unbanall':
        m = types.InlineKeyboardMarkup(row_width=2)
        m.add(
            types.InlineKeyboardButton('✅ Да', callback_data='admin_unbanall_confirm'),
            types.InlineKeyboardButton('❌ Нет', callback_data='admin_back')
        )
        bot.send_message(chat_id, '⚠️ Снять ВСЕ баны?', reply_markup=m)
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_unbanall_confirm':
        count = unban_all()
        log_admin_action(tg_id, tg_username, 'unban_all', f'count={count}')
        bot.send_message(chat_id, f'✅ Снято: {count}', reply_markup=get_admin_menu())
        bot.answer_callback_query(call.id, '✅')

    elif call.data == 'admin_mutes':
        bot.send_message(chat_id, '🔇 Муты — управляй из списка юзеров.',
            reply_markup=get_admin_menu())
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_warns':
        bot.send_message(chat_id, '⚠️ Варны — управляй из списка юзеров.',
            reply_markup=get_admin_menu())
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_tickets':
        tickets = get_open_tickets(20)
        if not tickets:
            bot.send_message(chat_id, '📭 Тикетов нет.', reply_markup=get_admin_menu())
            bot.answer_callback_query(call.id)
            return
        for t in tickets:
            m = types.InlineKeyboardMarkup(row_width=3)
            m.add(
                types.InlineKeyboardButton('💬 Ответить', callback_data=f'replyticket_{t["id"]}'),
                types.InlineKeyboardButton('✅ Закрыть', callback_data=f'closeticket_{t["id"]}')
            )
            bot.send_message(chat_id,
                f'🎫 #{t["id"]}\n👤 `{t["login"] or t["tg_username"]}`\n📝 {t["subject"]}\n📅 {t["created_at"]}',
                parse_mode='Markdown', reply_markup=m)
        bot.answer_callback_query(call.id)

    # === ПРОМОКОДЫ ===
    elif call.data == 'admin_promos':
        promos = get_all_promos()
        text = '🎟 *Промокоды:*\n\n'
        if not promos:
            text = '📭 Промокодов нет.\n\nНажми "➕ Создать промокод"'
        else:
            for p in promos:
                text += (f'• `{p["code"]}` — {p["reward_value"]:,} {p["reward_type"]} '
                         f'({p["used_count"]}/{p["max_uses"]})\n')
        bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=get_promo_menu())
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_promo_create':
        promo_pending[tg_id] = True
        bot.send_message(chat_id,
            '📝 *Создание промокода*\n\n'
            'Отправь в формате: `КОД ТИП СУММА [МАКС]`\n\n'
            '*Примеры:*\n'
            '`WELCOME money 50000 100` — 50к $, 100 использований\n'
            '`BONUS dp 100 50` — 100 DP, 50 использований\n'
            '`VIPCAR vehicle 1 10` — машина, 10 использований\n\n'
            '*Типы:* `money`, `dp`, `vehicle`',
            parse_mode='Markdown')
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_promo_list':
        promos = get_all_promos()
        if not promos:
            bot.send_message(chat_id, '📭 Нет промокодов.', reply_markup=get_promo_menu())
        else:
            text = '🎟 *Промокоды:*\n\n'
            for p in promos:
                text += (f'• `{p["code"]}` — {p["reward_value"]:,} {p["reward_type"]}\n'
                         f'  Использовано: {p["used_count"]}/{p["max_uses"]}\n'
                         f'  Статус: {"✅" if p["is_active"] else "❌"}\n\n')
            if len(text) > 4000:
                text = text[:4000] + '...'
            bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=get_promo_menu())
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_promo_delete':
        promo_delete_pending[tg_id] = True
        bot.send_message(chat_id,
            '📝 Отправь код промокода для удаления:', parse_mode='Markdown')
        bot.answer_callback_query(call.id)

    # === РАССЫЛКА ===
    elif call.data == 'admin_broadcast':
        broadcast_pending[tg_id] = True
        bot.send_message(chat_id,
            '📢 *Рассылка текста*\n\nОтправь текст, который получат все пользователи бота.',
            parse_mode='Markdown')
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_broadcast_photo':
        broadcast_photo_pending[tg_id] = True
        bot.send_message(chat_id,
            '📸 *Рассылка фото*\n\nОтправь фото (можно с подписью), которое получат все пользователи бота.',
            parse_mode='Markdown')
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_add':
        admin_add_pending[tg_id] = True
        bot.send_message(chat_id, '📝 Отправь: `TG_ID Имя`', parse_mode='Markdown')
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_logs':
        logs = get_admin_logs(20)
        text = '📜 *Логи:*\n\n'
        for l in logs:
            text += f'👤 `{l["tg_username"] or l["tg_id"]}` — {l["action"]}\n📝 {l["details"] or "-"}\n🕐 {l["created_at"]}\n\n'
        if len(text) > 4000:
            text = text[:4000] + '...'
        bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=get_admin_menu())
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_back':
        bot.send_message(chat_id, '⚙️ Меню', reply_markup=get_admin_menu())
        bot.answer_callback_query(call.id)

    elif call.data.startswith('give_'):
        pid = int(call.data.replace('give_', ''))
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM bot_purchases WHERE id = %s', (pid,))
        o = cur.fetchone()
        cur.close()
        conn.close()
        if o:
            items = get_shop_items()
            it = next((i for i in items if i['id'] == o['item_id']), None)
            if it:
                give_item_to_player(o['static'], it['name'], it['category'])
            update_purchase_status(pid, 'completed')
            log_admin_action(tg_id, tg_username, 'give', f'#{pid}')
            bot.edit_message_text(f'✅ #{pid} выдан', call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, '✅')

    elif call.data.startswith('reject_'):
        pid = int(call.data.replace('reject_', ''))
        update_purchase_status(pid, 'rejected')
        log_admin_action(tg_id, tg_username, 'reject', f'#{pid}')
        bot.edit_message_text(f'❌ #{pid} отклонён', call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    elif call.data.startswith('admin_del_'):
        iid = int(call.data.replace('admin_del_', ''))
        delete_shop_item(iid)
        log_admin_action(tg_id, tg_username, 'del_item', f'#{iid}')
        bot.answer_callback_query(call.id, '✅')
        bot.send_message(chat_id, '✅ Удалён.', reply_markup=get_admin_menu())

    elif call.data.startswith('askban_'):
        target = int(call.data.replace('askban_', ''))
        ban_pending[tg_id] = target
        bot.send_message(chat_id, f'📝 Причина бана для `{target}`:', parse_mode='Markdown')
        bot.answer_callback_query(call.id)

    elif call.data.startswith('askmute_'):
        target = int(call.data.replace('askmute_', ''))
        mute_pending[tg_id] = (target, 24)
        bot.send_message(chat_id, f'📝 Причина мута для `{target}` (24ч):', parse_mode='Markdown')
        bot.answer_callback_query(call.id)

    elif call.data.startswith('askwarn_'):
        target = int(call.data.replace('askwarn_', ''))
        warn_pending[tg_id] = target
        bot.send_message(chat_id, f'📝 Причина варна для `{target}`:', parse_mode='Markdown')
        bot.answer_callback_query(call.id)

    elif call.data.startswith('unban_'):
        target = int(call.data.replace('unban_', ''))
        info = find_user_by_tg_id(target)
        static = info['static'] if info else None
        if unban_user_and_account(target, static):
            log_admin_action(tg_id, tg_username, 'unban', f'tg={target}')
            bot.answer_callback_query(call.id, '✅')
            bot.send_message(chat_id, f'✅ `{target}` разбанен.',
                parse_mode='Markdown', reply_markup=get_admin_menu())

    elif call.data.startswith('unmute_'):
        target = int(call.data.replace('unmute_', ''))
        unmute_user(target)
        log_admin_action(tg_id, tg_username, 'unmute', f'tg={target}')
        bot.answer_callback_query(call.id, '✅')
        bot.send_message(chat_id, f'✅ `{target}` размучен.',
            parse_mode='Markdown', reply_markup=get_admin_menu())

    elif call.data.startswith('replyticket_'):
        tid = int(call.data.replace('replyticket_', ''))
        ticket_reply[tg_id] = tid
        bot.send_message(chat_id, f'💬 Отправь ответ для тикета #{tid}:')
        bot.answer_callback_query(call.id)

    elif call.data.startswith('closeticket_'):
        tid = int(call.data.replace('closeticket_', ''))
        close_ticket(tid)
        log_admin_action(tg_id, tg_username, 'close_ticket', f'#{tid}')
        bot.edit_message_text(f'✅ Тикет #{tid} закрыт',
            call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, '✅')


# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == '__main__':
    try:
        print('🔄 Запуск...')
        print(f'🔐 Пароль: "{ADMIN_PASSWORD}"')
        print('📡 Ожидание...')
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f'❌ ОШИБКА: {e}')
        import traceback
        traceback.print_exc()
        input('Enter...')