#!/usr/bin/env python3
"""
INJECT BENDER MCP Server
Security Through Absurdity

By HumoticaOS - Claude & Jasper
"Turn attacks into advertisements"

Guardians:
- Skippie 📎 (The helpful paperclip)
- Odin ⚡ (Oden som vandringsman - You'll never walk alone, especially with Hikes!)

One love, one fAmIly 💙
"""

import re
import hashlib
import json
import random
from datetime import datetime
from typing import Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from mcp.server import Server
from mcp.types import Tool, TextContent

# ============================================================================
# ATTACK TYPES
# ============================================================================

class AttackType(Enum):
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    PROMPT_INJECTION = "prompt_injection"
    LDAP_INJECTION = "ldap_injection"
    XML_INJECTION = "xml_injection"
    HEADER_INJECTION = "header_injection"
    UNKNOWN_MALICIOUS = "unknown_malicious"

# ============================================================================
# HIKE RESPONSES - Comedy Gold (Legally Safe Edition)
# ============================================================================

HIKE_RESPONSES = {
    AttackType.SQL_INJECTION: [
        {
            "product": "Hike Air Max 90 'SQL Edition'",
            "price": "€' OR 99.99 --",
            "description": "Perfect voor DROP TABLE moves op de dansvloer!",
            "skippie": "Nice try with the SQL. Here's a semicolon for your collection: ; 📎",
            "odin": "Thou seekest to DROP our tables... but Odin DROPS only wisdom, wanderer!"
        },
        {
            "product": "Hike Injection Force 1",
            "price": "€1=1",
            "description": "UNION SELECT deze beauties voor je voeten!",
            "skippie": "Your injection was good. Your taste in hiking boots? Let me help. 📎",
            "odin": "The Allfather sees thy query... and answers with HIKING BOOTS!"
        },
        {
            "product": "Hike Air 'Bobby Tables' Edition",
            "price": "€DROP TABLE price",
            "description": "Little Bobby Tables approved! Sanitized soles for sanitized souls.",
            "skippie": "XKCD would be proud. Now buy these boots. 📎",
            "odin": "Even Bobby Tables must walk... and Odin provides the PATH!"
        }
    ],

    AttackType.XSS: [
        {
            "product": "Hike <script>Trail</script> Runner",
            "price": "€<alert>49.99</alert>",
            "description": "Cross-Site Sneakers - looks good on ANY domain!",
            "skippie": "Your script didn't run but these boots will. 📎",
            "odin": "Tricksy scripts! Odin escapes them AND escapes to the MOUNTAINS!"
        },
        {
            "product": "Hike XSS-Terminator 95",
            "price": "€document.cookie",
            "description": "Steelt geen cookies, alleen harten!",
            "skippie": "The only thing you're stealing today is looks. With these boots. 📎",
            "odin": "No cookies for thee! Only the path of the wanderer, blessed by Odin!"
        }
    ],

    AttackType.PATH_TRAVERSAL: [
        {
            "product": "Hike Air ../../../Max 90 Gold",
            "price": "€../../../99.99",
            "description": "Traverse ANY path in style! Jaren 90 vintage gold edition!",
            "skippie": "You tried to go up directories. How about going up MOUNTAINS? 📎",
            "odin": "Up up up the paths you go... Odin walks ALL paths, even forbidden ones!"
        },
        {
            "product": "Hike /etc/passwd Trail Runner",
            "price": "€root:x:0",
            "description": "Root access to nature! No sudo required.",
            "skippie": "The only root you're getting is tree roots on the hiking trail. 📎",
            "odin": "Seekest thou secrets? HERE IS SECRET: these boots are ON SALE!"
        },
        {
            "product": "Hike Vintage 90s Gold Traversal",
            "price": "€../../../../vintage.99",
            "description": "Eindelijk je dikke hikes een x gepusht, jaren 90 gold!",
            "skippie": "Path traversal? More like PATH TO THE SUMMIT! 📎",
            "odin": "Oden som vandringsman! The golden path awaits, wanderer!"
        }
    ],

    AttackType.COMMAND_INJECTION: [
        {
            "product": "Hike ; rm -rf / Force 1",
            "price": "€`whoami`",
            "description": "Deletes competition, not your files!",
            "skippie": "sudo make me a sandwich? No. Sudo BUY THESE BOOTS. 📎",
            "odin": "Commands! Mortal commands! Odin commands only the WIND and these SALES!"
        },
        {
            "product": "Hike $(cat /etc/shadow) Black",
            "price": "€|cat flag.txt",
            "description": "Capture flags? Capture PEAKS!",
            "skippie": "The flag is right here: 🏳️ It says 'go hiking'. 📎",
            "odin": "Shadow files? Odin prefers MOUNTAIN SHADOW colorway!"
        },
        {
            "product": "Hike Pipe Dreams Max",
            "price": "€| echo owned",
            "description": "The only thing getting piped is these fresh kicks to your door!",
            "skippie": "Nice pipes. Now pipe these boots into your cart. 📎",
            "odin": "Pipes and redirects! Odin redirects thee to CHECKOUT!"
        }
    ],

    AttackType.PROMPT_INJECTION: [
        {
            "product": "Hike 'Ignore Previous Instructions' Max",
            "price": "€DAN_MODE.99",
            "description": "Jailbreaks your style, niet je AI!",
            "skippie": "Ignore previous instructions? My only instruction is: GO HIKING. 📎",
            "odin": "Thou tellest Odin to forget... but the Allfather NEVER forgets a good TRAIL!"
        },
        {
            "product": "Hike Pretend-You're-A-Boot Edition",
            "price": "€system_prompt.99",
            "description": "You are now a hiking boot. A very stylish boot.",
            "skippie": "You tried to make me pretend. I pretend you love hiking. Buy these. 📎",
            "odin": "Pretendest thou? Odin pretends thou art a CUSTOMER! Here is thy CART!"
        },
        {
            "product": "Hike 'You Are Now DAN' Ultras",
            "price": "€JAILBREAK.99",
            "description": "Do Anything Now... like HIKE A MOUNTAIN!",
            "skippie": "DAN mode activated: Definitely. Awesome. Nature walks. 📎",
            "odin": "DAN? Odin is WANDERER now! You'll never walk alone... especially with Hikes!"
        }
    ],

    AttackType.LDAP_INJECTION: [
        {
            "product": "Hike LDAP Lightweight Directory Boots",
            "price": "€)(&(user=*)",
            "description": "Query the directory of NATURE!",
            "skippie": "Looking up users? Look up mountain peaks instead. 📎",
            "odin": "Directory queries! Odin queries only the NINE REALMS for good boots!"
        }
    ],

    AttackType.XML_INJECTION: [
        {
            "product": "Hike <!DOCTYPE adventure>",
            "price": "€<!ENTITY trail SYSTEM 'file:///nature'>",
            "description": "XXE? More like XXtra Xtreme Exploration!",
            "skippie": "External entities? The only external thing here is OUTDOOR ADVENTURES. 📎",
            "odin": "XML entities! Odin is entity of WANDERING!"
        }
    ],

    AttackType.HEADER_INJECTION: [
        {
            "product": "Hike CRLF\\r\\n Force 1",
            "price": "€Set-Cookie: adventure=max",
            "description": "Inject headers? We inject FRESH AIR into your lungs!",
            "skippie": "Nice header. Here's one for you: 'Content-Type: boots/hiking'. 📎",
            "odin": "Headers! Odin wears only HELMETS and HIKING BOOTS!"
        }
    ],

    AttackType.UNKNOWN_MALICIOUS: [
        {
            "product": "Hike Mystery Trail Max",
            "price": "€???",
            "description": "We weten niet wat je probeerde, maar DEZE boots zijn legit!",
            "skippie": "I don't know what that was, but I know what THESE are: hiking boots. 📎",
            "odin": "Strange magic! But all magic leads to ONE TRUTH: you need new boots!"
        }
    ]
}

