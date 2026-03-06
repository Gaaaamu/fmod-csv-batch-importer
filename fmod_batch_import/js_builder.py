"""JS builder for FMOD scripting operations.

Active functions (used by orchestrator):
    js_batch_process()         — Single-call batch import for all rows
    js_save()                  — Save the FMOD project
    js_inspect_template_event()— Read bus/bank info from a template event

Deprecated functions (superseded by js_batch_process, not called anywhere):
    js_create_event, js_add_group_track, js_add_sound, js_import_audio,
    js_lookup, js_assign_bus, js_assign_bank, js_clear_and_copy_banks,
    js_ensure_folder_and_move
"""

import json as _json


def _esc(value: str) -> str:
    """Escape string for safe embedding in JS single quotes."""
    return value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")

def js_create_event(event_path: str) -> str:
    """DEPRECATED: superseded by js_batch_process(). Generate JS to create an event via workspace.addEvent and return its GUID."""
    safe = _esc(event_path)
    event_name = safe.split("/")[-1] if "/" in safe else safe
    return (
        f"(function(){{"
        f"var ev=studio.project.workspace.addEvent('{event_name}', false);"
        f"if(!ev)return JSON.stringify({{ok:false,error:'addEvent null'}});"
        f"return JSON.stringify({{ok:true,id:ev.id}});"
        f"}})();"
    )

def js_add_group_track(event_id: str, name: str) -> str:
    """DEPRECATED: superseded by js_batch_process(). Generate JS to add a GroupTrack to an event and return track GUID."""
    safe_e = _esc(event_id)
    safe_n = _esc(name)
    return (
        f"(function(){{"
        f"var ev=studio.project.lookup('{safe_e}');"
        f"if(!ev)return JSON.stringify({{ok:false,error:'Event not found'}});"
        f"var tr=ev.addGroupTrack('{safe_n}');"
        f"if(!tr)return JSON.stringify({{ok:false,error:'addGroupTrack null'}});"
        f"return JSON.stringify({{ok:true,track_id:tr.id}});"
        f"}})();"
    )

def js_add_sound(track_id: str, asset_id: str) -> str:
    """DEPRECATED: superseded by js_batch_process(). Generate JS to add a SingleSound to a track and link audioFile."""
    safe_t = _esc(track_id)
    safe_a = _esc(asset_id)
    return (
        f"(function(){{"
        f"var tr=studio.project.lookup('{safe_t}');"
        f"if(!tr)return JSON.stringify({{ok:false,error:'Track not found'}});"
        f"var asset=studio.project.lookup('{safe_a}');"
        f"var sndLen=(asset&&asset.length)?asset.length:tr.event.timeline.length;"
        f"var snd=tr.addSound(tr.event.timeline,'SingleSound',0,sndLen);"
        f"if(!snd)return JSON.stringify({{ok:false,error:'addSound null'}});"
        f"if(asset)snd.audioFile=asset;"
        f"return JSON.stringify({{ok:true,sound_id:snd.id}});"
        f"}})();"
    )

def js_import_audio(file_path: str, asset_relative_path: str | None = None) -> str:
    """DEPRECATED: superseded by js_batch_process(). Generate JS to import an audio file and optionally organize it in the Asset Browser.

    Args:
        file_path: Absolute filesystem path to the audio file.
        asset_relative_path: Relative path within the FMOD project's Assets folder,
            e.g. 'VO/Battle/hero.wav'. When provided, setAssetPath() is called after
            import to preserve the source directory structure. Verified via console.
    """
    safe = _esc(file_path.replace("\\", "/"))
    set_path_js = ""
    if asset_relative_path:
        safe_rel = _esc(asset_relative_path.replace("\\", "/"))
        set_path_js = f"a.setAssetPath('{safe_rel}');"
    return (
        f"(function(){{"
        f"var a=studio.project.importAudioFile('{safe}');"
        f"if(!a)return JSON.stringify({{ok:false,asset_id:null,error:'importAudioFile null'}});"
        f"{set_path_js}"
        f"return JSON.stringify({{ok:true,asset_id:a.id,error:null}});"
        f"}})();"
    )

