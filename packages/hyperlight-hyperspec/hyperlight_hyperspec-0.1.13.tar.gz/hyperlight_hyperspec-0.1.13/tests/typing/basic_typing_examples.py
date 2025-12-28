# fmt: off
from __future__ import annotations

import datetime
import decimal
import pickle
from typing import Any, Dict, Final, List, Type, Union

import hyperspec


def check___version__() -> None:
    reveal_type(hyperspec.__version__)  # assert "str" in typ


def check_exceptions() -> None:
    reveal_type(hyperspec.MsgspecError)  # assert "Any" not in typ
    reveal_type(hyperspec.EncodeError)  # assert "Any" not in typ
    reveal_type(hyperspec.DecodeError)  # assert "Any" not in typ
    reveal_type(hyperspec.ValidationError)  # assert "Any" not in typ


def check_unset() -> None:
    reveal_type(hyperspec.UNSET)  # assert "UnsetType" in typ
    if isinstance(hyperspec.UNSET, hyperspec.UnsetType):
        print("True")
    str(hyperspec.UNSET)
    pickle.dumps(hyperspec.UNSET)


def check_unset_type_lowering(x: int | hyperspec.UnsetType) -> None:
    if x is hyperspec.UNSET:
        reveal_type(x)  # assert "int" not in typ.lower()
    else:
        reveal_type(x)  # assert "unset" not in typ.lower()


def check_nodefault() -> None:
    reveal_type(hyperspec.NODEFAULT)  # assert "Any" not in typ
    str(hyperspec.NODEFAULT)
    pickle.dumps(hyperspec.NODEFAULT)


##########################################################
# Structs                                                #
##########################################################

def check_struct() -> None:
    class Test(hyperspec.Struct):
        x: int
        y: str

    t = Test(1, "foo")
    reveal_type(t)  # assert "Test" in typ
    reveal_type(t.x)  # assert "int" in typ
    reveal_type(t.y)  # assert "str" in typ


def check_struct_field() -> None:
    class Test(hyperspec.Struct):
        a: int
        b: int = hyperspec.field(name="b_field")
        x: int = hyperspec.field(default=1)
        y: List[int] = hyperspec.field(default_factory=lambda: [1, 2, 3])
        x2: int = hyperspec.field(default=1, name="x2_field")
        y2: List[int] = hyperspec.field(default_factory=lambda: [1, 2, 3], name="y2_field")

    Test(1, 2)
    Test(1, 2, 3)
    Test(1, 2, 3, [4])
    Test(1, 2, 3, [4], 5)
    Test(1, 2, 3, [4], 5, [6])


def check_struct_kw_only() -> None:
    class Test(hyperspec.Struct, kw_only=True):
        x: int
        y: str

    t = Test(y="foo", x=1)


def check_struct_kw_only_base_class() -> None:
    class Base(hyperspec.Struct, kw_only=True):
        d: bytes
        c: str = "default"

    class Test(Base):
        a: int
        b: list[int] = []

    Test(1, d=b"foo")
    Test(1, [1, 2, 3], d=b"foo", c="test")


def check_struct_kw_only_subclass() -> None:
    class Base(hyperspec.Struct):
        d: bytes
        c: str = "default"

    class Test(Base, kw_only=True):
        a: int
        b: list[int] = []

    Test(b"foo", a=1)
    Test(b"foo", "test", a=1, b=[1, 2, 3])


def check_struct_final_fields() -> None:
    """Test that type checkers support `Final` fields for
    dataclass_transform"""
    class Test(hyperspec.Struct):
        x: Final[int] = 0

    t = Test()
    t2 = Test(x=1)
    reveal_type(t.x)  # assert "int" in typ
    reveal_type(t2.x)  # assert "int" in typ


def check_struct_repr_omit_defaults() -> None:
    class Test(hyperspec.Struct, repr_omit_defaults=True):
        x: int
        y: str

    t = Test(1, "foo")
    reveal_type(t.x)  # assert "int" in typ


def check_struct_omit_defaults() -> None:
    class Test(hyperspec.Struct, omit_defaults=True):
        x: int
        y: str

    t = Test(1, "foo")
    reveal_type(t)  # assert "Test" in typ
    reveal_type(t.x)  # assert "int" in typ
    reveal_type(t.y)  # assert "str" in typ


def check_struct_forbid_unknown_fields() -> None:
    class Test(hyperspec.Struct, forbid_unknown_fields=True):
        x: int
        y: str

    t = Test(1, "foo")
    reveal_type(t)  # assert "Test" in typ
    reveal_type(t.x)  # assert "int" in typ
    reveal_type(t.y)  # assert "str" in typ


