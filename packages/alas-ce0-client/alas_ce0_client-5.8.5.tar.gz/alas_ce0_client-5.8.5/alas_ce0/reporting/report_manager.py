from alas_ce0.common.client_base import EntityClientBase


class ReportClient(EntityClientBase):
    entity_endpoint_base_url = '/reporting/reports-manager/'

    def get_delivery_orders_report(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_delivery-orders-report", params)
