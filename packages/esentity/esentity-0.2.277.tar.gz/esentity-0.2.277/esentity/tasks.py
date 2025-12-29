#coding: utf-8
from flask import current_app
import os
from datetime import datetime, timedelta
from json import dumps, loads
import requests
from loguru import logger 
from notifiers import get_notifier
import pycountry 
from emoji import emojize
from esentity.models import TdsCampaign, TdsHit, Page, Activity, u_func
from esentity.telegram import telegram_api
from esentity.filters import func_full_url
import time
import ipaddress
from celery import shared_task
import jinja2
import pendulum
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import pygal
from pygal.style import Style
from urllib.parse import urlparse
from curl_cffi import requests as req_cffi

@shared_task
def add_vote(activity):
    logger.info('Add Vote: {0}'.format(activity))

    objs, total = Page.get(_id=activity['casino_id'])
    if total == 1:
        obj = objs.pop()
        _res = []
        _found = False
        _update = True

        hash = Activity.generate_id(activity['ip'], activity['ua'], activity['cid'])
        hash_dt = Activity.generate_id(activity['createdon'], activity['ip'], activity['ua'], activity['cid'])

        for item in obj.comments:
            if 'hash' in item and item['hash'] in [hash, hash_dt]:
                if not item['is_disable']:
                    item['publishedon'] = activity['createdon'] 
                    item['rate'] = activity['rate']

                    item['comment_pros'] = activity['pros']
                    item['comment_cons'] = activity['cons']
                    item['author'] = activity['name']
                else:
                    logger.info('Vote found: {0}, but is_disable'.format(item['hash']))
                    _update = False
                _found = True
            _res.append(item)
        
        if not _found:
            _res.insert(0, {
                'is_disable': False,
                'publishedon': activity['createdon'],
                'ip': activity['ip'],
                'country': activity['country_iso'],
                'hash': hash,

                'rate': activity['rate'],
                'comment_pros': activity.get('pros'),
                'comment_cons': activity.get('cons'),
                'author': activity.get('name'),
            })                

        if _update:
            obj.comments = sorted(_res, key=lambda d: d['publishedon'])
            resp, obj = Page.put(obj._id, obj.to_dict(), _signal=False)
            logger.info('Update casino [{1}]: {0}'.format(resp, obj.title))


@shared_task
def send_notify(msg, channel='default'):
    n = get_notifier('telegram')

    bots = current_app.config['TELEGRAM_TOKEN']
    _c = None
    if isinstance(bots, dict):
        if channel in bots:
            _c = bots[channel]
    elif isinstance(bots, str):
        _c = bots

    if _c:
        for cid in current_app.config['TELEGRAM_RECIPIENTS']:
            res = n.notify(
                message=f"[{current_app.config['TELEGRAM_PREFIX_MESSAGE']}] {emojize(msg)}", 
                token=_c, 
                chat_id=cid,
                disable_web_page_preview=True,
                disable_notification=True,
            )
            logger.info('Notify response: {0}'.format(res))


