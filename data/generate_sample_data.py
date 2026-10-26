"""
Generate fully synthetic sample data for the Muwasil Fleet Analytics schema.

Output: sample_data.sql  (run AFTER sql/01_create_tables.sql)

All names, plates, residency numbers, prices and quantities are random.
Nothing here comes from real company data. Fixed seed => reproducible output.
"""
import random

random.seed(2026)

# ---------------------------------------------------------------- settings
N_DRIVERS = 110
MONTHS = [(2026, 8), (2026, 9)]          # (year, month)
OUT = "sample_data.sql"

FIRST = ["Ahmed", "Mohammed", "Ali", "Hassan", "Omar", "Khalid", "Yousef", "Ibrahim",
         "Tariq", "Imran", "Bilal", "Rashid", "Salman", "Nadeem", "Kamal", "Rahim",
         "Faisal", "Majid", "Saeed", "Waleed", "Adel", "Hamza", "Zaid", "Anwar"]
LAST = ["Al-Harbi", "Al-Otaibi", "Khan", "Hussain", "Rahman", "Saleh", "Farouk",
        "Nasser", "Karim", "Siddiqui", "Mahmoud", "Ansari", "Qureshi", "Sharif",
        "Abbas", "Latif", "Haidar", "Zaman", "Mansour", "Yaseen"]
COUNTRIES = ["Saudi Arabia", "Pakistan", "India", "Egypt", "Bangladesh", "Sudan", "Yemen"]
STATUSES = ["Active"] * 9 + ["Inactive"]

CITIES = ["Dammam", "Jubail", "Riyadh", "Jeddah", "Yanbu", "Abha", "Tabuk",
          "Jazan", "Qassim", "Khobar", "Hail", "Najran"]
CARGO = {1: "Fuel", 2: "Flatbed"}         # keyed by branch_id
CLIENTS = [("Gulf Petro Services", "Dammam"), ("Northern Energy", "Tabuk"),      # 1-3 fuel
           ("Coastal Industries", "Yanbu"),
           ("Najd Construction", "Riyadh"), ("Eastern Steel", "Jubail"),          # 4-8 flatbed
           ("Highland Trading", "Abha"), ("Red Sea Logistics", "Jeddah"),
           ("Desert Supply Co", "Qassim")]
CLIENT_IDS = {"Fuel": [1, 2, 3], "Flatbed": [4, 5, 6, 7, 8]}
PLATE_LETTERS = list("ABDEGHJKLNRSTUVXZ")

def q(s):
    return "N'" + str(s).replace("'", "''") + "'"

# ----------------------------------------------------------------- drivers
names = set()
drivers = []
while len(drivers) < N_DRIVERS:
    name = f"{random.choice(FIRST)} {random.choice(LAST)}"
    if name in names:
        continue
    names.add(name)
    did = len(drivers) + 1
    branch = 1 if random.random() < 0.45 else 2
    iqama = f"2{random.randint(0, 999999999):09d}"
    drivers.append((did, name, branch, iqama, random.choice(COUNTRIES), random.choice(STATUSES)))
assert len({d[3] for d in drivers}) == len(drivers)

# ------------------------------------------------------------------ trucks
trucks = []
used_plates = set()
for i in range(1, N_DRIVERS + 6):
    while True:
        letters = " ".join(random.sample(PLATE_LETTERS, 3))
        num = str(random.randint(1000, 9999))
        if (letters, num) not in used_plates:
            used_plates.add((letters, num))
            break
    trucks.append([i, letters, num, None])
shuffled = random.sample(range(len(trucks)), N_DRIVERS)
for d, t in zip(drivers, shuffled):
    trucks[t][3] = d[0]          # last 5 trucks stay without a driver

# ----------------------------------------------------------- route_rates
routes = []
seen = set()
rid = 0
for branch_id, cargo in CARGO.items():
    while sum(1 for r in routes if r[3] == cargo) < 14:
        o, d = random.sample(CITIES, 2)
        if (o, d, cargo) in seen:
            continue
        seen.add((o, d, cargo))
        rid += 1
        price = random.choice(range(300, 751, 25))
        routes.append((rid, o, d, cargo, price))

