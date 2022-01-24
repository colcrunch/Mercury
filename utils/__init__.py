import async_timeout
from datetime import timedelta


async def get_json(session, url, user_agent=None):
    headers = {'user-agent': f'application: MercuryBot contact: {user_agent}',
               'content-type': 'application/json'}
    with async_timeout.timeout(15):
        async with session.get(url, headers=headers) as response:
            resp = await response.json()
            resp_code = response.status
            return {'resp': resp, 'code': resp_code}


def strftdelta(tdelta: timedelta) -> str:
    """
    Converts a timedelta object to a string.
    :param tdelta:
    :return:
    """
    d = dict(days=tdelta.days)
    if d['days'] >= 365:
        d['yrs'], rem = divmod(d['days'], 365)
        d['mos'], rem = divmod(rem, 30)
        d['days'] = rem
    d['hrs'], rem = divmod(tdelta.seconds, 3600)
    d['min'], d['sec'] = divmod(rem, 60)

    if 'yrs' in d:
        fmt = '{yrs}y {mos}m {days}d {hrs}h {min}m'
    elif d['min'] == 0:
        fmt = '{sec}s'
    elif d['hrs'] == 0:
        fmt = '{min}m {sec}s'
    elif d['days'] == 0:
        fmt = '{hrs}h {min}m {sec}s'
    else:
        fmt = '{days}d {hrs}h {min}m {sec}s'

    return fmt.format(**d)
