# ============================================================
# db.py - ВСЕ ФУНКЦИИ БАЗЫ ДАННЫХ
# ============================================================

import mysql.connector
from mysql.connector import Error
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# ПОДКЛЮЧЕНИЕ
# ============================================================
def get_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASS', ''),
            database=os.getenv('DB_NAME', 'bloodydmbd')
        )
    except Error as e:
        print(f'❌ Ошибка БД: {e}')
        return None


# ============================================================
# АККАУНТ
# ============================================================
def get_account(login):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT static, login, money, dp, password, regdate, kills, deaths, glvl '
            'FROM accounts WHERE login = %s', (login,)
        )
        return cursor.fetchone()
    except Error as e:
        print(f'❌ Ошибка: {e}')
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_account_by_static(static):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT static, login, money, dp, kills, deaths, glvl '
            'FROM accounts WHERE static = %s', (static,)
        )
        return cursor.fetchone()
    except Error as e:
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_top_players(order_by='kills', limit=10):
    conn = get_connection()
    if not conn:
        return []
    try:
        if order_by not in ['kills', 'money', 'dp', 'glvl']:
            order_by = 'kills'
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            f'SELECT login, money, dp, kills, deaths, glvl '
            f'FROM accounts ORDER BY {order_by} DESC LIMIT %s', (limit,)
        )
        return cursor.fetchall()
    except Error as e:
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def add_money(static, amount):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE accounts SET money = money + %s WHERE static = %s',
            (amount, static)
        )
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def add_dp(static, amount):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE accounts SET dp = dp + %s WHERE static = %s',
            (amount, static)
        )
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ============================================================
# ПОЛЬЗОВАТЕЛИ БОТА
# ============================================================
def register_user(tg_id, tg_username, first_name=None, last_name=None,
                  language_code=None, is_premium=False):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        tg_id = int(tg_id) if tg_id is not None else 0
        is_premium_int = 1 if is_premium else 0
        cursor.execute(
            'INSERT INTO bot_users '
            '(tg_id, tg_username, first_name, last_name, language_code, is_premium) '
            'VALUES (%s, %s, %s, %s, %s, %s) '
            'ON DUPLICATE KEY UPDATE '
            'tg_username = VALUES(tg_username), '
            'first_name = VALUES(first_name), '
            'last_name = VALUES(last_name), '
            'last_seen = NOW(), '
            'msg_count = msg_count + 1',
            (tg_id, tg_username, first_name, last_name, language_code, is_premium_int)
        )
        conn.commit()
        return True
    except Error as e:
        print(f'❌ Ошибка: {e}')
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def update_user_link(tg_id, static, login):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE bot_users SET static = %s, login = %s, linked_at = NOW() '
            'WHERE tg_id = %s', (static, login, tg_id)
        )
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def clear_user_link(tg_id):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE bot_users SET static = NULL, login = NULL, linked_at = NULL '
            'WHERE tg_id = %s', (tg_id,)
        )
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ============================================================
# МАГАЗИН
# ============================================================
def get_shop_items():
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM bot_shop_items WHERE is_active = 1 '
            'ORDER BY category, price'
        )
        return cursor.fetchall()
    except Error as e:
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def add_shop_item(name, description, category, price):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO bot_shop_items (name, description, category, price) '
            'VALUES (%s, %s, %s, %s)', (name, description, category, price)
        )
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def delete_shop_item(item_id):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bot_shop_items WHERE id = %s', (item_id,))
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def update_shop_item_price(item_id, new_price):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE bot_shop_items SET price = %s WHERE id = %s',
            (new_price, item_id)
        )
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ============================================================
# ПРИВЯЗКИ
# ============================================================
def save_link(tg_id, tg_username, static, login):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO bot_links (tg_id, tg_username, static, login) '
            'VALUES (%s, %s, %s, %s) '
            'ON DUPLICATE KEY UPDATE login = VALUES(login)',
            (tg_id, tg_username, static, login)
        )
        conn.commit()
        update_user_link(tg_id, static, login)
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_link(tg_id):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM bot_links WHERE tg_id = %s', (tg_id,))
        return cursor.fetchone()
    except Error as e:
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def delete_link(tg_id):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bot_links WHERE tg_id = %s', (tg_id,))
        conn.commit()
        clear_user_link(tg_id)
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ============================================================
# АДМИНЫ
# ============================================================
def is_admin(tg_id):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM bot_admins WHERE tg_id = %s', (tg_id,))
        return cursor.fetchone() is not None
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def add_admin(tg_id, tg_username=None, name=None, level=5):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO bot_admins (tg_id, tg_username, name, level) '
            'VALUES (%s, %s, %s, %s) '
            'ON DUPLICATE KEY UPDATE tg_username = VALUES(tg_username), '
            'name = VALUES(name), level = VALUES(level)',
            (tg_id, tg_username, name, level)
        )
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def remove_admin(tg_id):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bot_admins WHERE tg_id = %s', (tg_id,))
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ============================================================
# ПОКУПКИ
# ============================================================
def get_purchases(status=None, limit=20):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        if status:
            cursor.execute(
                'SELECT * FROM bot_purchases WHERE status = %s '
                'ORDER BY created_at DESC LIMIT %s', (status, limit)
            )
        else:
            cursor.execute(
                'SELECT * FROM bot_purchases ORDER BY created_at DESC LIMIT %s',
                (limit,)
            )
        return cursor.fetchall()
    except Error as e:
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def create_purchase(tg_id, static, login, item_id, item_name, price):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO bot_purchases '
            '(tg_id, static, login, item_id, item_name, price, status) '
            'VALUES (%s, %s, %s, %s, %s, %s, "pending")',
            (tg_id, static, login, item_id, item_name, price)
        )
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def update_purchase_status(purchase_id, status):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        if status == 'completed':
            cursor.execute(
                'UPDATE bot_purchases SET status = %s, completed_at = NOW() '
                'WHERE id = %s', (status, purchase_id)
            )
        else:
            cursor.execute(
                'UPDATE bot_purchases SET status = %s WHERE id = %s',
                (status, purchase_id)
            )
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def give_item_to_player(static, item_name, category):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        if category == 'money':
            amount = int(''.join(filter(str.isdigit, item_name))) or 0
            cursor.execute(
                'UPDATE accounts SET money = money + %s WHERE static = %s',
                (amount, static)
            )
        elif category == 'donate':
            amount = int(''.join(filter(str.isdigit, item_name))) or 0
            cursor.execute(
                'UPDATE accounts SET dp = dp + %s WHERE static = %s',
                (amount, static)
            )
        elif category == 'vehicle':
            cursor.execute('SELECT cars FROM accounts WHERE static = %s', (static,))
            row = cursor.fetchone()
            if row:
                try:
                    cars = json.loads(row[0]) if row[0] else []
                except:
                    cars = []
                cars.append({"m": item_name, "s": "shop"})
                cursor.execute(
                    'UPDATE accounts SET cars = %s WHERE static = %s',
                    (json.dumps(cars), static)
                )
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ============================================================
# СТАТИСТИКА
# ============================================================
def get_bot_stats():
    conn = get_connection()
    if not conn:
        return {}
    try:
        cursor = conn.cursor(dictionary=True)
        stats = {}
        cursor.execute('SELECT COUNT(*) as count FROM bot_users')
        stats['users'] = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM bot_links')
        stats['links'] = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM bot_shop_items WHERE is_active = 1')
        stats['items'] = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM bot_purchases')
        stats['purchases'] = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM bot_purchases WHERE status = 'pending'")
        stats['pending'] = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM bot_admins')
        stats['admins'] = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM bot_bans WHERE is_active = 1")
        stats['bans'] = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM bot_mutes WHERE is_active = 1")
        stats['mutes'] = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM bot_tickets WHERE status = 'open'")
        stats['tickets'] = cursor.fetchone()['count']
        return stats
    except Error as e:
        return {}
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ============================================================
# ЛОГИ
# ============================================================
def log_admin_action(tg_id, tg_username, action, details=''):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO bot_admin_logs (tg_id, tg_username, action, details) '
            'VALUES (%s, %s, %s, %s)', (tg_id, tg_username, action, details)
        )
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_admin_logs(limit=50):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM bot_admin_logs ORDER BY created_at DESC LIMIT %s',
            (limit,)
        )
        return cursor.fetchall()
    except Error as e:
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ============================================================
# БАНЫ
# ============================================================
def is_banned(tg_id):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM bot_bans WHERE tg_id = %s AND is_active = 1', (tg_id,)
        )
        return cursor.fetchone() is not None
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def ban_user_and_account(tg_id, tg_username, static, login, reason, banned_by, banned_by_name):
    conn = get_connection()
    if not conn:
        return False, 'Ошибка БД'
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO bot_bans '
            '(tg_id, tg_username, static, login, reason, banned_by, banned_by_name, is_active) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, 1) '
            'ON DUPLICATE KEY UPDATE reason = VALUES(reason), '
            'banned_by = VALUES(banned_by), banned_by_name = VALUES(banned_by_name), '
            'is_active = 1, banned_at = NOW()',
            (tg_id, tg_username, static, login, reason, banned_by, banned_by_name)
        )
        if static:
            cursor.execute(
                'INSERT INTO ban (static, player_name, admin_name, reason, ban_time, time_left, is_banned) '
                'VALUES (%s, %s, %s, %s, 0, 0, 1)',
                (static, login, banned_by_name, reason)
            )
        cursor.execute('DELETE FROM bot_links WHERE tg_id = %s', (tg_id,))
        cursor.execute(
            'UPDATE bot_users SET static = NULL, login = NULL, linked_at = NULL '
            'WHERE tg_id = %s', (tg_id,)
        )
        conn.commit()
        return True, 'OK'
    except Error as e:
        return False, str(e)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def unban_user_and_account(tg_id, static=None):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE bot_bans SET is_active = 0 WHERE tg_id = %s', (tg_id,))
        if static:
            cursor.execute(
                'UPDATE ban SET is_banned = 0 WHERE static = %s AND is_banned = 1',
                (static,)
            )
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def unban_by_tg_id(tg_id):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT static FROM bot_users WHERE tg_id = %s', (tg_id,))
        row = cursor.fetchone()
        static = row[0] if row else None
        cursor.execute('UPDATE bot_bans SET is_active = 0 WHERE tg_id = %s', (tg_id,))
        if static:
            cursor.execute(
                'UPDATE ban SET is_banned = 0 WHERE static = %s AND is_banned = 1',
                (static,)
            )
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def unban_all():
    conn = get_connection()
    if not conn:
        return 0
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM bot_bans WHERE is_active = 1')
        count = cursor.fetchone()[0]
        cursor.execute('UPDATE bot_bans SET is_active = 0 WHERE is_active = 1')
        cursor.execute('UPDATE ban SET is_banned = 0 WHERE is_banned = 1')
        conn.commit()
        return count
    except Error as e:
        return 0
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_ban_by_tg_id(tg_id):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM bot_bans WHERE tg_id = %s AND is_active = 1', (tg_id,)
        )
        return cursor.fetchone()
    except Error as e:
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_banned_users(limit=50):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM bot_bans WHERE is_active = 1 '
            'ORDER BY banned_at DESC LIMIT %s', (limit,)
        )
        return cursor.fetchall()
    except Error as e:
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ============================================================
# МУТЫ БОТА
# ============================================================
def is_muted(tg_id):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM bot_mutes WHERE tg_id = %s AND is_active = 1 '
            'AND (expires_at IS NULL OR expires_at > NOW())', (tg_id,)
        )
        return cursor.fetchone() is not None
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def mute_user(tg_id, reason, muted_by, muted_by_name, hours=None):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        expires = None
        if hours:
            expires = datetime.now() + timedelta(hours=hours)
        cursor.execute(
            'INSERT INTO bot_mutes (tg_id, reason, muted_by, muted_by_name, expires_at, is_active) '
            'VALUES (%s, %s, %s, %s, %s, 1) '
            'ON DUPLICATE KEY UPDATE reason = VALUES(reason), '
            'muted_by = VALUES(muted_by), muted_by_name = VALUES(muted_by_name), '
            'expires_at = VALUES(expires_at), is_active = 1, muted_at = NOW()',
            (tg_id, reason, muted_by, muted_by_name, expires)
        )
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def unmute_user(tg_id):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE bot_mutes SET is_active = 0 WHERE tg_id = %s', (tg_id,))
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ============================================================
# ВАРНЫ
# ============================================================
def warn_user(tg_id, reason, warned_by, warned_by_name):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO bot_warns (tg_id, reason, warned_by, warned_by_name) '
            'VALUES (%s, %s, %s, %s)', (tg_id, reason, warned_by, warned_by_name)
        )
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_user_warns(tg_id):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM bot_warns WHERE tg_id = %s ORDER BY warned_at DESC', (tg_id,)
        )
        return cursor.fetchall()
    except Error as e:
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def clear_warns(tg_id):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bot_warns WHERE tg_id = %s', (tg_id,))
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ============================================================
# ТИКЕТЫ
# ============================================================
def create_ticket(tg_id, tg_username, login, subject):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO bot_tickets (tg_id, tg_username, login, subject) '
            'VALUES (%s, %s, %s, %s)', (tg_id, tg_username, login, subject)
        )
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def add_ticket_message(ticket_id, tg_id, message, is_admin=0):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO bot_ticket_messages (ticket_id, tg_id, message, is_admin) '
            'VALUES (%s, %s, %s, %s)', (ticket_id, tg_id, message, is_admin)
        )
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_ticket(ticket_id):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM bot_tickets WHERE id = %s', (ticket_id,))
        return cursor.fetchone()
    except Error as e:
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_open_tickets(limit=20):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM bot_tickets WHERE status = 'open' "
            'ORDER BY created_at DESC LIMIT %s', (limit,)
        )
        return cursor.fetchall()
    except Error as e:
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_user_tickets(tg_id):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM bot_tickets WHERE tg_id = %s ORDER BY created_at DESC',
            (tg_id,)
        )
        return cursor.fetchall()
    except Error as e:
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_ticket_messages(ticket_id):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM bot_ticket_messages WHERE ticket_id = %s '
            'ORDER BY created_at ASC', (ticket_id,)
        )
        return cursor.fetchall()
    except Error as e:
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def close_ticket(ticket_id):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE bot_tickets SET status = "closed", closed_at = NOW() '
            'WHERE id = %s', (ticket_id,)
        )
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ============================================================
# ПРОМОКОДЫ
# ============================================================
def create_promo(code, reward_type, reward_value, max_uses=1):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO bot_promocodes (code, reward_type, reward_value, max_uses) '
            'VALUES (%s, %s, %s, %s) '
            'ON DUPLICATE KEY UPDATE reward_type = VALUES(reward_type), '
            'reward_value = VALUES(reward_value), max_uses = VALUES(max_uses), '
            'is_active = 1',
            (code, reward_type, reward_value, max_uses)
        )
        conn.commit()
        return True
    except Error as e:
        print(f'❌ Ошибка создания промокода: {e}')
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def use_promo(tg_id, code):
    conn = get_connection()
    if not conn:
        return False, 'Ошибка БД'
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM bot_promocodes WHERE code = %s AND is_active = 1', (code,)
        )
        promo = cursor.fetchone()
        if not promo:
            return False, 'Промокод не найден'
        if promo['used_count'] >= promo['max_uses']:
            return False, 'Промокод исчерпан'
        cursor.execute(
            'SELECT * FROM bot_promo_uses WHERE promo_id = %s AND tg_id = %s',
            (promo['id'], tg_id)
        )
        if cursor.fetchone():
            return False, 'Вы уже использовали этот промокод'
        cursor.execute(
            'INSERT INTO bot_promo_uses (promo_id, tg_id) VALUES (%s, %s)',
            (promo['id'], tg_id)
        )
        cursor.execute(
            'UPDATE bot_promocodes SET used_count = used_count + 1 WHERE id = %s',
            (promo['id'],)
        )
        conn.commit()
        return True, promo
    except Error as e:
        return False, str(e)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_all_promos():
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM bot_promocodes ORDER BY created_at DESC')
        return cursor.fetchall()
    except Error as e:
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def delete_promo(code):
    """Удаляет промокод по коду."""
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bot_promocodes WHERE code = %s', (code,))
        conn.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f'❌ Ошибка удаления промокода: {e}')
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ============================================================
# ЕЖЕДНЕВНЫЙ БОНУС
# ============================================================
def claim_daily_bonus(tg_id):
    conn = get_connection()
    if not conn:
        return False, 0, 0
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM bot_daily_bonus WHERE tg_id = %s', (tg_id,))
        row = cursor.fetchone()

        if row and row['last_claim']:
            delta = datetime.now() - row['last_claim']
            if delta.total_seconds() < 86400:
                hours = int((86400 - delta.total_seconds()) // 3600)
                return False, hours, row['streak']

        if row and row['last_claim']:
            delta = datetime.now() - row['last_claim']
            new_streak = row['streak'] + 1 if delta.total_seconds() < 172800 else 1
        else:
            new_streak = 1

        reward = 10000 + (new_streak - 1) * 5000
        if reward > 100000:
            reward = 100000

        if row:
            cursor.execute(
                'UPDATE bot_daily_bonus SET last_claim = NOW(), streak = %s '
                'WHERE tg_id = %s', (new_streak, tg_id)
            )
        else:
            cursor.execute(
                'INSERT INTO bot_daily_bonus (tg_id, last_claim, streak) '
                'VALUES (%s, NOW(), %s)', (tg_id, new_streak)
            )
        conn.commit()
        return True, reward, new_streak
    except Error as e:
        return False, 0, 0
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ============================================================
# IP
# ============================================================
def save_user_ip(tg_id, ip):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO bot_user_ips (tg_id, ip) VALUES (%s, %s) '
            'ON DUPLICATE KEY UPDATE ip = VALUES(ip)', (tg_id, ip)
        )
        conn.commit()
        return True
    except Error as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ============================================================
