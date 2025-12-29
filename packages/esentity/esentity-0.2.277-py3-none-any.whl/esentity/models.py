#coding:utf-8
from flask import current_app, url_for, request, g
from flask_login import AnonymousUserMixin, current_user
from pydantic.types import constr
from user_agents import parse
from blinker import Signal
from datetime import datetime, date
from slugify import slugify 
from loguru import logger
from json import dumps, loads
from urllib.parse import unquote
import random
import string
import dateutil.parser
import hashlib
import pycountry
import os
import re
import hashlib
import shortuuid
import pendulum
from pydantic import BaseModel, validator, EmailStr, conint, conlist, HttpUrl, Field
from typing import Optional, List
from cryptography.fernet import Fernet
from typing import Union
from billiard.process import current_process
from copy import copy

class UndefinedEntityAttribute(Exception):
    pass


class DateTimeField(list):
    pass


class BaseEntity(object):
    _schemas = {}
    _doc = {}
    _id = None

    def _validate(self, doc):
        res = dict()

        # remove not schema attrs
        for k, v in doc.items():
            if k in self._schemas.keys():
                res[k] = v

        doc = res

        for k in self._schemas.keys():
            v = doc.get(k)
            try:
                res[k] = self.__class__.format_attribute(v, self._schemas[k])
            except Exception as e:
                logger.error('Attribute ({0}): {1}'.format(k, str(e)))
                raise e

        return res

    def __init__(self, doc, _id):
        self._doc = self._validate(doc)
        self._id = _id

    def __repr__(self):
        return self._id

    def __getattr__(self, item):
        if item in self._schemas.keys():
            return self._doc.get(item, '')
        elif item in ['__html__']:
            raise AttributeError
        elif item in ['__func__', '__self__']:
            pass
        else:
            raise UndefinedEntityAttribute(item)

    def __setattr__(self, item, value):
        if item in self._schemas.keys():
            self._doc[item] = value
        else:
            self.__dict__[item] = value

    def get_list_value(self, attr, key, value, field=None):
        if isinstance(self._doc[attr], list):
            for item in self._doc[attr]:
                if item.get(key) == value:
                    return item.get(field) if field else item
        return None
    
    def set_list_value(self, attr, key, value, _doc, _force=False):
        if isinstance(self._doc[attr], list):
            _found = False

            for item in self._doc[attr]:
                if item.get(key) == value:
                    for k, v in _doc.items():
                        item[k] = v
                    _found = True
                    break
            
            if not _found and _force:
                _res = {key: value, 'is_active': True}
                self._doc[attr].append(dict(_res, **_doc))
        return self._doc[attr]

    def to_dict(self):
        return self._doc    

    # CLASS METHODS
    @classmethod
    def get_random_string(cls, _len):
        return "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(_len)) 

    @classmethod
    def get_urlsafe_string(cls, _len):
        return shortuuid.ShortUUID().random(length=_len)

    @classmethod
    def format_attribute(cls, v, t):
        res = None

        if t == str:
            if isinstance(v, list):
                res = ", ".join(v)
            else:
                res = str(v).strip() if v else ''
        elif t == DateTimeField:
            if v:
                if isinstance(v, (date, datetime)):
                    res = v
                else:
                    res = dateutil.parser.isoparse(v)
        elif t == bool:
            res = bool(v)
        elif t == int:
            res = int(v) if v or v == 0 else None
        elif t == float:
            res = float(v) if v or v == 0 else None
        elif t == list:
            if v:
                v = v if type(v) == list else v.split(',')
                res = [item.strip() if type(item) in [str] else item for item in v]
            else:
                res = list()
        elif t == dict:
            if type(v) == dict:
                res = v
            else:
                res = dict()

        return res    


class ElasticEntity(BaseEntity):
    on_ready = Signal()
    on_pre_put = Signal()
    on_put = Signal()
    on_delete = Signal()

    _score = 0

    @classmethod
    def generate_id(cls, *args):
        return hashlib.sha224(":".join([str(item) for item in args]).encode('utf-8')).hexdigest()

    @classmethod
    def _table(cls):
        return "{0}.v1".format(cls.__name__.lower())

    @classmethod
    def get(cls, _id=None, _count=10, _offset=0, _sort=[], _process=True, _source=None, _include=[], _exclude=[], _exclude_params={}, _all=False, _random=False, _range=None, _query=None, _query_fields=[], **kwargs):
        if _id:
            resp = current_app.es.get(index=cls._table(), id=_id, ignore=[400, 404])
            # logger.debug(u'GET: {0}'.format(resp))
            if resp.get('found'):
                doc = resp['_source']
                if doc:
                    obj = cls(doc, _id)
                    cls.on_ready.send(obj)
                    return [obj], 1
        elif not _id:
            def pre_field(k, v):
                return k if isinstance(v, (bool, int)) else '{0}.keyword'.format(k)

            must_not = []
            must = [{"terms" if isinstance(v, list) else "term": {pre_field(k, v): v}} for k, v in kwargs.items()]

            def process_range(item):
                _f, _s, _e, _tz = item
                _rvalue = {"gte": _s, "lte": _e}
                if _tz:
                    _rvalue["time_zone"] = _tz
                must.append({"range": {_f: _rvalue}})

            if _range:
                if isinstance(_range, tuple):
                    process_range(_range)
                elif isinstance(_range, dict):
                    for k, v in _range.items():
                        __v = []
                        for _v in v:
                            _s = {}
                            _min, _max = _v
                            if _min != None:
                                _s['gte'] = _min
                            if _max != None:
                                _s['lte'] = _max
                            __v.append({'range': {k: _s}})
                        if __v:
                            must.append({'bool': {'should': __v}})

            if _query_fields and _query:
                must.append({
                    'multi_match': {
                        'query': _query,
                        'fields': _query_fields,
                        'operator': 'and',
                    }
                })
                
            if _include:
                must.append({'ids': {'values': _include}})

            qbool = {
                "must": must,
            }

            if _exclude_params:
                for k, v in _exclude_params.items():
                    must_not.append({"terms" if isinstance(v, list) else "term": {pre_field(k, v): v}})
            if _exclude:
                must_not.append({'ids': {'values': _exclude}})
            if must_not:
                qbool['must_not'] = must_not

            # logger.info(f'Query: {qbool}')

            if _random:
                def get_func():
                    flist = []
                    flist.append({
                        "random_score": {
                            "field": "_seq_no"
                        }
                    })
                    return flist

                q = {
                    "query": {
                        "function_score": {
                            "query": {
                                "bool": qbool
                            },
                            "boost": 1,
                            "boost_mode": "multiply",
                            "functions": get_func()
                        }
                    },
                    "size": _count,
                    "sort" : _sort,
                }
            else:
                q = {
                    "query": {
                        "bool": qbool
                    },
                    "size": _count,
                    "from": _offset,
                    "sort" : _sort,
                }
                
            if _source != None:
                q['_source'] = _source

            res = []
            found = 0

            if _all:
                _sid = None

                while True:
                    if _sid:
                        resp = current_app.es.scroll(scroll_id=_sid, scroll='20m') 
                    else:
                        q['size'] = 10000
                        # logger.debug(f'REQUEST: {q}')
                        resp = current_app.es.search(index=cls._table(), body=q, request_timeout=60, scroll='20m', ignore=[400, 404])
                        # logger.debug(f'RESPONSE: {resp}')

                    _sid = resp.get('_scroll_id')
                    if _sid is None or len(resp['hits']['hits']) == 0:
                        break

                    res += cls.process(resp['hits']['hits']) if _process else cls.format_source(resp['hits']['hits'])
                    found = resp['hits']['total']['value']

                if _sid:
                    resp = current_app.es.clear_scroll(scroll_id=_sid)
                    logger.debug(f'Scroll cleared: {resp}')
            else:
                # logger.debug(f'REQUEST: {q}')
                resp = current_app.es.search(index=cls._table(), body=q, request_timeout=60, ignore=[400, 404], track_total_hits=True)
                # logger.debug(f'RESPONSE: {resp}')

                if 'status' in resp and resp['status'] in [400, 404]:
                    return [], 0

                logger.debug(u'RESPONSE took: {0}'.format(resp['took']))

                res = cls.process(resp['hits']['hits']) if _process else cls.format_source(resp['hits']['hits'])
                found = resp['hits']['total']['value']
            return res, found
        return [], 0

    @classmethod
    def get_one(cls, **kwargs):
        objs, found = cls.get(**kwargs)
        if found == 1:
            return objs.pop()

    @classmethod
    def process(cls, data):
        logger.debug(u'START process result')
        res = []
        for item in data:
            obj = cls(item['_source'], item['_id'])
            obj._score = item['_score']
            cls.on_ready.send(obj)
            res.append(obj)
        logger.debug(u'END process result')
        return res

    @classmethod
    def format_source(cls, data):
        res = []
        for item in data:
            if '_source' in item:
                for k, v in cls._schemas.items():
                    if k in item['_source'] and item['_source'][k]:
                        if v == DateTimeField and '+' not in item['_source'][k]:
                            item['_source'][k] = f"{item['_source'][k]}Z"
            res.append(item)
        return res

    @classmethod
    def put(cls, _id, doc, _refresh=True, _signal=True):
        obj = cls(doc, _id)
        if _signal:
            cls.on_pre_put.send(obj)
        resp = current_app.es.update(index=cls._table(), id=obj._id, body={'doc': obj.to_dict(), 'doc_as_upsert': True}, refresh=_refresh, retry_on_conflict=3)
        logger.debug(u'PUT: {0}'.format(resp))
        if _signal:
            def process_doc(_d):
                _p = copy(_d)
                for attr in cls._schemas.keys():
                    if attr in _d:
                        del _p[attr]
                return _p
            cls.on_put.send(obj, response=resp, payload=process_doc(doc))
        return resp, obj

    @classmethod
    def delete(cls, _id, _refresh=True, _signal=True):
        resp = current_app.es.delete(index=cls._table(), id=_id, refresh=_refresh, ignore=[404])
        if _signal:
            cls.on_delete.send(response=resp)
        return resp

    @classmethod
    def aggs_request(cls, aggs, _range=None, _from=0, _count=0, _sort={}, _must=[], **kwargs):
        _m = _must.copy()
        if kwargs:
            def pre_field(k, v):
                return k if isinstance(v, (bool, int)) else '{0}.keyword'.format(k)
            _m += [{"terms" if isinstance(v, list) else "term": {pre_field(k, v): v}} for k, v in kwargs.items()]

        _filter = []
        if _range:
            if isinstance(_range, dict):
                for _f, v in _range.items():
                    if v:
                        _r = []
                        for _v in v:
                            _s, _e = _v
                            _r.append({"range": {_f: {"gte": _s, "lte": _e}}})
                        _filter.append({'bool': {'should': _r}})
            else:
                _f, _s, _e, _tz = _range
                _m.append({"range": {_f: {"gte": _s, "lte": _e, "time_zone": _tz}}})

        q = {
            "query": {
                "bool": {
                    "must": _m, 
                    "filter": _filter
                }
            },
            "size": _count,
            "from": _from,
            "aggs": aggs
        }
        if _sort:
            q['sort'] = _sort

        logger.debug(f'{cls.__name__}.aggs_request Request: {q}')
        resp = current_app.es.search(index=cls._table(), body=q, request_timeout=60, ignore=[400, 404], track_total_hits=True)
        logger.debug(f'{cls.__name__}.aggs_request Response: {resp}')

        aggregations = {}
        if 'status' in resp and resp['status'] in [400, 404]:
            pass
        else:
            aggregations = resp.get('aggregations', [])

        return aggregations, resp      

    @classmethod
    def aggs(cls, fields=[], _range=None, _cnt=500, _order={'_count': 'desc'}, _process=True, **kwargs):
        _aggs = {
            item: {
                "terms": {
                    "field": f'{item}.keyword',
                    "size": _cnt,
                    "order": _order
                }
            } for item in fields
        }        
        aggs, _ = cls.aggs_request(_aggs, _range, **kwargs)

        def process(items):
            return sorted([item['key'].strip() for item in items['buckets'] if item['key'].strip()]) if _process else items

        return {k: process(v) for k, v in aggs.items()}
    
        # must = []

        # if kwargs:
        #     def pre_field(k, v):
        #         return k if isinstance(v, (bool, int)) else '{0}.keyword'.format(k)
        #     must = [{"terms" if isinstance(v, list) else "term": {pre_field(k, v): v}} for k, v in kwargs.items()]

        # if _range:
        #     _f, _s, _e, _tz = _range
        #     must.append({"range": {_f: {"gte": _s, "lte": _e, "time_zone": _tz}}})

        # q = {
        #     "query": {
        #         "bool": {
        #             "must": must
        #         }
        #     },
        #     "size": 0,
        #     "aggs": aggs
        # }

        # # logger.info(f'Aggs Request: {q}')
        # resp = current_app.es.search(index=cls._table(), body=q, request_timeout=60, ignore=[400, 404])
        # # logger.info(f'Aggs Response: {resp}')

        # aggs = {}
        # if 'status' in resp and resp['status'] in [400, 404]:
        #     pass
        # else:
        #     aggs = resp.get('aggregations', [])            

        # def process(items):
        #     return sorted([item['key'].strip() for item in items['buckets'] if item['key'].strip()])


    @classmethod
    def humansize(cls, nbytes, base=1024, s=' '):
        v = nbytes
        # logger.info(f'humansize IN: {nbytes}')
        sf1 = ['', 'k', 'M', 'G', 'T', 'P']
        i = 0
        while nbytes >= base and i < len(sf1)-1:
            nbytes /= float(base)
            i += 1
        f = nbytes
        if v >= base:
            f = f'{nbytes:.1f}'.rstrip('0').rstrip('.')
        sf2 = 'B' if base == 1024 else ''
        res = f'{f}{s}{sf1[i]}{sf2}'
        # logger.info(f'humansize OUT: {res}')
        return res