def check_struct_rename() -> None:
    class TestLower(hyperspec.Struct, rename="lower"):
        x: int

    class TestUpper(hyperspec.Struct, rename="upper"):
        x: int

    class TestCamel(hyperspec.Struct, rename="camel"):
        x: int

    class TestPascal(hyperspec.Struct, rename="pascal"):
        x: int

    class TestKebab(hyperspec.Struct, rename="kebab"):
        x: int

    class TestCallable(hyperspec.Struct, rename=lambda x: x.title()):
        x: int

    class TestCallableNone(hyperspec.Struct, rename=lambda x: None):
        x: int

    class TestMapping(hyperspec.Struct, rename={"x": "X"}):
        x: int

    class TestNone(hyperspec.Struct, rename=None):
        x: int

    o = sum(
        [
            TestLower(1).x,
            TestUpper(2).x,
            TestCamel(3).x,
            TestPascal(4).x,
            TestCallable(5).x,
            TestNone(6).x,
        ]
    )

    reveal_type(o)  # assert "int" in typ


def check_struct_array_like() -> None:
    class Test(hyperspec.Struct, array_like=True):
        x: int
        y: str

    t = Test(1, "foo")
    reveal_type(t)  # assert "Test" in typ
    reveal_type(t.x)  # assert "int" in typ
    reveal_type(t.y)  # assert "str" in typ


def check_struct_frozen() -> None:
    class Test(hyperspec.Struct, frozen=True):
        x: int
        y: str

    t = Test(1, "foo")
    reveal_type(t)  # assert "Test" in typ
    reveal_type(t.x)  # assert "int" in typ
    reveal_type(t.y)  # assert "str" in typ


def check_struct_eq() -> None:
    class Test(hyperspec.Struct, eq=False):
        x: int
        y: str

    t = Test(1, "foo")
    t2 = Test(1, "foo")
    if t == t2:
        print("Here")
    reveal_type(t)  # assert "Test" in typ
    reveal_type(t.x)  # assert "int" in typ
    reveal_type(t.y)  # assert "str" in typ


def check_struct_order() -> None:
    class Test(hyperspec.Struct, order=True):
        x: int
        y: str

    t = Test(1, "foo")
    reveal_type(t)  # assert "Test" in typ
    reveal_type(t.x)  # assert "int" in typ
    reveal_type(t.y)  # assert "str" in typ


def check_struct_gc() -> None:
    class Test(hyperspec.Struct, gc=False):
        x: int
        y: str

    t = Test(1, "foo")
    reveal_type(t)  # assert "Test" in typ
    reveal_type(t.x)  # assert "int" in typ
    reveal_type(t.y)  # assert "str" in typ


def check_struct_weakref() -> None:
    class Test(hyperspec.Struct, weakref=True):
        x: int
        y: str

    t = Test(1, "foo")
    reveal_type(t)  # assert "Test" in typ
    reveal_type(t.x)  # assert "int" in typ
    reveal_type(t.y)  # assert "str" in typ


def check_struct_dict() -> None:
    class Test(hyperspec.Struct, dict=True):
        x: int
        y: str

    t = Test(1, "foo")
    reveal_type(t)  # assert "Test" in typ


def check_struct_cache_hash() -> None:
    class Test(hyperspec.Struct, cache_hash=True):
        x: int
        y: str

    t = Test(1, "foo")
    reveal_type(t)  # assert "Test" in typ


def check_struct_tag_tag_field() -> None:
    class Test1(hyperspec.Struct, tag=None):
        pass

    class Test2(hyperspec.Struct, tag=True):
        pass

    class Test3(hyperspec.Struct, tag=False):
        pass

    class Test4(hyperspec.Struct, tag="mytag"):
        pass

    class Test5(hyperspec.Struct, tag=123):
        pass

    class Test6(hyperspec.Struct, tag=str.lower):
        pass

    class Test7(hyperspec.Struct, tag=lambda n: len(n)):
        pass

    class Test8(hyperspec.Struct, tag_field=None):
        pass

    class Test9(hyperspec.Struct, tag_field="type"):
        pass


def check_struct_methods() -> None:
    class Point(hyperspec.Struct):
        x: int
        y: int


    a = Point(1, 2)
    b = Point(3, 4)
    if a == b:
        print("equal")
    a.x = a.x + b.y
    repr(a)

    for item in a.__rich_repr__():
        assert isinstance(item, tuple)
        assert len(item) == 2
        name, val = item
        print(f"{name} = {val}")


def check_struct_attributes() -> None:
    class Point(hyperspec.Struct):
        x: int
        y: int

    for field in Point.__struct_fields__:
        reveal_type(field)  # assert "str" in typ

    for field in Point.__match_args__:
        reveal_type(field)  # assert "any" not in typ.lower()

    p = Point(1, 2)

    for field in p.__struct_fields__:
        reveal_type(field)  # assert "str" in typ


