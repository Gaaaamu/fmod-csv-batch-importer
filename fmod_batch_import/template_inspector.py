"""Template event inspector for inheritance rules."""

from dataclasses import dataclass
from typing import cast

import json
import re

from fmod_batch_import.fmod_client import FMODClient
from fmod_batch_import.js_builder import js_inspect_template_event


@dataclass
class TemplateEventInfo:
    event_id: str = ""
    bus_id: str | None = None
    bus_path: str | None = None
    bank_id: str | None = None
    bank_name: str | None = None


def inspect_template_event(client: FMODClient, template_event_path: str) -> TemplateEventInfo:
    """Inspect the template event to extract bus/bank defaults."""
    response = client.execute(js_inspect_template_event(template_event_path))
    if response is None:
        return TemplateEventInfo()

    match = re.search(r'out\(\):\s*(\{.*\})', response, re.DOTALL)
    json_str = match.group(1).strip() if match else response.strip()
    try:
        data = cast(object, json.loads(json_str))
    except json.JSONDecodeError:
        return TemplateEventInfo()
    if not isinstance(data, dict):
        return TemplateEventInfo()

    data_dict = cast(dict[str, object], data)

    ok_value = data_dict.get("ok")
    if ok_value is not True:
        return TemplateEventInfo()

    event_raw = data_dict.get("event_id")
    event_id = event_raw if isinstance(event_raw, str) else ""
    info = TemplateEventInfo(event_id=event_id)

    bus_data = data_dict.get("bus")
    if isinstance(bus_data, dict):
        bus_dict = cast(dict[str, object], bus_data)
        bus_id_raw = bus_dict.get("id")
        bus_path_raw = bus_dict.get("path")
        bus_name_raw = bus_dict.get("name")
        bus_id = bus_id_raw if isinstance(bus_id_raw, str) else None
        bus_path = bus_path_raw if isinstance(bus_path_raw, str) else None
        if not bus_path:
            bus_path = bus_name_raw if isinstance(bus_name_raw, str) else None
        if bus_id:
            info.bus_id = bus_id
        if bus_path:
            info.bus_path = bus_path

    bank_data = data_dict.get("bank")
    if isinstance(bank_data, dict):
        bank_dict = cast(dict[str, object], bank_data)
        bank_id_raw = bank_dict.get("id")
        bank_path_raw = bank_dict.get("path")
        bank_name_raw = bank_dict.get("name")
        bank_id = bank_id_raw if isinstance(bank_id_raw, str) else None
        bank_name = bank_path_raw if isinstance(bank_path_raw, str) else None
        if not bank_name:
            bank_name = bank_name_raw if isinstance(bank_name_raw, str) else None
        if bank_id:
            info.bank_id = bank_id
        if bank_name:
            info.bank_name = bank_name

    return info
