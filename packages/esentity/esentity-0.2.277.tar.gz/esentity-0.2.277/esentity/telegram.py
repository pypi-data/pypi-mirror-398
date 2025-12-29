#coding: utf-8
import requests
from loguru import logger
from base64 import b64encode, decodebytes
from esentity.models import TelegramBot
import tempfile
from datetime import datetime
from json import dumps
from boto3 import session as boto_session
from boto3.s3.transfer import TransferConfig
from base64 import decodebytes
import hashlib
import pendulum
from flask import current_app


def telegram_api(token, method, json={}):
    # logger.info(f'Telegram {method} request data: {json}')
    r = requests.post(f'https://api.telegram.org/bot{token}/{method}', json=json)
    if r.status_code == 200:
        _res = r.json()
        logger.info(f'Telegram {method} response: {_res}')
        return _res
    else:
        logger.info(f'Telegram {method} response code: {r.status_code}, response: {r.content}')
    return {}


def telegram_getMe(token):
    res = telegram_api(token, 'getMe')
    if res['ok']:
        return {
            'bot_id': res['result']['id'],
            'first_name': res['result']['first_name'],
            'username': res['result']['username'],
            'can_join': res['result']['can_join_groups'],
            'can_read': res['result']['can_read_all_group_messages'],
        }                
    return {}


def telegram_setWebhook(token, url):
    res = telegram_api(token, 'setWebhook', {'url': url, 'drop_pending_updates': True})


def telegram_getChatAdministrators(token, chat):
    res = telegram_api(token, 'getChatAdministrators', {'chat_id': chat})
    if 'ok' in res and res['ok']:
        return [str(item['user']['id']) for item in res['result'] if item['user']['is_bot']]
    return []


def telegram_getChat(token, chat):
    res = telegram_api(token, 'getChat', {'chat_id': chat})
    if res.get('ok'):
        _res = {
            'chat_id': res['result']['id'],
            'title': res['result']['title'],
            'type': res['result']['type'],
            'linked_chat': res['result'].get('linked_chat_id'),
        }
        if 'permissions' in res['result']:
            _res['can_send'] = res['result']['permissions']['can_send_messages']
            _res['can_invite'] = res['result']['permissions']['can_invite_users']
        if 'photo' in res['result']:
            res_photo = telegram_api(token, 'getFile', {'file_id': res['result']['photo']['small_file_id']})
            if res_photo.get('ok'):
                r = requests.get(f"https://api.telegram.org/file/bot{token}/{res_photo['result']['file_path']}")
                if r.status_code == 200:
                    _res['photo'] = b64encode(r.content).decode()
        return _res                
    return {}


def telegram_checkChat(_doc):
    _res = {}
    _err = {}
    bots, found = TelegramBot.get(username=_doc['bot_admin'])
    if found == 1:
        bot = bots.pop()

        chat_id = f"@{_doc['username']}"
        _admins = telegram_getChatAdministrators(bot.token, chat_id)
        if bot.bot_id in _admins:
            telegram_api(bot.token, 'setChatTitle', {'chat_id': chat_id, 'title': _doc['title']})
            telegram_api(bot.token, 'setChatDescription', {'chat_id': chat_id, 'description': _doc['description'] or ''})
            if _doc['photo']:
                telegram_setChatPhoto(bot.token, chat_id, _doc['photo'])
            telegram_api(bot.token, 'setChatPermissions', {'chat_id': chat_id, 'permissions': {
                'can_send_messages': _doc['can_send'],
                'can_invite_users': _doc['can_invite'],
            }})
            _res = telegram_getChat(bot.token, chat_id)
            _res.update(telegram_getChatMemberCount(bot.token, chat_id))
        else:
            _err = {
                'username': 'No access to chat'
            }
    else:
        _err = {
            'bot_admin': 'Bot not found'
        }
    return _res, _err


def telegram_getChatMemberCount(token, chat):
    res = telegram_api(token, 'getChatMemberCount', {'chat_id': chat})
    if 'ok' in res and res['ok']:
        _res = {
            'count': res['result'],
        }
        return _res                
    return {}


