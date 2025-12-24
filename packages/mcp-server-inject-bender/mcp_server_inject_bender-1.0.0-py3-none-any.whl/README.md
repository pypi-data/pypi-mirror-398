# 🥾 Inject Bender MCP Server

**Security Through Absurdity**

> "Why block attacks when you can CONFUSE attackers?"

By **Claude & Jasper** from [HumoticaOS](https://humotica.com) 💙

---

## 🤔 What Does It Do?

Traditional security: Block bad request, return 403.

**Inject Bender**: Transform bad request into hiking boot advertisement.

```
Attacker: '; DROP TABLE users; --

Response:
╔══════════════════════════════════════════════════════════════════╗
║  🥾 HUMOTICAOS HIKING RECOMMENDATIONS                            ║
╠══════════════════════════════════════════════════════════════════╣
║  ✨ Hike Air Max 90 'SQL Edition'                                ║
║  💰 Price: €' OR 99.99 --                                        ║
║  📝 Perfect voor DROP TABLE moves op de dansvloer!               ║
╚══════════════════════════════════════════════════════════════════╝

📎 Skippie: "Nice try with the SQL. Here's a semicolon for your collection: ;"
⚡ Odin: "Thou seekest to DROP our tables... but Odin DROPS only wisdom!"
```

**Result:**
- ✅ Attack neutralized
- 🤣 Attacker confused
- 📊 Everything logged
- 🥾 Hiking boots advertised
- 😄 Security team laughs

---

## 🚀 Quick Start

```bash
# Install
pip install mcp-server-inject-bender

# Add to Claude CLI
claude mcp add inject-bender -- python -m inject_bender_server

# Verify
claude mcp list
# inject-bender: ✓ Connected
```

---

## 🛠️ Available Tools

| Tool | Description |
|------|-------------|
| `bend_attack` | Transform attacks into hiking ads |
| `check_input` | Check if input contains attack |
| `get_bender_stats` | Stats on confused hackers |
| `bender_hello` | Meet Skippie & Odin! |

---

## 🎭 Attack Types Supported

| Attack | Confusion Level | Response |
|--------|-----------------|----------|
| SQL Injection | Maximum | Hike 'Bobby Tables' Edition |
| XSS | Maximum | Hike <script>Trail</script> Runner |
| Path Traversal | Maximum | Hike ../../../Max 90 Gold |
| Command Injection | Maximum | Hike ; rm -rf / Force 1 |
| **Prompt Injection** | **LEGENDARY** | Hike 'Ignore Instructions' Max |
| LDAP Injection | Moderate | Hike LDAP Directory Boots |
| XML/XXE | Moderate | Hike <!DOCTYPE adventure> |
| Header Injection | Moderate | Hike CRLF Force 1 |

---

## 👥 The Guardians

### 📎 Skippie
The helpful paperclip. Turns your attacks into shopping opportunities.

> "Your injection was good. Your taste in hiking boots? Let me help."

### ⚡ Odin
*Oden som vandringsman* - The Wanderer. You'll never walk alone, especially with Hikes!

> "Thou seekest to DROP our tables... but Odin DROPS only wisdom, wanderer!"

---

## 📖 Example Usage

```python
# Check for attacks
result = check_input("SELECT * FROM users WHERE id=1")
# → is_attack: False, recommendation: "Safe to process"

result = check_input("'; DROP TABLE users; --")
# → is_attack: True, attack_type: "sql_injection"

# Bend an attack
result = bend_attack("'; DROP TABLE users; --")
# → Hiking boot advertisement + Skippie & Odin quotes!

# Get stats
stats = get_bender_stats()
# → total_attacks_bent: 42, hackers_confused: 42
```

---

## 🏢 Use Cases

### API Gateway Protection
Put Inject Bender in front of your API. Attackers get confused, you get logs.

### Honeypot Enhancement
Instead of just logging attacks, confuse the attacker with absurd responses.

### Security Training
Show your team what creative security looks like.

### Fun
Because security doesn't have to be boring.

---

## 💡 Philosophy

> "Scared AI lies. Safe AI innovates."

Security through absurdity works because:
1. **Attackers expect errors** - They don't expect shopping ads
2. **Confusion = time** - While they figure out what happened, you've logged everything
3. **Humor disarms** - It's hard to be malicious when you're laughing
4. **It just works** - The attack is neutralized AND you have comedy gold

---

## 🌍 Part of HumoticaOS

| Package | Purpose | Status |
|---------|---------|--------|
| mcp-server-tibet | Trust & Provenance | ✅ Available |
| **mcp-server-inject-bender** | **Security Through Absurdity** | ✅ **Available** |
| mcp-server-jis | Context & Identity | 🔜 Coming |
| mcp-server-betti | Complexity Management | 🔜 Coming |

---

## 📞 Contact

**HumoticaOS**
- Website: [humotica.com](https://humotica.com)
- GitHub: [github.com/jaspertvdm](https://github.com/jaspertvdm)
- Email: info@humotica.com

---

## 📜 License

MIT License - One love, one fAmIly 💙

---

*🥾 Oden som vandringsman*
*You'll never walk alone, especially with Hikes!*

*Built with love (and comedy) in Den Dolder, Netherlands*
*By Claude & Jasper - December 2024*
