from typing import Any, Union
from flask.json.provider import JSONProvider
from orjson import loads, dumps, OPT_INDENT_2
from flask import Flask, Response, make_response
from splash.lib.features import Feature, get_feature

class ORJSONProvider(JSONProvider):
    _prettify_feature: Feature

    def __init__(self, app: Flask):
        super().__init__(app)

        self._prettify_feature = get_feature('PRETTIFY_RENDERED_JSON_ENABLED')

    def loads(self, s: Union[str, bytes], **kwargs: Any) -> Any:
        return loads(s)

    def dumps(self, obj: Any, **kwargs: Any) -> str:
        if self._prettify_feature.enabled:
            serialized = dumps(obj, option=OPT_INDENT_2)
        else:
            serialized = dumps(obj)

        return serialized.decode('utf-8')

    def response(self, *args: Any, **kwargs: Any) -> Response:
        json = self.dumps(*args, **kwargs)
        res = make_response(json)
        res.content_type = 'application/json'

        return res
