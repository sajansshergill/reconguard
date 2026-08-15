"""Query a Power BI dataset via the XMLA endpoint (DAX).
Requires the workspace + XMLA read enabled; used in the Azure path."""


class XmlaClient:
    def __init__(self, endpoint: str, token: str):
        self.endpoint = endpoint
        self.token = token

    def query(self, dax: str):
        # Uses pyadomd / an XMLA connection under the hood.
        # from pyadomd import Pyadomd
        # conn = Pyadomd(f"Provider=MSOLAP;Data Source={self.endpoint};"
        #                f"Password={self.token}")
        # with conn: return list(conn.cursor().execute(dax).fetchall())
        raise NotImplementedError("Configure pyadomd + workspace credentials")