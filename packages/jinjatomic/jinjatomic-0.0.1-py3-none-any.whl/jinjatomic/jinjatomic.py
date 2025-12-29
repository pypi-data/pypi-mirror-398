from dataclasses import dataclass
import typing

from jinja2 import Template
from requests import post, Response
import edn_format as edn  # type: ignore[import-untyped]


@dataclass
class Jinjatomic:

    data_url: str
    query_url: str
    fq_alias: str

    @classmethod
    def create(cls, host: str, storage_alias: str, db_name: str) -> "Jinjatomic":
        fq_alias: str = f"{storage_alias}/{db_name}"

        return Jinjatomic(
            data_url=f"{host}/data/{fq_alias}/",
            query_url=f"{host}/api/query",
            fq_alias=fq_alias,
        )

    def transact(self, datoms: str, **kwargs) -> list[list | dict]:
        payload: str = edn.dumps(
            edn.loads(Template("{:tx-data " + datoms + "}").render(dict(**kwargs)))
        )
        tx: Response = post(
            self.data_url,
            data=payload,
            headers={"Content-Type": "application/edn", "Accept": "application/edn"},
        )

        assert tx.status_code in range(200, 300), [tx.status_code, tx.text]
        return edn.loads(tx.text)

    def query(self, query: str, **kwargs) -> list[list | dict]:
        """ """
        _query: str = edn.dumps(edn.loads(Template(query).render(dict(**kwargs))))
        _args: str = edn.dumps(
            edn.loads(
                Template("""{:db/alias "{{alias}}"}""").render({"alias": self.fq_alias})
            )
        )

        payload: str = edn.dumps(
            edn.loads(Template("{:q {{_query}} :args [{{_args}}]}").render(locals()))
        )

        res: Response = post(
            self.query_url,
            data=payload,
            headers={"Content-Type": "application/edn", "Accept": "application/edn"},
        )

        assert res.status_code in range(200, 300), [res.status_code, res.text]
        return edn.loads(res.text)