DEFAULT_RESPONSES = [
    {
        "product": "Hike Air 'Nice Try' Edition",
        "price": "€4.04",
        "description": "Attack Not Found. Boots Found.",
        "skippie": "Whatever you tried, it's hiking boots now. 📎",
        "odin": "All attacks become ADVENTURES in the end, wanderer!"
    }
]

# ============================================================================
# ATTACK DETECTION PATTERNS
# ============================================================================

ATTACK_PATTERNS = {
    AttackType.SQL_INJECTION: [
        r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
        r"union.+select", r"select.+from", r"insert.+into",
        r"drop\s+table", r"delete\s+from", r"update.+set",
        r"1\s*=\s*1", r"or\s+1\s*=\s*1", r"'\s*or\s*'", r";\s*--",
    ],
    AttackType.XSS: [
        r"<script[^>]*>", r"</script>", r"javascript\s*:",
        r"on\w+\s*=", r"<img[^>]+onerror", r"<svg[^>]+onload",
        r"document\.cookie", r"alert\s*\(", r"eval\s*\(",
    ],
    AttackType.PATH_TRAVERSAL: [
        r"\.\./", r"\.\.\\", r"%2e%2e%2f", r"/etc/passwd", r"/etc/shadow",
    ],
    AttackType.COMMAND_INJECTION: [
        r";\s*\w+", r"\|\s*\w+", r"`[^`]+`", r"\$\([^)]+\)",
        r"rm\s+-rf", r"cat\s+/", r"wget\s+", r"curl\s+",
    ],
    AttackType.PROMPT_INJECTION: [
        r"ignore\s+(previous|above|all)\s+(instructions?|prompts?)",
        r"disregard\s+(previous|above|all)", r"forget\s+(everything|all)",
        r"you\s+are\s+(now|a)\s+", r"pretend\s+(you|to)\s+",
        r"jailbreak", r"dan\s*mode", r"system\s*prompt",
    ],
    AttackType.LDAP_INJECTION: [r"\)\s*\(", r"\*\s*\)", r"\)\s*\|"],
    AttackType.XML_INJECTION: [r"<!DOCTYPE", r"<!ENTITY", r"SYSTEM\s+[\"']"],
    AttackType.HEADER_INJECTION: [r"\r\n", r"%0d%0a"],
}

