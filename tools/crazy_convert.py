#!/usr/bin/env python3
"""Converts the Crazy repack's Twin Peaks (726) and Maelstrom Zone (730) spawns from its old TrinityCore/YTDB world
database to this AzerothCore's world schema. The other Crazy maps are already in mod-temucraft-world from better
sources (TDB 4.3.4, LegionCore), so they are left out here.

Reads two databases on one MariaDB server: `cz` (the Crazy world dump) and `acw` (AzerothCore's base world database,
to skip creatures, models and so on that the core already has).
The Cataclysm displays get their creature_model_info row (sizes from the Crazy database) and, so the server never
depends on its Data/dbc files having them, their CreatureDisplayInfo / CreatureModelData rows as patch-T has them.
usage: crazy_convert.py SOCKET OUT.sql PATCH_T_DBC_DIR STOCK_CreatureModelData.dbc (the 3.3.5 client's own copy)"""
import sys, os, struct, pymysql
from pymysql.converters import escape_string
SOCK, OUT, PT, STOCK = sys.argv[1:5]; _b = open(STOCK, 'rb').read(); STOCK = {struct.unpack_from('<I', _b, 20 + i * struct.unpack_from('<I', _b, 12)[0])[0] for i in range(struct.unpack_from('<I', _b, 4)[0])}
con = pymysql.connect(unix_socket=SOCK, user='root', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
def q(sql, *a):
    with con.cursor() as c: c.execute(sql, a); return c.fetchall()
MAPS = {726: 'Twin Peaks', 730: 'Maelstrom Zone'}
GUID, PATH = 7800000, 78000000
# faction templates the 3.3.5 FactionTemplate.dbc doesn't have (patch-T doesn't change that table): closest 3.3.5 one
FACTION = {2339: 1732,   # Wildhammer Clan (Alliance side)  -> Alliance generic
           2362: 1732,   # Wildhammer gryphon hatchlings    -> Alliance generic
           2305: 1735,   # Dragonmaw (Horde side)           -> Horde generic
           2329: 60,     # Maelstrom effect bunnies          -> same faction (50), 3.3.5 template
           2256: 35,     # Aggra, Earthen Ring               -> friendly
           2167: 35}     # Thrall, Earthen Ring (no row in any client) -> friendly
def lvl(v): return min(v, 80)
def lit(v):
    if v is None: return 'NULL'
    if isinstance(v, (bytes, bytearray)): v = v.decode('utf8', 'replace')
    if isinstance(v, str): return "'" + escape_string(v) + "'"
    if isinstance(v, float): return repr(round(v, 6))
    return str(v)
out = open(OUT, 'w', encoding='utf8', newline='\n')
def emit(table, rows, comment=None):
    if not rows: return
    cols = list(rows[0].keys())
    if comment: out.write(f'-- {comment}\n')
    out.write(f"INSERT INTO `{table}` ({', '.join('`%s`' % c for c in cols)}) VALUES\n")
    out.write(',\n'.join('(' + ', '.join(lit(r[c]) for c in cols) + ')' for r in rows) + ';\n\n')
def inlist(v): return ','.join(map(str, sorted(v))) or '0'

inmaps = inlist(MAPS)
cre = q(f"select * from cz.creature where map in ({inmaps}) order by map, guid")
guid = {r['guid']: GUID + i for i, r in enumerate(cre)}
ac_ct = {r['entry'] for r in q(f"select entry from acw.creature_template where entry in ({inlist({r['id'] for r in cre})})")}
want = sorted({r['id'] for r in cre} - ac_ct)
tpl = {t['entry']: t for t in q(f"select * from cz.creature_template where entry in ({inlist(want)})")}

out.write('-- mod-temucraft-crazy: Twin Peaks (726) and Maelstrom Zone (730) spawns, from the Crazy repack world database.\n'
          f'-- Creature GUIDs {GUID}-{GUID + 9999}, waypoint paths from {PATH}. Made by tools/crazy_convert.py.\n'
          '-- The templates are Cataclysm creatures the core does not have; levels above 80 are set to 80.\n\n')
out.write(f"DELETE FROM `creature` WHERE `guid` BETWEEN {GUID} AND {GUID + 9999};\n")
out.write(f"DELETE FROM `creature_addon` WHERE `guid` BETWEEN {GUID} AND {GUID + 9999};\n")
out.write(f"DELETE FROM `waypoint_data` WHERE `id` BETWEEN {PATH} AND {PATH + 99999};\n")
for t in ('creature_template', 'creature_template_model', 'creature_template_addon', 'creature_template_movement'):
    col = {'creature_template': 'entry', 'creature_template_model': 'CreatureID', 'creature_template_addon': 'entry',
           'creature_template_movement': 'CreatureId'}[t]
    out.write(f"DELETE FROM `{t}` WHERE `{col}` IN ({inlist(want)});\n")
out.write('\n')

ct, models, mov, displays = [], [], [], set()
for e in want:
    t = tpl[e]
    ct.append(dict(entry=e, difficulty_entry_1=0, difficulty_entry_2=0, difficulty_entry_3=0, KillCredit1=0, KillCredit2=0,
                   name=t['name'], subname=t['subname'] or '', IconName='', gossip_menu_id=0,
                   minlevel=lvl(t['minlevel']), maxlevel=lvl(t['maxlevel']), exp=min(t['exp'], 2),
                   faction=FACTION.get(t['faction_A'], t['faction_A']),
                   npcflag=0,      # no gossip, quest, vendor or taxi rows came with them
                   speed_walk=t['speed_walk'], speed_run=t['speed_run'], speed_swim=1, speed_flight=1, detection_range=20,
                   rank=t['rank'], dmgschool=t['dmgschool'], DamageModifier=t['dmg_multiplier'] or 1,
                   BaseAttackTime=t['baseattacktime'] or 2000, RangeAttackTime=t['rangeattacktime'] or 2000,
                   BaseVariance=1, RangeVariance=1, unit_class=t['unit_class'] or 1, unit_flags=t['unit_flags'],
                   unit_flags2=t['unit_flags2'], dynamicflags=t['dynamicflags'], family=t['family'], type=t['type'],
                   type_flags=0,  # Cataclysm type flag bits mean other things in 3.3.5
                   lootid=0, pickpocketloot=0, skinloot=0, PetSpellDataId=0, VehicleId=0, mingold=0, maxgold=0,
                   AIName='',     # the only SmartAI row (the Maelstrom wyvern's portal) needs a gossip menu it never had
                   MovementType=t['MovementType'], HoverHeight=t['HoverHeight'], HealthModifier=t['Health_mod'],
                   ManaModifier=t['Mana_mod'], ArmorModifier=t['Armor_mod'], ExperienceModifier=1, RacialLeader=0,
                   movementId=0, RegenHealth=t['RegenHealth'], CreatureImmunitiesId=0, flags_extra=t['flags_extra'],
                   ScriptName='', VerifiedBuild=0))
    idx = 0
    for k in ('modelid1', 'modelid2', 'modelid3', 'modelid4'):
        if t[k]:
            models.append(dict(CreatureID=e, Idx=idx, CreatureDisplayID=t[k], DisplayScale=t['scale'] or 1, Probability=1, VerifiedBuild=0))
            displays.add(t[k]); idx += 1
    inh = t['InhabitType']
    mov.append(dict(CreatureId=e, Ground=1 if inh & 1 else 0, Swim=1 if inh & 2 else 0, Flight=1 if inh & 4 else 0,
                    Rooted=0, Chase=0, Random=0, InteractionPauseTimer=None))
emit('creature_template', ct, f'{len(ct)} creature templates')
emit('creature_template_model', models)
emit('creature_template_movement', mov)
# model sizes the core needs to load the creature (it refuses a display with no creature_model_info row)
have = {r['DisplayID'] for r in q(f"select DisplayID from acw.creature_model_info where DisplayID in ({inlist(displays)})")}
mi = [dict(DisplayID=r['modelid'], BoundingRadius=r['bounding_radius'], CombatReach=r['combat_reach'], Gender=r['gender'],
           DisplayID_Other_Gender=r['modelid_other_gender'], VerifiedBuild=0)
      for r in q(f"select * from cz.creature_model_info where modelid in ({inlist(displays - have)}) order by modelid")]
if mi:
    out.write('-- INSERT IGNORE: another module may bring the same Cataclysm model sizes\n')
    out.write('INSERT IGNORE INTO `creature_model_info` (`DisplayID`, `BoundingRadius`, `CombatReach`, `Gender`, `DisplayID_Other_Gender`, `VerifiedBuild`) VALUES\n')
    out.write(',\n'.join('(' + ', '.join(lit(r[c]) for c in r) + ')' for r in mi) + ';\n\n')
def dbc(name, strings, floats, ids):
    b = open(os.path.join(PT, name + '.dbc'), 'rb').read(); n, f, rs, ss = struct.unpack_from('<4I', b, 4); sb = b[20 + n * rs:]
    rows = []
    for i in range(n):
        r = list(struct.unpack_from('<%dI' % f, b, 20 + i * rs))
        if r[0] not in ids: continue
        for k in range(f):
            if k in strings: r[k] = sb[r[k]:sb.index(b'\0', r[k])].decode('utf8')
            elif k in floats: r[k] = struct.unpack('<f', struct.pack('<I', r[k]))[0]
            else: r[k] = struct.unpack('<i', struct.pack('<I', r[k]))[0]
        rows.append(r)
    return sorted(rows)
def emit_dbc(table, rows):
    if not rows: return
    cols = [c['c'] for c in q("select column_name c from information_schema.columns where table_schema='acw' and table_name=%s order by ordinal_position", table)]
    assert len(cols) == len(rows[0]), table
    out.write(f"INSERT IGNORE INTO `{table}` ({', '.join('`%s`' % c for c in cols)}) VALUES\n")
    out.write(',\n'.join('(' + ', '.join(lit(v) for v in r) + ')' for r in rows) + ';\n\n')
newdisp = sorted(r['DisplayID'] for r in mi)
cdi = dbc('CreatureDisplayInfo', {6, 7, 8, 9}, {4}, set(newdisp))
cmd = dbc('CreatureModelData', {2}, {4, 7, 8, 9} | set(range(14, 28)), {r[1] for r in cdi} - STOCK)
out.write('-- The same Cataclysm display and model rows as patch-T, for the server (INSERT IGNORE)\n')
emit_dbc('creaturedisplayinfo_dbc', cdi)
emit_dbc('creaturemodeldata_dbc', cmd)
ta = [dict(entry=r['entry'], path_id=0, mount=r['mount'], bytes1=r['bytes1'], bytes2=r['bytes2'], emote=r['emote'],
           visibilityDistanceType=0, auras=r['auras'] or '')
      for r in q(f"select * from cz.creature_template_addon where entry in ({inlist(want)}) order by entry")]
emit('creature_template_addon', ta)

addon = {r['guid']: r for r in q(f"select * from cz.creature_addon where guid in ({inlist(guid)})")}
paths, wp, ca, spawns = {}, [], [], []
for r in cre:
    a = addon.get(r['guid']); mt = r['MovementType']; pid = 0
    if a and a['path_id']:
        pts = q("select * from cz.waypoint_data where id=%s order by point", a['path_id'])
        if pts:
            pid = paths.setdefault(a['path_id'], PATH + len(paths)); mt = 2   # had a path but stood still: walk it
            if len(paths) > len({w['id'] for w in wp}):
                for p in pts:
                    wp.append(dict(id=pid, point=p['point'], position_x=p['position_x'], position_y=p['position_y'],
                                   position_z=p['position_z'], orientation=p['orientation'] or None, velocity=0,
                                   delay=p['delay'], smoothTransition=0, move_type=p['move_flag'], action=0,
                                   action_chance=100, wpguid=0))
    if a:
        ca.append(dict(guid=guid[r['guid']], path_id=pid, mount=a['mount'], bytes1=a['bytes1'], bytes2=a['bytes2'],
                       emote=a['emote'], visibilityDistanceType=0, auras=a['auras'] or ''))
    spawns.append(dict(guid=guid[r['guid']], id=r['id'], map=r['map'], zoneId=0, areaId=0, spawnMask=1,
                       phaseMask=r['phaseMask'], equipment_id=0, position_x=r['position_x'], position_y=r['position_y'],
                       position_z=r['position_z'], orientation=r['orientation'], spawntimesecs=r['spawntimesecs'],
                       wander_distance=r['spawndist'] if mt == 1 else 0, currentwaypoint=0, curhealth=1, curmana=0,
                       MovementType=mt, npcflag=0, unit_flags=0, dynamicflags=0, ScriptName='', VerifiedBuild=0,
                       CreateObject=0, Comment=None))
for m, name in MAPS.items():
    emit('creature', [s for s in spawns if s['map'] == m], f"{name} ({m}): {sum(1 for s in spawns if s['map'] == m)} creatures")
emit('creature_addon', ca)
emit('waypoint_data', wp, f'{len(paths)} waypoint paths')
# staff .tele point on the Maelstrom (the repack's own). Twin Peaks is a battleground map: the core only lets players
# in through a real battleground, which this core does not have for it, so it gets no .tele point.
out.write("-- .tele TheMaelstrom\n"
          "DELETE FROM `game_tele` WHERE `name` IN ('TheMaelstrom');\n"
          "INSERT INTO `game_tele` (`id`, `position_x`, `position_y`, `position_z`, `orientation`, `map`, `name`) SELECT MAX(`id`) + 1, 851.307, 1067.76, -10.0183, 4.50656, 730, 'TheMaelstrom' FROM `game_tele`;\n")
out.close()
print(f"templates {len(ct)}, models {len(models)}, model sizes {len(mi)}, display rows {len(cdi)}, model data rows {len(cmd)}, spawns " +
      ', '.join(f"{n} {sum(1 for s in spawns if s['map'] == m)}" for m, n in MAPS.items()) + f", addons {len(ca)}, paths {len(paths)} ({len(wp)} points)")