def check_struct_config() -> None:
    class Point(hyperspec.Struct):
        x: int
        y: int

    config = Point.__struct_config__

    reveal_type(config)  # assert "StructConfig" in typ
    reveal_type(config.frozen)  # assert "bool" in typ
    reveal_type(config.eq)  # assert "bool" in typ
    reveal_type(config.order)  # assert "bool" in typ
    reveal_type(config.array_like)  # assert "bool" in typ
    reveal_type(config.gc)  # assert "bool" in typ
    reveal_type(config.repr_omit_defaults)  # assert "bool" in typ
    reveal_type(config.omit_defaults)  # assert "bool" in typ
    reveal_type(config.forbid_unknown_fields)  # assert "bool" in typ
    reveal_type(config.weakref)  # assert "bool" in typ
    reveal_type(config.dict)  # assert "bool" in typ
    reveal_type(config.cache_hash)  # assert "bool" in typ
    reveal_type(config.tag)  # assert "str" in typ and "int" in typ
    reveal_type(config.tag_field)  # assert "str" in typ


##########################################################
# defstruct                                              #
##########################################################


def check_defstruct() -> None:
    Test = hyperspec.defstruct("Test", ["x", "y"])
    for field in Test.__struct_fields__:
        reveal_type(field)  # assert "str" in typ
    Test(1, y=2)


def check_defstruct_field_types() -> None:
    Test = hyperspec.defstruct(
        "Test",
        ("x", ("y", int), ("z", str, "default"))
    )


def check_defstruct_bases() -> None:
    class Base(hyperspec.Struct):
        pass

    hyperspec.defstruct("Test", ["x", "y"], bases=(Base,))
    hyperspec.defstruct("Test2", ["x", "y"], bases=None)


def check_defstruct_namespace() -> None:
    hyperspec.defstruct("Test", ["x", "y"], namespace={"classval": 1})
    hyperspec.defstruct("Test2", ["x", "y"], namespace=None)


def check_defstruct_module() -> None:
    hyperspec.defstruct("Test", ["x", "y"], module="mymod")
    hyperspec.defstruct("Test2", ["x", "y"], module=None)


def check_defstruct_config_options() -> None:
    Test = hyperspec.defstruct(
        "Test",
        ("x", "y"),
        omit_defaults=True,
        forbid_unknown_fields=True,
        frozen=True,
        order=True,
        eq=True,
        kw_only=True,
        repr_omit_defaults=True,
        array_like=True,
        dict=True,
        weakref=True,
        cache_hash=True,
        gc=False,
        tag="mytag",
        tag_field="mytagfield",
        rename="lower"
    )

##########################################################
# hyperspec.structs                                        #
##########################################################

def check_replace() -> None:
    class Test(hyperspec.Struct):
        x: int
        y: int
        struct: int

    struct = Test(1, 2, 3)
    reveal_type(hyperspec.structs.replace(struct))  # assert "Test" in typ
    reveal_type(hyperspec.structs.replace(struct, x=1))  # assert "Test" in typ
    reveal_type(hyperspec.structs.replace(struct, struct=1))  # assert "Test" in typ


def check_asdict() -> None:
    class Test(hyperspec.Struct):
        x: int
        y: int

    x = Test(1, 2)
    o = hyperspec.structs.asdict(x)
    reveal_type(o)  # assert "dict" in typ
    reveal_type(o["foo"])  # assert "Any" in typ


def check_astuple() -> None:
    class Test(hyperspec.Struct):
        x: int
        y: int

    x = Test(1, 2)
    o = hyperspec.structs.astuple(x)
    reveal_type(o)  # assert "tuple" in typ
    reveal_type(o[0])  # assert "Any" in typ


def check_force_setattr() -> None:
    class Point(hyperspec.Struct, frozen=True):
        x: int
        y: int

    obj = Point(1, 2)
    hyperspec.structs.force_setattr(obj, "x", 3)


def check_fields() -> None:
    class Test(hyperspec.Struct):
        x: int
        y: int

    x = Test(1, 2)
    res1 = hyperspec.structs.fields(x)
    reveal_type(res1)  # assert "tuple" in typ.lower() and "FieldInfo" in typ
    res2 = hyperspec.structs.fields(Test)
    reveal_type(res2)  # assert "tuple" in typ.lower() and "FieldInfo" in typ

    for field in res1:
        reveal_type(field)  # assert "FieldInfo" in typ
        reveal_type(field.required)  # assert "bool" in typ
        reveal_type(field.name)  # assert "str" in typ


##########################################################
# Meta                                                   #
##########################################################

def check_meta_constructor() -> None:
    hyperspec.Meta()
    for val in [1, 1.5, None]:
        hyperspec.Meta(gt=val)
        hyperspec.Meta(ge=val)
        hyperspec.Meta(lt=val)
        hyperspec.Meta(le=val)
        hyperspec.Meta(multiple_of=val)
    for val2 in ["string", None]:
        hyperspec.Meta(pattern=val2)
        hyperspec.Meta(title=val2)
        hyperspec.Meta(description=val2)
    for val3 in [1, None]:
        hyperspec.Meta(min_length=val3)
        hyperspec.Meta(max_length=val3)
    for val4 in [True, False, None]:
        hyperspec.Meta(tz=val4)
    for val5 in [[1, 2, 3], None]:
        hyperspec.Meta(examples=val5)
    for val6 in [{"foo": "bar"}, None]:
        hyperspec.Meta(extra_json_schema=val6)
        hyperspec.Meta(extra=val6)