@shared_task
def send_email(template, to, subject, tv):
    _res = None
    _endpoint = current_app.config['MAIL_ENDPOINT']
    logger.info(f'Send email by: {_endpoint}')

    if 'mailgun.net/v3/' in _endpoint:
        _res = requests.post(
            _endpoint,
            auth=("api", current_app.config['MAIL_TOKEN']),
            data={
                "from": current_app.config['MAIL_FROM'],
                "to": to,
                "subject": subject,
                "template": template,
                "h:X-Mailgun-Variables": dumps(tv)
            })
    elif '10.8.0.1' in _endpoint or 'smtp.' in _endpoint:
        _, sender_email = current_app.config['MAIL_FROM']

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = formataddr(current_app.config['MAIL_FROM'])
        message["To"] = to

        t_plain = current_app.jinja_env.get_template(f'_email-plain-{template}.html')
        message.attach(MIMEText(t_plain.render(**tv), "plain"))

        t_html = current_app.jinja_env.get_template(f'_email-html-{template}.html')
        message.attach(MIMEText(t_html.render(**tv), "html") )

        context = ssl._create_unverified_context()
        host, port = _endpoint.split(":")

        with smtplib.SMTP_SSL(host, port, context=context) as server:
            try:
                login = sender_email
                token = current_app.config['MAIL_TOKEN']
                if ':' in token:
                    login, token = token.split(':')

                server.login(login, token)
                server.sendmail(sender_email, to, message.as_string())
                logger.info(f'Email ({template}) to {to} has been sent')
            except Exception as e:
                logger.warning(f'Email ({template}) to {to} send exception: {e}')
            finally:
                server.quit() 

    elif 'api.elasticemail.com/v4/' in _endpoint:
        _project = os.environ.get('PROJECT', 'project')
        _data = {
            "Recipients": {
                "To": [to]
            },
            "Content": {
                "Merge": tv,
                "From": current_app.config['MAIL_FROM'],
                "ReplyTo": current_app.config['MAIL_FROM'],
                "Subject": subject,
                "TemplateName": f"{_project}.{template}"
            }
        }

        _res = requests.post(
            _endpoint, 
            headers={'X-ElasticEmail-ApiKey': current_app.config['MAIL_TOKEN']},
            json=_data
        )

    if _res != None:
        logger.info(f'API response code: {_res.status_code}, content: {_res.json()}')
        
        if _res.status_code in [200]:
            logger.info(f'Email ({template}) send result: {_res.json()}')
        else:
            logger.info(f'Email ({template}) response: {_res.status_code}')


@shared_task
def tdscampaign_bots(data, section):

    def process_item(v, k):
        current_app.redis.sadd(f'tds_bots_{k}', v)

    for item in data:
        s = item
        if not '#' in s:
            if section == 'ip':
                if '-' in s:
                    min, max = s.split('-')
                    min = ipaddress.ip_address(min)
                    max = ipaddress.ip_address(max)
                    if min.version == 4 and max.version == 4 and min < max:
                        i = 0
                        while min <= max:
                            _v = ipaddress.ip_address(min) + i
                            logger.info(f'ip_address found: {_v}')
                            process_item(int(_v), 'ip')
                            i += 1
                else:
                    try:
                        ip_obj = ipaddress.ip_address(s)
                        if ip_obj.version == 4:
                            logger.info(f'ip_address found: {ip_obj}')
                            process_item(int(ip_obj), 'ip')
                    except ValueError:
                        try:
                            network = ipaddress.ip_network(s)
                            logger.info(f'ip_network found: {network}, hosts: {network.num_addresses}')

                            for _ip in network:
                                if _ip.version == 4:
                                    logger.info(f'ip_address found: {_ip}')
                                    process_item(int(_ip), 'ip')

                        except ValueError:
                            pass
            elif section == 'ua':
                logger.info(f'ua found: {s}')
                process_item(s, 'ua')


@shared_task
def tdscampaign_setup(id, campaign):
    logger.info('Setup TDS campaign: {0}'.format(campaign['name']))
    key = '{0}{1}'.format(campaign['domain'], campaign['alias'])
    current_app.redis.hset('tds_channels_url', id, key)

    if campaign['is_active']:
        campaign['id'] = id
        current_app.redis.hset('tds_channels', key, dumps(campaign, default=str))
        logger.info('Add campaign')
    else:
        current_app.redis.hdel('tds_channels', key)
        logger.info('Remove campaign')


@shared_task
def tdscampaign_clear(id):
    logger.info('Clear campaign stats: {0}'.format(id))
    campaigns, total = TdsCampaign.get(_id=id)
    if total == 1:
        campaign = campaigns.pop()
        if not campaign.is_active:
            hits, total = TdsHit.get(
                campaign_id=campaign._id,
                _process=False, 
                _source=False, 
                _all=True,
            )
            logger.info(f'Hits for remove: {total}')
            for item in hits:
                resp = TdsHit.delete(item['_id'], _refresh=False)
                logger.info(f'Hit removed: {resp}')

            current_app.redis.delete(f"tds_uniq_{campaign.alias}")
            logger.info(f'Uniq stack for {campaign.alias} removed')
        else:
            logger.warning(f'Campaign {campaign.name} is active, only disabled may by cleared')


