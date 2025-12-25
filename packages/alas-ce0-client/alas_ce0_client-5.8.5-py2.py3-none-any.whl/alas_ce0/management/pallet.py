from alas_ce0.common.client_base import EntityClientBase


class PalletClient(EntityClientBase):
    entity_endpoint_base_url = '/management/pallets/'

    def __init__(self, country_code='cl', **kwargs):
        super(PalletClient, self).__init__(**kwargs)
        self.entity_endpoint_base_url += country_code + '/'
        self.headers['Authorization'] = self.headers['Authorization'].replace("\n", "")

    def generate_pallets(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_generate-pallets", params)

    def get_attachment_content(self, id, att_file_name):
        return self.http_get(
            self.entity_endpoint_base_url + "{0}/attachment/{1}".format(id, att_file_name)
        )