def check_meta_attributes() -> None:
    c = hyperspec.Meta()
    print(c.gt)
    print(c.ge)
    print(c.lt)
    print(c.le)
    print(c.multiple_of)
    print(c.pattern)
    print(c.min_length)
    print(c.max_length)
    print(c.tz)
    print(c.title)
    print(c.description)
    print(c.examples)
    print(c.extra_json_schema)
    print(c.extra)


def check_meta_equal() -> None:
    c1 = hyperspec.Meta()
    c2 = hyperspec.Meta()
    if c1 == c2:
        print("ok")


def check_meta_methods() -> None:
    c = hyperspec.Meta()
    for name, val in c.__rich_repr__():
        print(f"{name} = {val}")


##########################################################
# Raw                                                    #
##########################################################

def check_raw_constructor() -> None:
    r = hyperspec.Raw()
    r2 = hyperspec.Raw(b"test")
    r3 = hyperspec.Raw(bytearray(b"test"))
    r4 = hyperspec.Raw(memoryview(b"test"))
    r2 = hyperspec.Raw("test")


def check_raw_copy() -> None:
    r = hyperspec.Raw()
    r2 = r.copy()
    reveal_type(r2)  # assert "Raw" in typ


def check_raw_methods() -> None:
    r1 = hyperspec.Raw(b"a")
    r2 = hyperspec.Raw(b"b")
    if r1 == r2:
        print(r1)

    m = memoryview(r1)  # buffer protocol


def check_raw_pass_to_decode() -> None:
    r = hyperspec.Raw()
    res = hyperspec.json.decode(r)
    res2 = hyperspec.msgpack.decode(r)


##########################################################
# MessagePack                                            #
##########################################################

def check_msgpack_Encoder_encode() -> None:
    enc = hyperspec.msgpack.Encoder()
    b = enc.encode([1, 2, 3])

    reveal_type(b)  # assert "bytes" in typ


def check_msgpack_Encoder_encode_into() -> None:
    enc = hyperspec.msgpack.Encoder()
    buf = bytearray(48)
    enc.encode_into([1, 2, 3], buf)
    enc.encode_into([1, 2, 3], buf, 2)


def check_msgpack_encode() -> None:
    b = hyperspec.msgpack.encode([1, 2, 3])

    reveal_type(b)  # assert "bytes" in typ


def check_msgpack_Decoder_decode_any() -> None:
    dec = hyperspec.msgpack.Decoder()
    b = hyperspec.msgpack.encode([1, 2, 3])
    o = dec.decode(b)

    reveal_type(dec)  # assert "Decoder" in typ and "Any" in typ
    reveal_type(o)  # assert "Any" in typ


def check_msgpack_Decoder_decode_typed() -> None:
    dec = hyperspec.msgpack.Decoder(List[int])
    b = hyperspec.msgpack.encode([1, 2, 3])
    o = dec.decode(b)

    reveal_type(dec)  # assert "Decoder" in typ and ("List" in typ or "list" in typ) and "int" in typ
    reveal_type(o)  # assert ("List" in typ or "list" in typ) and "int" in typ


def check_msgpack_Decoder_decode_union() -> None:
    # Pyright doesn't require the annotation, but mypy does until TypeForm
    # is supported. This is mostly checking that no error happens here.
    dec: hyperspec.msgpack.Decoder[Union[int, str]] = hyperspec.msgpack.Decoder(Union[int, str])
    o = dec.decode(b'')
    reveal_type(o)  # assert ("int" in typ and "str" in typ)


def check_msgpack_Decoder_decode_type_comment() -> None:
    dec = hyperspec.msgpack.Decoder()  # type: hyperspec.msgpack.Decoder[List[int]]
    b = hyperspec.msgpack.encode([1, 2, 3])
    o = dec.decode(b)

    reveal_type(dec)  # assert "Decoder" in typ and ("List" in typ or "list" in typ) and "int" in typ
    reveal_type(o)  # assert ("List" in typ or "list" in typ) and "int" in typ


def check_msgpack_decode_any() -> None:
    b = hyperspec.msgpack.encode([1, 2, 3])
    o = hyperspec.msgpack.decode(b)

    reveal_type(o)  # assert "Any" in typ


def check_msgpack_decode_typed() -> None:
    b = hyperspec.msgpack.encode([1, 2, 3])
    o = hyperspec.msgpack.decode(b, type=List[int])

    reveal_type(o)  # assert ("List" in typ or "list" in typ) and "int" in typ