# СПИСКИ
# ============================================================
def get_all_users_info(limit=50):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f'''
            SELECT 
                u.tg_id, u.tg_username, u.first_name, u.last_name,
                u.login, u.static, u.first_seen, u.last_seen, u.msg_count,
                ip.ip AS user_ip, a.money, a.dp,
                CASE WHEN adm.tg_id IS NOT NULL THEN 1 ELSE 0 END AS is_admin,
                CASE WHEN b.tg_id IS NOT NULL AND b.is_active = 1 THEN 1 ELSE 0 END AS is_banned,
                CASE WHEN m.tg_id IS NOT NULL AND m.is_active = 1 THEN 1 ELSE 0 END AS is_muted,
                CASE WHEN w.tg_id IS NOT NULL THEN 1 ELSE 0 END AS has_warn
            FROM bot_users u
            LEFT JOIN bot_user_ips ip ON u.tg_id = ip.tg_id
            LEFT JOIN accounts a ON u.static = a.static
            LEFT JOIN bot_admins adm ON u.tg_id = adm.tg_id
            LEFT JOIN bot_bans b ON u.tg_id = b.tg_id
            LEFT JOIN bot_mutes m ON u.tg_id = m.tg_id
            LEFT JOIN bot_warns w ON u.tg_id = w.tg_id
            ORDER BY u.last_seen DESC
            LIMIT {int(limit)}
        ''')
        return cursor.fetchall()
    except Error as e:
        print(f'❌ Ошибка списка: {e}')
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def find_user_by_login(login):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM bot_users WHERE login = %s LIMIT 1', (login,)
        )
        return cursor.fetchone()
    except Error as e:
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def find_user_by_tg_id(tg_id):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM bot_users WHERE tg_id = %s', (tg_id,))
        return cursor.fetchone()
    except Error as e:
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()