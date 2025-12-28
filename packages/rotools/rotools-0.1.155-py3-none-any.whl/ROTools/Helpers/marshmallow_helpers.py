import logging

from ROTools.core.DictObj import DictObj


log = logging.getLogger(__name__)

def parse_marshmallow(schema, request, log_name=False, raw_dict=False, throw=False):
    from flask import jsonify
    from marshmallow import ValidationError
    try:
        data = schema.load(request.form if request.form else request.get_json())
        if log_name:
            log.info(f"parsed data [{log_name}] : {data}")
        return data if raw_dict else DictObj(data)
    except ValidationError as err:
        if throw:
            raise
        return jsonify({"error": "Invalid data", "messages": err.messages}), 400
