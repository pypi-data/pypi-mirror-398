from alas_ce0.common.client_base import EntityClientBase


class BulkClient(EntityClientBase):
    entity_endpoint_base_url = '/management/bulks/'

    def __init__(self, country_code='cl', **kwargs):
        super(BulkClient, self).__init__(**kwargs)
        self.entity_endpoint_base_url += country_code + '/'
        self.headers['Authorization'] = self.headers['Authorization'].replace("\n", "")

    def generate_bulks(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_generate-bulks", params)

    def change_status(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_change-status", params)

    def ti_controlled_receive(self, code):
        return self.http_post_json(self.entity_endpoint_base_url + "_ti-controlled-receive", code)

    def ser_travelling_receive(self, code):
        return self.http_post_json(self.entity_endpoint_base_url + "_ser-travelling-receive", code)

    def ser_travelling_receive_right(self, code, event_info):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_ser-travelling-receive-right".format(code), event_info)
    
    def cd_travelling_receive(self, id, event_info):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_cd-travelling-receive".format(id), event_info)

    def get_attachment_content(self, id, att_file_name):
        return self.http_get(
            self.entity_endpoint_base_url + "{0}/attachment/{1}".format(id, att_file_name)
        )