def js_lookup(event_path: str) -> str:
    """DEPRECATED: superseded by js_batch_process(). Generate JS to lookup an event or entity by its path."""
    safe = _esc(event_path)
    return (
        f"(function(){{"
        f"var obj=studio.project.lookup('{safe}');"
        f"if(!obj)return JSON.stringify({{ok:false}});"
        f"return JSON.stringify({{ok:true,id:obj.id}});"
        f"}})();"
    )

def js_save() -> str:
    """Generate JS to save the project."""
    return "studio.project.save();"


def js_inspect_template_event(event_path: str) -> str:
    """Generate JS to inspect a template event for bus/bank details."""
    safe = _esc(event_path)
    return (
        f"(function(){{"
        f"var ev=studio.project.lookup('{safe}');"
        f"if(!ev)return JSON.stringify({{ok:false,error:'Template event not found'}});"
        f"var result={{ok:true,event_id:ev.id}};"
        # FIXED: Use ev.mixerInput.output for bus
        f"if(ev.mixerInput && ev.mixerInput.output){{"
        f"var out=ev.mixerInput.output;"
        f"result.bus={{id:out.id,name:out.name,path:(out.getPath?out.getPath():'')}};"
        f"}}"
        # FIXED: Use relationships.banks.destinations for bank
        f"if(ev.relationships && ev.relationships.banks && ev.relationships.banks.destinations){{"
        f"var bankDests=ev.relationships.banks.destinations;"
        f"var firstBank=null;"
        f"if(bankDests.length && bankDests.length>0){{firstBank=bankDests[0];}}"
        f"else if(bankDests.forEach){{bankDests.forEach(function(bk){{if(!firstBank)firstBank=bk;}});}}"
        f"if(firstBank){{"
        f"result.bank={{id:firstBank.id,name:firstBank.name,path:(firstBank.getPath?firstBank.getPath():'')}};"
        f"}}"
        f"}}"
        f"return JSON.stringify(result);"
        f"}})();"
    )


def js_assign_bus(event_id: str, bus_id: str) -> str:
    """DEPRECATED: superseded by js_batch_process(). Generate JS to assign event output to a bus (by GUID)."""
    safe_e = _esc(event_id)
    safe_b = _esc(bus_id)
    return (
        f"(function(){{"
        f"var ev=studio.project.lookup('{safe_e}');"
        f"if(!ev)return JSON.stringify({{ok:false,error:'Event not found'}});"
        f"var bus=studio.project.lookup('{safe_b}');"
        f"if(!bus)return JSON.stringify({{ok:false,error:'Bus not found'}});"
        f"ev.mixerInput.output = bus;"
        f"return JSON.stringify({{ok:true,error:null}});"
        f"}})();"
    )

def js_assign_bank(event_id: str, bank_id: str) -> str:
    """DEPRECATED: superseded by js_batch_process(). Generate JS to add event to a bank (by GUID)."""
    safe_e = _esc(event_id)
    safe_bk = _esc(bank_id)
    return (
        f"(function(){{"
        f"var ev=studio.project.lookup('{safe_e}');"
        f"if(!ev)return JSON.stringify({{ok:false,error:'Event not found'}});"
        f"var bank=studio.project.lookup('{safe_bk}');"
        f"if(!bank)return JSON.stringify({{ok:false,error:'Bank not found'}});"
        f"ev.relationships.banks.add(bank);"
        f"return JSON.stringify({{ok:true,error:null}});"
        f"}})();"
    )


