import base64
import gzip
import json

class FormatConvert:
    @staticmethod
    def bytes2base64(text, encoding="utf-8"):
        return base64.encodebytes(text).decode(encoding)

    @staticmethod
    def base642bytes(text, encoding="utf-8"):
        return base64.decodebytes(text.encode(encoding))

    @staticmethod
    def json2str(data):
        return json.dumps(data, separators=(",", ":"))

    @staticmethod
    def str2json(strs):
        return json.loads(strs)

    @staticmethod
    def base642json(text, encoding="utf-8"):
        return json.loads(base64.decodebytes(text.encode(encoding)).decode(encoding))

    @staticmethod
    def json2base64(data, encoding="utf-8"):
        return base64.encodebytes(json.dumps(data, separators=(",", ":")).encode(encoding)).decode(encoding)

    @staticmethod
    def ungzip_base64_to_json(text, encoding="utf-8"):
        return json.loads(gzip.decompress(base64.b64decode(text)).decode(encoding))

    @staticmethod
    def ungzip_base64_to_str(text, encoding="utf-8"):
        return gzip.decompress(base64.b64decode(text)).decode(encoding)

    @staticmethod
    def gzip_json_to_base64(data, encoding="utf-8"):
        return base64.encodebytes(
            gzip.compress(json.dumps(data, separators=(", ", ": ")).encode(encoding), compresslevel=9)
        ).decode(encoding)

    @staticmethod
    def gzip_base64_to_base64(data, encoding="utf-8"):
        return base64.encodebytes(gzip.compress(base64.b64decode(data))).decode(encoding)