@shared_task
def tdscampaign_hit(_doc):
    logger.info(f'Process TDS click: {_doc}')

    _cn = pycountry.countries.get(alpha_2=_doc['country_iso'])
    _doc['country'] = _cn.name if _cn else 'United Kingdom'

    resp, _ = TdsHit.put(TdsHit.generate_id(_doc['ip'], _doc['click_id']), _doc, _refresh=False, _signal=False)
    logger.info(f'Hit response: {resp}')

    _a = ''
    if _doc['action'] == '404':
        _a = ', 404'
    elif _doc['action'] in ['http', 'campaign', 'js']:
        _a = f", url: {_doc['url']}"

    msg = f"Hit: {_doc['campaign_name']} | {_doc['stream_name']} [{_doc['click_id']}], IP: {_doc['ip']} [{_doc['country_iso'].upper()}], is_bot: {_doc['is_bot']}{_a}"
    send_notify.apply_async(args=[msg])


@shared_task
def backup(indices, prefix):
    host = '{0}:{1}'.format(os.environ.get('ES', 'localhost'), 9200)
    logger.info('Process Snapshot Elasticsearch: {0}'.format(host))

    snap = f"{prefix}{datetime.utcnow().strftime('%Y-%m-%d')}"
    logger.info('Snap: {0}'.format(snap))

    snap_url = 'http://{0}/_snapshot/backup/{1}'.format(host, snap)

    r = requests.get(snap_url)
    if r.status_code == 200:
        r = requests.delete(snap_url)        
        logger.info('Snapshot {0} already exist, remove it: {1}'.format(snap, r.json()))

    if indices:
        r = requests.put(snap_url, json={'indices': indices})
        logger.info('Snapshot create: {0}, response: {1}'.format(r.status_code, r.json()))

        if r.status_code == 200:
            while True:
                time.sleep(5)
                r = requests.get(snap_url)
                res = r.json()

                for item in res['snapshots']:
                    if item['snapshot'] == snap:
                        if item['state'] == 'SUCCESS':
                            logger.info('Snapshot created: {0}'.format(res))

                            wl = [snap] + ['{1}{0}'.format((datetime.utcnow()-timedelta(days=i)).strftime('%Y-%m-%d'), prefix) for i in [1, 2, 3, 4, 5]]
                            logger.info('Actual Snaps: {0}'.format(wl))

                            snaps_url = 'http://{0}/_snapshot/backup/_all'.format(host)
                            r = requests.get(snaps_url)
                            if r.status_code == 200:
                                res = r.json()
                                for item in res['snapshots']:
                                    if prefix in item['snapshot'] and item['snapshot'] not in wl:
                                        snap_url = 'http://{0}/_snapshot/backup/{1}'.format(host, item['snapshot'])
                                        r = requests.delete(snap_url)        
                                        logger.info('Remove old snapshot: {0}'.format(item['snapshot']))
                            return
                        else:
                            logger.info('Snapshot {0} status: {1}'.format(snap, item['state']))
                        break


@shared_task
def process_tg_message(domain, bot_id, message):
    # delete_chat_photo
    # group_chat_created
    # supergroup_chat_created
    # channel_chat_created

    _data = current_app.redis.hget('tg_webhooks', f'{domain}:{bot_id}')
    if _data:
        _jobs = loads(_data)
        logger.info(f'Webhook jobs found: {_jobs}')

        uid = message['update_id']
        msg = message['message']
        mid = msg['message_id']
        cid = msg['chat']['id']

        logger.info(f'Process message, bot: {bot_id}, update_id: {uid}')
        logger.info(f'Message body: {msg}')

        if 'spectator' in _jobs['modules']:
            job = _jobs['jobs'].get(str(cid))
            if job:
                logger.info(f'Job for {cid} found: {job}')
                if job['job_remove_system_msg'] and ('new_chat_title' in msg or 'left_chat_member' in msg or 'new_chat_member' in msg or 'new_chat_photo' in msg):
                    telegram_api(_jobs['token'], 'deleteMessage', json={'chat_id': cid, 'message_id': mid})
                    logger.info(f"Message {mid} in {msg['chat']['title']} removed")
            else:
                logger.info(f'Job for {cid} not found')
    else:
        logger.info(f'Webhook disable or not found, bot_id: {bot_id}, domain: {domain}')