def check_msgpack_decode_from_buffer() -> None:
    msg = hyperspec.msgpack.encode([1, 2, 3])
    hyperspec.toml.decode(memoryview(msg))


def check_msgpack_decode_typed_union() -> None:
    o: Union[int, str] = hyperspec.msgpack.decode(b"", type=Union[int, str])
    reveal_type(o)  # assert "int" in typ and "str" in typ


def check_msgpack_encode_enc_hook() -> None:
    hyperspec.msgpack.encode(object(), enc_hook=lambda x: None)


def check_msgpack_Encoder_enc_hook() -> None:
    hyperspec.msgpack.Encoder(enc_hook=lambda x: None)


def check_msgpack_order() -> None:
    enc = hyperspec.msgpack.Encoder(order=None)
    hyperspec.msgpack.Encoder(order='deterministic')
    hyperspec.msgpack.Encoder(order='sorted')
    reveal_type(enc.order)  # assert "deterministic" in typ

    hyperspec.msgpack.encode({"a": 1}, order=None)
    hyperspec.msgpack.encode({"a": 1}, order='deterministic')
    hyperspec.msgpack.encode({"a": 1}, order='sorted')


def check_msgpack_Encoder_decimal_format() -> None:
    enc = hyperspec.msgpack.Encoder(decimal_format="string")
    hyperspec.msgpack.Encoder(decimal_format="number")
    reveal_type(enc.decimal_format)  # assert "string" in typ.lower() and "number" in typ.lower()


def check_msgpack_Encoder_uuid_format() -> None:
    enc = hyperspec.msgpack.Encoder(uuid_format="canonical")
    hyperspec.msgpack.Encoder(uuid_format="hex")
    hyperspec.msgpack.Encoder(uuid_format="bytes")
    reveal_type(enc.uuid_format)  # assert all(s in typ.lower() for s in ("canonical", "hex", "bytes"))


def check_msgpack_decode_dec_hook() -> None:
    def dec_hook(typ: Type, obj: Any) -> Any:
        return typ(obj)

    hyperspec.msgpack.decode(b"test", dec_hook=dec_hook)
    hyperspec.msgpack.Decoder(dec_hook=dec_hook)


def check_msgpack_decode_ext_hook() -> None:
    def ext_hook(code: int, data: memoryview) -> Any:
        return pickle.loads(data)

    hyperspec.msgpack.decode(b"test", ext_hook=ext_hook)
    hyperspec.msgpack.Decoder(ext_hook=ext_hook)


def check_msgpack_Decoder_strict() -> None:
    dec = hyperspec.msgpack.Decoder(List[int], strict=False)
    reveal_type(dec.strict)  # assert "bool" in typ


def check_msgpack_decode_strict() -> None:
    out = hyperspec.msgpack.decode(b'', type=List[int], strict=False)
    reveal_type(out)  # assert "list" in typ.lower()


def check_msgpack_Ext() -> None:
    ext = hyperspec.msgpack.Ext(1, b"test")
    reveal_type(ext.code)  # assert "int" in typ
    reveal_type(ext.data)  # assert "bytes" in typ


##########################################################
# JSON                                                   #
##########################################################

def check_json_Encoder_encode() -> None:
    enc = hyperspec.json.Encoder()
    b = enc.encode([1, 2, 3])

    reveal_type(b)  # assert "bytes" in typ


def check_json_Encoder_encode_lines() -> None:
    enc = hyperspec.json.Encoder()
    items = [{"x": 1}, 2]
    b = enc.encode_lines(items)
    b2 = enc.encode_lines((i for i in items))

    reveal_type(b)  # assert "bytes" in typ
    reveal_type(b2)  # assert "bytes" in typ


def check_json_Encoder_encode_into() -> None:
    enc = hyperspec.json.Encoder()
    buf = bytearray(48)
    enc.encode_into([1, 2, 3], buf)
    enc.encode_into([1, 2, 3], buf, 2)


def check_json_encode() -> None:
    b = hyperspec.json.encode([1, 2, 3])

    reveal_type(b)  # assert "bytes" in typ


def check_json_Decoder_decode_any() -> None:
    dec = hyperspec.json.Decoder()
    b = hyperspec.json.encode([1, 2, 3])
    o = dec.decode(b)

    reveal_type(dec)  # assert "Decoder" in typ and "Any" in typ
    reveal_type(o)  # assert "Any" in typ


def check_json_Decoder_decode_typed() -> None:
    dec = hyperspec.json.Decoder(List[int])
    b = hyperspec.json.encode([1, 2, 3])
    o = dec.decode(b)

    reveal_type(dec)  # assert "Decoder" in typ and ("List" in typ or "list" in typ) and "int" in typ
    reveal_type(o)  # assert ("List" in typ or "list" in typ) and "int" in typ