# -------------------------------------------------------------- route_stats
stats = []
seen_key = set()
for (year, month) in MONTHS:
    for d in drivers:
        if d[5] != "Active":
            continue
        cargo = CARGO[d[2]]
        my_routes = [r for r in routes if r[3] == cargo]
        for r in random.sample(my_routes, random.randint(1, 3)):
            client = random.choice(CLIENT_IDS[cargo])
            key = (d[0], r[0], client, month, year)
            if key in seen_key:
                continue
            seen_key.add(key)
            stats.append((len(stats) + 1, d[0], r[0], client, month, year, random.randint(4, 10)))

# ------------------------------------------------------------------ diesel
diesel = []
for (year, month) in MONTHS:
    for d in drivers:
        if d[5] != "Active":
            continue
        diesel.append((len(diesel) + 1, d[0], month, year, round(random.uniform(600, 2600), 2)))

# ------------------------------------------------------------- adjustments
REASONS_DED = ["Traffic fine", "Damage"]
REASONS_ADD = ["Waiting pay", "Bonus"]
adj = []
for (year, month) in MONTHS:
    for d in random.sample([x for x in drivers if x[5] == "Active"], 12):
        if random.random() < 0.6:
            reason = random.choice(REASONS_DED)
            amount = -float(random.choice([150, 300, 500, 900]))
            typ = "deduction"
        else:
            reason = random.choice(REASONS_ADD)
            amount = float(random.choice([200, 400, 800, 1200]))
            typ = "addition"
        adj.append((len(adj) + 1, d[0], month, year, typ, reason, amount))

# ------------------------------------------- force a few debtors per month
# 3 low-trip drivers per branch each month end up with a negative balance
price_of = {r[0]: r[4] for r in routes}
forced = set()
for (year, month) in MONTHS:
    tv = {}
    for s_ in stats:
        if (s_[5], s_[4]) == (year, month):
            tv[s_[1]] = tv.get(s_[1], 0) + s_[6] * price_of[s_[2]]
    for branch_id in (1, 2):
        pool = [d[0] for d in drivers if d[2] == branch_id and 0 < tv.get(d[0], 0) <= 3500]
        picked = random.sample(pool, min(3, len(pool)))
        forced.update((did, year, month) for did in picked)
        for did in picked:
            adjsum = sum(a[6] for a in adj if a[1] == did and (a[3], a[2]) == (year, month))
            debt = random.choice([150, 280, 400, 550, 700, 900])
            for i, x in enumerate(diesel):
                if x[1] == did and (x[3], x[2]) == (year, month):
                    diesel[i] = (x[0], x[1], x[2], x[3], round(tv[did] + adjsum + debt, 2))

# everyone else keeps a non-negative balance (diesel capped below their earnings)
tv_all = {}
for s_ in stats:
    k = (s_[1], s_[5], s_[4])
    tv_all[k] = tv_all.get(k, 0) + s_[6] * price_of[s_[2]]
for i, x in enumerate(diesel):
    k = (x[1], x[3], x[2])
    if k in forced:
        continue
    earn = tv_all.get(k, 0) + sum(a[6] for a in adj if a[1] == x[1] and (a[3], a[2]) == (x[3], x[2]))
    if earn > 0 and x[4] > earn:
        diesel[i] = (x[0], x[1], x[2], x[3], round(earn * random.uniform(0.25, 0.7), 2))
    elif earn <= 0:
        diesel[i] = (x[0], x[1], x[2], x[3], 0.0)

# ------------------------------------------------------------- user_access
users = [("admin@example.com", "Admin", None, None),
         ("manager@example.com", "Manager", None, None),
         ("dammam.delegate@example.com", "Delegate", "Dammam", 2),
         ("dammam.delegate@example.com", "Delegate", "Jubail", 2),
         ("jeddah.delegate@example.com", "Delegate", "Jeddah", 2)]

