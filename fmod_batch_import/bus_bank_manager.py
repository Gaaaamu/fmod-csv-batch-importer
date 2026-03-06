"""
DEPRECATED — Bus and Bank Manager module for FMOD Batch Import.

This module was used in the old per-row import architecture.
Bus and bank operations are now handled entirely inline inside
js_batch_process() in js_builder.py.

This file is no longer imported or called anywhere.
Do not add new code here. Retained for historical reference only.
"""

from fmod_batch_import.js_builder import _esc


def lookup_bus(bus_path: str) -> str:
    """
    Generate JavaScript to lookup a bus via studio.project.lookup.

    Args:
        bus_path: The bus path (e.g., 'bus:/SFX')

    Returns:
        JavaScript string returning JSON {ok, bus_id, error}
    """
    safe = _esc(bus_path)
    return (
        f"(function(){{"
        f"var bus=studio.project.lookup('{safe}');"
        f"if(!bus)return JSON.stringify({{ok:false,bus_id:null,error:'Bus not found: {safe}'}});"
        f"return JSON.stringify({{ok:true,bus_id:bus.id,error:null}});"
        f"}})();"
    )


def lookup_bank(bank_path: str) -> str:
    """
    Generate JavaScript to lookup a bank via studio.project.lookup.

    Args:
        bank_path: The bank path (e.g., 'bank:/Master Bank')

    Returns:
        JavaScript string returning JSON {ok, bank_id, error}
    """
    safe = _esc(bank_path)
    return (
        f"(function(){{"
        f"var bank=studio.project.lookup('{safe}');"
        f"if(!bank)return JSON.stringify({{ok:false,bank_id:null,error:'Bank not found: {safe}'}});"
        f"return JSON.stringify({{ok:true,bank_id:bank.id,error:null}});"
        f"}})();"
    )