def check_json_Decoder_decode_type_comment() -> None:
    dec = hyperspec.json.Decoder()  # type: hyperspec.json.Decoder[List[int]]
    b = hyperspec.json.encode([1, 2, 3])
    o = dec.decode(b)

    reveal_type(dec)  # assert "Decoder" in typ and ("List" in typ or "list" in typ) and "int" in typ
    reveal_type(o)  # assert ("List" in typ or "list" in typ) and "int" in typ


def check_json_Decoder_decode_union() -> None:
    dec: hyperspec.json.Decoder[Union[int, str]] = hyperspec.json.Decoder(Union[int, str])
    o = dec.decode(b'')
    reveal_type(o)  # assert ("int" in typ and "str" in typ)


def check_json_Decoder_decode_from_str() -> None:
    dec = hyperspec.json.Decoder(List[int])
    o = dec.decode("[1, 2, 3]")
    reveal_type(o)  # assert ("List" in typ or "list" in typ) and "int" in typ


def check_json_Decoder_decode_lines_any() -> None:
    dec = hyperspec.json.Decoder()
    o = dec.decode_lines(b'1\n2\n3')

    reveal_type(o)  # assert "list" in typ.lower() and "any" in typ.lower()


def check_json_Decoder_decode_lines_typed() -> None:
    dec = hyperspec.json.Decoder(int)
    o = dec.decode_lines(b'1\n2\n3')
    reveal_type(o)  # assert "list" in typ.lower() and "int" in typ.lower()


def check_json_decode_any() -> None:
    b = hyperspec.json.encode([1, 2, 3])
    o = hyperspec.json.decode(b)

    reveal_type(o)  # assert "Any" in typ


def check_json_decode_typed() -> None:
    b = hyperspec.json.encode([1, 2, 3])
    o = hyperspec.json.decode(b, type=List[int])

    reveal_type(o)  # assert ("List" in typ or "list" in typ) and "int" in typ


def check_json_decode_typed_union() -> None:
    o: Union[int, str] = hyperspec.json.decode(b"", type=Union[int, str])
    reveal_type(o)  # assert "int" in typ and "str" in typ


def check_json_decode_from_str() -> None:
    hyperspec.json.decode("[1, 2, 3]")

    o = hyperspec.json.decode("[1, 2, 3]", type=List[int])
    reveal_type(o)  # assert ("List" in typ or "list" in typ) and "int" in typ


def check_json_decode_from_buffer() -> None:
    hyperspec.json.decode(memoryview(b"[1, 2, 3]"))


def check_json_encode_enc_hook() -> None:
    hyperspec.json.encode(object(), enc_hook=lambda x: None)


def check_json_Encoder_enc_hook() -> None:
    hyperspec.json.Encoder(enc_hook=lambda x: None)


def check_json_order() -> None:
    enc = hyperspec.json.Encoder(order=None)
    hyperspec.json.Encoder(order='deterministic')
    hyperspec.json.Encoder(order='sorted')
    reveal_type(enc.order)  # assert "deterministic" in typ

    hyperspec.json.encode({"a": 1}, order=None)
    hyperspec.json.encode({"a": 1}, order='deterministic')
    hyperspec.json.encode({"a": 1}, order='sorted')


def check_json_Encoder_decimal_format() -> None:
    enc = hyperspec.json.Encoder(decimal_format="string")
    hyperspec.json.Encoder(decimal_format="number")
    reveal_type(enc.decimal_format)  # assert "string" in typ.lower() and "number" in typ.lower()


def check_json_Encoder_uuid_format() -> None:
    enc = hyperspec.json.Encoder(uuid_format="canonical")
    hyperspec.json.Encoder(uuid_format="hex")
    reveal_type(enc.uuid_format)  # assert all(s in typ.lower() for s in ("canonical", "hex"))


def check_json_decode_dec_hook() -> None:
    def dec_hook(typ: Type, obj: Any) -> Any:
        return typ(obj)

    hyperspec.json.decode(b"test", dec_hook=dec_hook)
    hyperspec.json.Decoder(dec_hook=dec_hook)


def check_json_Decoder_float_hook() -> None:
    hyperspec.json.Decoder(float_hook=None)
    hyperspec.json.Decoder(float_hook=float)
    dec = hyperspec.json.Decoder(float_hook=decimal.Decimal)
    if dec.float_hook is not None:
        dec.float_hook("1.5")


def check_json_Decoder_strict() -> None:
    dec = hyperspec.json.Decoder(List[int], strict=False)
    reveal_type(dec.strict)  # assert "bool" in typ


def check_json_decode_strict() -> None:
    out = hyperspec.json.decode(b'', type=List[int], strict=False)
    reveal_type(out)  # assert "list" in typ.lower()


def check_json_format() -> None:
    reveal_type(hyperspec.json.format(b"test"))  # assert "bytes" in typ
    reveal_type(hyperspec.json.format(b"test", indent=4))  # assert "bytes" in typ
    reveal_type(hyperspec.json.format("test"))  # assert "str" in typ
    reveal_type(hyperspec.json.format("test", indent=4))  # assert "str" in typ

