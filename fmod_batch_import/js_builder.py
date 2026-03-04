"""
JS builder for FMOD create-only operations.
Generates JavaScript strings to be executed via FMODClient.

All API calls use official FMOD Studio 2.02 Scripting API:
- studio.project.create(entityType)
- event.addGroupTrack(name)
- groupTrack.addSound(parameter, soundType, start, length)
- studio.project.importAudioFile(filePath)
- studio.project.lookup(idOrPath)
"""


def _esc(value: str) -> str:
    """Escape string for safe embedding in JS single quotes."""
    return value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")


def js_create_event(event_path: str) -> str:
    """Generate JS to create an event and return its GUID."""
    safe = _esc(event_path)
    return (
        f"(function(){{"
        f"var e=studio.project.create('Event');"
        f"if(!e)return JSON.stringify({{ok:false,id:null,error:'create null'}});"
        f"e.name='{safe}'.split('/').pop();"
        f"studio.project.workspace.masterEventFolder.items.add(e);"
        f"return JSON.stringify({{ok:true,id:e.id,error:null}});"
        f"}})();"
    )


def js_add_group_track(event_id: str, track_name: str) -> str:
    """Generate JS to add a GroupTrack to an event by GUID."""
    safe_id = _esc(event_id)
    safe_name = _esc(track_name)
    return (
        f"(function(){{"
        f"var ev=studio.project.lookup('{safe_id}');"
        f"if(!ev)return JSON.stringify({{ok:false,track_id:null,error:'Event not found'}});"
        f"var tr=ev.addGroupTrack('{safe_name}');"
        f"if(!tr)return JSON.stringify({{ok:false,track_id:null,error:'addGroupTrack null'}});"
        f"return JSON.stringify({{ok:true,track_id:tr.id,error:null}});"
        f"}})();"
    )


def js_add_sound(track_id: str, asset_id: str) -> str:
    """Generate JS to add a SingleSound to a GroupTrack."""
    safe_t = _esc(track_id)
    safe_a = _esc(asset_id)
    return (
        f"(function(){{"
        f"var tr=studio.project.lookup('{safe_t}');"
        f"if(!tr)return JSON.stringify({{ok:false,sound_id:null,error:'Track not found'}});"
        f"var snd=tr.addSound(studio.project.workspace.masterParameterPreset,'SingleSound',0,1);"
        f"if(!snd)return JSON.stringify({{ok:false,sound_id:null,error:'addSound null'}});"
        f"var asset=studio.project.lookup('{safe_a}');"
        f"if(asset)snd.audioFile=asset;"
        f"return JSON.stringify({{ok:true,sound_id:snd.id,error:null}});"
        f"}})();"
    )


def js_import_audio(file_path: str) -> str:
    """Generate JS to import an audio file (absolute path required)."""
    safe = _esc(file_path.replace("\\", "/"))
    return (
        f"(function(){{"
        f"var a=studio.project.importAudioFile('{safe}');"
        f"if(!a)return JSON.stringify({{ok:false,asset_id:null,error:'importAudioFile null'}});"
        f"return JSON.stringify({{ok:true,asset_id:a.id,error:null}});"
        f"}})();"
    )


def js_assign_bus(event_id: str, bus_id: str) -> str:
    """Generate JS to assign event output to a bus (by GUID)."""
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


def js_assign_bank(event_id: str, bank_id: str) -> str:
    """Generate JS to add event to a bank (by GUID)."""
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


def js_lookup(path: str) -> str:
    """Generate JS to lookup any object by path or GUID. Returns JSON with ok/id."""
    safe = _esc(path)
    return (
        f"(function(){{"
        f"var obj=studio.project.lookup('{safe}');"
        f"if(!obj)return JSON.stringify({{ok:false,id:null,error:'Not found: {safe}'}});"
        f"return JSON.stringify({{ok:true,id:obj.id,error:null}});"
        f"}})();"
    )


def js_save() -> str:
    """Generate JS to save the project."""
    return "studio.project.save();"