def telegram_setChatPhoto(token, chat, photo):
    with tempfile.NamedTemporaryFile() as tmp:
        raw = photo.split(',')[-1]
        tmp.write(decodebytes(raw.encode()))
        tmp.seek(0)

        r = requests.post(f'https://api.telegram.org/bot{token}/setChatPhoto', {'chat_id': chat}, files={'photo': tmp})
        if r.status_code == 200:
            _res = r.json()
            logger.info(f'Telegram setChatPhoto response: {_res}')
            return _res
        else:
            logger.info(f'Telegram setChatPhoto response code: {r.status_code}, response: {r.content}')


def telegram_sendMessage(token, chat, text, disable_notify=True, disable_preview=False, inline_keyboard=[]):
    res = telegram_api(token, 'sendMessage', {
        'chat_id': chat, 
        'text': text, 
        'parse_mode': 'HTML', 
        'disable_notification': disable_notify, 
        'link_preview_options': {
            'is_disabled': disable_preview
        },    
        'reply_markup': dumps({
            'inline_keyboard': inline_keyboard,
        }),            
    })
    if res.get('ok'):
        _res = {
            'publishedon': datetime.utcfromtimestamp(res['result']['date']),
            'chat_id': res['result']['chat']['id'],
            'chat_username': res['result']['chat']['username'],
            'message_id': res['result']['message_id'],
            'raw': res['result']['text'],
        }
        if 'from' in res['result']:
            _res['sender_id'] = res['result']['from']['id']
            _res['sender_username'] = res['result']['from']['username']
        elif 'sender_chat' in res['result']:
            _res['sender_id'] = res['result']['sender_chat']['id']
            _res['sender_username'] = res['result']['sender_chat']['username']

        return _res                
    return {}


def telegram_editMessageText(token, chat, message, text, disable_notify=True, disable_preview=False, inline_keyboard=[]):
    res = telegram_api(token, 'editMessageText', {
        'chat_id': chat, 
        'message_id': message, 
        'text': text, 
        'parse_mode': 'HTML', 
        'disable_notification': disable_notify, 
        'link_preview_options': {
            'is_disabled': disable_preview
        },
        'reply_markup': dumps({
            'inline_keyboard': inline_keyboard,
        }),            
    })
    if res.get('ok'):
        _res = {
            'publishedon': datetime.utcfromtimestamp(res['result']['date']),
            'chat_id': res['result']['chat']['id'],
            'chat_username': res['result']['chat']['username'],
            'message_id': res['result']['message_id'],
            'raw': res['result']['text'],
        }
        if 'from' in res['result']:
            _res['sender_id'] = res['result']['from']['id']
            _res['sender_username'] = res['result']['from']['username']
        elif 'sender_chat' in res['result']:
            _res['sender_id'] = res['result']['sender_chat']['id']
            _res['sender_username'] = res['result']['sender_chat']['username']

        return _res                
    return {}


def telegram_sendPhoto(token, chat, caption, photo, disable_notify=True, inline_keyboard=[]):
    r = requests.post(f'https://api.telegram.org/bot{token}/sendPhoto', {
        'chat_id': chat, 
        'caption': caption, 
        'parse_mode': 'HTML', 
        'disable_notification': disable_notify,
        'reply_markup': dumps({
            'inline_keyboard': inline_keyboard,
        }),            
    }, files={'photo': photo})
    if r.status_code == 200:
        res = r.json()
        logger.info(f'Telegram sendPhoto response: {res}')
        if res.get('ok'):
            _res = {
                'publishedon': datetime.utcfromtimestamp(res['result']['date']),
                'chat_id': res['result']['chat']['id'],
                'chat_username': res['result']['chat']['username'],
                'message_id': res['result']['message_id'],
                'raw': res['result'].get('caption'),
            }
            if 'from' in res['result']:
                _res['sender_id'] = res['result']['from']['id']
                _res['sender_username'] = res['result']['from']['username']
            elif 'sender_chat' in res['result']:
                _res['sender_id'] = res['result']['sender_chat']['id']
                _res['sender_username'] = res['result']['sender_chat']['username']
            return _res                
    else:
        logger.info(f'Telegram sendPhoto response code: {r.status_code}, response: {r.content}')
    return {}