##########################################################
# YAML                                                   #
##########################################################

def check_yaml_encode() -> None:
    b = hyperspec.yaml.encode([1, 2, 3])

    reveal_type(b)  # assert "bytes" in typ


def check_yaml_decode_any() -> None:
    o = hyperspec.yaml.decode(b"[1, 2, 3]")
    reveal_type(o)  # assert "Any" in typ


def check_yaml_decode_typed() -> None:
    o = hyperspec.yaml.decode(b"[1, 2, 3]", type=List[int])
    reveal_type(o)  # assert "list" in typ.lower() and "int" in typ


def check_yaml_decode_typed_union() -> None:
    o: Union[int, str] = hyperspec.yaml.decode(b"1", type=Union[int, str])
    reveal_type(o)  # assert "int" in typ and "str" in typ


def check_yaml_decode_from_str() -> None:
    hyperspec.yaml.decode("[1, 2, 3]")
    o = hyperspec.yaml.decode("[1, 2, 3]", type=List[int])
    reveal_type(o)  # assert "list" in typ.lower() and "int" in typ


def check_yaml_decode_from_buffer() -> None:
    hyperspec.yaml.decode(memoryview(b"[1, 2, 3]"))


def check_yaml_encode_enc_hook() -> None:
    hyperspec.yaml.encode(object(), enc_hook=lambda x: None)


def check_yaml_encode_order() -> None:
    hyperspec.yaml.encode(object(), order=None)
    hyperspec.yaml.encode(object(), order="deterministic")
    hyperspec.yaml.encode(object(), order="sorted")


def check_yaml_decode_dec_hook() -> None:
    def dec_hook(typ: Type, obj: Any) -> Any:
        return typ(obj)

    hyperspec.yaml.decode(b"test", dec_hook=dec_hook)


def check_yaml_decode_strict() -> None:
    out = hyperspec.yaml.decode(b'', type=List[int], strict=False)
    reveal_type(out)  # assert "list" in typ.lower()


##########################################################
# TOML                                                   #
##########################################################

def check_toml_encode() -> None:
    b = hyperspec.toml.encode({"a": 1})

    reveal_type(b)  # assert "bytes" in typ


def check_toml_decode_any() -> None:
    o = hyperspec.toml.decode(b"a = 1")
    reveal_type(o)  # assert "Any" in typ


def check_toml_decode_typed() -> None:
    o = hyperspec.toml.decode(b"a = 1", type=Dict[str, int])
    reveal_type(o)  # assert "dict" in typ.lower() and "int" in typ


def check_toml_decode_from_str() -> None:
    hyperspec.toml.decode("a = 1")
    o = hyperspec.toml.decode("a = 1", type=Dict[str, int])
    reveal_type(o)  # assert "dict" in typ.lower() and "int" in typ


def check_toml_decode_from_buffer() -> None:
    hyperspec.toml.decode(memoryview(b"a = 1"))


def check_toml_encode_enc_hook() -> None:
    hyperspec.toml.encode(object(), enc_hook=lambda x: None)


def check_toml_encode_order() -> None:
    hyperspec.toml.encode(object(), order=None)
    hyperspec.toml.encode(object(), order="deterministic")
    hyperspec.toml.encode(object(), order="sorted")


def check_toml_decode_dec_hook() -> None:
    def dec_hook(typ: Type, obj: Any) -> Any:
        return typ(obj)

    hyperspec.toml.decode(b"a = 1", dec_hook=dec_hook)


def check_toml_decode_strict() -> None:
    out = hyperspec.toml.decode(b'', type=List[int], strict=False)
    reveal_type(out)  # assert "list" in typ.lower()


##########################################################
# hyperspec.inspect                                        #
##########################################################

def check_inspect_type_info() -> None:
    o = hyperspec.inspect.type_info(List[int])
    reveal_type(o)  # assert "Type" in typ

    hyperspec.inspect.type_info(int)
    hyperspec.inspect.type_info(int)
    hyperspec.inspect.type_info(int)


def check_inspect_multi_type_info() -> None:
    o = hyperspec.inspect.multi_type_info([int, float])
    reveal_type(o)  # assert "Type" in typ and "tuple" in typ.lower()

    o2 = hyperspec.inspect.multi_type_info((int, float))
    reveal_type(o2)  # assert "Type" in typ and "tuple" in typ.lower()

    hyperspec.inspect.multi_type_info([int])
    hyperspec.inspect.multi_type_info([int])
    hyperspec.inspect.multi_type_info([int])