def u_func(endpoint, lang_code=None, **kwargs):
    _e = endpoint
    if cp := current_app.config.get('CORE_PREFIX'):
        _e = f'{cp}{lang_code or g.language}.{_e}'
    return url_for(_e, **kwargs)


def p_func(paths):
    if isinstance(paths, dict):
        return paths.get(g.language, 'undefined')
    elif isinstance(paths, list):
        idx = current_app.config['AVAILABLE_LOCALE'].index(g.language)
        return paths[idx]
    elif isinstance(paths, str):
        return paths


class Page(ElasticEntity):
    on_put = Signal()
    
    _schemas = {     
        'project': str, 
        'suggest': str, # search_as_you_type
        'path': str,                                                                                                                
        'category': str,
        'locale': str,
        'locale_available': list, # for lang version
        'hreflang': str, # current lang for page
        'hreflang_tags': list,
        'hreflang_key': str,
        'source_chain': list,
        'api_source': str,
        'alias': str,
        'title': str,
        'alt_title': str,
        'publishedon': DateTimeField,
        'updatedon': DateTimeField,
        'is_active': bool,
        'is_redirect': bool,
        'redirect': str,
        'redirect_geo': list,
        'is_searchable': bool,
        'meta_title': str,
        'meta_description': str,
        'meta_image': str,
        'breadcrumbs': list,
        'views_count': int,
        'activity_count': int,
        'authors': str,
        'template': str,
        'parent': str,
        'order': int,
        'overview': str,
        'content': str,
        # 'custom_text': str,
        'has_toc': bool,
        'attachs': list,
        'screen_list': list,
        'software': list,
        'rating': int,
        'boost': float,
        'rank': int,
        'default_currency': str,
        'faq': list,
        'is_commented': bool,
        'comments': list,
        'is_amp': bool,
        'params': list,
        'translations': list,

        'tags': list, # for page: news, category
        'cover': str, # for page: collection, provider, page

        'screen': str,
        'themes': list,
        'releasedon': DateTimeField,
        'volatility': list,
        'rtp': float,
        'slot_pros': list,
        'slot_cons': list,
        'slot_features': list,
        'layout': list,
        'lines': int,
        'is_coins': bool,
        'min_bet': float,
        'max_bet': float,
        'max_win': int,
        'is_jackpot': bool,
        'jackpot': float,
        'is_freeplay': bool,
        'freeplay_url': str,
        'related': list,
        'preferred': list,

        'intro': str,
        'is_new': bool,
        'is_featured': bool,
        'is_sponsored': bool,
        'owner': str,
        'status': str, # status approve: draft, in review, published (manager editor mode)
        'is_draft': bool,
        'is_sandbox': bool,
        'user_rating': float,
        'user_pros_count': int,
        'user_cons_count': int,
        'games_count': int,
        'operator': str,
        'establishedon': DateTimeField,
        'affiliate': str,
        'affiliate_contact': str,
        'affiliate_email': str,
        'affiliate_ref': str,
        'website': str,
        'traffic': int,
        'traffic_delta': int,
        'traffic_delta_percent': int,
        'local_domains': list,
        'ref_link_geo': list,
        'ref_link': str,
        'ref_link_tc': str,
        'theme_color': str,
        'logo': str,
        'logo_white': str,
        'logo_small': str,
        'logo_favicon': str,
        'services': list,
        'games': list,
        'provider_tags': list,
        'provider_pros': list,
        'provider_cons': list,
        'licences': list,
        'licences_info': list,
        'languages': list,
        'support_languages': list,
        'support_livechat': bool,
        'support_email': str,
        'support_phone': str,
        'support_worktime': str,
        'currencies': list,
        'deposits': list,
        'withdrawal': list,
        'min_deposit': int,
        'min_withdrawal': int,
        'min_deposit_float': float,
        'max_deposit_float': float,
        'min_withdrawal_float': float,
        'max_withdrawal_float': float,
        'cashiers_limits': list,
        'games_limits': list,
        'withdrawal_time': list,
        'withdrawal_time_value': float,
        'withdrawal_limits': list,
        'withdrawal_monthly': int,
        'withdrawal_weekend': bool,
        'kyc_deposit': bool,
        'kyc_withdrawal': bool,
        'welcome_package': str,
        'welcome_package_geo': list,
        'welcome_package_max_bonus': int,
        'welcome_package_match': int,
        'welcome_package_note': str,
        'welcome_package_wager': int,
        'wager_type': str,
        'welcome_package_fs': int,
        'welcome_package_min_dep': int,
        'no_deposit': str,
        'no_deposit_fs': int,
        'no_deposit_note': str,
        'cashback': int,
        'promotions': list,
        'promocode': str,
        'geo_blacklist': str,
        'geo_whitelist': str,
        'geo_priority': list,
        'geo': list,
        'external_id': str,
        'rank_alexa': int, # remove to traffic
        'group_ranks': list,
        'applications': list,
        # 'applications_review': str,
        'trustpilot_url': str,
        'trustpilot_rate_value': float,
        'trustpilot_reviews_value': int,

        'collection': list,
        'collection_group': bool,
        'collection_category': str,
        'collection_datasource': str,
        'collection_mode': str,
        'collection_is_current_geo': bool,
        'collection_is_readonly': bool,
        'collection_is_static': bool,
        'collection_is_recommends': bool,
        'collection_paging': str,
        'collection_cpp': int,
        'collection_sort': str,
        'collection_sort_direction': str,
        'collection_column_title': str,

        'geo_zones': list,
        'geo_regions': list,

        'aff_location': str,
        'aff_tags': list,
        'aff_pros': list,
        'aff_platform': list,
        'aff_brands': list,
        'aff_exclusive_offer': str,
        'aff_rs_min': float,
        'aff_rs_max': float,
        'aff_cpa_min': float,
        'aff_cpa_max': float,
        'aff_subaff': float,
        'aff_admin_fee': float,
        'aff_deals': list,
        'aff_payout_methods': list,
        'aff_payout': str,
        'aff_payout_min': float,
        'aff_payout_date': str,
        'is_aff_nnco': bool,
        'is_aff_separate_brand': bool,
        'aff_support_skype': str,
        'aff_support_telegram': str,
        'aff_support_email': str,

        'app_store': str,
        'is_apk': bool,
        'app_store_link': str,
        'app_download_link': str,
        'app_model': str,
        'app_categories': list,
        'app_devices': list,
        'app_rank': int,
        'app_rating': float,
        'app_reviews': int,
        'app_reviews_short': str,
        'app_downloads': int,
        'app_downloads_short': str,
        'app_dev_profile': str,
        'app_dev_name': str,
        'app_dev_website': str,
        'app_id': str,
        'app_version': str,
        'app_last_update': DateTimeField,
        'app_released': DateTimeField,

        'notification_mode': str, # popup, header, corner, 
        'notification_template': str, 
        'notification_start': DateTimeField, 
        'notification_end': DateTimeField, 
        'notification_silent': bool,
        'notification_timeout': int,
        'notification_cookies': int,
    }

    @classmethod
    def _table(cls):
        return "{0}_page.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))

    @classmethod
    def process_country(cls, _clist):
        zones = {k.decode('utf-8'): loads(v) for k, v in current_app.redis.hgetall('geo_zones').items()}

        _c = []
        _m = []
        if len(_clist):
            for item in _clist:
                item = item.strip()
                if item:
                    _cn = None
                    if len(item) == 2:
                        _cn = pycountry.countries.get(alpha_2=item.upper())
                    else:
                        _cn = pycountry.countries.get(name=item)
                    if item in zones:
                        for c in zones[item]:
                            _c.append(c)
                    else:
                        if not _cn:
                            try:
                                _found = pycountry.countries.search_fuzzy(item)
                                if len(_found) == 1:
                                    _cn = _found[0]
                                else:
                                    _m.append({'term': item, 'options': [{'name': c.name, 'iso': c.alpha_2} for c in _found]})
                            except LookupError:
                                _m.append({'term': item, 'options': []})
                        if _cn:
                            _c.append(_cn.name)
        return _c, _m
                
    @classmethod
    def get_countries(cls, w='', b=''):
        geo_wl = w.split(",")
        geo_bl = b.split(",")

        _countries_wl, _m1 = cls.process_country(geo_wl)
        _countries_bl, _m2 = cls.process_country(geo_bl)
                    
        if len(_countries_wl) == 0:
            _countries_wl = [_cn.name for _cn in pycountry.countries]

        _countries = list(set(_countries_wl) - set(_countries_bl))
        _countries.sort()
        _messages = {'w': _m1, 'b': _m2}

        return _countries, _messages, len(_m1 + _m2) > 0
    
    @classmethod
    def get_options(cls, aggs=['geo', 'tags', 'software', 'currencies', 'games', 'provider_tags', 'provider_pros', 'provider_cons', 'licences', 'languages', 'support_languages', 'deposits', 'withdrawal', 'themes', 'slot_pros', 'slot_cons', 'slot_features', 'layout', 'authors', 'geo_zones', 'geo_regions', 'operator'], count=1000):

        _aggs = {item: {"terms": {"field": f"{item}.keyword", "size": count}} for item in aggs}

        q = {
            "query": {
                "match_all": {}
            },
            "size": 0,
            "aggs": _aggs
        }

        # logger.info(f'get_options request: {q}')
        resp = current_app.es.search(index=cls._table(), body=q, request_timeout=60, ignore=[400, 404])
        # logger.info(f'get_options response: {resp}')

        aggs = {}
        if 'status' in resp and resp['status'] in [400, 404]:
            pass
        else:
            aggs = resp.get('aggregations', [])            

        def process(items, key):
            if key in items:
                _res = [{'title': item['key'].strip(), 'count': item['doc_count']} for item in items[key]['buckets'] if item['key'].strip()]
                return sorted(_res, key=lambda d: d['title'])
            return []

        def merge_lists(*args):
            _res = {}
            for _list in args:
                for _item in _list:
                    _title = _item['title']
                    _v = _res.get(_title, 0)
                    _res[_title] = _v + _item['count'] 
            return sorted([{'title': k, 'count': v} for k, v in _res.items()], key=lambda d: d['title'])

        opts = {
            'authors': process(aggs, 'authors'),
            'custom_templates': [],
            'currency': process(aggs, 'currencies'),
            'provider_tags': process(aggs, 'provider_tags'),
            'provider_pros': process(aggs, 'provider_pros'),
            'provider_cons': process(aggs, 'provider_cons'),
            'software': process(aggs, 'software'),
            'licences': process(aggs, 'licences'),
            'languages': merge_lists(process(aggs, 'languages'), process(aggs, 'support_languages')),
            'payment_methods': merge_lists(process(aggs, 'deposits'), process(aggs, 'withdrawal')),
            'games': process(aggs, 'games'),

            'themes': process(aggs, 'themes'),
            'slot_pros': process(aggs, 'slot_pros'),
            'slot_cons': process(aggs, 'slot_cons'),
            'slot_features': process(aggs, 'slot_features'),
            'layout': process(aggs, 'layout'),

            'tags': process(aggs, 'tags'),

            'countries': [{'iso': item.alpha_2, 'country': item.name} for item in pycountry.countries],
            'countries_name': [item.name for item in pycountry.countries],
            'geo': process(aggs, 'geo'),
            'geo_zones': process(aggs, 'geo_zones'),
            'geo_regions': process(aggs, 'geo_regions'),
            'operator': process(aggs, 'operator'),
            'custom_zones': [],
            'services': process(aggs, 'services') or ['casino', 'poker', 'betting', 'lotto', 'bingo', 'social'],
            'status': ['published', 'draft', 'on_review'],
            'category': ['page', 'collection', 'provider', 'slot'], # 'collection', 'provider', 'slot', 'affiliate', 'app'
            'collection_category': [
                'provider', 
                'slot',
                'bonus',
            ],
            'collection_datasource': [],
            'wager_types': ['xb', 'x(d+b)'],
            'volatility': ['Low', 'Medium', 'High'],
            'media_presets': [
                'origin', 
                'square_w50', 
                'slogo_w150', 
                'logo_w250', 
                'cover_w300', 
                'cover_w300_h200',
                'cover_w600',
                'cover_w1200', 
                'content_w700',
                'meta_w1200_h630',
            ],
            'media_rename': ['none', 'entity', 'hash'],
            'promo_types': ['Welcome Bonus', '1st Deposit Bonus', '2nd Deposit Bonus', '3rd Deposit Bonus', '4th Deposit Bonus', 'No Deposit', 'Cashback', 'Freespins'],
            'promo_tags': ['Exclusive'],
            'apps': ['google_play', 'app_store'],
            'times': ['ewallets', 'cards', 'bank', 'cryptocurrency'],
            'limits': ['transaction', 'day', 'week', 'month'],
            'game_types': ['slots', 'roulette', 'blackjack'],
            'locale': [],
            'bgcolor': [],
            'collection_mode': [], # 'Best', 'New', 'Software'
            'collection_params': [
                'software:select:software', 
                'geo:select:geo',
                'geo_regions:select:geo_regions',
                'deposits:select:payment_methods', 
                'withdrawal:select:payment_methods', 
                'services:select:services', 
                'games:select:games', 
                'licences:select:licences', 
                'provider_tags:select:provider_tags', 
                'languages:select:languages', 
                'support_languages:select:languages',
                'currencies:select:currency',
                'operator:str', 
                'affiliate:str', 
                'website:str',
                'establishedon:range',
                'is_searchable:bool',
                'is_new:bool',
                'is_featured:bool',
                'is_sponsored:bool',
                'withdrawal_weekend:bool',
                'kyc_deposit:bool',
                'kyc_withdrawal:bool',
                'themes:select:themes',
                'slot_features:select:slot_features',
                'is_jackpot:bool',
                'licences_info.number:str',
            ],
            'collection_sort': ['Func_1', 'Func_2', 'Rate', 'Rank', 'Views', 'Activity', 'Alexa', 'Games', 'Trustpilot Rate', 'Trustpilot Reviews', 'Adding', 'AZ', 'Launched', 'RTP', 'MaxWin', 'Jackpot', 'Min.Deposit'],
            'collection_sort_direction': ['Desc', 'Asc'],
            'collection_paging': ['FirstPage', 'Paging'],
            'hreflangs': [],
            'params_presets': {},
            'field_notes': {},

            'aff_tags': process(aggs, 'aff_tags'),
            'aff_pros': process(aggs, 'aff_pros'),
            'aff_platform': process(aggs, 'aff_platform'),
            'aff_payout_methods': process(aggs, 'aff_payout_methods'),    

            'app_categories': process(aggs, 'app_categories'),        
            'app_devices': process(aggs, 'app_devices'),        
        }
        
        return opts

    @property
    def software_key(self):
        if self.category == 'slot' and self.software:
            return slugify(self.software[0], separator='').lower()
        return None

    @classmethod
    def query(cls, query, is_full=False, locale_list=[], category=[], page=1, count=10, match_type='bool_prefix'):
        if not query:
            return []

        def escape_query_string(text):
            # Экранируем спецсимволы Lucene: + - = && || > < ! ( ) { } [ ] ^ " ~ * ? : \ /
            # return re.sub(r'([+\-=&|><!(){}\[\]^"~*?:\\/])', r'\\\1', text)
            return text.replace('-', ' ')

        query = ' AND '.join([f'*{escape_query_string(item)}*' for item in query.split()])

        must = [
            # {"multi_match" : {
            #     "query": query, 
            #     "type": match_type,
            #     "fields": [
            #         "suggest",
            #         "suggest._2gram",
            #         "suggest._3gram",
            #         "title^3",
            #         "alias",
            #         "intro^2",
            #         "overview",
            #         "content",
            #     ] 
            # }}
            {
                "query_string": {
                    "query": query,
                    "fields": [
                        # "suggest",
                        # "suggest._2gram",
                        # "suggest._3gram",
                        "title^3",
                        "alias",
                        "intro^2",
                        "overview",
                        "content",
                        "website",
                    ] 
                }
            }
        ]
        if not is_full:
            must += [
                {"term": {"is_active": True}},
                {"term": {"is_searchable": True}},
                {"term": {"is_redirect": False}},
                {"term": {"is_draft": False}},
                {"term": {"is_sandbox": False}},
            ]
            if category:
                must.append({"terms": {"category.keyword": category}})

            # TODO: search slots and casinos ??? 
            # if current_app.config.get('ENTITY_MULTIPLE_LOCALE', False):
            #     params['locale_available'] = _locale or g.language
            #     _locale = None
            # else:
            #     _locale = _locale or g.language                

        if locale_list:
            must.append({"terms": {"locale.keyword": locale_list}})
        # elif al := current_app.config.get('AVAILABLE_LOCALE'):
        #     must.append({"terms": {"locale.keyword": al}})

            # if in_locale:
            #     must.append({"term": {"locale_available.keyword": in_locale}})

        q = {
            "query": {
                "bool": {
                    "must": must
                }
            },
            "from": (page - 1) * count,
            "size": count,
            "highlight": {
                "fields": {
                    "title": {},
                    "content": {},
                    "intro": {},
                    "overview": {}
                }
            }             
        }

        logger.debug(f'Search query: {q}')
        resp = current_app.es.search(index=cls._table(), body=q, request_timeout=60, ignore=[404])
        logger.debug(f'Search query response: {resp}')

        if 'status' in resp and resp['status'] in [400, 404]:
            return []

        for item in resp['hits']['hits']:
            obj = cls(item['_source'], item['_id'])
            cls.on_ready.send(obj)
            yield obj, item.get('highlight', {})

    @property
    def visit_url(self):
        return u_func('visit', alias=self.external_id or self.alias)

    @property
    def acceptable(self):
        if self.category == 'provider':
            return self.ref_link and self.accept_geo
        return True

    @property
    def accept_geo(self):
        if self.category == 'provider':
            return current_user.country_full in self.geo
        return True

    @property
    def activity_str(self):
        return self.activity_count or 0

    @property
    def query_by_collection_params(self):
        qp = dict()
        ep = dict()

        if self.collection_category  == 'provider':
            for item in self.collection:
                if item.get('key'):
                    pdata = item['key'].split(':')
                    _v = item.get('value_str')
                    _exclude = item.get('is_exclude')
                    if pdata[1] in ['select']:
                        if _v: 
                            if _exclude:
                                _prev = ep.get(pdata[0])
                            else:
                                _prev = qp.get(pdata[0])
                            if _prev:
                                if isinstance(_prev, tuple):
                                    _prev += (_v ,)
                                elif isinstance(_prev, list):
                                    _prev.append(_v)
                            else:
                                if _exclude:
                                    _prev = [_v]
                                else:
                                    _prev = (_v ,) if self.collection_group else [_v]
                            if _exclude:
                                ep[pdata[0]] = _prev
                            else:
                                qp[pdata[0]] = _prev
                    elif pdata[1] == 'bool':
                        if _exclude:
                            ep[pdata[0]] = item.get('value', False)
                        else:
                            qp[pdata[0]] = item.get('value', False)
                    elif pdata[1] == 'range':
                        if _v: 
                            _s = (pdata[0], _v, _v, 'UTC')
                            if _exclude:
                                _prev = ep.get('_range', [])
                                _prev.append(_s)
                                ep['_range'] = _prev
                            else:
                                _prev = qp.get('_range', [])
                                _prev.append(_s)
                                qp['_range'] = _prev
                    elif pdata[1] in ['str']: 
                        if _v: 
                            if _exclude:
                                ep[pdata[0]] = _v
                            else:
                                qp[pdata[0]] = _v

        logger.info(f'collection params: {self.collection}')
        logger.info(f'qp: {qp}')
        logger.info(f'ep: {ep}')

        return qp, ep

    @classmethod
    def provider_by_context(cls, country=None, _exclude=[], _exclude_params={}, _exclude_tags=['closed'], _count=12, _page=1, _offset=None, _source=["title", "alias", "logo"], _aggs={}, _sorting=None, _locale=None, _fn_geo_priority=False, _geo_priority_weight=10, **params):
        filter_list =  [ 
            {"term": {"is_active": True}},
            {"term": {"is_draft": False}},
            {"term": {"is_sandbox": False}},
            {"term": {"category.keyword": 'provider'}},
        ]

        if current_app.config.get('ENTITY_MULTIPLE_LOCALE', False):
            params['locale_available'] = _locale or g.language
            _locale = None
        else:
            _locale = _locale or g.language

        if _locale:
            filter_list.append({"term": {"locale.keyword": _locale}})            
        if country and not _fn_geo_priority:
            filter_list.append({"term": {"geo.keyword": country}})            
        for key, value in params.items():
            if key not in ['sorting', 'cpp', 'query', 'is_grid', 'is_geo', '_range']:
                if isinstance(value, bool):
                    filter_list.append({"term": {key: value}})
                elif isinstance(value, list):
                    if value:
                        filter_list.append({"terms": {
                            f"{key}.keyword": value,
                        }})
                elif isinstance(value, tuple):
                    if value:
                        filter_list.append({
                            "terms_set": {
                                f"{key}.keyword": {
                                    "terms": list(value),
                                    "minimum_should_match_script": {
                                        "source": "params.num_terms"
                                    }
                                }
                            },
                        })
                else:
                    if '*' in value:
                        filter_list.append({"wildcard": {key: value}})
                    else:                
                        filter_list.append({"term": {"{0}.keyword".format(key): value}})
            elif key in ['_range']:
                # {'updatedon': [['now-10d', 'now']]}
                # 'updatedon', 'now-10d', 'now', 'UTC'  
                def process_range(item):
                    _f, _s, _e, _tz = item
                    _rvalue = {"gte": _s, "lte": _e}
                    if _tz:
                        _rvalue["time_zone"] = _tz
                    filter_list.append({"range": {_f: _rvalue}})

                if isinstance(value, tuple):
                    process_range(value)
                elif isinstance(value, list):
                    __v = []
                    for _k in value:
                        _f, _s, _e, _tz = _k
                        _rvalue = {"gte": _s, "lte": _e}
                        if _tz:
                            _rvalue["time_zone"] = _tz
                        __v.append({"range": {_f: _rvalue}})
                    if __v:
                        filter_list.append({'bool': {'should': __v}})                
                elif isinstance(value, dict):
                    for k, v in value.items():
                        __v = []
                        for _v in v:
                            _s = {}
                            _min, _max = _v
                            if _min != None:
                                _s['gte'] = _min
                            if _max != None:
                                _s['lte'] = _max
                            __v.append({'range': {k: _s}})
                        if __v:
                            filter_list.append({'bool': {'should': __v}})                
            elif key == 'query':
                if value:
                    filter_list.append(
                        {"multi_match" : {
                            "query": value, 
                            "type": "bool_prefix",
                            "fields": [
                                "suggest",
                                "suggest._2gram",
                                "suggest._3gram"
                            ] 
                        }})

        def get_func():
            flist = list()

            flist.append({
                "field_value_factor": {
                    "field": "rating",
                    "factor": 1,
                    "missing": 50
                },
                "weight": 2
            })

            flist.append({
                "field_value_factor": {
                    "field": "boost",
                    "factor": 1,
                    "missing": 1
                },
                "weight": 1
            })

            if country:
                flist.append({
                    "filter": {
                        "bool": {
                            "must": {
                                "term": {
                                    "geo_priority.keyword": country
                                }
                            }
                        }
                    },
                    "weight": _geo_priority_weight
                })

            flist.append({
                "filter": {
                    "term": {
                        "is_sponsored": True
                    }
                },
                "weight": 3
            })

            if _fn_geo_priority and country:
                flist.append({
                    "filter": {
                        "term": {
                            "geo.keyword": country
                        }
                    },
                    "weight": 1000
                })

            return flist

        def pre_field(k, v):
            return k if isinstance(v, bool) else '{0}.keyword'.format(k)

        exclude_list = []
        if _exclude_tags:
            exclude_list.append({'terms': {'provider_tags.keyword': _exclude_tags}})
        if _exclude_params:
            exclude_list.append({"terms" if isinstance(v, list) else "term": {pre_field(k, v): v} for k, v in _exclude_params.items()})
        if _exclude:
            exclude_list.append({'ids': {'values': _exclude}})

        qbool = {
            "must": filter_list,
            "must_not": exclude_list
        }

        _from = _offset if _offset else (_page - 1)*_count
        # logger.info(f'from: {_from}, {_offset}, {_page}, {_count}')

        q = {
            "query": {
                "function_score": {
                    "query": {
                        "bool": qbool
                    },
                    "boost": 1,
                    "boost_mode": "multiply",
                    "functions": get_func()
                }
            },
            "from": _from,
            "size": _count,
            "_source": _source,
        }

        _hash = None
        if _aggs:
            q["aggs"] = _aggs
            _hash = hashlib.md5(dumps(q).encode()).hexdigest()

        if _sorting:
            q["sort"] = _sorting

        logger.debug(u'QUERY: {0}'.format(q))
        resp = current_app.es.search(index=cls._table(), body=q, request_timeout=60, ignore=[400, 404])
        # logger.debug(u'RESPONSE: {0}'.format(resp))

        if 'status' in resp and resp['status'] in [400, 404]:
            if _aggs:
                return [], 0, {}, _hash
            else:
                return [], 0

        def process_aggs(_a):
            _res = {}
            for k, v in _a.items():
                buckets = v['buckets']
                if isinstance(buckets, dict):
                    _res[k] = [{'item': r, 'alias': slugify(r), 'count': dia['doc_count']} for r, dia in v['buckets'].items()]
                else:
                    _res[k] = [{'item': i['key'], 'alias': slugify(i['key']), 'count': i['doc_count']} for i in v['buckets']]
            return _res

        logger.debug(u'RESPONSE provider_by_context took: {0}'.format(resp['took']))
        if _aggs:
            return cls.process(resp['hits']['hits']), resp['hits']['total']['value'], process_aggs(resp['aggregations']), _hash
        else:
            return cls.process(resp['hits']['hits']), resp['hits']['total']['value']


    @classmethod
    def slots_by_context(cls, _exclude=[], _count=12, _page=1, _source=["title", "alias", "cover"], _aggs={}, _sorting=None, _locale=None, **params):
        filter_list =  [ 
            {"term": {"is_active": True}},
            {"term": {"category.keyword": 'slot'}},
        ]

        if current_app.config.get('ENTITY_MULTIPLE_LOCALE', False):
            params['locale_available'] = _locale or g.language
            _locale = None
        else:
            _locale = _locale or g.language        
        if _locale:
            filter_list.append({"term": {"locale.keyword": _locale}})            

        for key, value in params.items():
            if key not in ['sorting', 'cpp', 'query']:
                if isinstance(value, bool):
                    filter_list.append({"term": {key: value}})
                elif isinstance(value, list):
                    if value:
                        filter_list.append({"terms": {
                            f"{key}.keyword": value,
                        }})
                elif isinstance(value, tuple):
                    if value:
                        filter_list.append({
                            "terms_set": {
                                f"{key}.keyword": {
                                    "terms": list(value),
                                    "minimum_should_match_script": {
                                        "source": "params.num_terms"
                                    }
                                }
                            },
                        })
                else:                
                    filter_list.append({"term": {"{0}.keyword".format(key): value}})
            elif key == 'query':
                if value:
                    filter_list.append(
                        {"multi_match" : {
                            "query": value, 
                            "type": "bool_prefix",
                            "fields": [
                                "suggest",
                                "suggest._2gram",
                                "suggest._3gram"
                            ] 
                        }})

        def get_func():
            flist = list()

            flist.append({
                "field_value_factor": {
                    "field": "rating",
                    "factor": 1,
                    "missing": 0
                },
                "weight": 2
            })


            flist.append({
                "filter": {
                    "term": {
                        "is_featured": True
                    }
                },
                "weight": 3
            })

            return flist

        qbool = {
            "must": filter_list,
            "must_not": {'ids': {'values': _exclude}}
        }

        q = {
            "query": {
                "function_score": {
                    "query": {
                        "bool": qbool
                    },
                    "boost": 1,
                    "boost_mode": "multiply",
                    "functions": get_func()
                }
            },
            "from": (_page - 1)*_count,
            "size": _count,
            "_source": _source,
        }

        _hash = None
        if _aggs:
            q["aggs"] = _aggs
            _hash = hashlib.md5(dumps(q).encode()).hexdigest()

        if _sorting:
            q["sort"] = _sorting

        resp = current_app.es.search(index=cls._table(), body=q, request_timeout=60, ignore=[400, 404])
        # logger.debug(u'RESPONSE: {0}'.format(resp))

        if 'status' in resp and resp['status'] in [400, 404]:
            if _aggs:
                return [], 0, {}, _hash
            else:
                return [], 0

        def process_aggs(_a):
            _res = {}
            for k, v in _a.items():
                _res[k] = [{'item': i['key'], 'count': i['doc_count']} for i in v['buckets']]
            return _res

        logger.debug(u'RESPONSE slots_by_context took: {0}'.format(resp['took']))
        if _aggs:
            return cls.process(resp['hits']['hits']), resp['hits']['total']['value'], process_aggs(resp['aggregations']), _hash
        else:
            return cls.process(resp['hits']['hits']), resp['hits']['total']['value']


