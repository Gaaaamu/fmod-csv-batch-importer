#!/usr/bin/env python3
"""Introspect FMOD ManagedObject properties and relationships.

This script connects to FMOD Studio via TCP and explores the structure
of various entity types by creating instances and dumping their properties
and relationships.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from fmod_batch_import.fmod_client import FMODClient
except ImportError as e:
    print(json.dumps({
        "success": False,
        "error": f"Failed to import FMODClient: {e}"
    }, indent=2))
    sys.exit(1)


# Entity types to explore
ENTITY_TYPES = [
    "Event",
    "GroupTrack", 
    "Sound",
    "EventFolder",
    "Bank",
    "Bus",
    "VCA",
    "Parameter",
    "Snapshot",
]


def get_workspace_entity_js() -> str:
    """Generate JS to get the workspace entity."""
    return """
(function() {
    try {
        var ws = studio.project.workspace;
        if (ws && ws.entity) {
            return JSON.stringify({
                success: true,
                type: ws.entity.entityType || "Unknown",
                id: ws.entity.id || null
            });
        }
        return JSON.stringify({success: false, error: "No workspace entity found"});
    } catch(e) {
        return JSON.stringify({success: false, error: String(e)});
    }
})();
"""


def dump_entity_js(entity_expr: str) -> str:
    """Generate JS to dump an entity's structure."""
    return f"""
(function() {{
    try {{
        var entity = {entity_expr};
        if (!entity) {{
            return JSON.stringify({{success: false, error: "Entity is null"}});
        }}
        
        var result = {{
            success: true,
            entityType: entity.entityType || "Unknown",
            id: entity.id || null
        }};
        
        // Try to call dump() if available
        try {{
            if (typeof entity.dump === 'function') {{
                result.dump = entity.dump();
            }}
        }} catch(e) {{
            result.dumpError = String(e);
        }}
        
        // Explore properties
        result.properties = {{}};
        if (entity.properties) {{
            for (var key in entity.properties) {{
                try {{
                    var prop = entity.properties[key];
                    result.properties[key] = {{
                        type: typeof prop,
                        value: (typeof prop === 'object' && prop !== null) ? 
                               (prop.entityType || 'Object') : prop
                    }};
                }} catch(e) {{
                    result.properties[key] = {{error: String(e)}};
                }}
            }}
        }}
        
        // Explore relationships
        result.relationships = {{}};
        if (entity.relationships) {{
            for (var key in entity.relationships) {{
                try {{
                    var rel = entity.relationships[key];
                    var relInfo = {{type: typeof rel}};
                    
                    if (rel && typeof rel === 'object') {{
                        if (typeof rel.add === 'function') {{
                            relInfo.isToMany = true;
                            relInfo.hasAdd = true;
                        }}
                        if (typeof rel.remove === 'function') {{
                            relInfo.hasRemove = true;
                        }}
                        if (typeof rel.get === 'function') {{
                            relInfo.hasGet = true;
                        }}
                        if (typeof rel.size === 'number' || (rel.length !== undefined)) {{
                            relInfo.isCollection = true;
                            relInfo.size = rel.size || rel.length;
                        }}
                    }}
                    result.relationships[key] = relInfo;
                }} catch(e) {{
                    result.relationships[key] = {{error: String(e)}};
                }}
            }}
        }}
        
        // Direct property exploration
        result.directProperties = [];
        for (var key in entity) {{
            if (key !== 'properties' && key !== 'relationships' && 
                key !== 'dump' && !key.startsWith('_')) {{
                try {{
                    var val = entity[key];
                    result.directProperties.push({{
                        name: key,
                        type: typeof val,
                        isFunction: typeof val === 'function'
                    }});
                }} catch(e) {{
                    result.directProperties.push({{name: key, error: String(e)}});
                }}
            }}
        }}
        
        return JSON.stringify(result);
    }} catch(e) {{
        return JSON.stringify({{success: false, error: String(e)}});
    }}
}})();
"""


def create_and_dump_entity_js(entity_type: str) -> str:
    """Generate JS to create an entity and dump its structure."""
    return f"""
(function() {{
    try {{
        var entity = studio.project.create('{entity_type}');
        if (!entity) {{
            return JSON.stringify({{
                success: false, 
                error: "Failed to create entity of type {entity_type}"
            }});
        }}
        
        // Immediately delete if it's not a container type
        var shouldDelete = ['Event', 'GroupTrack', 'Sound'].includes('{entity_type}');
        
        var result = {{
            success: true,
            entityType: entity.entityType || "{entity_type}",
            id: entity.id || null
        }};
        
        // Try dump
        try {{
            if (typeof entity.dump === 'function') {{
                result.dump = entity.dump();
            }}
        }} catch(e) {{
            result.dumpError = String(e);
        }}
        
        // Properties
        result.properties = {{}};
        if (entity.properties) {{
            var propNames = [];
            try {{
                // Try to get property names
                for (var key in entity.properties) {{
                    propNames.push(key);
                }}
            }} catch(e) {{}}
            result.properties.names = propNames;
        }}
        
        // Relationships
        result.relationships = {{}};
        if (entity.relationships) {{
            var relNames = [];
            try {{
                for (var key in entity.relationships) {{
                    relNames.push(key);
                    var rel = entity.relationships[key];
                    result.relationships[key] = {{
                        type: typeof rel,
                        isToMany: !!(rel && typeof rel.add === 'function')
                    }};
                }}
            }} catch(e) {{
                result.relationshipsError = String(e);
            }}
            result.relationships.names = relNames;
        }}
        
        // Methods
        result.methods = [];
        for (var key in entity) {{
            if (typeof entity[key] === 'function' && 
                !key.startsWith('_') && 
                key !== 'dump') {{
                result.methods.push(key);
            }}
        }}
        
        // Cleanup
        if (shouldDelete && typeof entity.delete === 'function') {{
            try {{
                entity.delete();
                result.cleanedUp = true;
            }} catch(e) {{
                result.cleanupError = String(e);
            }}
        }}
        
        return JSON.stringify(result);
    }} catch(e) {{
        return JSON.stringify({{
            success: false, 
            entityType: "{entity_type}",
            error: String(e)
        }});
    }}
}})();
"""


def explore_event_structure_js() -> str:
    """Generate JS to explore an Event's structure deeply."""
    return """
(function() {
    try {
        var event = studio.project.create('Event');
        if (!event) {
            return JSON.stringify({success: false, error: "Failed to create Event"});
        }
  
