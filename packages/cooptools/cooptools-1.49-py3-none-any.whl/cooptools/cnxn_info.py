from dataclasses import dataclass, field
from cooptools.config import JsonConfigHandler
from typing import Callable
from cooptools.typeProviders import resolve
from cooptools.typeProviders import StringProvider

USER_TXT = 'user'
PW_TXT = 'pw'
URI_TXT = 'uri'
USESSL_TXT = 'use_ssl'
MOCK_TXT = 'mock'

@dataclass(frozen=True)
class Creds:
    user: str
    pw: str

    def as_dict(self):
        return {USER_TXT: self.user,
                PW_TXT: self.pw}

    @classmethod
    def mock(cls):
        return Creds(
            user='MOCK_USER',
            pw='MOCK_PW'
        )

    @classmethod
    def from_json_config(cls,
                         config: JsonConfigHandler,
                         user_key: str = USER_TXT,
                         pw_key: str = PW_TXT,
                         user_fallback_provider: StringProvider = None,
                         pw_fallback_provider: StringProvider = None,
                         ):
        user = config.resolve(
            config=user_key,
            fallback_val_provider=user_fallback_provider
        )
        pw = config.resolve(
            config=pw_key,
            fallback_val_provider=pw_fallback_provider
        )
        return Creds(
            user=user,
            pw=pw,
        )
@dataclass(frozen=True)
class CnxnInfo:
    uri: str = None
    creds: Creds = None
    mock: bool = False
    use_ssl: bool = True

    def __post_init__(self):
        if self.mock == True and self.uri is None:
            object.__setattr__(self, f'{self.uri=}'.split('=')[0].replace('self.', ''), 'MOCK_URL')

        if self.mock == True and self.creds is None:
            object.__setattr__(self, f'{self.creds=}'.split('=')[0].replace('self.', ''), Creds.mock())

        if self.mock == False and self.uri is None:
            raise ValueError(f"uri cannot be None if not mocking")

        if self.mock == False and self.creds is None:
            raise ValueError(f"creds cannot be None if not mocking")

    @classmethod
    def mocked(cls,
             creds: Creds = None,
             uri: str = None):
        return CnxnInfo(mock=True,
                        creds=creds if creds is not None else Creds.mock(),
                        uri=uri if uri else "MOCK_URI")

    @classmethod
    def from_json_config(cls,
                         config: JsonConfigHandler,
                         uri_key: str = URI_TXT,
                         user_key: str = USER_TXT,
                         pw_key: str = PW_TXT,
                         use_ssl_key: str = USESSL_TXT,
                         mock_key: str = MOCK_TXT,
                         uri_fallback_provider: StringProvider = None,
                         user_fallback_provider: StringProvider = None,
                         pw_fallback_provider: StringProvider = None,
                         usessl_fallback_provider=None,
                         mock_fallback_provider=None
                         ):
        uri = config.resolve(
            config=uri_key,
            fallback_val_provider=uri_fallback_provider
        )
        use_ssl = config.resolve(
            config=use_ssl_key,
            fallback_val_provider=usessl_fallback_provider,
            is_bool=True
        )
        mock = config.resolve(
            config=mock_key,
            fallback_val_provider=mock_fallback_provider,
            is_bool=True
        )
        return CnxnInfo(
            uri=uri,
            creds=Creds.from_json_config(
                config=config,
                user_key=user_key,
                pw_key=pw_key,
                user_fallback_provider=user_fallback_provider,
                pw_fallback_provider=pw_fallback_provider
            ),
            use_ssl=use_ssl,
            mock=mock
        )



CnxnProvider = CnxnInfo | Callable[[], CnxnInfo]
def resolve_cnxn_provider(cnxn_provider: CnxnProvider) ->CnxnInfo:
    return resolve(cnxn_provider)