class Guest(AnonymousUserMixin):
    @property
    def is_admin(self):
        return False

    @property
    def user_agent(self):
        return parse(request.user_agent.string)

    @property
    def ip(self):
        return request.remote_addr

    @property
    def location_iso(self):
        if self.user_agent.is_bot:
            return 'gb'
        else:
            return request.headers.get('X-Geo-Country', 'gb').lower()

    @property
    def location(self):
        _cn = pycountry.countries.get(alpha_2=self.location_iso.upper())
        return _cn.name if _cn else 'United Kingdom'

    @property
    def country(self):
        return request.cookies.get('iso', self.location_iso)

    @property
    def country_full(self):
        c = request.cookies.get('country', self.location)
        return unquote(c.encode('latin-1').decode('utf-8'))

    @property
    def timezone(self):
        return 'Europe/London'

    @property
    def client_id(self):
        return ".".join(request.cookies.get("_ga", "").split(".")[-2:])

    def __repr__(self):
        return str(self.user_agent)


class Actor(ElasticEntity, Guest):
    on_put = Signal()

    _schemas = {
        'id': str,
        'project': str,
        'username': str,
        'password': str,
        'last_auth': DateTimeField,
        'last_country': str,
        'actor_is_active': bool,
        'actor_is_admin': bool,
        'zones': list,
        'ip': str,
        'ua': str,
        'cid': str,
        'sign_date': DateTimeField,
        'skype': str,
        'comment': str,
    }
    
    @classmethod
    def _table(cls):
        return "{0}_actor.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))

    @property
    def is_authenticated(self):
        return True

    @property
    def is_admin(self):
        return self.actor_is_admin

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self._id

    def __repr__(self):
        return self._doc.get('username')        
        

