from alas_ce0.common.client_base import EntityClientBase


class PolygonClient(EntityClientBase):
    entity_endpoint_base_url = '/management/polygons/'

    def __init__(self, country_code='cl', **kwargs):
        super(PolygonClient, self).__init__(**kwargs)
        self.entity_endpoint_base_url += country_code + '/'
        self.headers['Authorization'] = self.headers['Authorization'].replace("\n", "")

