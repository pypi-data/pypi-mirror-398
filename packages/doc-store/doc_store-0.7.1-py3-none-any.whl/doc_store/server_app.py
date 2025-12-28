from .doc_server import DocServer
from .doc_store import DocStore

app = DocServer(store=DocStore(decode_value=False)).app

__all__ = ["app"]