class Activity(ElasticEntity):
    on_put = Signal()

    _schemas = {
        'createdon': DateTimeField,
        'project': str,
        'ip': str,
        'country': str,
        'country_iso': str,
        'country_selected': str,
        'ua': str,
        'is_bot': bool,
        'cid': str,
        'activity': str,
        'name': str,
        'casino': str,

        # ticket
        'subject': str,
        'contacts': str,
        'message': str,

        # subscribe
        'email': str,

        # vote, rate + old review
        'rate': int,
        'casino_id': str,
        'pros': str,
        'cons': str,

        # complaint
        'username': str,
        'amount': str,
        'currency': str,
        'completedon': DateTimeField,
        'status': str,
        'replies': list,
        'is_active': bool,
        'comment': str,
        'alias': str, # for view 

        # click
        'url': str,
        'landing': str,
    }
        
    @classmethod
    def _table(cls):
        return "{0}_activity.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))


class TdsHit(ElasticEntity):
    on_put = Signal()

    _schemas = {
        'createdon': DateTimeField,
        'stream': str,
        'stream_name': str,
        'campaign_name': str,
        'campaign_alias': str,
        'campaign_id': str,
        'click_id': str,
        'ip': str,
        'country': str,
        'country_iso': str,
        'ua': str,
        'is_bot': bool,
        'is_uniq': bool,
        'action': str,
        'url': str,
        'subid': str,
        'referrer': str,
        'fingerprint': str,
    }
        
    @classmethod
    def _table(cls):
        return "{0}_tds_hits.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))

    @classmethod
    def aggs_stats(cls, _field, _range=None, _filters={}, _cnt=500):

        def get_subaggs(_a={}):
            _b = {
                "fingerprint": {
                    "cardinality": {
                        "field": "fingerprint.keyword"
                    }
                },
                "is_bot": {
                    "terms": {
                        "field": "is_bot",
                    }
                }
            }
            if _a:
                _b = dict(_b, **_a)
            return _b

        if _field in ['createdon']:
            aggs = {
                _field: {
                    "date_histogram": {
                        "field": _field,
                        "calendar_interval": "1d"
                    },
                    "aggs": get_subaggs()
                },
            }        
        elif _field in ['country']:
            aggs = {
                _field: {
                    "terms": {
                        "field": f"{_field}.keyword",
                        "size": _cnt
                    },
                    "aggs": get_subaggs({
                        "country_iso": {
                            "terms": {
                                "field": "country_iso.keyword"
                            },
                        }
                    })
                },
            }        
        elif _field in ['campaign_id']:
            aggs = {
                _field: {
                    "terms": {
                        "field": f"{_field}.keyword",
                        "size": _cnt
                    },
                    "aggs": get_subaggs({
                        "campaign_name": {
                            "terms": {
                                "field": "campaign_name.keyword"
                            },
                        }
                    })
                },
            }        
        elif _field in ['stream_key']:
            aggs = {
                _field: {
                    "terms": {
                        "field": 'stream.keyword',
                        "size": _cnt
                    },
                    "aggs": get_subaggs({
                        "campaign_name": {
                            "terms": {
                                "field": "campaign_name.keyword"
                            },
                        },
                        "stream_name": {
                            "terms": {
                                "field": "stream_name.keyword"
                            },
                        },
                    })
                },
            }        
        else:
            aggs = {
                _field: {
                    "terms": {
                        "field": f"{_field}.keyword",
                        "size": _cnt
                    },
                    "aggs": get_subaggs()
                },
            }        

        must = []

        if _filters:
            def pre_field(k, v):
                return k if isinstance(v, bool) else '{0}.keyword'.format(k)
            must = [{"terms" if isinstance(v, list) else "term": {pre_field(k, v): v}} for k, v in _filters.items()]

        if _range:
            _f, _s, _e, _tz = _range
            must.append({"range": {_f: {"gte": _s, "lte": _e, "time_zone": _tz}}})

        q = {
            "query": {
                "bool": {
                    "must": must
                }
            },
            "size": 0,
            "aggs": aggs
        }

        resp = current_app.es.search(index=cls._table(), body=q, request_timeout=60, ignore=[400, 404])
        logger.info(f'Response: {resp}')

        aggs = {}
        if 'status' in resp and resp['status'] in [400, 404]:
            pass
        else:
            aggs = resp.get('aggregations', [])            

        logger.info(f'Aggs found: {aggs}')

        def get_uc(item):
            return item['fingerprint']['value']

        def get_bots(item):
            _v = [item['doc_count'] for item in item['is_bot']['buckets'] if item['key_as_string'] == 'true']
            return _v.pop() if _v else 0

        def process(items, key):
            if key in items:
                if key == 'createdon':
                    return [{'term': item['key_as_string'].strip(), 'hits': item['doc_count'], 'uc': get_uc(item), 'bots': get_bots(item)} for item in items[key]['buckets']]
                elif key == 'country':
                    return [{'term': item['key'].strip(), 'country_iso': item['country_iso']['buckets'][0]['key'].lower(), 'hits': item['doc_count'], 'uc': get_uc(item), 'bots': get_bots(item)} for item in items[key]['buckets']]
                elif key in ['campaign_id']:
                    return [{'term': ', '.join([k['key'] for k in item['campaign_name']['buckets']]), 'hits': item['doc_count'], 'uc': get_uc(item), 'bots': get_bots(item)} for item in items[key]['buckets']]
                elif key in ['stream_key']:
                    return [{'term': item['key'].strip() + ' | Name: ' + ', '.join([k['key'] for k in item['stream_name']['buckets']]) + ' | Campaign: ' + ', '.join([k['key'] for k in item['campaign_name']['buckets']]), 'hits': item['doc_count'], 'uc': get_uc(item), 'bots': get_bots(item)} for item in items[key]['buckets']]
                else:
                    return [{'term': item['key'].strip(), 'hits': item['doc_count'], 'uc': get_uc(item), 'bots': get_bots(item)} for item in items[key]['buckets']]
            return []

        return process(aggs, _field), 0 #resp['hits']['total']['value']