@shared_task
def build_sitemap():
    env = jinja2.Environment()
    tpl = env.from_string('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{% for item in items %}<url><loc>{{ item.url }}</loc><lastmod>{{ item.lastmod }}</lastmod></url>{% endfor %}</urlset>')

    sitemaps = list()

    with current_app.test_request_context(base_url=func_full_url()):
        for item in ['home']:
            for locale in current_app.config['AVAILABLE_LOCALE']:
                url = u_func(item, lang_code=locale, _external=True)
                sitemaps.append({
                    'url': url, 
                    'lastmod': pendulum.now('UTC')
                })
                logger.info('Add static page: {0}'.format(url))

        pages, found = Page.get(
            is_active=True, 
            is_searchable=True, 
            is_redirect=False, 
            _all=True,
        )
        logger.info('Searchable pages: {0}'.format(found))

        for page in pages:
            if url := page.path:
                url = func_full_url(url)
                sitemaps.append({
                    'url': url, 
                    'lastmod': page.updatedon.date() if page.updatedon else pendulum.now('UTC')
                })
                logger.info('Add searchable page: {0}'.format(url))

    sitemap_path = f'{current_app.static_folder}/sitemap.xml'
    with open(sitemap_path, 'w+') as f:
        f.write(tpl.render(items=sitemaps))

    logger.info(f'Complete build sitemap, total pages: {len(sitemaps)}')


@shared_task
def process_geo(condition):
    logger.info('Task process_geo: {0}'.format(condition))

    items, found = Page.get(
        category='provider',
        is_active=True,
        is_searchable=True,
        is_redirect=False,
        is_draft=False,
        is_sandbox=False,
        locale='en',
        _all=True,
        _sort=[{'title.keyword': {'order': 'asc'}}]
    )        
    logger.info(f'We found casinos: {found}')

    send_notify.apply_async(args=[f'process_geo: total casino found: {found}, started', 'notify'])

    i = 0
    for item in items:
        if condition in item.geo_whitelist:
            i += 1

            logger.info(f'#{i}. Process casino: {item.title}')

            _doc = item.to_dict()

            _c, _, _ = Page.get_countries(_doc['geo_whitelist'], _doc['geo_blacklist'])

            if _c:
                logger.info(f"Countries IN: {len(_doc['geo'])}")
                _doc['geo'] = _c
                logger.info(f"Countries OUT: {len(_doc['geo'])}")

                resp, _ = Page.put(item._id, _doc, _signal=False)
                logger.info(f'Response on save: {resp}')

    send_notify.apply_async(args=[f'process_geo: finished, processed casinos: {i}', 'notify'])