def js_clear_and_copy_banks(event_id: str, template_event_id: str) -> str:
    """DEPRECATED: superseded by js_batch_process(). Generate JS to clear all banks on target and copy from template event."""
    safe_e = _esc(event_id)
    safe_t = _esc(template_event_id)
    return (
        f"(function(){{"
        f"var target=studio.project.lookup('{safe_e}');"
        f"if(!target)return JSON.stringify({{ok:false,error:'Event not found'}});"
        f"var template=studio.project.lookup('{safe_t}');"
        f"if(!template)return JSON.stringify({{ok:false,error:'Template event not found'}});"
        f"if(target.relationships && target.relationships.banks && target.relationships.banks.destinations){{"
        f"var toRemove=[];"
        f"target.relationships.banks.destinations.forEach(function(b){{toRemove.push(b);}});"
        f"toRemove.forEach(function(b){{target.relationships.banks.remove(b);}});"
        f"}}"
        f"if(template.relationships && template.relationships.banks && template.relationships.banks.destinations){{"
        f"template.relationships.banks.destinations.forEach(function(b){{target.relationships.banks.add(b);}});"
        f"}}"
        f"return JSON.stringify({{ok:true,error:null}});"
        f"}})();"
    )


def js_batch_process(
    rows_data: list[dict],
    template_event_id: str | None = None,
) -> str:
    """Generate a single JS function that processes ALL rows in one TCP call.

    Each dict in rows_data must contain:
        row_index       (int)   CSV row number
        audio_abs_path  (str)   Absolute path to audio file, forward slashes
        asset_rel_path  (str|None) Relative path under Assets/ for setAssetPath
        event_path      (str)   Normalized FMOD event path, e.g. "event:/VO/hero"
        audio_name      (str)   Original audio filename (for display in results)
        bus_path        (str)   Normalized bus path, e.g. "bus:/SFX", or ""
        bank_name       (str)   Normalized bank path, e.g. "bank:/Master", or ""
        use_template_banks (bool) If True, copy banks from template_event_id instead
        folder_path     (str|None) Event folder to move into, e.g. "event:/VO"

    Returns JSON: {ok: true, results: [{row_index, status, event_path,
                                         audio_name, message, warnings}, ...]}
    """
    rows_json = _json.dumps(rows_data)
    tmpl_js = f"'{_esc(template_event_id)}'" if template_event_id else "null"

    return (
        "(function(){"
        f"var rows={rows_json};"
        f"var templateEventId={tmpl_js};"
        "var results=[];"
        "for(var i=0;i<rows.length;i++){"
        "var row=rows[i];"
        "var result={row_index:row.row_index,status:'fail',event_path:row.event_path,"
        "audio_name:row.audio_name,message:'',warnings:[]};"
        "try{"

        # Step 1: Duplicate check
        "var existing=studio.project.lookup(row.event_path);"
        "if(existing){"
        "result.status='skip';"
        "result.message='Event already exists: '+row.event_path;"
        "results.push(result);continue;"
        "}"

        # Step 2: Import audio + optional setAssetPath
        "var asset=studio.project.importAudioFile(row.audio_abs_path);"
        "if(!asset){result.message='importAudioFile null';results.push(result);continue;}"
        "if(row.asset_rel_path){asset.setAssetPath(row.asset_rel_path);}"

        # Step 3: Create event (name = last path segment)
        "var eventName=row.event_path.split('/').pop();"
        "var ev=studio.project.workspace.addEvent(eventName,false);"
        "if(!ev){result.message='addEvent null';results.push(result);continue;}"

        # Step 4: Add group track
        "var tr=ev.addGroupTrack('Audio');"
        "if(!tr){result.message='addGroupTrack null';results.push(result);continue;}"

        # Step 5: Add sound + link asset
        "var sndLen=(asset&&asset.length)?asset.length:ev.timeline.length;"
        "var snd=tr.addSound(ev.timeline,'SingleSound',0,sndLen);"
        "if(!snd){result.message='addSound null';results.push(result);continue;}"
        "snd.audioFile=asset;"

        # Step 6: Bus assignment (warn-and-continue on not found)
        "if(row.bus_path){"
        "var bus=studio.project.lookup(row.bus_path);"
        "if(!bus){result.warnings.push('Bus not found: '+row.bus_path);}"
        "else{ev.mixerInput.output=bus;}"
        "}"

        # Step 7: Bank assignment
        # use_template_banks=true → copy all banks from template event
        # bank_name non-empty  → assign that specific bank
        # both empty           → no bank assignment
        "if(row.use_template_banks&&templateEventId){"
        "var tmpl=studio.project.lookup(templateEventId);"
        "if(tmpl&&tmpl.relationships&&tmpl.relationships.banks&&tmpl.relationships.banks.destinations){"
        "tmpl.relationships.banks.destinations.forEach(function(b){ev.relationships.banks.add(b);});"
        "}"
        "}else if(row.bank_name){"
        "var bank=studio.project.lookup(row.bank_name);"
        "if(!bank){result.warnings.push('Bank not found: '+row.bank_name);}"
        "else{ev.relationships.banks.add(bank);}"
        "}"

        # Step 8: Move event to folder, auto-creating missing folders
        "if(row.folder_path){"
        "var parts=row.folder_path.replace(/^event:\\/\\//,'').replace(/^event:\\//,'').split('/');"
        "var createdFolders=[];"
        "var cur=studio.project.workspace.masterEventFolder;"
        "for(var j=0;j<parts.length;j++){"
        "var seg=parts[j];if(!seg)continue;"
        "var segPath='event:/'+parts.slice(0,j+1).join('/');"
        "var child=studio.project.lookup(segPath);"
        "if(!child){"
        "child=studio.project.create('EventFolder');"
        "child.name=seg;"
        "cur.relationships.items.add(child);"
        "createdFolders.push(segPath);"
        "}"
        "cur=child;"
        "}"
        "cur.relationships.items.add(ev);"
        "if(createdFolders.length>0){"
        "result.warnings.push('Created folders: '+createdFolders.join(', '));"
        "}"
        "}"

        "result.status='success';result.message='OK';"
        "}catch(e){"
        "result.status='fail';"
        "result.message='Exception: '+(e.message||String(e));"
        "}"
        "results.push(result);"
        "}"
        "return JSON.stringify({ok:true,results:results});"
        "})();"
    )