# ------------------------------------------------------------------ write
def block(table, cols, rows, identity=True):
    out = []
    if identity:
        out.append(f"SET IDENTITY_INSERT {table} ON;")
    out.append(f"INSERT INTO {table} ({', '.join(cols)}) VALUES")
    lines = []
    for r in rows:
        vals = []
        for v in r:
            if v is None:
                vals.append("NULL")
            elif isinstance(v, str):
                vals.append(q(v))
            else:
                vals.append(str(v))
        lines.append("    (" + ", ".join(vals) + ")")
    out.append(",\n".join(lines) + ";")
    if identity:
        out.append(f"SET IDENTITY_INSERT {table} OFF;")
    out.append("GO\n")
    return "\n".join(out)

parts = ["""-- =====================================================================
-- Synthetic sample data for Muwasil Fleet Analytics (NOT real data)
-- Run after sql/01_create_tables.sql. Generated by generate_sample_data.py
-- Months covered: Aug 2026 and Sep 2026
-- =====================================================================
USE muwasil_db;
GO
"""]
parts.append("-- branches already seeded by 01_create_tables.sql (1 = fuel, 2 = flatbed)\n")
parts.append("-- drivers\n" + block("drivers", ["driver_id", "name", "branch_id", "iqama_number", "country", "status"], drivers))
parts.append("-- trucks\n" + block("trucks", ["truck_id", "plate_letters", "plate_number", "driver_id"], trucks))
parts.append("-- clients\n" + block("clients", ["client_id", "client_name", "city"],
                                   [(i + 1, c[0], c[1]) for i, c in enumerate(CLIENTS)]))
parts.append("-- route_rates\n" + block("route_rates", ["route_id", "origin", "destination", "cargo_type", "price_per_trip"], routes))
parts.append("-- route_stats\n" + block("route_stats", ["id", "driver_id", "route_id", "client_id", "month", "year", "trips_count"], stats))
parts.append("-- driver_monthly_diesel\n" + block("driver_monthly_diesel", ["id", "driver_id", "month", "year", "diesel_cost"], diesel))
parts.append("-- driver_adjustments (amount: negative = deduction)\n" + block("driver_adjustments",
             ["adjustment_id", "driver_id", "month", "year", "adjustment_type", "reason", "amount"], adj))
parts.append("-- user_access (placeholder emails)\n" + block("user_access",
             ["email", "access_role", "city", "branch_id"], users, identity=False))

with open(OUT, "w", encoding="utf-8-sig") as f:
    f.write("\n".join(parts))

# ------------------------------------------------------------ self-check
print("drivers", len(drivers), "| trucks", len(trucks), "| routes", len(routes),
      "| route_stats", len(stats), "| diesel", len(diesel), "| adjustments", len(adj))
price = {r[0]: r[4] for r in routes}
sep = [s for s in stats if (s[5], s[4]) == (2026, 9)]
trips_val = {}
for s in sep:
    trips_val[s[1]] = trips_val.get(s[1], 0) + s[6] * price[s[2]]
dz = {x[1]: x[4] for x in diesel if (x[3], x[2]) == (2026, 9)}
ad = {}
for a in adj:
    if (a[3], a[2]) == (2026, 9):
        ad[a[1]] = ad.get(a[1], 0) + a[6]
dues = {d[0]: trips_val.get(d[0], 0) - dz.get(d[0], 0) + ad.get(d[0], 0) for d in drivers}
neg = sum(1 for v in dues.values() if v < 0)
print("Sep-2026 dues: min", round(min(dues.values())), "max", round(max(dues.values())), "| negative:", neg)
active = [v for d, v in zip(drivers, dues.values()) if d[5] == "Active"]
print("Active avg dues:", round(sum(active) / len(active)), "| median:", round(sorted(active)[len(active)//2]))
