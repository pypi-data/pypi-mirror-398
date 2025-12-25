from base64 import b64encode as encodestring

from alas_ce0.common.client_base import ApiClientBase


class ConfigurationClient(ApiClientBase):
    entity_endpoint_base_url = '/management/configurations/'

    def set(self, config_name, content):
        b = encodestring(content.encode('utf-8', errors='strict'))
        base64_content = b.decode('utf-8')

        params = {
            'file_name': config_name,
            'base64_content': base64_content
        }
        return self.http_post_json(self.entity_endpoint_base_url + '_set', params)

    def get(self, config_name):
        return self.http_get(self.entity_endpoint_base_url + config_name)