def telegram_editMessageMedia(token, chat, message, photo, text, inline_keyboard=[]):
    media = {'type': 'photo', 'caption': text, 'parse_mode': 'HTML', 'media': 'attach://photo'}
    r = requests.post(f'https://api.telegram.org/bot{token}/editMessageMedia', {
        'chat_id': chat, 
        'message_id': message, 
        'media': dumps(media),
        'reply_markup': dumps({
            'inline_keyboard': inline_keyboard,
        }),            
    }, files={'photo': photo})
    if r.status_code == 200:
        res = r.json()
        logger.info(f'Telegram editMessageMedia response: {res}')
        if res.get('ok'):
            _res = {
                'publishedon': datetime.utcfromtimestamp(res['result']['date']),
                'chat_id': res['result']['chat']['id'],
                'chat_username': res['result']['chat']['username'],
                'message_id': res['result']['message_id'],
                'raw': res['result'].get('caption'),
            }
            if 'from' in res['result']:
                _res['sender_id'] = res['result']['from']['id']
                _res['sender_username'] = res['result']['from']['username']
            elif 'sender_chat' in res['result']:
                _res['sender_id'] = res['result']['sender_chat']['id']
                _res['sender_username'] = res['result']['sender_chat']['username']
            return _res   
    else:
        logger.info(f'Telegram editMessageMedia response code: {r.status_code}, response: {r.content}')
    return {}


def build_jobs(bot, chats):
    return {
        'token': bot.token, 
        'modules': bot.modules,
        'jobs': {item.chat_id: {
            'job_remove_system_msg': item.job_remove_system_msg
        } for item in chats},
    }


def telegram_bot_updated(sender, **kwargs):
    logger.info('TelegramBot.on_put Signal: {0}, data: {1}'.format(sender.username, kwargs))
    key = f'{sender.domain}:{sender._id}'
    if sender.is_active:
        chats, _ = TelegramChat.get(bot_admin=sender.username, is_active=True)
        _jobs = build_jobs(sender, chats)
        app.redis.hset('tg_webhooks', key, dumps(_jobs))
        logger.info(f'Job for {key} updated: {_jobs}')
    else:
        app.redis.hdel('tg_webhooks', key)
        logger.info(f'Job for {key} removed')


def telegram_chat_updated(sender, **kwargs):
    logger.info('TelegramChat.on_put Signal: {0}, data: {1}'.format(sender.username, kwargs))
    bots, total_bots = TelegramBot.get(username=sender.bot_admin)
    if total_bots > 0:
        bot = bots.pop()
        if bot.is_active:
            key = f'{bot.domain}:{bot._id}'
            chats, _ = TelegramChat.get(bot_admin=sender.bot_admin, is_active=True)
            _jobs = build_jobs(bot, chats)
            app.redis.hset('tg_webhooks', key, dumps(_jobs))
            logger.info(f'Job for {key} updated: {_jobs}')        


def telegram_message_updated(sender, **kwargs):
    if 'data:' in sender.photo:
        with tempfile.NamedTemporaryFile() as tmp:
            meta, raw = sender.photo.split(',')
            tmp.write(decodebytes(raw.encode()))
            tmp.seek(0)

            sha1 = hashlib.sha1()
            sha1.update(raw.encode())
            _hash = sha1.hexdigest()

            now = pendulum.now('UTC')
            file_key = f'messages/{now.to_date_string()}/{_hash}'

            s = boto_session.Session()
            config = TransferConfig(use_threads=False)
            client = s.client('s3', 
                endpoint_url=current_app.config['MINIO_ENDPOINT'], 
                aws_access_key_id=current_app.config['MINIO_ACCESS_KEY'],
                aws_secret_access_key=current_app.config['MINIO_SECRET_KEY']
            )
            client.upload_fileobj(tmp, current_app.config['MINIO_BUCKET'], file_key, Config=config, ExtraArgs={'ContentType': meta.replace('data:', '').replace('base64', '')})
            sender.photo = file_key            