class TdsDomain(ElasticEntity):
    on_put = Signal()

    _schemas = {
        'createdon': DateTimeField,
        'domain': str,
        'endpoint': str,
        'is_https': bool,
    }
        
    @classmethod
    def _table(cls):
        return "{0}_tds_domain.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))


class TdsCampaign(ElasticEntity):
    on_put = Signal()

    _schemas = {
        'createdon': DateTimeField,
        'updatedon': DateTimeField,
        'name': str,
        'domain': str,
        'alias': str,
        'groups': list,
        'ttl': int,
        'is_split': bool,
        'is_active': bool,
        'is_archive': bool,
        'notes': str,
        'streams': list,
        'postback_processor': str,
    }
        
    @classmethod
    def _table(cls):
        return "{0}_tds_campaign.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))


class TelegramBot(ElasticEntity):
    on_put = Signal()

    _schemas = {
        'createdon': DateTimeField,
        'is_active': bool,
        'token': str,
        'domain': str,
        'tags': list,
        'bot_id': str,
        'username': str,
        'first_name': str,
        'can_join': bool,
        'can_read': bool,
        'modules': list,
    }
        
    @classmethod
    def _table(cls):
        return "{0}_telegram_bot.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))


class TelegramChat(ElasticEntity):
    on_put = Signal()

    _schemas = {
        'createdon': DateTimeField,
        'updatedon': DateTimeField,
        'is_active': bool,
        'bot_admin': str,
        'chat_id': str,
        'type': str,
        'username': str,
        'count': int,
        'title': str,
        'description': str,
        'photo': str,
        'tags': list,
        'linked_chat': str,
        'can_send': bool,
        'can_invite': bool,
        'job_remove_system_msg': bool,
    }
        
    @classmethod
    def _table(cls):
        return "{0}_telegram_chat.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))


class TelegramMessage(ElasticEntity):
    on_put = Signal()
    on_pre_put = Signal()
    on_delete = Signal()

    _schemas = {
        'createdon': DateTimeField,
        'type': str,
        'title': str,
        'content': str,
        'photo': str,
        'tags': list,
        'recipients': list,
        'send_without_notify': bool,
        'send_without_link_preview': bool,
        'send_pin_message': bool,
        'send_schedule': bool,
        'scheduledon': DateTimeField,
        'remove_schedule': bool,
        'removedon': DateTimeField,
        'buttons': list,

        'status': str,
        'publishedon': DateTimeField,
        'chat_id': int,
        'chat_username': str,
        'message_id': int,
        'sender_id': int,
        'sender_username': str,
        'raw': str,
    }
        
    @classmethod
    def _table(cls):
        return "{0}_telegram_message.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))


class TdsPostback(ElasticEntity):
    on_put = Signal()

    _schemas = {
        'createdon': DateTimeField,
        'postback_id': str,
        'ip': str,
        'ua': str,
        'campaign_id': str,
        'campaign_name': str,
        'method': str,
        'args': str,
        'content_type': str,
        'payload': str,
        # 'click_id': str,
        # 'action': str, # reg, fdep, dep
        # 'player_id': str, # internal id
        # 'amount': float,
        # 'currency': str,
        # 'payment_id': str,
    }
        
    @classmethod
    def _table(cls):
        return "{0}_tds_postback.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))


class CasinoCommit(ElasticEntity):
    on_put = Signal()

    _schemas = {
        'updatedon': DateTimeField,
        'source_id': str,
        'actor_id': str,
        'casino': str,
        ###
        'title': str,
        'website': str,
        'languages': list,
        'services': list,
        'year': int,
        'support_languages': list,
        'support_livechat': bool,
        'support_email': str,
        'support_phone': str,
        'attachs': list,
        'logo': str,
        'logo_small': str,
        'licences': list,
        'games': list,
        'games_count': int,
        'games_limits': list,
        'cashiers_limits': list,
        'software': list,
        'currencies': list,
        'default_currency': str,
        'deposits': list,
        'min_deposit': int,
        'min_deposit_float': float,
        'kyc_deposit': bool,
        'withdrawal': list,
        'min_withdrawal': int,
        'min_withdrawal_float': float,
        'withdrawal_monthly': int,
        'kyc_withdrawal': bool,
        'welcome_package_max_bonus': int,
        'welcome_package_match': int,
        'welcome_package_fs': int,
        'welcome_package': str,
        'welcome_package_note': str,
        'welcome_package_wager': int,
        'cashback': int,
        'geo_whitelist': str,
        'geo_blacklist': str,
        'geo': list,
        'content': str,
    }
        
    @classmethod
    def _table(cls):
        return "{0}_casino_commit.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))