@shared_task()
def traffic_check(id, folder=None, color=None, proxy_host=None, proxy_ports=[], ua=None, _version='6.12.11'):
    if item := Page.get_one(_id=id):
        logger.info(f'traffic_check: casino found: {item.title}, path: {item.path}, domain: {item.website}, traffic: {item.traffic}, rank: {item.rank}')

        def req(url):
            session = req_cffi.Session()

            for port in proxy_ports or [None]:
                logger.info(f'Use proxy port: {port}')

                _headers = {'X-Extension-Version': _version}
                if ua:
                    _headers['User-Agent'] = ua

                try:
                    r = session.get(url,
                        proxies=dict(http=f'{proxy_host}:{port}', https=f'{proxy_host}:{port}') if proxy_host and port else None,
                        headers=_headers
                    )

                    if r:
                        logger.success(f'traffic_check response {url}: {r.status_code}')
                        data = r.json()
                        logger.info(f'Data: {data}')

                        history = data['EstimatedMonthlyVisits']
                        geo = data['TopCountryShares']

                        return history, geo
                    else:
                        logger.error(f'traffic_check response {url}: {r.status_code}')

                except Exception as e:
                    logger.error(f'traffic_check response {url} exception: {e}')            

        need_update = False
        for version in [item.to_dict()] + [_t for _t in item.translations if _t.get('is_active')]:
            _locale = version.get('locale')
            logger.info(f"Process version: {_locale}")

            if version.get('website'):
                uri = urlparse(version['website'])

                if uri.hostname:
                    url = f'https://data.similarweb.com/api/v1/data?domain={uri.hostname}'
                    if resp := req(url):
                        history, geo = resp

                        tf = False
                        tg = False

                        version['params'] = version.get('params', [])

                        for k in version['params']:
                            if k['key'] == 'traffic':
                                _h = dict(loads(k['value']), **history)
                                if history:
                                    k['value'] = dumps(_h)
                                tf = True
                                history = _h
                            elif k['key'] == 'geo':
                                k['value'] = dumps(geo)
                                tg = True

                        if not tf:
                            version['params'].append({'key': 'traffic', 'value': dumps(history)})
                        if not tg:
                            version['params'].append({'key': 'geo', 'value': dumps(geo)})

                        logger.info(f"Version locale: {_locale}, param for update: {version['params']}")

                        if history:
                            p = version.get('traffic')
                            version['traffic'] = int(history[list(history)[-1]])
                            logger.info(f"New traffic value: {version['traffic']}")

                            version['traffic_delta'] = 0
                            version['traffic_delta_percent'] = 0

                            if len(history) > 1:
                                kc = list(history)[-1]
                                kp = list(history)[-2]

                                version['traffic_delta'] = history[kc] - history[kp]
                                if history[kp]:
                                    version['traffic_delta_percent'] = int((version['traffic_delta'] / history[kp]) * 100 * 100)
                                else:
                                    if version['traffic']:
                                        version['traffic_delta_percent'] = 100

                                if filter:
                                    hash = Activity.generate_id(uri.hostname)
                                    s = current_app.config['UPLOADS_DEFAULT_DEST'] + f'/{folder}/v2/{hash}.svg'
                                    with open(s, 'wb') as tmp:
                                        custom_style = Style(
                                            background='transparent',
                                            plot_background='transparent',
                                            stroke_width=3,
                                            colors=(color or '#43a047', )
                                        )
                                        chart = pygal.Line(style=custom_style) # interpolate='cubic', 
                                        v = [int(v) for _, v in history.items()]
                                        chart.add('', v)
                                        _raw = chart.render_sparkline(width=300, height=70)
                                        tmp.write(_raw)
                                        logger.success(f'Casino: {item.title}, traffic chart generated: {s}, values for chart: {v}')

                            if not version['traffic']:
                                msg = f":high_voltage: Empty traffic ({item.title}), locale: {_locale}, website: {version['website']}, path: {item.path}"
                                send_notify.apply_async(args=[msg, 'notify'])
                            else:
                                if p != version['traffic']:
                                    msg = f"Update traffic ({item.title}), locale: {_locale}: {p} => {version['traffic']}, website: {version['website']}"
                                    send_notify.apply_async(args=[msg, 'notify'])

                        need_update = True
                else:
                    msg = f":high_voltage: Casino ({item.title}), locale: {_locale} need fix domain: {version['website']}, path: {item.path}"
                    send_notify.apply_async(args=[msg, 'notify'])
            else:
                msg = f":high_voltage: Casino ({item.title}), locale: {_locale} empty website, path: {item.path}"
                send_notify.apply_async(args=[msg, 'notify'])

        if need_update:
            _doc = item.to_dict()
            # logger.info(f'Document for update: {_doc}')

            resp, _ = Page.put(item._id, _doc, _signal=False)
            logger.info(f'Response on save: {resp}')