def max_depth(t: hyperspec.inspect.Type, depth: int = 0) -> int:
    # This isn't actually a complete max_depth implementation
    if isinstance(t, hyperspec.inspect.CollectionType):
        reveal_type(t.item_type)  # assert "Type" in typ
        return max_depth(t.item_type, depth + 1)
    elif isinstance(t, hyperspec.inspect.DictType):
        reveal_type(t.key_type)  # assert "Type" in typ
        return max(
            max_depth(t.key_type, depth + 1),
            max_depth(t.value_type, depth + 1)
        )
    elif isinstance(t, hyperspec.inspect.TupleType):
        reveal_type(t.item_types)  # assert "Type" in typ and "tuple" in typ.lower()
        return max(max_depth(a, depth + 1) for a in t.item_types)
    else:
        return depth


def check_consume_inspect_types() -> None:
    t = hyperspec.inspect.type_info(List[int])
    o = max_depth(t)
    reveal_type(o)  # assert "int" in typ.lower()

    t = hyperspec.inspect.UnionType(
        (hyperspec.inspect.IntType(), hyperspec.inspect.NoneType())
    )
    reveal_type(t.includes_none)  # assert "bool" in typ.lower()


def check_inspect_is_struct() -> None:
    class Point(hyperspec.Struct):
        x: int

    obj: object = Point(1)
    if hyperspec.inspect.is_struct(obj):
        reveal_type(obj)  # assert "Struct" in typ
    else:
        reveal_type(obj)  # assert "Struct" not in typ

    ns: object = object()
    if hyperspec.inspect.is_struct(ns):
        reveal_type(ns)  # assert "Struct" in typ
    else:
        reveal_type(ns)  # assert "Struct" not in typ


def check_inspect_is_struct_type() -> None:
    class Point(hyperspec.Struct):
        x: int

    tp: type[Any] = Point
    if hyperspec.inspect.is_struct_type(tp):
        reveal_type(tp)  # assert "type" in typ and "Struct" in typ
    else:
        reveal_type(tp)  # assert "Struct" not in typ

    other: type[Any] = type("NotStruct", (), {})
    if hyperspec.inspect.is_struct_type(other):
        reveal_type(other)  # assert "Struct" in typ
    else:
        reveal_type(other)  # assert "Struct" not in typ


##########################################################
# JSON Schema                                            #
##########################################################


def check_json_schema() -> None:
    o1 = hyperspec.json.schema(List[int])
    reveal_type(o1)  # assert ("Dict" in typ or "dict" in typ)

    o2 = hyperspec.json.schema(List[int], schema_hook=lambda t: {"type": "object"})
    reveal_type(o2)  # assert ("Dict" in typ or "dict" in typ)


def check_json_schema_components() -> None:
    s1, c1 = hyperspec.json.schema_components([List[int]])
    reveal_type(s1)  # assert ("dict" in typ.lower()) and ("tuple" in typ.lower())
    reveal_type(c1)  # assert ("dict" in typ.lower())

    s2, c2 = hyperspec.json.schema_components([List[int]], ref_template="#/definitions/{name}")
    reveal_type(s2)  # assert ("dict" in typ.lower()) and ("tuple" in typ.lower())
    reveal_type(c2)  # assert ("dict" in typ.lower())

    s3, c3 = hyperspec.json.schema_components(
        [List[int]], schema_hook=lambda t: {"type": "object"}
    )
    reveal_type(s3)  # assert ("dict" in typ.lower()) and ("tuple" in typ.lower())
    reveal_type(c3)  # assert ("dict" in typ.lower())


##########################################################
# Converters                                             #
##########################################################

def check_to_builtins() -> None:
    hyperspec.to_builtins(1)
    hyperspec.to_builtins({1: 2}, str_keys=False)
    hyperspec.to_builtins(b"test", builtin_types=(bytes, bytearray, memoryview))
    hyperspec.to_builtins([1, 2, 3], enc_hook=lambda x: None)
    hyperspec.to_builtins([1, 2, 3], order=None)
    hyperspec.to_builtins([1, 2, 3], order="deterministic")
    hyperspec.to_builtins([1, 2, 3], order="sorted")


def check_convert() -> None:
    o1 = hyperspec.convert(1, int)
    reveal_type(o1)  # assert "int" in typ.lower()

    o2 = hyperspec.convert([1, 2], List[float])
    reveal_type(o2)  # assert "list" in typ.lower()

    o3 = hyperspec.convert(1, int, strict=False)
    reveal_type(o3)  # assert "int" in typ.lower()

    o4 = hyperspec.convert(1, int, from_attributes=True)
    reveal_type(o4)  # assert "int" in typ.lower()

    o5 = hyperspec.convert(1, int, dec_hook=lambda typ, x: None)
    reveal_type(o5)  # assert "int" in typ.lower()

    o6 = hyperspec.convert(1, int, builtin_types=(bytes, bytearray, memoryview))
    reveal_type(o6)  # assert "int" in typ.lower()

    o7 = hyperspec.convert("1", int, str_keys=True)
    reveal_type(o7)  # assert "int" in typ.lower()
