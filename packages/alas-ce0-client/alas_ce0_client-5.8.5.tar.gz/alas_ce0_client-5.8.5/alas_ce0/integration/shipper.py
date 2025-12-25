from alas_ce0.common.client_base import EntityClientBase


class ShipperOrderClient(EntityClientBase):
    entity_endpoint_base_url = 'integration/shipper/shipperorder/'


class WebhookClient(EntityClientBase):
    entity_endpoint_base_url = 'integration/shipper/webhooks/'
