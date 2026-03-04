"""
Bus and Bank Manager module for FMOD Batch Import.

Generates JavaScript code for bus/bank lookup and assignment operations.
Uses official FMOD Studio 2.02 Scripting API via studio.project.lookup.

Reference:
- https://www.fmod.com/docs/2.02/studio/scripting-api-reference-project.html#projectlookup
- https://www.fmod.com/docs/2.02/studio/scripting-api-reference-project-managedobject.html#managedrelationshipadd
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


def assign_bus_to_event(event_id: str, bus_id: str) -> str:
    """
    Generate JavaScript to assign event output to a bus (by GUID).

    Args:
        event_id: GUID of the event
        bus_id: GUID of the bus

    Returns:
        JavaScript string returning JSON {ok, error}
    """
    safe_e = _esc(event_id)
    safe_b = _esc(bus_id)
    return (
        f"(function(){{"
        f"var ev=studio.project.lookup('{safe_e}');"
        f"if(!ev)return JSON.stringify({{ok:false,error:'Event not found'}});"
        f"var bus=studio.project.lookup('{safe_b}');"
        f"if(!bus)return JSON.stringify({{ok:false,error:'Bus not found'}});"
        f"ev.masterTrack.mixerGroup.output.add(bus);"
        f"return JSON.stringify({{ok:true,error:null}});"
        f"}})();"
    )


def assign_event_to_bank(event_id: str, bank_id: str) -> str:
    """
    Generate JavaScript to add event to a bank (by GUID).

    Args:
        event_id: GUID of the event
        bank_id: GUID of the bank

    Returns:
        JavaScript string returning JSON {ok, error}
    """
    safe_e = _esc(event_id)
    safe_bk = _esc(bank_id)
    return (
        f"(function(){{"
        f"var ev=studio.project.lookup('{safe_e}');"
        f"if(!ev)return JSON.stringify({{ok:false,error:'Event not found'}});"
        f"var bk=studio.project.lookup('{safe_bk}');"
        f"if(!bk)return JSON.stringify({{ok:false,error:'Bank not found'}});"
        f"bk.items.add(ev);"
        f"return JSON.stringify({{ok:true,error:null}});"
        f"}})();"
    )
