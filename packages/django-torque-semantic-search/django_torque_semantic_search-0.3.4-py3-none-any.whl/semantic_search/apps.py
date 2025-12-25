from django.apps import AppConfig


class SemanticSearchConfig(AppConfig):
    name = "semantic_search"

    def ready(self):
        from semantic_search import receivers
