import pytest

from kaiju_tools.templates import Template


@pytest.mark.parametrize(
    ['template', 'kws', 'result'],
    (
        ({'key': '`[value]`'}, {'value': 1}, {'key': '[value]'}),
        ({'key': '[value]'}, {'value': 1}, {'key': 1}),
        ({'key': '[value:default]'}, {}, {'key': 'default'}),
        ({'key': '[value:"default"]'}, {}, {'key': 'default'}),
        ({'key': '[[value]]'}, {'value': 'key_2', 'key_2': 0}, {'key': 0}),
        ({'key': ['[value]', '[value]']}, {'value': 1}, {'key': (1, 1)}),
        ({'key': '[value.nested]'}, {'value': {'nested': 1}}, {'key': 1}),
        ({'key': '[value.nested:3]'}, {'value': [{'nested': 1}, {'nested': 2}, {}]}, {'key': [1, 2, 3]}),
        ({'key': '[!e:True]'}, {}, {'key': True}),
        ({'key': '[!e:[value]]'}, {'value': 'True'}, {'key': True}),
        ({'key': '[!f:{value}]'}, {'value': '123'}, {'key': '123'}),
        (
            {'key': '[!f:{obj-name} price is {obj-price}]'},
            {'obj': {'name': 'dog', 'price': 42}},
            {'key': 'dog price is 42'},
        ),
        ({'key': '[!f:{value_1}:{value_2}]'}, {'value_1': 1, 'value_2': 2}, {'key': '1,2'}),
        ({'key': '[!x:true]'}, {}, {'key': True}),
        ({'key': '[!x:sum:1:2:3]'}, {}, {'key': 6}),
        ({'key': '[!x:sum:1:[value]:3]'}, {'value': 2}, {'key': 6}),
    ),
    ids=[
        'escaping',
        'ref: simple',
        'ref: simple default',
        'ref: simple default (quoted)',
        'ref: nested ref',
        'ref: multiple',
        'ref: nested key',
        'ref: nested key list',
        'eval: simple',
        'eval: by ref',
        'format: simple',
        'format: nested',
        'format: join args',
        'exec: simple',
        'exec: with args',
        'exec: with ref args',
    ],
)
def test_templates(template, kws, result):
    assert Template(template).fill(kws) == result