def js_ensure_folder_and_move(event_id: str, folder_path: str) -> str:
    """DEPRECATED: superseded by js_batch_process() (folder creation is now inline). Generate JS to move an event to a folder, creating any missing parent folders.

    folder_path should be the event folder path, e.g. 'event:/VO/Narration/Battle'.
    Missing folders are created via studio.project.create('EventFolder') and chained
    in-memory before a single save — verified to work for multi-level nesting.
    Returns {ok, created: [...newly created folder paths]}.
    """
    safe_e = _esc(event_id)
    safe_f = _esc(folder_path)
    return (
        f"(function(){{"
        f"var ev=studio.project.lookup('{safe_e}');"
        f"if(!ev)return JSON.stringify({{ok:false,error:'Event not found'}});"
        f"var parts='{safe_f}'.replace(/^event:\\/\\//,'').replace(/^event:\\//,'').split('/');"
        f"var created=[];"
        f"var current=studio.project.workspace.masterEventFolder;"
        f"for(var i=0;i<parts.length;i++){{"
        f"var seg=parts[i];"
        f"if(!seg)continue;"
        f"var segPath='event:/'+parts.slice(0,i+1).join('/');"
        f"var child=studio.project.lookup(segPath);"
        f"if(!child){{"
        f"child=studio.project.create('EventFolder');"
        f"child.name=seg;"
        f"current.relationships.items.add(child);"
        f"created.push(segPath);"
        f"}}"
        f"current=child;"
        f"}}"
        f"current.relationships.items.add(ev);"
        f"return JSON.stringify({{ok:true,created:created}});"
        f"}})();"
    )
