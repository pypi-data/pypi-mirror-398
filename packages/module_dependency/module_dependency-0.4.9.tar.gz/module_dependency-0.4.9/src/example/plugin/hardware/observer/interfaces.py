from library.mixin.observer import EventContext, EventSubscriber

class HardwareEventContext(EventContext):
    pass

class EventHardwareCreated(HardwareEventContext):
    def __init__(self, product: str):
        self.product = product

class EventHardwareOperation(HardwareEventContext):
    def __init__(self, product: str, operation: str):
        self.product = product
        self.operation = operation