class Product(ElasticEntity):
    on_put = Signal()
    on_change = Signal()

    _schemas = {     
        'suggest': str, # search_as_you_type
        'category': str,
        'path': str,                                                                                                                
        'alias': str,
        'title': str,
        'alt_title': str,
        'publishedon': DateTimeField,
        'updatedon': DateTimeField,
        'is_active': bool,
        'is_redirect': bool,
        'redirect': str,
        'redirect_geo': list, # TODO - remove
        'is_searchable': bool,
        'is_amp': bool, # TODO - remove
        'meta_title': str,
        'meta_description': str,
        'meta_image': str,
        'tags': list, # for page: news, category
        'breadcrumbs': list,
        'views_count': int,
        'activity_count': int,
        'authors': str,
        'template': str,
        'parent': str,
        'order': int,
        'source_chain': list,
        'locale': str,
        'locale_available': list, # for lang version
        'hreflang': str, # current lang for page
        'hreflang_tags': list,

        'intro': str,
        'params': list,
        'overview': str,
        'content': str,
        'attachs': list,

        'theme_color': str,
        'cover': str,
        'screen': str,
        'logo': str,
        'logo_small': str,
        'screen_list': list,

        'faq': list,

        'is_commented': bool,
        'comments': list,

        # product attrs

        'product_id': int,
        'product_type': str, # simple, grouped_key, grouped_list
        'product_salt': str,
        'product_group_key': str,
        'product_group_list': list,
        'product_status': str,
        'stock_status': str,
        'is_available': bool,
        'stock_quantity': int,
        'limit_quantity': int,
        'brand_title': str,
        'brand_title_local': str,
        'brand_alias': str,
        'brand_code': str,
        'category_tree': list,
        'category_tree_details': list,
        'category_name': str,
        'category_alias': str,
        'category_id': int,
        # 'category_external_id': str,
        'product_external_id': str, # saleor ID
        'product_tags': list,
        'part_number': str,
        'upc_code': str,
        'image_indices': list,
        'image_primary': str,
        'price_currency': str,
        'price_list': float,
        'is_discounted': bool,
        'price_discount': float,
        'discount_amount': float,
        'discount_percent': float,
        'price_per_unit': float,
        'price_discount_prev_date': DateTimeField,
        'price_discount_prev': float,
        'price_discount_delta': float,
        'price_discount_delta_percent': float,
        'shipping_cost': float, # Additional
        'weight': list,
        'dimensions': list,
        'package_quantity': int,
        'package_quantity_float': float,
        'ranks': list,
        'is_affiliate_mode': bool, # if storefront (link to stores)
        'partner_stores': list, # deep_link here
        'rating_avg': float,
        'rating_count': int,
        'rating_count_local': int, # local reviews on native lang
        'rating_stars': list,
        'faq_questions': int,
        # 'faq_questions_local': int,
        'faq_answers': int,
        'create_raw': str,
        'update_raw': str,
        'is_reviewed': bool,
        'products_related': list,
        'products_xsell': list,
        'specs': list, # for filters
        'supplement': list, # nutrition facts
        'variants': list, # if simple type: size, colors, dimesions, quantity - maybe diff prices: +/- or amount 
        'text_ingredients': str,
        'text_suggested': str,
        'text_warnings': str,
        'text_disclaimer': str,
        'hash_state': str,
    }

    @classmethod
    def _table(cls):
        return "{0}_product.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))

    @classmethod
    def load_raw(cls, data, _filter=[]):

        def process_num(v, prefix='.', to_int=False, delimiter='x'):
            if v:
                if '/' in v:
                    v = v.split('/')[0]
                v = re.sub(f"[^0-9{prefix}]", "", v)
                v = v.strip().rstrip('.').strip()
                if v and to_int:
                    v = int(v)
                if isinstance(v, str):
                    if delimiter and delimiter in v:
                        v = v.split(delimiter)
                return v

        _doc = {
            'category': 'product',
            'alias': data['urlName'],
            'title': data['displayName'],
            'publishedon': datetime.utcnow(),
            'is_active': True,
            'is_searchable': True,
            'tags': [],
            'content': data['description'],
            'product_id': data['id'],
            'product_type': 'grouped_key',
            'product_status': data['productStatus'], # str -> term string
            'stock_status': data['stockStatus'], # srt -> term string
            'stock_quantity': process_num(data['stockStatusMessage'], prefix='', to_int=True),
            'limit_quantity': data['quantityLimit'],
            'is_available': data['isAvailableToPurchase'],
            'brand_title_local': data['brandName'],
            'brand_alias': data['brandUrl'].split('/')[-1],
            'brand_code': data['brandCode'],
            'category_paths': data['canonicalPaths'],
            'product_tags': [item['displayName'] for item in data['flag']],
            'part_number': data['partNumber'],
            'image_indices': data['imageIndices'],
            'image_primary': data['primaryImageIndex'],
            'price_currency': 'USD',
            'price_list': data['listPriceAmount'],
            'price_discount': data['discountPriceAmount'],
            'is_discounted': (data['listPriceAmount'] - data['discountPriceAmount']) > 0,
            'discount_amount': data['listPriceAmount'] - data['discountPriceAmount'],
            # TODO if value < 0 process discount
            'discount_percent': (((data['listPriceAmount'] - data['discountPriceAmount']) * 100) / data['listPriceAmount']) if data['listPriceAmount'] > 0 else 0,
            'price_per_unit': process_num(data['pricePerUnit']),
            'price_discount_delta': 0,
            'price_discount_delta_percent': 0,
            'price_discount_prev': 0,
            'weight': [{'key': 'lb', 'value': process_num(data['weightLb'])}, {'key': 'kg', 'value': process_num(data['weightKg'])}],
            'dimensions': [{'key': 'in', 'value': process_num(data['dimensionsIn'], prefix='.x', delimiter='x')}, {'key': 'cm', 'value': process_num(data['dimensionsCm'], prefix='.x', delimiter='x')}],
            'package_quantity': process_num(data['packageQuantity'], prefix='', to_int=True),
            'package_quantity_float': process_num(data['packageQuantity'], prefix='.'),
            'ranks': [{'cid': item['categoryId'], 'rank': item['rank'], 'title': item['categoryDisplayName'], 'alias': item['categoryUrl'].split('/')[-1]} for item in data['productRanks']] if data['productRanks'] else [],
            'rating_avg': data['averageRating'],
            'rating_count': data['totalRatingCount'],
            'faq_questions': data['qna']['questionCount'],
            'faq_answers': data['qna']['answerCount'],
            'is_reviewed': True,
            'is_affiliate_mode': False,
            'partner_stores': [{
                'store': 'iherb.com',
                'deeplink': data['url'],
            }],
            'text_ingredients': data['ingredients'],
            'text_suggested': data['suggestedUse'],
            'text_warnings': data['warnings'],
            'text_disclaimer': data['disclaimer'],
        }

        if _filter:
            _doc = {k: v for k, v in _doc.items() if k in _filter}

        return _doc

    # @classmethod
    # def get_group_key(cls, items):
    #     return cls.generate_id(items)


class ProductUserContent(ElasticEntity):
    on_put = Signal()

    _schemas = {     
        'product_id': str,
        'category': str, # review, qna, qna_answer
        'publishedon': DateTimeField,
        'updatedon': DateTimeField,
        'postedon': DateTimeField,
        'is_active': bool,
        'language_code': str,
        'customer_nickname': str,
        'customer_username': str, # 88467CA91B, profile
        'customer_helpful': int,
        'customer_reviews': int,
        'customer_answers': int,
        'customer_images': int,
        'title': str,
        'content': str,
        'question_id': str,
        'helpful_yes': int,
        'helpful_no': int,
        'is_best': bool,
        'has_rewarded': bool,
        'verified_purchase': bool,
        'answers_count': int,
        'rating': int,
    }

    @classmethod
    def _table(cls):
        return "{0}_ugc.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))


class SnapProduct(ElasticEntity):
    on_put = Signal()
    on_complete = Signal()

    _schemas = { 
        'updatedon': DateTimeField,
        'update_raw': str,
        'price_discount_prev_date': DateTimeField,
        'price_discount_prev': float,
        'price_discount_delta': float,
        'price_discount_delta_percent': float,
        'product_id': int,

        'product_status': str,
        'stock_status': str,
        'stock_quantity': int,
        'limit_quantity': int,
        'is_available': bool,
        'price_list': float,
        'is_discounted': bool,
        'price_discount': float,
        'discount_amount': float,
        'discount_percent': float,
        'price_per_unit': float,
        'ranks': list,
        'rating_avg': float,
        'rating_count': int,
        'rating_count_local': int,
        'rating_stars': list,
        'faq_questions': int,
        'faq_answers': int,            
    }

    @classmethod
    def _table(cls):
        return "{0}_snap.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))


class SnapCategory(ElasticEntity):
    on_put = Signal()

    _schemas = { 
        'updatedon': DateTimeField,
        'update_raw': str,
        'title': str,
        'alias': str,
        'total': int,
        'ancestors': list,
        'ancestors_keys': list,
        'children': list,
        'cid': str,
        'external_id': str,
        'external_ancestors': list,
        'is_active': bool,
    }

    @classmethod
    def _table(cls):
        return "{0}_snap_category.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))


class ProductAggs(ElasticEntity):
    on_put = Signal()

    _schemas = { 
        'updatedon': DateTimeField,
        'publishedon': DateTimeField,
        'is_active': bool,
        'is_available': bool,
        'is_searchable': bool,
        'category_tree': list,
        'brand_title': str,
        'brand_alias': str,
        'brand_code': str,
        'rating_avg': float,
        'rating_count': int,
        'weight_kg': float,
        'price': float,
        'external_id': str,
        'suggest': str, # search_as_you_type
        'cover': str,
        'part_number': str,
        'slug': str,
        'vid': str,
        'name': str,
    }

    @classmethod
    def _table(cls):
        return "{0}_product_aggs.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))

    @classmethod
    def aggs_product(cls, _cnt=5000, _aggs_sort={'_key': 'asc'}, _ranges={}, **kwargs):
        _aggs = {
            "category": {
                "terms": {
                    "field": "category_tree.keyword",
                    "size": _cnt,
                    "order": _aggs_sort
                },
            },
            "brand": {
                "terms": {
                    "field": "brand_title.keyword",
                    "size": _cnt,
                    "order": _aggs_sort
                },
                "aggs": {
                    "brand_code": {
                        "terms": {
                            "field": "brand_code.keyword"
                        },
                    },
                },
            },
        }

        fields = {
            'rating': 'rating_avg',
            'price': 'price',
            'weight': 'weight_kg',
        }

        for k, v in _ranges.items():
            _aggs[k] = {
                'range': {
                    "field": fields[k],
                    "keyed": True,
                    "ranges": v
                }
            }

        aggs, resp = cls.aggs_request(_aggs, **kwargs) 

        def process_brand(item):
            return {
                'title': item['key'], 
                'count': item['doc_count'],
                'code': item['brand_code']['buckets'][0]['key'], 
            }

        def process_range(k, v):
            return {
                'value': v, 
                'code': k
            }

        return resp['hits']['hits'], resp['hits']['total']['value'], {
            'category': {item['key']: item['doc_count'] for item in aggs['category']['buckets']},
            'brand': [process_brand(item) for item in aggs['brand']['buckets']],
            'rating': reversed([process_range(k, v) for k, v in aggs['rating']['buckets'].items()]) if aggs.get('rating') else [],
            'price': [process_range(k, v) for k, v in aggs['price']['buckets'].items()] if aggs.get('price') else [],
            'weight': [process_range(k, v) for k, v in aggs['weight']['buckets'].items()]  if aggs.get('weight') else [],
        }


    @classmethod
    def search(cls, query, match_type='bool_prefix'):
        page = 1
        cpp = 6

        must = [
            {"multi_match" : {
                "query": query, 
                "type": match_type,
                "fields": [
                    "suggest",
                    "suggest._2gram",
                    "suggest._3gram",
                ] 
            }},
            {"term": {"is_active": True}},
            {"term": {"is_searchable": True}},
        ]

        q = {
            "query": {
                "bool": {
                    "must": must
                }
            },
            "highlight": {
                "pre_tags" : ['<em class="weight-600">'],
                "post_tags" : ['</em>'],
                "fields": {
                    "suggest._index_prefix": {
                        "type": "unified"
                    }
                }
            },
            "from": (page - 1) * cpp,
            "size": cpp
        }

        resp = current_app.es.search(index=cls._table(), body=q, request_timeout=60, ignore=[404], track_total_hits=True)
        logger.debug(f'Search query response: {resp}')

        if 'status' in resp and resp['status'] in [400, 404]:
            return []

        return resp


