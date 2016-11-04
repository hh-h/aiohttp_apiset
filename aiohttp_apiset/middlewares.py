import asyncio
import collections
import json

from aiohttp import web, multidict


class JsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, multidict.MultiDict):
            return {k: o.getall(k) for k in o}
        elif isinstance(o, collections.MutableMapping):
            return {**o}
        return super().default(o)

    @classmethod
    def dumps(cls, *args, **kwargs):
        kwargs.setdefault('cls', cls)
        return json.dumps(*args, **kwargs)


@asyncio.coroutine
def jsonify(app, handler):
    dumps = app.get('dumps', JsonEncoder.dumps)

    @asyncio.coroutine
    def process(request):
        try:
            response = yield from handler(request)
        except web.HTTPException as ex:
            if not isinstance(ex.reason, str):
                return web.json_response(
                    {'errors': ex.reason}, status=ex.status, dumps=dumps)
            elif ex.status > 399:
                return web.json_response(
                    {'error': ex.reason}, status=ex.status, dumps=dumps)
            raise
        else:
            if isinstance(response, dict):
                status = response.get('status', 200)
                if not isinstance(status, int):
                    status = 200
                return web.json_response(
                    response, status=status, dumps=dumps)
            elif not isinstance(response, web.StreamResponse):
                return web.json_response(response, dumps=dumps)
            return response
    return process
