import async_timeout


async def get_json(session, url, user_agent=None):
    headers = {'user-agent': f'application: MercuryBot contact: {user_agent}',
               'content-type': 'application/json'}
    with async_timeout.timeout(15):
        async with session.get(url, headers=headers) as response:
            resp = await response.json()
            resp_code = response.status
            return {'resp': resp, 'code': resp_code}