class ProductEvent(ElasticEntity):
    on_put = Signal()

    _schemas = { 
        'createdon': DateTimeField,
        'ip': str,
        'country': str,
        'country_iso': str,
        'ua': str,
        'checkout_id': str,
        'customer_id': str,
        'session_id': str,
        'event_type': str,
        'product_id': str,
        'variant_id': str,
        'external_id': str,
        'part_number': str,
        'price': float,
    }

    @classmethod
    def _table(cls):
        return "{0}_product_event.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))

    @classmethod
    def get_events(cls, event_type='wish', **kwargs):
        kwargs.update({'event_type': event_type})
        if current_user.is_authenticated and current_user.is_customer:
            kwargs.update({'customer_id': current_user.id})
        else:
            kwargs.update({'session_id': current_user.session_id})
        return ProductEvent.get(**kwargs)


class LoyaltyPoint(ElasticEntity):
    on_put = Signal()

    _schemas = { 
        'createdon': DateTimeField,
        'updatedon': DateTimeField,
        'customer_id': str,
        'customer_email': str,
        'order_id': str,
        'order_amount': float,
        'record_type': str, # debit, credit
        'is_hold': bool,
        'holdedon': DateTimeField,
        'amount': float,
        'description': str,
    }

    @classmethod
    def _table(cls):
        return "{0}_loyalty_point.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))

    @classmethod
    def balances(cls, _count=5, _count_aggs=10, _sort=[{'createdon': {'order': 'desc'}}], **kwargs):
        # interval, timezone, _range=None _aggs_cnt=1000
        _aggs = {
            'customer': {
                "terms": {
                    "field": "customer_id.keyword",
                    "size": _count_aggs,
                },
                "aggs": {
                    "amount_stats": {
                        "stats": {
                            "field": "amount"
                        },
                    },
                    "record_type": {
                        "terms": {
                            "field": "record_type.keyword"
                        },
                        "aggs": {
                            "amount_stats": {
                                "stats": {
                                    "field": "amount"
                                },
                            },
                        }
                    },
                },
            },
        } 

        aggs, resp = cls.aggs_request(_aggs, _count=_count, _sort=_sort, **kwargs)

        # must = []

        # if kwargs:
        #     def pre_field(k, v):
        #         return k if isinstance(v, (bool, int)) else '{0}.keyword'.format(k)
        #     must = [{"terms" if isinstance(v, list) else "term": {pre_field(k, v): v}} for k, v in kwargs.items()]

        # # if _range:
        # #     _f, _s, _e, _tz = _range
        # #     must.append({"range": {_f: {"gte": _s, "lte": _e, "time_zone": _tz}}})

        # q = {
        #     "query": {
        #         "bool": {
        #             "must": must
        #         }
        #     },
        #     "size": _count,
        #     "sort": _sort,
        #     "aggs": aggs
        # }

        # # logger.info(f'LoyaltyPoint.balances Request: {q}')
        # resp = current_app.es.search(index=cls._table(), body=q, request_timeout=60, ignore=[400, 404], track_total_hits=True)
        # # logger.info(f'LoyaltyPoint.balances Response: {resp}')

        # if 'status' in resp and resp['status'] in [400, 404]:
        #     return [], 0, {}

        # aggs = resp.get('aggregations', [])     

        if not aggs:
            return [], 0, {}

        balances = {}

        def process_record(items, k, v=0):
            for item in items:
                if item['key'] == k:
                    return item['amount_stats']['sum']
            return v

        for item in aggs['customer']['buckets']:
            balances[item['key']] = {
                'total': item['amount_stats']['sum'],
                'debit': process_record(item['record_type']['buckets'], 'DEBIT'),
                'credit': process_record(item['record_type']['buckets'], 'CREDIT')
            }

        return resp['hits']['hits'], resp['hits']['total']['value'], balances


class TaskLog(ElasticEntity):
    on_put = Signal()

    _schemas = { 
        'task_id': str,
        'worker': str,
        'timestamp': DateTimeField,
        'message': str,
        'event': str,
        'level': str,
        'size': int,
        'tags': list,
        'sid': str,
        'pid': str,
        'value': float,
    }

    @classmethod
    def _table(cls):
        return "{0}_tasklog.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))

    @classmethod
    def log(cls, **kwargs):
        _doc = {
            'worker': current_process().index + 1,
            'timestamp': pendulum.now('UTC'),
            'level': 'info',
            'size': 0,
        }
        _doc.update(kwargs)
        msg = _doc['message']
        logger.warning(f'Log message: {msg}')
        cls.put(cls.generate_id(_doc['timestamp'], _doc['task_id']), _doc)


    @classmethod
    def aggs_logs(cls, interval, timezone, _range=None, _cnt=1000, **kwargs):
        _aggs = {
            'sid': {
                "terms": {
                    "field": "sid.keyword",
                    "size": _cnt,
                    "order": { "_key": "desc" }
                },
                "aggs": {
                    "level": {
                        "terms": {
                            "field": "level.keyword"
                        },
                    },
                    "event": {
                        "terms": {
                            "field": "event.keyword"
                        },
                        "aggs": {
                            "traffic": {
                                "stats": {
                                    "field": "size"
                                },
                            },
                        }
                    },
                    "start": {
                        "min": {
                            "field": "timestamp"
                        },
                    },
                },
                
            },
            'timestamp': {
                "date_histogram": {
                    "field": 'timestamp',
                    "fixed_interval": interval,
                    "time_zone": timezone,
                },
                "aggs": {
                    "event": {
                        "terms": {
                            "field": "event.keyword"
                        },
                    }
                }
            },
        } 

        aggs, _ = cls.aggs_request(_aggs, _range, **kwargs)

        # must = []

        # if kwargs:
        #     def pre_field(k, v):
        #         return k if isinstance(v, (bool, int)) else '{0}.keyword'.format(k)
        #     must = [{"terms" if isinstance(v, list) else "term": {pre_field(k, v): v}} for k, v in kwargs.items()]

        # if _range:
        #     _f, _s, _e, _tz = _range
        #     must.append({"range": {_f: {"gte": _s, "lte": _e, "time_zone": _tz}}})

        # q = {
        #     "query": {
        #         "bool": {
        #             "must": must
        #         }
        #     },
        #     "size": 0,
        #     "aggs": aggs
        # }

        # # logger.info(f'aggs_logs Request: {q}')
        # resp = current_app.es.search(index=cls._table(), body=q, request_timeout=60, ignore=[400, 404])
        # # logger.info(f'aggs_logs Response: {resp}')

        # aggs = {}
        # if 'status' in resp and resp['status'] in [400, 404]:
        #     pass
        # else:
        #     aggs = resp.get('aggregations', [])            

        # logger.info(f'Aggs found: {aggs}')

        def process_sid(item):
            return {
                'sid': item['key'], 
                'event': item['event']['buckets'], 
                'level': item['level']['buckets'],
                'start': item['start']['value_as_string'],
            }

        def process_timestamp(item):
            return {'key': item['key_as_string'], 'count': item['doc_count'], 'event': item['event']['buckets']}

        return {
            'sid': [process_sid(item) for item in aggs['sid']['buckets']],
            'timestamp': [process_timestamp(item) for item in aggs['timestamp']['buckets']]
        }


class SyncLog(TaskLog):
    on_put = Signal()

    @classmethod
    def _table(cls):
        return "{0}_synclog.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))


class Affiliate(ElasticEntity):
    on_put = Signal()

    _schemas = { 
        'createdon': DateTimeField,
        'updatedon': DateTimeField,
        'status': str,
        'is_active': bool,
        'is_traffic_enabled': bool,
        'referral_id': str,
        'email': str,
        'password': str,
        'full_name': str,
        'external_id': str,
        'currency': str,
        'payment_method': str,
        'payment_account': str,
        'payment_note': str,
        'tier': str,
        'country': str,
        'country_iso': str,
        'language': str,
        'timezone': str,
        'comment': str,
        'api_private_token': bool,
        'api_public_token': str,
        'api_private_token': str,
    }

    @classmethod
    def _table(cls):
        return "{0}_affiliate.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))


class AffiliateOffer(ElasticEntity):
    on_put = Signal()

    _schemas = { 
        'createdon': DateTimeField,
        'updatedon': DateTimeField,
        'name': str,
        'is_active': bool,
        'is_private': bool,
        'tags': list,
        'content': str,
        'comment': str,
        'landing_pages': list,
        'conversion_types': list,
        'conversion_types_data': list,
        'tiers': list,
        'segments': list,
    }

    @classmethod
    def _table(cls):
        return "{0}_affiliate_offer.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))


class AffiliateCoupon(ElasticEntity):
    on_put = Signal()

    _schemas = { 
        'createdon': DateTimeField,
        'updatedon': DateTimeField,
        'is_active': bool,
        'promocode': str,
        'referral_id': str,
        'offer': str,
    }

    @classmethod
    def _table(cls):
        return "{0}_affiliate_coupon.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))


class AffiliateEvent(ElasticEntity):
    on_put = Signal()

    _schemas = { 
        'event': str,
        'timestamp': DateTimeField,
        'country': str,
        'country_iso': str,
        'cid': str,
        'sid': str,
        'external_cid': str,
        'fingerprint_id': str,
        'referral_id': str,
        'partner_tier': str,
        'promocode': str,
        'offer_id': str,
        'offer_name': str,
        'landing_id': str,
        'landing_name': str,
        'ip': str,
        'ua': str,
        'is_mobile': bool,
        'device': str,
        'browser': str,
        'browser_version': str,
        'os': str,
        'os_version': str,
        'ua_raw': str,
        's1': str,
        's2': str,
        's3': str,
        's4': str,
        's5': str,
        'v1': str,
        'v2': str,
        'v3': str,
        'v4': str,
        'v5': str,
        'conversion_status': str,
        'conversion_id': str,
        'conversion_type': str,
        'segment_name': str,
        'external_id': str,
        'customer_id': str,
        'customer_name': str,
        'currency': str,
        'revenue': float,
        'payable': float,
        'payout': float,
        'profit': float,
        'level': int,
        'is_paid': bool,
        'paid_on': DateTimeField,
        'paid_trx': str,
        'paid_note': str,
    }

    @classmethod
    def _table(cls):
        return "{0}_affiliate_event.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))

    @classmethod
    def aggs_payments(cls, **kwargs):
        _aggs = {
            'conversion_status': {
                "terms": {
                    "field": "conversion_status.keyword",
                },
                "aggs": {
                    "payout": {
                        "stats": {
                            "field": "payout"
                        },
                    },
                }
            },
        } 

        aggs, _ = cls.aggs_request(_aggs, **kwargs)

        if 'conversion_status' in aggs:
            return {item['key']: item['payout']['sum'] for item in aggs['conversion_status']['buckets']}

        return {}

    @classmethod
    def aggs_stats(cls, items, _range=None, timezone='UTC', **kwargs):
        _sub = {
            "event": {
                "terms": {
                    "field": "event.keyword",
                },
                "aggs": {
                    "payout": {
                        "stats": {
                            "field": "payout"
                        },
                    },
                    "payable": {
                        "stats": {
                            "field": "payable"
                        },
                    },
                    "revenue": {
                        "stats": {
                            "field": "revenue"
                        },
                    },
                }                
            }
        }
        _aggs = {}
        _aggs.update(_sub)
        for k, v in items:
            _aggs[k] = {
                "date_histogram": {
                    "field": 'timestamp',
                    "calendar_interval": v,
                    "time_zone": timezone,
                    "keyed": True,
                    "format": "yyyy-MM-dd",
                },
                "aggs": _sub
            }
 
        aggs, _ = cls.aggs_request(_aggs, _range, **kwargs)
        return aggs
    

