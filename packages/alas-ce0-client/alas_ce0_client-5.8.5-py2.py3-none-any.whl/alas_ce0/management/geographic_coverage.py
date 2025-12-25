from alas_ce0.common.client_base import EntityClientBase


class GeographicCoverageClient(EntityClientBase):
    entity_endpoint_base_url = '/management/geographic-coverages/'

    def __init__(self, country_code='cl', **kwargs):
        super(GeographicCoverageClient, self).__init__(**kwargs)
        self.entity_endpoint_base_url += country_code + '/'

    def get_structure_id(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_get-structure-id", params)

    def get_structure_id(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_get-structure-id", params)


    def polygon_finder(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_polygon-finder", params)

    def polygon_list(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_polygons-list", params)

