# coding=utf-8
from enum import Enum

from alas_ce0.common.client_base import EntityClientBase
from alas_ce0.management.task import TaskClient

from datetime import datetime
import datetime as _datetime
from pytz import timezone as _timezone


def get_delivery_order_process_type_dic():
    return {
        2: "Recepción Física TL (Viejo Formato)",
        8: "Agendamiento de Entrega",
        9: "Ingreso a Ce0",
        10: "Recepción Física TL (Nuevo Formato)",
    }
    
def get_lob_order_dic():
    return {
        1: "Entrega",
        2: "Retorno",
        3: "Intercambio",
        4: "Entrega Online",
        5: "Entrega Flex"
    }
    
def get_delivery_order_status_description_dic():
    return {
        1: "En proceso de planificación",
        4: "En proceso de planificación",
        5: "Recibida por el tren logístico",
        7: "Rechazada por el tren logístico o B2B",
        9: "Entrega en Tránsito a base de distribución",
        10: "Entrega Recibida en base de distribución",
        12: "Entrega Agendada con validación de B2C",
        13: "Entrega Agendada sin validación de B2C",
        16: "Entrega lista para visitar al B2C",
        17: "Entrega en Ruta hacia el cliente B2C",
        19: "En espera de poner en tránsito para próximo intento de entrega",
        25: "Superó los 3 intentos",
        32: "Recibida en el centro de distribución",
        33: "Recibida por personal que hará entrega al B2C",
    }
    
def get_delivery_order_status_dic():
    return {
        1: "Planificación",
        2: "Planificación Modificada",
        3: "Planificación Aprobada",
        4: "Recibida Virtual",
        5: "Recibida Físico",
        6: "En Maquilado",
        7: "Rechazado B2B",
        8: "Espera TI",
        9: "Viajando a SER",
        10: "Recibido SER",
        11: "Espera Reemplazo",
        12: "Entrega Confirmada",
        13: "Entrega No Confirmada",
        14: "Entrega Aplazada",
        15: "Entrega Rechazada",
        16: "Entrega Ruteada",
        17: "Viajando B2C",
        18: "Entregada",
        19: "No Entregada",
        20: "PackagingIssueReturned",
        21: "ODFReturned",
        22: "ODSFReturned",
        23: "Pending",
        24: "PrioritizedPending",
        25: "No Entregable",
        26: "B2BReturning",
        27: "B2BReturned",
        28: "Evaluada B2C",
        29: "Rechazada en Terreno",
        30: "Reagendada",
        31: "Intento de Contacto",
        32: "Recibido CD",
        33: "Recibido Mensajero",
        34: "Recuperada",
        35: "Rechazado Cliente",
        36: "Rechazado Alas",
        37: "Robada",
        38: "Extraviada",
        39: "Retirada",
        40: "No Retirada",
        41: "No Retirable",
        42: "Viajando a CD",
        43: "Viajando B2B",
        44: "Entregada B2B",
        45: "Asignado Mensajero",
        46: "Intercambiada",
        47: "No Intercambiada",
        48: "No Intercambiable",
        49: "Recibido SER",
        50: "Recibido Devoluciones",
        51: "Cambio de Comuna",
        52: "Cuarentena",
        53: "PreAsignado Mensajero"
    }

def get_delivery_order_rejected_dic():
    return {
        1: "No hay quien reciba",
        2: "Dirección Incompleta'",
        3: "Problema de Documentación",
        4: "Código Erróneo",
        5: "Paso Automático",
        6: "A pedido del B2B",
        9: "Compra Anulada",
        10: "Orden Duplicada",
        11: "Paquete Dañado",
        12: "Retiro Anulado",
        14: "Sin Stock Para Remaquilar"
    }

class LineOfBusinessType(Enum):
    Delivery = 1
    Pickup = 2
    Exchange = 3
    DeliveryOnline = 4
    DeliveryFlex = 5
    
LOB_TYPES = [e.value for e in LineOfBusinessType]

class DeliveryOrderProcessType(Enum):
    B2bDelivery = 1
    B2bReception = 2
    Packaging = 3
    CarrierDispatch = 4
    CarrierDelivery = 5
    SerReception = 6
    VehicleLoad = 7
    B2cDelivery = 8
    Ce0Reception = 9
    # Inboxs
    B2bReceived = 10
    DcReceived = 11
    CarrierReceived = 12
    SerReceived = 13
    CourierReceived = 14


class DeliveryOrderStakeholderType(Enum):
    Sender = 1
    Receiver = 2
    ReceiverEmployee = 3
    PackagerEmployee = 4
    DispatcherEmployee = 5
    IntermediateCarrier = 6
    RegionalPartner = 7
    SchedulerEmployee = 8
    ControllerEmployee = 9
    MessengerEmployee = 10
    DeliveryManager = 11


class DeliveryOrderStatusType(Enum):
    Planning = 1
    PlanningChanged = 2
    PlanningApproved = 3
    VirtuallyReceived = 4
    PhysicallyReceived = 5
    Packaging = 6
    B2BReceptionRejected = 7
    TIReceptionWaiting = 8
    SERTravelling = 9
    SERReceived = 10
    ReplacementWaiting = 11
    DeliveryConfirmed = 12
    DeliveryNotConfirmed = 13
    DeliveryPostponed = 14
    DeliveryRejected = 15
    DeliveryScheduled = 16
    B2CTraveling = 17
    Delivered = 18
    NotDelivered = 19
    PackagingIssueReturned = 20
    ODFReturned = 21
    ODSFReturned = 22
    Pending = 23
    PrioritizedPending = 24
    NotDeliverable = 25
    B2BReturning = 26
    B2BReturned = 27
    B2CEvaluated = 28
    B2CRejected = 29
    DeliveryRescheduled = 30
    ContactAttempt = 31
    DistributionCenterReceived = 32
    DeliveryCourierReceived = 33
    Recovered = 34
    B2CReceptionRejected = 35
    ALASRejected = 36
    Steal = 37
    Missing  = 38    
    Withdrawn = 39 #Picking = 39
    NotWithdrawn = 40 #NotPicking = 40
    Nonwithdrable = 41 #NotPickingable = 41
    DistributionCenterTravelling = 42
    B2BTraveling = 43
    B2BDelivered = 44
    DeliveryCourierAssigned = 45
    Exchanged = 46
    NotExchanged = 47
    NotExchangable = 48
    PickupSERReceived = 49
    PickupDistributionCenterReceived = 50
    WrongCrossDocking = 51
    Quarantine = 52
    DeliveryCourierPreAssigned = 53


    
DELIVERY_ORDER_STATUS_TYPES = [e.value for e in DeliveryOrderStatusType]