class OddsEvent(ElasticEntity):
    on_put = Signal()

    _schemas = { 
        'source': str,
        'is_active': bool,
        'startedon': DateTimeField,
        'external_id': str,
        'category': str,
        'sub_category': str,
        'name': str,
    }

    @classmethod
    def _table(cls):
        return "{0}_odds_event.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))


class OddsMarket(ElasticEntity):
    on_put = Signal()

    _schemas = { 
        'source': str,
        'event_id': str,
        'updatedon': DateTimeField,
        'group_name': str,
        'external_id': str,
        'is_active': bool,
        'name': str,
        'odds': str, # '2.1'
        'odds_uk': str, # '7/1'
        'odds_us': str, # '+120'
    }

    @classmethod
    def _table(cls):
        return "{0}_odds_market.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))


class OddsWidget(ElasticEntity):
    on_put = Signal()

    _schemas = { 
        'createdon': DateTimeField,
        'updatedon': DateTimeField,
        'is_active': bool,
        'title': str,
        'alias': str,
        'startedon': DateTimeField,
        'notes': str,
        'groups': list,
        'sources': list,
        'events': list,
        'markets': list,
    }

    @classmethod
    def _table(cls):
        return "{0}_odds_widget.{1}".format(os.environ.get('PROJECT', 'project'), os.environ.get('VERSION', 'v1'))


# pydantic models


class UserModel(BaseModel):
    login: EmailStr

    @validator('login', allow_reuse=True)
    def fn_not_empty(cls, v):
        assert v != '', 'Required field'
        return v


class ManagerModel(BaseModel):
    login: EmailStr
    skype: str = ...

    @validator('login', 'skype', allow_reuse=True)
    def fn_not_empty(cls, v):
        assert v != '', 'Required field'
        return v


class SignupModel(BaseModel):
    login: EmailStr
    skype: str = ...
    invite_code: Optional[str] = None

    @validator('login', 'skype', allow_reuse=True)
    def fn_not_empty(cls, v):
        assert v != '', 'Required field'
        return v


class SignupModelInvite(SignupModel):
    invite_code: str = ...

    @validator('invite_code', allow_reuse=True)
    def fn_invite_code(cls, v):
        assert v != '', 'Required field'
        if v == current_app.config['DASHBOARD_INVITE']:
            return v

        try:
            f = Fernet(current_app.config['FERNET_KEY'])
            _obj = f.decrypt(v.encode())
            _token = loads(_obj)
            if isinstance(_token, dict):
                _ts = datetime.timestamp(datetime.utcnow())
                if _ts > _token['expired']:
                    logger.info(f'Token expired: {_token}, now: {_ts}')
                    assert False, 'Invite Expired'
                else:
                    logger.info(f'Token valid: {_token}')
                    return v
        except Exception as e:
            logger.error(f'Exception encrypt token: {e}')

        assert False, 'Invite Expired'


class AuthModel(BaseModel):
    login: EmailStr
    password: str = ...

    @validator('login', 'password', allow_reuse=True)
    def fn_not_empty(cls, v):
        assert v != '', 'Required field'
        return v


class CasinoModel(BaseModel):
    @validator('*', pre=True, allow_reuse=True)
    def empty_str_to_none(cls, v):
        if v == '':
            return None
        return v

    @validator('year', pre=True, allow_reuse=True)
    def year_validator(cls, v):
        if v:
            s = str(v)
            if s.isdigit() and (int(s) < 1990 or int(s) > datetime.utcnow().year):
                raise ValueError('Incorrect value')
        return v        

    @validator('games_limits', pre=True, allow_reuse=True)
    def games_limits_validator(cls, v):
        if v:
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        if item.get('min') and not item.get('min').isdigit():
                            raise ValueError('Only integer values accepted')
                        if item.get('max') and not item.get('max').isdigit():
                            raise ValueError('Only integer values accepted')
                return v
            raise ValueError('Incorrect value')
        return v        

    title: str = ...
    website: HttpUrl = ...
    languages: List[str] = []
    services: List[str] = []
    year: Optional[int]
    support_languages: List[str] = []
    support_livechat: bool = False
    support_email: Optional[EmailStr] = None
    support_phone: Optional[str] = None
    attachs: List[dict] = []
    logo: Optional[str] = None
    logo_small: Optional[str] = None
    licences: List[str] = []
    games: List[str] = []
    games_count: Optional[int]
    games_limits: List[dict] = []
    cashiers_limits: List[dict] = []
    software: List[str] = []
    currencies: conlist(str, min_length=1)
    default_currency: str
    deposits: List[str] = []
    min_deposit: Optional[int] = None
    min_deposit_float: float
    kyc_deposit: bool = False
    withdrawal: List[str] = []
    min_withdrawal: Optional[int] = None
    min_withdrawal_float: float
    withdrawal_monthly: Optional[int] = None
    kyc_withdrawal: bool = False
    welcome_package_max_bonus: Optional[int] = None
    welcome_package_match: Optional[int] = None
    welcome_package_fs: Optional[int] = None
    welcome_package: constr(max_length=50)
    welcome_package_note: Optional[constr(max_length=500)] = None
    welcome_package_wager: Optional[int] = None
    cashback: Optional[int] = None
    geo_whitelist: Optional[str] = None
    geo_blacklist: Optional[str] = None
    geo: List[str] = []
    content: Optional[str] = None


class CasinoProxyModel(CasinoModel):
    website: Optional[str] = None
    currencies: Optional[list] = []
    default_currency: Optional[str] = None
    min_deposit_float: Optional[float] = None
    min_withdrawal_float: Optional[float] = None
    welcome_package: Optional[str] = None
    welcome_package_note: Optional[str] = None

    @validator('games_limits', pre=True, allow_reuse=True)
    def games_limits_validator(cls, v):
        return v

class DomainModel(BaseModel):
    @validator('*', pre=True, allow_reuse=True)
    def empty_str_to_none(cls, v):
        if v == '':
            return None
        return v

    domain: str = ...
    endpoint: str = ...
    is_https: bool = False


class CampaignModel(BaseModel):
    @validator('*', pre=True, allow_reuse=True)
    def empty_str_to_none(cls, v):
        if v == '':
            return None
        return v

    name: str = ...
    domain: str = ...
    alias: str = ...
    groups: Optional[List[str]] = []
    ttl: int
    is_split: bool = False
    is_active: bool = False
    is_archive: bool = False
    notes: Optional[str] = None
    streams: conlist(dict, min_length=1)
    postback_processor: Optional[str] = None


class ActivityTicketModel(BaseModel):
    subject: str = ...
    contacts: str = ...
    name: str = ...
    message: str = ...

    @validator('subject', 'contacts', 'name', 'message', allow_reuse=True)
    def not_empty(cls, v):
        assert v != '', 'Required field'
        return v
    

class ActivitySubscribeModel(BaseModel):
    email: EmailStr
    is_agree: bool = False

    @validator('is_agree', pre=True, always=True, allow_reuse=True)
    def check_agree(cls, v):
        assert v == True, 'You must accept our terms'
        return v   


class ActivityFeedbackModel(BaseModel):
    rate: conint(ge=1, le=5)
    casino: str = ...
    casino_id: str = ...
    # name: Optional[str]
    # pros: Optional[str]
    # cons: Optional[str]                


class ActivityMissingModel(BaseModel):
    message: str = Field(..., max_length=1024)
    casino: str = ...
    casino_id: str = ...


class ActivityComplaintListModel(BaseModel):
    casino: str = ...
    amount: str = ...
    message: str = ...
    subject: str = ...
    username: str = ...
    email: EmailStr

    @validator('casino', 'message', 'subject', allow_reuse=True)
    def not_empty(cls, v):
        assert v != '', 'Required field'
        return v


class ActivityComplaintNameModel(BaseModel):
    casino_name: str = ...
    amount: str = ...
    message: str = ...
    subject: str = ...
    username: str = ...
    email: EmailStr

    @validator('casino_name', 'message', 'subject', allow_reuse=True)
    def not_empty(cls, v):
        assert v != '', 'Required field'
        return v


class ComplaintModel(BaseModel):
    @validator('*', pre=True, allow_reuse=True)
    def empty_str_to_none(cls, v):
        if v == '':
            return None
        return v

    username: str = None
    email: EmailStr = None
    country: str = ...
    casino_selected: dict = ...
    amount: str = None
    currency: str = None
    message: str = None
    comment: str = None
    status: str = ...
    subject: Optional[str] = None
    ip: str = ...
    is_active: bool = False
    rate: Optional[conint(ge=1, le=5)] = None
    replies: List[dict] = []
    createdon: Union[str, date] = ...
    completedon: Optional[Union[str, date]] = ...


class ComplaintReplyModel(BaseModel):
    @validator('*', pre=True, allow_reuse=True)
    def empty_str_to_none(cls, v):
        if v == '':
            return None
        return v

    reply: Optional[str] = ...


class TelegramBotModel(BaseModel):
    @validator('*', pre=True, allow_reuse=True)
    def empty_str_to_none(cls, v):
        if v == '':
            return None
        return v

    is_active: bool = False
    token: str = ...
    domain: str = ...
    tags: Optional[List[str]] = []
    username: Optional[str] = None
    modules: Optional[List[str]] = []
    can_join: bool = False
    can_read: bool = False


class TelegramChatModel(BaseModel):
    @validator('*', pre=True, allow_reuse=True)
    def empty_str_to_none(cls, v):
        if v == '':
            return None
        return v

    is_active: bool = False
    bot_admin: str = ...
    username: str = ...
    title: str = ...
    description: Optional[str] = None
    photo: Optional[str] = None
    tags: Optional[List[str]] = []
    can_send: bool = False
    can_invite: bool = False
    job_remove_system_msg: bool = False


class TelegramMessageModel(BaseModel):
    @validator('*', pre=True, allow_reuse=True)
    def empty_str_to_none(cls, v):
        if v == '':
            return None
        return v

    @validator('photo', pre=True)
    def photo_required(cls, v, values):
        if values['type'] == 'photo' and not v:
            raise ValueError('Required field')
        return v

    type: str = ...
    title: str = ...
    content: str = ...
    photo: Optional[str] = None
    recipients: conlist(str, min_length=1)
    tags: Optional[List[str]] = []
    send_without_notify: bool = False
    send_without_link_preview: bool = False
    send_pin_message: bool = False
    send_schedule: bool = False
    remove_schedule: bool = False
    scheduledon: Optional[str] = None
    removedon: Optional[str] = None
    send_task: bool = False
    status: Optional[str] = None
    buttons: List[dict] = []

class OddsWidgetModel(BaseModel):
    @validator('*', pre=True, allow_reuse=True)
    def empty_str_to_none(cls, v):
        if v == '':
            return None
        return v

    title: str = ...
    alias: str = ...
    groups: Optional[List[str]] = []
    is_active: bool = False
    notes: Optional[str] = None
    sources: Optional[List[str]] = []
    events: conlist(dict, min_length=1)
    markets: conlist(dict, min_length=1)
    startedon: Optional[Union[str, datetime]] = ...
