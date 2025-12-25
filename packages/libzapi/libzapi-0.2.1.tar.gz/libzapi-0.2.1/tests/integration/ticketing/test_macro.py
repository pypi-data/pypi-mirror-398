from libzapi import Ticketing


def test_list_and_get_macro(ticketing: Ticketing):
    macros = list(ticketing.macros.list())
    assert len(macros) > 0
    macro = ticketing.macros.get(macros[0].id)
    assert macro.raw_title == macros[0].raw_title
