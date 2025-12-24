from pydantic import BaseModel, ConfigDict


class BaseKafka(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    security_protocol: str | None = None
    sasl_mechanism: str | None = None
    sasl_plain_username: str | None = None
    sasl_plain_password: str | None = None
    request_timeout_ms: int = 9_000

    @property
    def con_kw(self):
        d = dict(
            security_protocol=self.security_protocol,
            sasl_mechanism=self.sasl_mechanism,
            sasl_plain_username=self.sasl_plain_username,
            sasl_plain_password=self.sasl_plain_password,
        )
        for k in tuple( d.keys()):
            if d[k] is None:
                d.pop(k)
        return d
