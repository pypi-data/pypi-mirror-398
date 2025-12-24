import abc

from apppy.env import AppNames


class WebhookInfo:
    def __init__(
        self,
        name: str,
        parent_app_names: AppNames | None = None,
        method: str = "POST",
        requires_queue: bool = False,
    ):
        if parent_app_names is not None:
            # CASE: The webhook is part of a larger application
            self.names = AppNames(prefix=parent_app_names.prefix_lower, suffix=name)
        else:
            self.names = AppNames(prefix=name)

        self.method = method
        self.requires_queue = requires_queue


class Webhook(abc.ABC):
    def __init__(self, webhook_info: WebhookInfo):
        self.info = webhook_info

    @abc.abstractmethod
    def process(self, event, _ctx):
        pass

    @abc.abstractmethod
    def verify(self, raw_body: bytes, signature_header: str | None) -> bool:
        pass
