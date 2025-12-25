from alas_ce0.common.client_base import EntityClientBase


class DiaryClient(EntityClientBase):
    entity_endpoint_base_url = '/management/diary/'

    def __init__(self, country_code='cl', **kwargs):
        super(DiaryClient, self).__init__(**kwargs)
        self.entity_endpoint_base_url += country_code + '/'
        self.headers['Authorization'] = self.headers['Authorization'].replace("\n", "")