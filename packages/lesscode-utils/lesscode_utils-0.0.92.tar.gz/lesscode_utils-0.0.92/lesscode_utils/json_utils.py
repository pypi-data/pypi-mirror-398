import json


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        object_class_name = o.__class__.__name__
        if object_class_name == "ObjectId":
            return str(o)
        elif object_class_name == "datetime":
            return str(o)
        elif object_class_name == "date":
            return str(o)
        elif object_class_name == "bytes":
            return str(o, encoding="utf-8")
        elif object_class_name == "set":
            return list(o)
        elif object_class_name == "Decimal":
            return str(o)
        elif object_class_name == "ndarray":
            return o.tolist()
        elif object_class_name == "Series":
            return o.tolist()
        elif object_class_name == "DataFrame":
            return o.to_dict(orient='records')
        return json.JSONEncoder.default(self, o)
