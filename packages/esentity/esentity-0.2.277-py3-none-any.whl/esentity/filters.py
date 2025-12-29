#coding: utf-8
from flask import g, current_app
import os
import pendulum
from jinja2.exceptions import TemplateSyntaxError
from datetime import date
from json import dumps
from loguru import logger 
from urllib.parse import urlparse
from slugify import slugify 
import re


def func_format_date(s, format='LL'):
    if s:
        t = pendulum.instance(s) if isinstance(s, date) else pendulum.parse(s)
        try:
            return t.format(format, locale=g.language)
        except ValueError:
            logger.warning('func_format_date: Locale {0} not found'.format(g.language))
            return t.format(format, locale=current_app.config['BABEL_DEFAULT_LOCALE'])
    return ''

# @app.template_filter('format_number')
# def func_format_number(s):
#     if s:
#         s = str(s)
#         if s.isdecimal() and s.isdigit():
#             s = int(s)
#             if isinstance(s, int):
#                 return format_number(s, locale='en_IE')
#         return s
#     return ''

# @app.template_filter('currency')
# def func_currency(s, currency=None):
#     if s:
#         fn = func_format_number(s)

#         if currency == 'EUR':
#             return f'€{fn}'
#         elif currency == 'USD':
#             return f'${fn}'
#         elif currency == 'GBP':
#             return f'£{fn}'
#         elif currency in ['NOK', 'SEK', 'DKK']:
#             return f'{fn} kr'
#         elif currency == 'RUB':
#             return f'{fn} ₽'
#         elif currency in ['BTC']:
#             return f'{fn} {currency}'
#         elif currency == 'mBTC':
#             if s[-3:] == '000':
#                 return f'{str(int(int(s) / 1000))} BTC'
#             return f'{fn} mBTC'
#         else:
#             return s
#     return s

# @app.template_filter('rating')
# def func_rating(s):
# 	if s:
# 		return "{:.1f}".format(s)
# 	return '-'

# @app.template_filter('rate_star')
# def func_rate_star(s, half=False, max=5):
#     if s and not half:
#         return int(s) * ['active'] + (max-int(s)) * ['inactive']
#     if s and half:
#         _r = int(s) * ['active']
#         _d = float(s) - int(s)

#         _k = 0
#         if _d > 0:
#             _k = 1
#             if _d >= .5:
#                 _r += ['half']
#             else:
#                 _r += ['inactive']

#         return _r  + (max-_k-int(s)) * ['inactive']
#     return []

def inject_vars():
    def inject_static(file):
        file = os.path.join(current_app.root_path, file[1:])
        with open(file, 'r') as reader:
            return reader.read()

    now = pendulum.now('UTC')

    return dict(
            inject_static=inject_static,
            now=now,
            y=now.format('YYYY'),
            my=now.format('MMMM YYYY'),
            root=func_full_url(),
            locale_all=current_app.config['AVAILABLE_LOCALE'],
        )

def func_process_content(s):
    try:
        t = current_app.jinja_env.from_string(s)
        res = t.render(**inject_vars())
        return res
    except TemplateSyntaxError as e:
        logger.error(str(e))
    return s

def func_slugify(s):
	if s:
		return slugify(s).lower()
	return ''

def func_get_details(data, value, key='key', attr=None):
    if data and isinstance(data, list):
        for item in data:
            if item[key] == value:
                return item if not attr else item.get(attr)
    return {}

def func_escape_quotes(s):
    return dumps(s) if s else '""'

# @app.template_filter('b64')
# def func_b64(s):
#     return b64encode(dumps(s).encode('ascii')).decode('ascii')

def func_host(s):
    if s:
        return urlparse(s).hostname
    return ''

def func_normalize_path(s, lang):
    res = s.replace(f'/{lang}/', '/')
    return res

def func_to_plus(s):
    return f'{s}+' if str(s)[-2:] == '00' else s

def func_args_remove(s, args):
    uri = urlparse(s)
    return uri._replace(**args).geturl()

def func_toc_offset(s):
    _c = 0
    for c in s:
        if c in ['@']:
            _c += 1
        else:
            break
    return _c

def func_toc_format(s):
    return s[func_toc_offset(s):]

def func_full_url(path=''):
    s = current_app.config['PREFERRED_URL_SCHEME']
    h = current_app.config['DOMAIN']
    return f'{s}://{h}{path}'

def func_is_hexcolor(s):
    return re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', s)

def func_translate_entity(e, lang_code=None):
    if e.category == 'provider':
        if data := func_get_details(e.translations, lang_code or g.language, 'locale'):
            if data.get('is_active'):
                logger.info(f'Translate data in: {data}')
                for k in data.get('reset_list', []):
                    setattr(e, k, None)
                for k, v in data.items():
                    if k not in ['locale', 'is_active', 'reset_list']:
                        if v and isinstance(v, (str, list, int)):
                            setattr(e, k, v)
                e._doc = e._validate(e._doc)
                logger.info(f'Translate out: {e._doc}')
    return e

def func_format_color(s, default='transparent'):
    if s:
        if func_is_hexcolor(s):
            return s
        if len(s) == 6 and func_is_hexcolor(f'#{s}'):
            return f'#{s}'
    return default
