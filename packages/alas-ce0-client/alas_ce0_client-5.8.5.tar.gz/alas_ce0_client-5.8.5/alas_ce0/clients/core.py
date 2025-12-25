from alas_ce0.common.client_base import ApiClientBase


class CoreClient(ApiClientBase):
    entity_endpoint_base_url = '/core'

    def get_mock_rut(self, full_name):
        params = {
            'full_name': full_name,
        }
        result= self.http_post_json(self.entity_endpoint_base_url + '/mock/get-rut', params)
        if result.response.status == 200:
            return result.content["rut"]

        return None

    def validate_matrix(self, structure_id):
        params = {
            'structure_id': structure_id,
        }
        result = self.http_post_json(self.entity_endpoint_base_url + '/comune/validate-matrix', params)
        if result.response.status == 200:
            return result.content["result"]

        return None