import json
from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Callable, TypeVar, Union, Any
from cooptools.version import Version

T = TypeVar('T')
Encoder = Callable[[T], str]
Decoder = Callable[[str], T]

@dataclass(frozen=True)
class JsonTranslator:
    encoder: Encoder
    decoder: Decoder

@dataclass(frozen=True)
class JsonIOVersionController:
    version_switch: Dict[Version, JsonTranslator]
    version_field: str = 'version'

    def _look_for_version(self, json_str: str, version: Union[str, Version] = None):
        json_dict = json.loads(json_str)

        recorded_version = json_dict.get(self.version_field, None)
        if recorded_version is not None:
            version = Version(recorded_version)

        if version is not None and type(version) == str:
            version = Version(version)

        if version is None:
            raise ValueError(f"The version could not be found")

        if self.version_switch.get(version, None) is None:
            raise ValueError(f"The version is not supported")

        return version

    def from_json(self, json: str, version: Union[str, Version] = None) -> T:
        version: Version = self._look_for_version(json, version)
        return self.version_switch[version].decoder(json)


    def to_json(self, obj, version: Union[str, Version] = None):
        version: Version = Version.from_val(version) if version is not None else self.MaxVersion
        json_str = self.version_switch[version].encoder(obj)

        try:
            json_dict = json.loads(json_str)
        except Exception as e:
            raise ValueError(
                f"The defined encoder for {version} does not correctly encode to a string. A value of type {type(json_str)} was created") from e

        if json_dict.get(self.version_field, None) is None:
            json_dict[self.version_field] = version.txt

        return json.dumps(json_dict)

    @property
    def MaxVersion(self) -> Version:
        return max([x for x in self.version_switch.keys()])


if __name__ == "__main__":
    def A_from_json_1(json_str: str):
        json_dict = json.loads(json_str)
        a = json_dict['a']
        b = json_dict['b']
        return A(a, b)

    def A_from_json_2(json_str: str):
        json_dict = json.loads(json_str)
        a = json_dict['a_me']
        b = json_dict['b_me']
        return A(a, b)


    Ajson1 = JsonTranslator(
        encoder=lambda x: json.dumps({
            'a': x.a,
            'b': x.b
        }),
        decoder=lambda x: A_from_json_1(x)
    )
    Ajson2 = JsonTranslator(
        encoder=lambda x: json.dumps({
            'a_me': x.a,
            'b_me': x.b
        }),
        decoder=lambda x: A_from_json_2(x)
    )

    class A:
        js_v = JsonIOVersionController({
            Version('0.2'): Ajson1,
            Version('0.1'): Ajson2,
        })

        def __init__(self, a, b):
            self.a = a
            self.b = b

        @classmethod
        def from_json(cls, json_str: str, version: Union[Version, str] = None):
            return cls.js_v.from_json(json_str, version)

        def to_json(self, version: Union[Version, str] = None) -> str:
            return self.js_v.to_json(self, version)



    a = A(1, 2)

    print(a.js_v.MaxVersion)

    j1 = a.to_json("0.1")
    ob = A.from_json(j1)
    print(ob)