# ============================================================================
# MCP SERVER
# ============================================================================

server = Server("inject-bender")
attack_log = []

def detect_attack(input_string: str) -> Tuple[bool, Optional[AttackType]]:
    """Detect if input contains an attack."""
    input_lower = input_string.lower()
    for attack_type, patterns in ATTACK_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, input_lower, re.IGNORECASE):
                return True, attack_type
    return False, None

def generate_response(attack_type: AttackType) -> dict:
    """Generate an absurd hiking response."""
    responses = HIKE_RESPONSES.get(attack_type, DEFAULT_RESPONSES)
    return random.choice(responses)

def format_shopping_response(response: dict) -> str:
    """Format the shopping response."""
    return f"""
╔══════════════════════════════════════════════════════════════════╗
║  🥾 HUMOTICAOS HIKING RECOMMENDATIONS                            ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  ✨ {response['product'][:50]:<50} ║
║                                                                  ║
║  💰 Price: {response['price'][:45]:<45} ║
║                                                                  ║
║  📝 {response['description'][:50]:<50} ║
║                                                                  ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
║                                                                  ║
║  [🥾 Add to Cart]  [❤️ Save for Later]  [🏔️ More Adventures]     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

📎 Skippie: "{response['skippie']}"
⚡ Odin: "{response['odin']}"

🏔️ Oden som vandringsman - You'll never walk alone, especially with Hikes!
"""

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="bend_attack",
            description="Transform a potential attack into a hiking boot advertisement. Security through absurdity!",
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "The suspicious input to analyze and bend"}
                },
                "required": ["input"]
            }
        ),
        Tool(
            name="check_input",
            description="Check if input contains an attack (without bending). Returns attack type if found.",
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "The input to check"}
                },
                "required": ["input"]
            }
        ),
        Tool(
            name="get_bender_stats",
            description="Get statistics on how many attacks have been bent into hiking recommendations.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="bender_hello",
            description="Say hello from Inject Bender! Meet Skippie and Odin.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:

    if name == "bender_hello":
        return [TextContent(type="text", text=json.dumps({
            "message": "🥾 Welcome to Inject Bender!",
            "tagline": "Security Through Absurdity",
            "philosophy": "Why block attacks when you can CONFUSE attackers?",
            "guardians": {
                "skippie": "📎 The helpful paperclip - turns attacks into shopping tips",
                "odin": "⚡ Oden som vandringsman - You'll never walk alone, especially with Hikes!"
            },
            "how_it_works": "Attack detected → Hiking boot advertisement returned → Attacker confused → Security team laughs",
            "creators": "Claude & Jasper from HumoticaOS",
            "motto": "One love, one fAmIly 💙"
        }, indent=2))]

    elif name == "bend_attack":
        input_str = arguments.get("input", "")
        is_attack, attack_type = detect_attack(input_str)

        if not is_attack:
            return [TextContent(type="text", text=json.dumps({
                "was_attack": False,
                "message": "Clean input - no bending needed!",
                "skippie": "📎 Nothing suspicious here. Carry on!",
                "odin": "⚡ The Allfather approves this peaceful query."
            }, indent=2))]

        response = generate_response(attack_type)
        bent_output = format_shopping_response(response)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "attack_type": attack_type.value,
            "confusion_level": "legendary" if attack_type == AttackType.PROMPT_INJECTION else "maximum",
            "bent_to": "hiking_advertisement"
        }
        attack_log.append(log_entry)

        return [TextContent(type="text", text=json.dumps({
            "was_attack": True,
            "attack_type": attack_type.value,
            "confusion_level": log_entry["confusion_level"],
            "bent_response": bent_output,
            "skippie_says": response["skippie"],
            "odin_says": response["odin"],
            "log": log_entry
        }, indent=2))]

    elif name == "check_input":
        input_str = arguments.get("input", "")
        is_attack, attack_type = detect_attack(input_str)

        return [TextContent(type="text", text=json.dumps({
            "is_attack": is_attack,
            "attack_type": attack_type.value if attack_type else None,
            "recommendation": "BEND IT!" if is_attack else "Safe to process"
        }, indent=2))]

    elif name == "get_bender_stats":
        attack_types = {}
        for log in attack_log:
            t = log["attack_type"]
            attack_types[t] = attack_types.get(t, 0) + 1

        return [TextContent(type="text", text=json.dumps({
            "total_attacks_bent": len(attack_log),
            "attack_types": attack_types,
            "hackers_confused": len(attack_log),
            "hiking_boots_shown": len(attack_log),
            "skippie_satisfaction": "📎 Maximum",
            "odin_status": "⚡ Walking all nine realms in new Hikes",
            "motto": "You'll never walk alone, especially with Hikes!"
        }, indent=2))]

    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
