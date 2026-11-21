# mod-temucraft-crazy

World data salvaged from the Crazy repack (an old TrinityCore 3.3.5 server with Cataclysm and Mists content) that
no other Temucraft module has yet. SQL only.

## What is in it

`data/sql/db-world/base/mod_temucraft_crazy_world.sql` (made by `tools/crazy_convert.py`):

| Map | Creatures | What they are |
|---|---|---|
| 726 Twin Peaks | 70 | Wildhammer guards and gryphons (Alliance side), Dragonmaw workers (Horde side), boars, one trigger |
| 730 Maelstrom Zone | 51 | Thrall, Aggra, Farseer Nobundo, Muln Earthfury, a wyvern and the effect bunnies of the Maelstrom |

- 15 creature templates (Cataclysm creatures the core does not have), with their models, movement and addon rows.
  Levels above 80 are set to 80. They have no loot, gossip, quests or scripts (the repack had none for them either).
- 4 Twin Peaks workers and guards walk their waypoint paths (the repack gave them paths but left them standing).
- `creature_model_info` for the 11 Cataclysm displays they use, and the same display and model rows patch-T has
  (`creaturedisplayinfo_dbc`, `creaturemodeldata_dbc`), so the server can load them even if its `Data/dbc` files
  lack them. All three use INSERT IGNORE.
- `.tele TheMaelstrom` for staff.

How the rows were fitted to this core:
- Factions the 3.3.5 FactionTemplate.dbc does not have (patch-T does not change it) use the closest 3.3.5 one:
  Wildhammer 2339 and 2362 -> 1732 (Alliance), Dragonmaw 2305 -> 1735 (Horde), 2329 -> 60, Aggra 2256 and Thrall
  2167 -> 35 (friendly).
- Cataclysm type flags are dropped (their bits mean other things in 3.3.5), npc flags are cleared (no gossip, quest,
  vendor or taxi rows came with them), and the wyvern's SmartAI (cast 84515 on a gossip option of a menu that never
  existed) is left out.

Twin Peaks is a battleground map. The core only lets players in through a real battleground, and it has no Twin
Peaks battleground, so these spawns wait for that (core work). The Maelstrom is a normal map and can be visited.

## Ids

| What | Range |
|---|---|
| `creature` GUIDs (and `creature_addon`) | 7800000-7809999 (121 used) |
| `waypoint_data` paths | 78000000-78099999 (4 used) |
| `creature_template` | the retail entries (42615, 43718, 45005, 45006, 45042, 48051, 48157, 48202, 51060, 51065, 51126, 51127, 51128, 51130, 52977) |

## What was not brought over, and why

- Halls of Origination, Vortex Pinnacle, Firelands, Throne of the Four Winds, Lost City of the Tol'vir, Well of
  Eternity and Mogu'shan Vaults: already in [mod-temucraft-world](https://github.com/Temucraft/mod-temucraft-world)
  from the TrinityCore 4.3.4 and LegionCore databases, which match the ported boss scripts. The repack has more rows
  on some of them (Halls of Origination 341 against 233, Lost City 405 against 194), but they are duplicates of the
  same spawns, not new content.
- The three free-for-all maps (1210, 1211, 1212): left out on purpose in mod-temucraft-world (mostly 1,410 copies of
  one custom creature).
- Gilneas, Tol'viron Arena, Temple of Kotmogu, The Tiger's Peak, the scenarios and Draenor: the repack has no spawns
  there.
- The repack's own custom content: about 1,500 custom quests (item upgrade "stages" and a donation shop), 4,500 custom
  items and 830 custom creatures (vendors for donation, transmog and upgrade systems, mostly in its mall on map 621).
  They belong to systems Temucraft does not use or does better already, and many carry another server's name.
- Map and scenario scripts (Firelands, Throne of the Four Winds and others): not now.

## The repack's server scripts (step 5)

| Script | Status |
|---|---|
| Reforging | Done better in [mod-temucraft-gear](https://github.com/Temucraft/mod-temucraft-gear) (`.temucraft reforge`). |
| Item upgrader | Done in mod-temucraft-gear (Mists-style item upgrades). |
| Item improver | Not ported: swaps an item for another from a `update_item` table that has no rows, and crashes on an empty slot. Item upgrades cover it. |
| Spell learner (learn spells on level up) | Done better in [mod-temucraft-auto-learn](https://github.com/Temucraft/mod-temucraft-auto-learn) (uses the trainers' lists). |
| Multi-trainer | Not ported: one NPC that opens weapon and riding trainer lists, the class trainer, buys dual spec and resets talents. It needs a core change (`Creature::GetMultitrainerEntry`, trainer list by id). Auto-learn covers class spells. A Temucraft version as gossip options on one NPC would be about half a day. |
| Guild houses | Done in [mod-temucraft-housing](https://github.com/Temucraft/mod-temucraft-housing) (`.temucraft guildhouse`). |
| 1v1 arena | Not ported: the repack's version (Teiby's script) needs core changes (an arena type, its own config and talent checks in the core). The maintained AzerothCore module `mod-1v1-arena` does the same as a module. Forking it as `mod-temucraft-1v1-arena`, with its commands under `.temucraft` and RBAC, is about one day. |

## Install

1. Put the folder in `modules/` (next to the other Temucraft modules) and re-run CMake. The worldserver applies the
   SQL on its next start.
2. The server needs the maps, vmaps and mmaps of 726 and 730: `extract_new_maps.bat` already lists them.
3. The client already has everything (the displays are in patch-T).

`tools/crazy_convert.py` rebuilds the SQL from the repack's world dump and this core's base world database loaded
in a scratch MariaDB (see the script's header).

Part of the Temucraft modules for AzerothCore 3.3.5a.