DELIVERY_ORDER_REJECTED_STATUSES = [
    DeliveryOrderStatusType.DeliveryRejected.value,
    DeliveryOrderStatusType.B2CRejected.value,
    DeliveryOrderStatusType.B2BReceptionRejected.value,
    DeliveryOrderStatusType.B2CReceptionRejected.value,
    DeliveryOrderStatusType.ALASRejected.value,
    DeliveryOrderStatusType.Steal.value,
    DeliveryOrderStatusType.Missing.value,
    DeliveryOrderStatusType.WrongCrossDocking.value,
]
DELIVERY_ORDER_FINAL_STATUSES = [
    DeliveryOrderStatusType.Delivered.value,
    DeliveryOrderStatusType.NotDeliverable.value,
    DeliveryOrderStatusType.Exchanged.value,
    DeliveryOrderStatusType.NotExchangable.value
] + DELIVERY_ORDER_REJECTED_STATUSES

DELIVERY_ORDER_FLEX_STATE_MACHINE = {
    DeliveryOrderStatusType.Planning.value: [
        DeliveryOrderStatusType.PlanningApproved.value,
        DeliveryOrderStatusType.PlanningChanged.value,
        DeliveryOrderStatusType.Planning.value,
    ],
    DeliveryOrderStatusType.PlanningChanged.value: [
        DeliveryOrderStatusType.PlanningApproved.value,
    ],
    DeliveryOrderStatusType.PlanningApproved.value: [
        DeliveryOrderStatusType.VirtuallyReceived.value,
    ],
    DeliveryOrderStatusType.VirtuallyReceived.value: [
        DeliveryOrderStatusType.Packaging.value,
    ],
    DeliveryOrderStatusType.Packaging.value: [
        DeliveryOrderStatusType.SERReceived.value,
    ],
    DeliveryOrderStatusType.SERReceived.value: [
        DeliveryOrderStatusType.DeliveryCourierReceived.value,
        DeliveryOrderStatusType.Packaging.value
    ],
    DeliveryOrderStatusType.DeliveryCourierReceived.value: [
        DeliveryOrderStatusType.DeliveryScheduled.value,
        DeliveryOrderStatusType.DeliveryRejected.value, #entrega rechazada
        DeliveryOrderStatusType.Packaging.value,
        DeliveryOrderStatusType.SERReceived.value
    ],
    DeliveryOrderStatusType.DeliveryScheduled.value: [
        DeliveryOrderStatusType.B2CTraveling.value,
        DeliveryOrderStatusType.SERReceived.value
    ],
    DeliveryOrderStatusType.B2CTraveling.value: [
        DeliveryOrderStatusType.Delivered.value,
        DeliveryOrderStatusType.NotDelivered.value,
        DeliveryOrderStatusType.B2BReceptionRejected.value, #rechazado b2b
        DeliveryOrderStatusType.B2CReceptionRejected.value, # rechazado cliente
        DeliveryOrderStatusType.ALASRejected.value, # rechazado alas
        DeliveryOrderStatusType.Steal.value, #robada
        DeliveryOrderStatusType.Missing.value, #extraviada
        DeliveryOrderStatusType.SERReceived.value
    ],
    DeliveryOrderStatusType.NotDelivered.value: [
        DeliveryOrderStatusType.SERReceived.value,
        DeliveryOrderStatusType.NotDeliverable.value,
        DeliveryOrderStatusType.Recovered.value,
    ],
    DeliveryOrderStatusType.Delivered.value: [
        DeliveryOrderStatusType.Recovered.value,
    ],
    DeliveryOrderStatusType.B2BReceptionRejected.value: [ #rechazado b2b
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.Recovered.value: [
        DeliveryOrderStatusType.SERReceived.value
    ],
}

DELIVERY_ORDER_STATE_MACHINE = {
    DeliveryOrderStatusType.Planning.value: [
        DeliveryOrderStatusType.PlanningApproved.value,
        DeliveryOrderStatusType.PlanningChanged.value,
        DeliveryOrderStatusType.Planning.value,
    ],
    DeliveryOrderStatusType.PlanningChanged.value: [
        DeliveryOrderStatusType.PlanningApproved.value,
    ],
    DeliveryOrderStatusType.PlanningApproved.value: [
        DeliveryOrderStatusType.VirtuallyReceived.value,
    ],
    DeliveryOrderStatusType.VirtuallyReceived.value: [
        DeliveryOrderStatusType.PhysicallyReceived.value,
        #DeliveryOrderStatusType.B2BReceptionRejected.value, #rechazado b2b
        DeliveryOrderStatusType.DeliveryRejected.value, #entrega rechazada
        DeliveryOrderStatusType.Packaging.value,
    ],
    DeliveryOrderStatusType.Packaging.value: [
        DeliveryOrderStatusType.PhysicallyReceived.value,
        # DeliveryOrderStatusType.B2BReceptionRejected.value, #rechazado b2b
        DeliveryOrderStatusType.DeliveryRejected.value,  # entrega rechazada
    ],
    DeliveryOrderStatusType.PhysicallyReceived.value: [
        DeliveryOrderStatusType.DistributionCenterReceived.value,
        DeliveryOrderStatusType.DeliveryRejected.value, #entrega rechazada
    ],
    DeliveryOrderStatusType.DistributionCenterReceived.value: [
        DeliveryOrderStatusType.DeliveryCourierPreAssigned.value,
        DeliveryOrderStatusType.SERTravelling.value,
        DeliveryOrderStatusType.DeliveryRejected.value, #entrega rechazada
        DeliveryOrderStatusType.PhysicallyReceived.value,
    ],
    DeliveryOrderStatusType.DeliveryCourierPreAssigned.value: [
        DeliveryOrderStatusType.DeliveryCourierAssigned.value,
    ],
    DeliveryOrderStatusType.DeliveryCourierAssigned.value: [
        DeliveryOrderStatusType.SERTravelling.value,
        DeliveryOrderStatusType.DeliveryCourierReceived.value,
    ],
    DeliveryOrderStatusType.SERTravelling.value: [
        DeliveryOrderStatusType.SERReceived.value,
        DeliveryOrderStatusType.PhysicallyReceived.value,
    ],
    DeliveryOrderStatusType.SERReceived.value: [
        DeliveryOrderStatusType.DeliveryCourierReceived.value,
        DeliveryOrderStatusType.PhysicallyReceived.value
    ],
    DeliveryOrderStatusType.PickupSERReceived.value: [
        DeliveryOrderStatusType.DistributionCenterTravelling.value
    ],
    DeliveryOrderStatusType.DistributionCenterTravelling.value: [
        DeliveryOrderStatusType.DistributionCenterReceived.value
    ],
    DeliveryOrderStatusType.DeliveryCourierReceived.value: [
        DeliveryOrderStatusType.DeliveryScheduled.value,
        DeliveryOrderStatusType.DeliveryRejected.value, #entrega rechazada
        DeliveryOrderStatusType.PhysicallyReceived.value,
        DeliveryOrderStatusType.DistributionCenterReceived.value,
        DeliveryOrderStatusType.SERReceived.value
    ],
    DeliveryOrderStatusType.DeliveryConfirmed.value: [
        DeliveryOrderStatusType.DeliveryScheduled.value,
    ],
    DeliveryOrderStatusType.DeliveryNotConfirmed.value: [
        DeliveryOrderStatusType.DeliveryScheduled.value,
    ],
    DeliveryOrderStatusType.DeliveryRejected.value: [ #entrega rechazada
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.DeliveryScheduled.value: [
        DeliveryOrderStatusType.B2CTraveling.value,
        DeliveryOrderStatusType.DistributionCenterReceived.value,
        DeliveryOrderStatusType.SERReceived.value
    ],
    DeliveryOrderStatusType.B2CTraveling.value: [
        DeliveryOrderStatusType.Delivered.value,
        DeliveryOrderStatusType.NotDelivered.value,
        DeliveryOrderStatusType.B2BReceptionRejected.value, #rechazado b2b
        DeliveryOrderStatusType.B2CReceptionRejected.value, # rechazado cliente
        DeliveryOrderStatusType.ALASRejected.value, # rechazado alas
        DeliveryOrderStatusType.Steal.value, #robada
        DeliveryOrderStatusType.Missing.value, #extraviada
        DeliveryOrderStatusType.DistributionCenterReceived.value,
        DeliveryOrderStatusType.SERReceived.value
    ],
    DeliveryOrderStatusType.NotDelivered.value: [
        DeliveryOrderStatusType.DeliveryCourierReceived.value,
        DeliveryOrderStatusType.NotDeliverable.value,
        DeliveryOrderStatusType.Recovered.value,
        DeliveryOrderStatusType.PhysicallyReceived.value,
        DeliveryOrderStatusType.DistributionCenterReceived.value,
        DeliveryOrderStatusType.SERReceived.value
    ],
    DeliveryOrderStatusType.Delivered.value: [
        DeliveryOrderStatusType.Recovered.value,
        DeliveryOrderStatusType.B2CEvaluated.value
    ],
    DeliveryOrderStatusType.B2CReceptionRejected.value: [ # rechazado cliente
        DeliveryOrderStatusType.Quarantine.value,
        DeliveryOrderStatusType.Recovered.value,
    ],
    DeliveryOrderStatusType.Quarantine.value: [
        DeliveryOrderStatusType.PickupSERReceived.value,
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.PickupSERReceived.value: [
        DeliveryOrderStatusType.DistributionCenterTravelling.value
    ],
    DeliveryOrderStatusType.DistributionCenterTravelling.value: [
        DeliveryOrderStatusType.PickupDistributionCenterReceived.value
    ],
    DeliveryOrderStatusType.ALASRejected.value: [ # rechazado alas
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.Steal.value: [ # robada
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.Missing.value: [ # extraviada
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.B2CRejected.value: [ # rechazada en terreno
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.WrongCrossDocking.value: [ # error de base
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.NotDeliverable.value: [
        DeliveryOrderStatusType.Quarantine.value,
        DeliveryOrderStatusType.Recovered.value,
    ],
    DeliveryOrderStatusType.Recovered.value: [
        DeliveryOrderStatusType.DistributionCenterReceived.value,
        DeliveryOrderStatusType.SERReceived.value,
        DeliveryOrderStatusType.VirtuallyReceived.value,
        DeliveryOrderStatusType.Planning.value,
        DeliveryOrderStatusType.PhysicallyReceived.value
    ],
    DeliveryOrderStatusType.B2BReceptionRejected.value: [ #rechazado b2b
        DeliveryOrderStatusType.Recovered.value
    ]
}

# PICKUP_ORDER_STATE_MACHINE = {
#     DeliveryOrderStatusType.Planning.value: [
#         DeliveryOrderStatusType.PlanningApproved.value,
#         DeliveryOrderStatusType.Planning.value
#     ],
#     DeliveryOrderStatusType.PlanningApproved.value: [
#         DeliveryOrderStatusType.VirtuallyReceived.value
#     ],
#     DeliveryOrderStatusType.VirtuallyReceived.value: [
#         DeliveryOrderStatusType.DeliveryCourierReceived.value
#     ],
#     DeliveryOrderStatusType.DeliveryCourierReceived.value: [
#         DeliveryOrderStatusType.Withdrawn.value,
#         DeliveryOrderStatusType.NotWithdrawn.value
#     ],
#     DeliveryOrderStatusType.NotWithdrawn.value: [
#         DeliveryOrderStatusType.DeliveryCourierReceived.value,
#         DeliveryOrderStatusType.Nonwithdrable.value
#     ],
#     DeliveryOrderStatusType.Withdrawn.value: [
#         DeliveryOrderStatusType.SERReceived.value
#     ],
#     DeliveryOrderStatusType.SERReceived.value: [
#         DeliveryOrderStatusType.DistributionCenterTravelling.value
#     ],
#     DeliveryOrderStatusType.DistributionCenterTravelling.value: [
#         DeliveryOrderStatusType.DistributionCenterReceived.value
#     ],
#     DeliveryOrderStatusType.DistributionCenterReceived.value: [
#         DeliveryOrderStatusType.B2BTraveling.value
#     ],
#     DeliveryOrderStatusType.B2BTraveling.value: [
#         DeliveryOrderStatusType.B2BDelivered.value
#     ],
#     DeliveryOrderStatusType.B2BDelivered.value: [
#
#     ],
#     DeliveryOrderStatusType.B2CReceptionRejected.value: [
#         DeliveryOrderStatusType.Recovered.value
#     ],
#     DeliveryOrderStatusType.ALASRejected.value: [
#         DeliveryOrderStatusType.Recovered.value
#     ],
#     DeliveryOrderStatusType.Steal.value: [
#         DeliveryOrderStatusType.Recovered.value
#     ],
#     DeliveryOrderStatusType.Missing.value: [
#         DeliveryOrderStatusType.Recovered.value
#     ],
#     DeliveryOrderStatusType.Nonwithdrable.value: [
#         DeliveryOrderStatusType.Recovered.value
#     ],
#     DeliveryOrderStatusType.Recovered.value: [
#         DeliveryOrderStatusType.DistributionCenterReceived.value
#     ],
#     DeliveryOrderStatusType.B2BReceptionRejected.value: [
#         DeliveryOrderStatusType.Recovered.value
#     ]
# }

PICKUP_ORDER_STATE_MACHINE_NEW = {
    DeliveryOrderStatusType.Planning.value: [
        DeliveryOrderStatusType.PlanningApproved.value,
        DeliveryOrderStatusType.Planning.value
    ],
    DeliveryOrderStatusType.PlanningApproved.value: [
        DeliveryOrderStatusType.VirtuallyReceived.value
    ],
    DeliveryOrderStatusType.VirtuallyReceived.value: [
        DeliveryOrderStatusType.DeliveryCourierReceived.value
    ],
    DeliveryOrderStatusType.DeliveryCourierReceived.value: [
        DeliveryOrderStatusType.Withdrawn.value,
        DeliveryOrderStatusType.NotWithdrawn.value
    ],
    DeliveryOrderStatusType.NotWithdrawn.value: [
        DeliveryOrderStatusType.DeliveryCourierReceived.value,
        DeliveryOrderStatusType.Nonwithdrable.value
    ],
    DeliveryOrderStatusType.Withdrawn.value: [
        DeliveryOrderStatusType.PickupSERReceived.value
    ],
    DeliveryOrderStatusType.PickupSERReceived.value: [
        DeliveryOrderStatusType.DistributionCenterTravelling.value
    ],
    DeliveryOrderStatusType.DistributionCenterTravelling.value: [
        DeliveryOrderStatusType.PickupDistributionCenterReceived.value
    ],
    DeliveryOrderStatusType.PickupDistributionCenterReceived.value: [
        DeliveryOrderStatusType.B2BTraveling.value
    ],
    DeliveryOrderStatusType.B2BTraveling.value: [
        DeliveryOrderStatusType.B2BDelivered.value
    ],
    # Rejected States
    DeliveryOrderStatusType.B2CReceptionRejected.value: [
        DeliveryOrderStatusType.Quarantine.value,
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.NotDeliverable.value: [
        DeliveryOrderStatusType.Quarantine.value,
        DeliveryOrderStatusType.Recovered.value,
    ],
    DeliveryOrderStatusType.Quarantine.value: [
        DeliveryOrderStatusType.PickupSERReceived.value,
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.WrongCrossDocking.value: [
        DeliveryOrderStatusType.PickupSERReceived.value
    ],
    DeliveryOrderStatusType.ALASRejected.value: [
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.Steal.value: [
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.Missing.value: [
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.Nonwithdrable.value: [
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.Recovered.value: [
        DeliveryOrderStatusType.PickupDistributionCenterReceived.value
    ],
    DeliveryOrderStatusType.B2BReceptionRejected.value: [
        DeliveryOrderStatusType.Recovered.value
    ]
}

EXCHANGE_ORDER_STATE_MACHINE = {
    DeliveryOrderStatusType.Planning.value: [
        DeliveryOrderStatusType.PlanningApproved.value,
        DeliveryOrderStatusType.Planning.value,
    ],
    DeliveryOrderStatusType.PlanningApproved.value: [
        DeliveryOrderStatusType.VirtuallyReceived.value,
    ],
    DeliveryOrderStatusType.VirtuallyReceived.value: [
        DeliveryOrderStatusType.PhysicallyReceived.value,
    ],
    DeliveryOrderStatusType.PhysicallyReceived.value: [
        DeliveryOrderStatusType.DistributionCenterReceived.value,
    ],
    DeliveryOrderStatusType.DistributionCenterReceived.value: [
        DeliveryOrderStatusType.DeliveryCourierPreAssigned.value,
        DeliveryOrderStatusType.SERTravelling.value,
        DeliveryOrderStatusType.PhysicallyReceived.value,
    ],
    DeliveryOrderStatusType.DeliveryCourierPreAssigned.value: [
        DeliveryOrderStatusType.DeliveryCourierAssigned.value,
    ],
    DeliveryOrderStatusType.DeliveryCourierAssigned.value: [
        DeliveryOrderStatusType.SERTravelling.value,
        DeliveryOrderStatusType.DeliveryCourierReceived.value,
    ],
    DeliveryOrderStatusType.SERTravelling.value: [
        DeliveryOrderStatusType.SERReceived.value,
        DeliveryOrderStatusType.PhysicallyReceived.value,
    ],
    DeliveryOrderStatusType.SERReceived.value: [
        DeliveryOrderStatusType.DeliveryCourierReceived.value,
        DeliveryOrderStatusType.PhysicallyReceived.value,
        DeliveryOrderStatusType.DeliveryCourierAssigned.value,
    ],
    DeliveryOrderStatusType.DeliveryCourierReceived.value: [
        DeliveryOrderStatusType.DeliveryScheduled.value,
        DeliveryOrderStatusType.PhysicallyReceived.value,
        DeliveryOrderStatusType.DistributionCenterReceived.value,
        DeliveryOrderStatusType.SERReceived.value
    ],
    DeliveryOrderStatusType.DeliveryScheduled.value: [
        DeliveryOrderStatusType.B2CTraveling.value,
        DeliveryOrderStatusType.DistributionCenterReceived.value,
        DeliveryOrderStatusType.SERReceived.value
    ],
    DeliveryOrderStatusType.B2CTraveling.value: [
        DeliveryOrderStatusType.Exchanged.value,
        DeliveryOrderStatusType.NotExchanged.value,
        DeliveryOrderStatusType.B2BReceptionRejected.value,
        DeliveryOrderStatusType.B2CReceptionRejected.value,
        DeliveryOrderStatusType.ALASRejected.value,
        DeliveryOrderStatusType.Steal.value,
        DeliveryOrderStatusType.Missing.value,
        DeliveryOrderStatusType.DistributionCenterReceived.value,
        DeliveryOrderStatusType.SERReceived.value
    ],
    DeliveryOrderStatusType.NotExchanged.value: [
        DeliveryOrderStatusType.DeliveryCourierReceived.value,
        DeliveryOrderStatusType.NotExchangable.value,
        DeliveryOrderStatusType.Recovered.value,
        DeliveryOrderStatusType.PhysicallyReceived.value,
        DeliveryOrderStatusType.DistributionCenterReceived.value,
        DeliveryOrderStatusType.SERReceived.value
    ],
    DeliveryOrderStatusType.Exchanged.value: [
        DeliveryOrderStatusType.PickupSERReceived.value
    ],
    DeliveryOrderStatusType.PickupSERReceived.value: [
        DeliveryOrderStatusType.DistributionCenterTravelling.value
    ],
    DeliveryOrderStatusType.DistributionCenterTravelling.value: [
        DeliveryOrderStatusType.PickupDistributionCenterReceived.value
    ],
    DeliveryOrderStatusType.PickupDistributionCenterReceived.value: [
        DeliveryOrderStatusType.B2BTraveling.value
    ],
    DeliveryOrderStatusType.B2BTraveling.value: [
        DeliveryOrderStatusType.B2BDelivered.value
    ],
    # Rejected States
    DeliveryOrderStatusType.B2CReceptionRejected.value: [
        DeliveryOrderStatusType.Quarantine.value,
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.ALASRejected.value: [
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.Steal.value: [
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.Missing.value: [
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.NotExchangable.value: [
        DeliveryOrderStatusType.Quarantine.value,
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.Quarantine.value: [
        DeliveryOrderStatusType.PickupSERReceived.value,
        DeliveryOrderStatusType.Recovered.value
    ],
    DeliveryOrderStatusType.Recovered.value: [
        DeliveryOrderStatusType.DistributionCenterReceived.value,
        DeliveryOrderStatusType.SERReceived.value,
        DeliveryOrderStatusType.VirtuallyReceived.value,
        DeliveryOrderStatusType.Planning.value,
        DeliveryOrderStatusType.PhysicallyReceived.value
    ],
    DeliveryOrderStatusType.B2BReceptionRejected.value: [
        DeliveryOrderStatusType.Recovered.value
    ]
}


def get_contact_client_dic():
    return {
        1: "B2B",
        2: "B2C"
    }

def get_contact_channel_dic():
    return {
        1: "Whatsapp",
        2: "Telefono",
        3: "Portal",
        4: "Correo",
        5: "Otros"
    }

def get_contact_category_dic():
    return {
        1: "Entrega",
        2: "Comercial",
        3: "Finanzas",
        4: "Retiro TL",
        5: "Maquila Interna",
        6: "RRHH",
        7: "Reversa"
    }

def get_contact_reason_dic():
    return {
        1.1: "Actualizacion Datos de Entrega",
        1.2: "Cambio de Comuna",
        1.3: "Entrega Parcial",
        1.4: "Merma",
        1.5: "Extravio",
        1.6: "Robo",
        1.7: "Cuando Llega  el Pedido",
        1.8: "Disconformidad Servicio",
        1.9: "Cambio Fecha de Entrega",
        1.10: "Desconocimiento de Entrega",
        1.11: "Error Proceso de Entrega",
        2.12: "Consulta Tarifa",
        2.13: "Areas de Cobertura",
        2.14: "Soporte TI",
        3.15: "Pedido de Prefactura",
        3.16: "Suspension de Servicio",
        4.17: "Hora de Retiro",
        4.18: "Solicitar Retiro Especial",
        4.19: "Informe de Recepcion",
        4.20: "Error Recepcion de Orden",
        5.21: "Error de Maquila",
        5.22: "Actualizacion Datos de Compra",
        5.23: "Consulta Stock",
        6.24: "Felicitaciones",
        6.25: "Sugerencias",
        7.26: "Fecha de Retorno al B2B",
        7.27: "Reclamo por Retorno"
    }

def get_contact_status_dic():
    return {
        1: "Completo",
        2: "Pendiente",
        3: "En Proceso B2B",
        4: "En Proceso B2C",
        5: "En Proceso Interno"
    }

class ContactStatusType(Enum):
    Complete = 1
    Pending = 2
    InB2BProcess = 3
    InB2CProcess = 4
    InInternalProcess = 5




class BulkStatusType(Enum):
    Started = 1
    DCReceived = 2
    ITControlled = 3
    SERTravelling = 4
    Opened = 5


class PalletStatusType(Enum):
    Started = 1
    PreAssigned = 2
    Assigned = 3


class BulkOperationStatusType(Enum):
    Created = 1
    Packaged = 2
    Controlled = 3
    Travelling = 4
    Received = 5


class PalletOperationStatusType(Enum):
    Created = 1
    Packaged = 2
    Controlled = 3
    Travelling = 4
    Received = 5
    
class PackageSerReceiveStatusType(Enum):
    Pending = 1
    Accepted = 2
    Damaged = 3
    
def get_delivery_rejected_reason_dic():  
    return {
        1: "Cliente desiste",
        2: "Retiro en sucursal",
        3: "Fuera de Matriz",
        4: "Producto No solicitado",
        5: "Mermado",
        6: "A pedido del B2B",
        9: "Compra Anulada",
        10: "Orden Duplicada",
        11: "Paquete Dañado",
        12: "Retiro Anulado",
        14: "Sin Stock Para Remaquilar"
    }

def _get_schedule_rejected_comments(event_info):
    if 'schedule_rejected_1_comments' in event_info and event_info['schedule_rejected_1_comments']:
        return event_info['schedule_rejected_1_comments']
    if 'schedule_rejected_2_comments' in event_info and event_info['schedule_rejected_2_comments']:
        return event_info['schedule_rejected_2_comments']
    if 'schedule_rejected_3_comments' in event_info and event_info['schedule_rejected_3_comments']:
        return event_info['schedule_rejected_3_comments']
    return None

def get_status_info_wom(delivery_order):
    events_info, status, last_event_timestamp = None, None, None

    if delivery_order['status'] == DeliveryOrderStatusType.PhysicallyReceived.value:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status = 'Despacho recepcionado'

    elif delivery_order['status'] == DeliveryOrderStatusType.B2BReceptionRejected.value:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status = 'Orden Cancelada por Logística'


    elif delivery_order['status'] in [DeliveryOrderStatusType.B2CTraveling.value,
                                      DeliveryOrderStatusType.DeliveryCourierReceived.value]:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status = 'Despacho en ruta'

    elif delivery_order['status'] in [DeliveryOrderStatusType.NotDelivered.value, DeliveryOrderStatusType.NotDeliverable.value, DeliveryOrderStatusType.NotExchanged.value, DeliveryOrderStatusType.NotExchangable.value]:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status = "Intento {}".format( str(delivery_order['delivery_attemps']) )

    elif delivery_order['status'] in [DeliveryOrderStatusType.Delivered.value, DeliveryOrderStatusType.Exchanged.value]:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status = 'Entregado'

    #elif delivery_order['status'] == DeliveryOrderStatusType.NotDeliverable.value:
    #    events_info = list(filter(
    #        lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
    #    ))
    #    status = 'Orden Cancelada'

    elif delivery_order['status'] == DeliveryOrderStatusType.B2CReceptionRejected.value:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status = 'Cliente desiste'

    elif delivery_order['status'] == DeliveryOrderStatusType.ALASRejected.value:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status = 'No Entregado'

    elif delivery_order['status'] in [DeliveryOrderStatusType.Steal.value, DeliveryOrderStatusType.Missing.value]:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status = 'Mermada'

    else:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))

        status_dic = get_delivery_order_status_dic()
        status = status_dic[delivery_order['status']]

    if events_info:
        last_event_timestamp = events_info[len(events_info) - 1]['timestamp'].split('.')[0]

    return status, last_event_timestamp

def get_status_info(delivery_order, r_reason = False):
    events_info, status, description, last_event_timestamp = None, None, None, None

    if delivery_order['status'] == DeliveryOrderStatusType.Planning.value:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status_dic = get_delivery_order_status_dic()
        status = status_dic[delivery_order['status']]

        description_dic = get_delivery_order_status_description_dic()
        description = description_dic[delivery_order['status']] if delivery_order['status'] in description_dic else status

    elif delivery_order['status'] == DeliveryOrderStatusType.VirtuallyReceived.value:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status = 'Planificación'

        description_dic = get_delivery_order_status_description_dic()
        description = description_dic[delivery_order['status']] if delivery_order['status'] in description_dic else status

    elif delivery_order['status'] == DeliveryOrderStatusType.PhysicallyReceived.value:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status = 'Recepción Física'

        description_dic = get_delivery_order_status_description_dic()
        description = description_dic[delivery_order['status']] if delivery_order['status'] in description_dic else status

    elif delivery_order['status'] == DeliveryOrderStatusType.B2BReceptionRejected.value:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status = 'Rechazada B2B'

        description_dic = get_delivery_order_status_description_dic()
        description = description_dic[delivery_order['status']] if delivery_order['status'] in description_dic else status

    elif delivery_order['status'] == DeliveryOrderStatusType.DistributionCenterReceived.value:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status_dic = get_delivery_order_status_dic()
        status = status_dic[delivery_order['status']]

        description_dic = get_delivery_order_status_description_dic()
        description = description_dic[delivery_order['status']] if delivery_order['status'] in description_dic else status

    elif delivery_order['status'] == DeliveryOrderStatusType.SERTravelling.value:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status = 'Viajando SER'

        description_dic = get_delivery_order_status_description_dic()
        description = description_dic[delivery_order['status']] if delivery_order['status'] in description_dic else status

    elif delivery_order['status'] == DeliveryOrderStatusType.SERReceived.value:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status_dic = get_delivery_order_status_dic()
        status = status_dic[delivery_order['status']]

        description_dic = get_delivery_order_status_description_dic()
        description = description_dic[delivery_order['status']] if delivery_order['status'] in description_dic else status

    elif delivery_order['status'] == DeliveryOrderStatusType.DeliveryConfirmed.value:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status = 'Entrega Agendada'

        description_dic = get_delivery_order_status_description_dic()
        description = description_dic[delivery_order['status']] if delivery_order['status'] in description_dic else status

    elif delivery_order['status'] == DeliveryOrderStatusType.DeliveryNotConfirmed.value:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status = 'Entrega Agendada'

        description_dic = get_delivery_order_status_description_dic()
        description = description_dic[delivery_order['status']] if delivery_order['status'] in description_dic else status

    elif delivery_order['status'] == DeliveryOrderStatusType.DeliveryScheduled.value:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status_dic = get_delivery_order_status_dic()
        status = status_dic[delivery_order['status']]

        description_dic = get_delivery_order_status_description_dic()
        description = description_dic[delivery_order['status']] if delivery_order['status'] in description_dic else status

    elif delivery_order['status'] in [DeliveryOrderStatusType.B2CTraveling.value, DeliveryOrderStatusType.DeliveryCourierReceived.value]:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status = 'En Ruta'

        description_dic = get_delivery_order_status_description_dic()
        description = description_dic[delivery_order['status']] if delivery_order['status'] in description_dic else status

    elif delivery_order['status'] in [DeliveryOrderStatusType.NotDelivered.value, DeliveryOrderStatusType.NotExchanged.value]:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status_dic = get_delivery_order_status_dic()
        status = status_dic[delivery_order['status']]

        description_dic = get_delivery_order_status_description_dic()
        description = description_dic[delivery_order['status']] if delivery_order['status'] in description_dic else status

    elif delivery_order['status'] == DeliveryOrderStatusType.Delivered.value:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status = 'Entregado'
        description = 'Entrega realizada'

    elif delivery_order['status'] == DeliveryOrderStatusType.Exchanged.value:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status = 'Intercambiada'
        description = 'Intercambio realizada'

    elif delivery_order['status'] in DELIVERY_ORDER_REJECTED_STATUSES:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status_dic = get_delivery_order_status_dic()
        status = status_dic[delivery_order['status']]

        description = get_rejected_reason(events_info[len(events_info) - 1]['info'])
        if description is None:
            description = "Entrega Rechazada"

    elif delivery_order['status'] in [DeliveryOrderStatusType.NotDeliverable.value, DeliveryOrderStatusType.NotExchangable.value]:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))
        status_dic = get_delivery_order_status_dic()
        status = status_dic[delivery_order['status']]

        description_dic = get_delivery_order_status_description_dic()
        description = description_dic[delivery_order['status']] if delivery_order['status'] in description_dic else status
    else:
        events_info = list(filter(
            lambda x: x['status'] == delivery_order['status'], delivery_order['events_info']
        ))

        status_dic = get_delivery_order_status_dic()
        status = status_dic[delivery_order['status']]

        description_dic = get_delivery_order_status_description_dic()
        description = description_dic[delivery_order['status']] \
            if delivery_order['status'] in description_dic \
                else status


    if events_info:
        last_event_timestamp = events_info[-1]['timestamp']
        last_event_timestamp = gtm_time(last_event_timestamp)
        last_event_timestamp = last_event_timestamp.split('.')[0]

    reason = None
    if r_reason:
        for key in events_info[-1]['info'].keys():
            if 'reason' in key:
                reason = events_info[-1]['info'][key]
        if reason is not None:
            reason_dic = get_delivery_order_rejected_dic()
            reason = reason_dic[reason]

        return status, description, last_event_timestamp, reason

    return status, description, last_event_timestamp


def gtm_time(str_local_time):
    _format = '%Y-%m-%dT%H:%M:%S.%f'
    timestamp = datetime.strptime(str_local_time[:26], _format)

    t1 = _datetime.datetime.utcnow().hour
    t2 = _datetime.datetime.now(_timezone('America/Santiago')).hour
    if t2 > t1:
        t1 += 24
    gtm3 = t1 - t2

    timestamp = timestamp - _datetime.timedelta(hours=gtm3)

    return timestamp.strftime(_format)

def get_macro_status(delivery_order):
    in_route_amount = len(
        list(filter(
            lambda x: x == 17, delivery_order['statuses']
        ))
    )
    in_quarantine_amount = len(
        list(filter(
            lambda x: x == 52, delivery_order['statuses']
        ))
    )
    status = get_delivery_order_status_dic()

    if delivery_order['status'] in [
        DeliveryOrderStatusType.DeliveryRejected.value,
        DeliveryOrderStatusType.B2CRejected.value,
        DeliveryOrderStatusType.B2CReceptionRejected.value]:
        return 'Rechazado Cliente'

    elif delivery_order['status'] == DeliveryOrderStatusType.Quarantine.value or (
            delivery_order['status'] != DeliveryOrderStatusType.Quarantine.value and in_quarantine_amount > 0 and
            delivery_order['lob'] == 1 and
            delivery_order['lob'] != delivery_order['branch']
    ):
        return 'En Cuarentena {0}'.format(in_quarantine_amount)

        statuses = delivery_order['statuses'][:]
        statuses.reverse()
        index = len(statuses) - statuses.index(52) - 1

        value = delivery_order['statuses'][:index][-1]
        return status[value]

    elif delivery_order['status'] == DeliveryOrderStatusType.B2CTraveling.value:
        return 'En Ruta {0}'.format(in_route_amount)

    elif delivery_order['status'] in [DeliveryOrderStatusType.NotDeliverable.value, DeliveryOrderStatusType.NotWithdrawn.value, DeliveryOrderStatusType.NotExchangable.value]:
        return 'Rechazado 3 Intentos'

    return status[delivery_order['status']]

def get_b2c_delivery_events(delivery_order):
    return list(filter(
        lambda x: (x['status'] == 15 and 'b2c_delivery_actual' in x['info']) or
                    x['status'] == 18 or
                    x['status'] == 19 or
                    x['status'] in DELIVERY_ORDER_REJECTED_STATUSES,
        delivery_order['events_info']
    ))
    
def get_not_delivered_reason(event_info):
    reasons = ['No hay quien reciba', 'Dirección Incompleta', 'Problema Documentación', 'Código Erróneo', 'Paso Automatico', 'Siniestro', 'Merma']

    if 'not_delivered_3_reason' in event_info and event_info['not_delivered_3_reason']:
        return reasons[event_info['not_delivered_3_reason'] - 1]
    if 'not_delivered_2_reason' in event_info and event_info['not_delivered_2_reason']:
        return reasons[event_info['not_delivered_2_reason'] - 1]
    if 'not_delivered_1_reason' in event_info and event_info['not_delivered_1_reason']:
        return reasons[event_info['not_delivered_1_reason'] - 1]
    return None
    
def get_b2c_delivery_status(b2c_delivery_events, b2c_delivery_date, attempt):
    if b2c_delivery_date:
        if b2c_delivery_events[attempt-1]['status'] in [29, 35] \
                or (b2c_delivery_events[attempt-1]['status'] == 15
                    and 'b2c_delivery_actual' in b2c_delivery_events[attempt-1]['info']):
            return 'Rechazado Cliente'
        elif b2c_delivery_events[attempt-1]['status'] == 18:
            return 'Entregado'
        else:
            reason = get_not_delivered_reason(b2c_delivery_events[attempt-1]['info'])
            return 'No Entregado' if not reason else reason
    return ''

def get_rejected_reason(event_info):
    reasons = get_delivery_rejected_reason_dic()
    reason = ""
    
    if 'delivery_rejected_3_reason' in event_info and event_info['delivery_rejected_3_reason']:
        rejected = int(event_info['delivery_rejected_3_reason'])
        reason = reasons[rejected]
    if 'schedule_rejected_3_reason' in event_info and event_info['schedule_rejected_3_reason']:
        rejected = int(event_info['schedule_rejected_3_reason'])
        reason = reasons[rejected]
    
    if 'delivery_rejected_2_reason' in event_info and event_info['delivery_rejected_2_reason']:
        rejected = int(event_info['delivery_rejected_2_reason'])
        reason = reasons[rejected]
    if 'schedule_rejected_2_reason' in event_info and event_info['schedule_rejected_2_reason']:
        rejected = int(event_info['schedule_rejected_2_reason'])
        reason = reasons[rejected]
    
    if 'delivery_rejected_1_reason' in event_info and event_info['delivery_rejected_1_reason']:
        rejected = int(event_info['delivery_rejected_1_reason'])
        reason = reasons[rejected]
    if 'schedule_rejected_1_reason' in event_info and event_info['schedule_rejected_1_reason']:
        rejected = int(event_info['schedule_rejected_1_reason'])
        reason = reasons[rejected]
    return reason

def get_status(delivery_order):
    status = get_delivery_order_status_dic()
    return status[delivery_order['status']]

def get_lob(delivery_order):
    lob = get_lob_order_dic()
    return lob[delivery_order['lob']] if 'lob' in delivery_order else lob[1]

class DeliveryOrderRequestClient(EntityClientBase):
    entity_endpoint_base_url = '/delivery/delivery-order-requests/'

    def __init__(self, country_code='cl', **kwargs):
        super(DeliveryOrderRequestClient, self).__init__(**kwargs)
        self.entity_endpoint_base_url += country_code + '/'


class DeliveryOrderExpectedClient(EntityClientBase):
    entity_endpoint_base_url = '/delivery/delivery-order-expecteds/'

    def __init__(self, country_code='cl', **kwargs):
        super(DeliveryOrderExpectedClient, self).__init__(**kwargs)
        self.entity_endpoint_base_url += country_code + '/'


class DeliveryOrderClient(EntityClientBase):
    entity_endpoint_base_url = '/delivery/delivery-orders/'

    def __init__(self, country_code='cl', **kwargs):
        super(DeliveryOrderClient, self).__init__(**kwargs)
        self.entity_endpoint_base_url += country_code + '/'
        self.headers['Authorization'] = self.headers['Authorization'].replace("\n", "")

    def create_from_request(self, delivery_order_request_id, pasync=True):
        params = {
            'delivery_order_request_id': delivery_order_request_id
        }

        if pasync:
            return TaskClient(**self.args).enqueue('delivery-order-create', params)
        else:
            return self.http_post_json(self.entity_endpoint_base_url + "_create-from-request", params)

    def create_delivery_order_label_sync(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_create-delivery-order-label-sync", params)

    def get_agenda(self, date_from, date_to, process_types, stakeholder_types=None):
        param = {
            'date_from': date_from,
            'date_to': date_to,
            'process_types': process_types,
            'stakeholder_types': stakeholder_types
        }

        return self.http_post_json(self.entity_endpoint_base_url + "_agenda", param)

    def change_status(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_change-status".format(id), params)

    def change_planning(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_change-planning".format(id), params)

    def upload_file(self, user_name, sender_code, base64_content, file_format="txt", file_name=None, lob=1, target_name=None):
        params = {
            'user_name': user_name,
            'sender_code': sender_code,
            'base64_content': base64_content,
            'format': file_format,
            'file_name': file_name,
            'lob': lob
        }
        if target_name is not None:
            params.update({'target_name': target_name})
        return self.http_post_json(self.entity_endpoint_base_url + "_upload-file", params)

    def validate_customer(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_validate-customer".format(id), params)

    def confirm_b2c_delivery(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_confirm-b2c-delivery".format(id), params)

    def search_for_daily_planning(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_search-for-daily-planning", params)

    def start_planning(self, id):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_start-planning".format(id), {})

    def search_for_route_creation(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_search-for-route-creation", params)

    def get_items(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_get-items", params)

    def send_notification(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_send-notification".format(id), params)

    def change_b2c_delivery(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_change-b2c-delivery".format(id), params)

    def change_b2b_delivery(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_change-b2b-delivery".format(id), params)

    def massive_change_b2c_delivery(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_massive_change-b2c-delivery", params)

    def polygons_finder(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_polygons-finder", params)

    def polygons_list(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_polygons-list", params)

    def change_destination(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_change-destination".format(id), params)

    def set_b2c_informed_geo_location(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_set-b2c-informed-geo-location".format(id), params)

    def route_now(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_route-now".format(id), params)

    def get_document_content(self, id, doc_type):
        return self.http_get(
            self.entity_endpoint_base_url + "{0}/document/{1}/_content".format(id, doc_type)
        )

    def get_attachment_content(self, id, att_file_name):
        return self.http_get(
            self.entity_endpoint_base_url + "{0}/attachment/{1}".format(id, att_file_name)
        )

    def get_delivery_form(self, id):
        return self.http_get_json(
            self.entity_endpoint_base_url + "{0}/_delivery-form".format(id)
        )

    def set_delivery_form(self, id, delivery_form):
        return self.http_post_json(
            self.entity_endpoint_base_url + "{0}/_delivery-form".format(id), delivery_form
        )

    def force_b2c_contact(self, id):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_force-b2c-contact".format(id), {})

    def validate_package(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_validate-package".format(id), params)
    
    def assign_package(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_assign-package".format(id), params)

    def assign_simserial_package(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_assign-simserial-package".format(id), params)

    def assign_simserial_packages(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_assign-simserial-packages".format(id), params)

    def process_create_labels_by_ids(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_process-create-labels-by-ids", params)
    
    def process_create_generic_labels(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_process-create-generic-labels", params)

    def create_label_sync(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_create-label-sync".format(id), params)

    def create_label_zpl(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_create-label-zpl".format(id), params)

    def get_b2b_reception_expected(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_get-b2b-reception-expected".format(id), params)

    def process_physical_reception(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_process-physical-reception", params)

    def process_b2b_receive_reception(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_process-b2b-receive-reception", params)
    
    def slack_report_send(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_slack-report-send", params)

    def in_postgresql(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_in-postgresql", params)

    def set_packed_items(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_set-packed_items".format(id), params)

    def modify_package_quantity(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_modify-package-quantity".format(id), params)

    def physically_receive(self, id, event_info, pasync=True):
        if pasync:
            return TaskClient(**self.args).enqueue('delivery-order-physically-receive', {
                'delivery_order_id': id,
                'event_info': event_info
            })
        else:
            return self.http_post_json(self.entity_endpoint_base_url + "{0}/_physically-receive".format(id), event_info)

    # region added by new project inboxs
    def distribution_center_receive(self, id, event_info, pasync=True):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_distribution-center-receive".format(id), event_info)

    def ser_travelling_receive(self, id, event_info, pasync=True):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_ser-travelling-receive".format(id), event_info)

    def ser_received_receive(self, id, event_info, pasync=True):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_ser-received-receive".format(id), event_info)

    def delivery_courier_receive(self, id, event_info, pasync=True):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_delivery-courier-receive".format(id), event_info)

    def delivery_courier_assigned(self, id, event_info, pasync=True):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_delivery-courier-assigned".format(id), event_info)
    
    def b2b_travelling(self, id, event_info):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_b2b-travelling".format(id), event_info)
    
    def b2b_receive(self, id, event_info):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_b2b-receive".format(id), event_info)
    # endregion

    def search_batch(self, search_info):
        return self.http_post_json(self.entity_endpoint_base_url + "_search-batch", search_info)

    def get_device_assigned(self, id):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_device-assigned".format(id), {})

    def recover(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_recover".format(id), params)

    def submit_form(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_submit-form".format(id), params)

    def notification_forwarding(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_notification-forwarding".format(id), params)

    def info_next_status(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_info-next-status", params)

    def next_status(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_next-status".format(id), params)

    def prev_status(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_prev-status".format(id), params)

    def hook_alas(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_hook-alas", params)

    def update_documents(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_update-documents".format(id), params)

    def assignment_courier(self, params):
        return self.http_post_json(self.entity_endpoint_base_url + "_assignment-courier", params)

class DeliveryOrderMessagingClient(EntityClientBase):
    entity_endpoint_base_url = '/delivery/delivery-orders-messaging/'


class DeliveryOrdersForRouteClient(EntityClientBase):
    entity_endpoint_base_url = '/delivery/delivery-orders-for-route/'


class DeliveryOrderIntegrationAuditClient(EntityClientBase):
    entity_endpoint_base_url = '/delivery/delivery-orders-integration-audit/'

class DeliveryOrderAttempClient(EntityClientBase):
    entity_endpoint_base_url = '/delivery/delivery-order-attempts/'

    def __init__(self, country_code='cl', **kwargs):
        super(DeliveryOrderAttempClient, self).__init__(**kwargs)
        self.entity_endpoint_base_url += country_code + '/'
        self.headers['Authorization'] = self.headers['Authorization'].replace("\n", "")

class DeliveryOrderTransitoryClient(EntityClientBase):
    entity_endpoint_base_url = '/delivery/delivery-order-transitory/'

    def __init__(self, country_code='cl', **kwargs):
        super(DeliveryOrderTransitoryClient, self).__init__(**kwargs)
        self.entity_endpoint_base_url += country_code + '/'
        self.headers['Authorization'] = self.headers['Authorization'].replace("\n", "")

    def create_from_request(self, delivery_order_request_id, pasync=True):
        params = {
            'delivery_order_request_id': delivery_order_request_id
        }

        return self.http_post_json(self.entity_endpoint_base_url + "_create-from-request", params)

    def create_label_sync(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_create-label-sync".format(id), params)

    def create_label_zpl(self, id, params):
        return self.http_post_json(self.entity_endpoint_base_url + "{0}/_create-label-zpl".format(id), params)

    def get_attachment_content(self, id, att_file_name):
        return self.http_get(
            self.entity_endpoint_base_url + "{0}/attachment/{1}".format(id, att_file_name)
        )
