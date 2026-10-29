
import json, os, sys, urllib.request
from datetime import date

USER = os.environ.get("GH_USER", "VACRandomSample")
TOKEN = os.environ.get("GH_TOKEN", "")
API = "https://api.github.com"
OUT = os.environ.get("CARDS_OUT", "assets/cards")

BG, BORDER = "#0D1117", "#30363D"
TITLE, TEXT, SUB, PAPER = "#E63946", "#C9D1D9", "#8B949E", "#F0F0F5"
ACC, ACC2 = "#FF6B6B", "#8A0E20"
LANG_COLORS = ["#E63946", "#FF6B6B", "#FF9AA4", "#C1121F", "#FF4757", "#B02A37", "#6E7681"]

def api(path):
    req = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "crimson-nocturne-cards",
        **({"Authorization": "Bearer " + TOKEN} if TOKEN else {}),
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def graphql(q, variables):
    body = json.dumps({"query": q, "variables": variables}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Content-Type": "application/json",
        "User-Agent": "crimson-nocturne-cards",
        **({"Authorization": "Bearer " + TOKEN} if TOKEN else {}),
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

u = api("/users/" + USER)
repos = api("/users/%s/repos?per_page=100&sort=pushed" % USER)
stars = sum(r.get("stargazers_count", 0) for r in repos)
forks = sum(r.get("forks_count", 0) for r in repos)

weeks = None
total_commits = None
try:
    q = "query($u:String!){ user(login:$u){ contributionsCollection { contributionCalendar { totalContributions weeks { firstDay contributionDays { contributionCount date } } } } } }"
    res = graphql(q, {"u": USER})
    cal = res["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    total_commits = cal["totalContributions"]
    weeks = cal["weeks"]
except Exception as e:
    print("graphql failed -> REST fallback:", e)

langs = {}
for r in repos[:12]:
    try:
        for lang, b in api("/repos/%s/%s/languages" % (USER, r["name"])).items():
            langs[lang] = langs.get(lang, 0) + b
    except Exception as e:
        print("langs skip", r["name"], e)
lang_total = sum(langs.values()) or 1

print("data:", {"repos": u.get("public_repos"), "stars": stars, "forks": forks,
                "followers": u.get("followers"), "commits": total_commits,
                "weeks": len(weeks) if weeks else 0, "langs": len(langs)})

os.makedirs(OUT, exist_ok=True)

def svg_open(w, h, title):
    return ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img">' % (w, h, w, h),
            '<title>%s</title>' % esc(title),
            '<rect x="0.5" y="0.5" width="%d" height="%d" rx="12" fill="%s" stroke="%s"/>' % (w - 1, h - 1, BG, BORDER),
            '<rect x="0.5" y="10" width="4" height="%d" rx="2" fill="%s"/>' % (h - 20, ACC2)]

def save(name, lines):
    p = os.path.join(OUT, name)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n</svg>\n")
    print("wrote", p, os.path.getsize(p))

rows = [
    ("⚔", "Commits (year)", total_commits if total_commits is not None else "—"),
    ("★", "Stars earned", stars),
    ("▣", "Repositories", u.get("public_repos", 0)),
    ("◉", "Followers", u.get("followers", 0)),
]
L = svg_open(470, 195, USER + " - soul stats")
L.append('<text x="26" y="38" font-family="Verdana,Segoe UI,sans-serif" font-size="16" font-weight="bold" letter-spacing="2" fill="%s">SOUL STATS 「魂の統計」</text>' % TITLE)
L.append('<line x1="26" y1="52" x2="444" y2="52" stroke="%s" stroke-width="1"/>' % BORDER)
y = 82
for icon, label, val in rows:
    L.append('<text x="28" y="%d" font-family="Verdana,Segoe UI,sans-serif" font-size="13" fill="%s">%s</text>' % (y, ACC, icon))
    L.append('<text x="54" y="%d" font-family="Verdana,Segoe UI,sans-serif" font-size="13" fill="%s">%s</text>' % (y, TEXT, esc(str(label))))
    L.append('<text x="444" y="%d" font-family="Verdana,Segoe UI,sans-serif" font-size="13" font-weight="bold" fill="%s" text-anchor="end">%s</text>' % (y, PAPER, esc(str(val))))
    y += 27
save("stats.svg", L)

top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]
other = lang_total - sum(v for _, v in top)
segs = [(n, v) for n, v in top if v > 0]
if other > 0:
    segs.append(("Other", other))
L = svg_open(470, 195, USER + " - languages")
L.append('<text x="26" y="38" font-family="Verdana,Segoe UI,sans-serif" font-size="16" font-weight="bold" letter-spacing="2" fill="%s">LANGUAGES 「言霊」</text>' % TITLE)
L.append('<line x1="26" y1="52" x2="444" y2="52" stroke="%s" stroke-width="1"/>' % BORDER)
bar_w, x0 = 420, 26
cx = x0
for i, (n, v) in enumerate(segs):
    w = max(2, round(bar_w * v / lang_total)) if len(segs) > 1 else bar_w
    w = min(w, x0 + bar_w - cx)
    L.append('<rect x="%d" y="76" width="%d" height="14" rx="3" fill="%s"/>' % (cx, w, LANG_COLORS[i % len(LANG_COLORS)]))
    cx += w
ly = 122
for i, (n, v) in enumerate(segs[:7]):
    col_x = 26 if i % 2 == 0 else 240
    row_y = ly + (i // 2) * 22
    L.append('<circle cx="%d" cy="%d" r="4" fill="%s"/>' % (col_x + 4, row_y - 4, LANG_COLORS[i % len(LANG_COLORS)]))
    L.append('<text x="%d" y="%d" font-family="Verdana,Segoe UI,sans-serif" font-size="12" fill="%s">%s %.1f%%</text>' % (col_x + 14, row_y, TEXT, esc(n), 100.0 * v / lang_total))
save("langs.svg", L)

W, H = 1000, 300
L = svg_open(W, H, USER + " - contribution graph")
L.append('<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s" stop-opacity="0.05"/></linearGradient></defs>' % (ACC, ACC))
L.append('<text x="26" y="38" font-family="Verdana,Segoe UI,sans-serif" font-size="16" font-weight="bold" letter-spacing="2" fill="%s">CONTRIBUTION GRAPH 「月報」</text>' % TITLE)
L.append('<line x1="26" y1="52" x2="974" y2="52" stroke="%s" stroke-width="1"/>' % BORDER)
if weeks:
    weekly = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks]
    n = len(weekly)
    gx0, gx1, gy0, gy1 = 70, 960, 72, 236
    vmax = max(weekly + [1])
    vmax = max(10, ((vmax + 9) // 10) * 10)
    for i in range(5):
        gy = gy1 - (gy1 - gy0) * i / 4
        L.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1" opacity="0.35"/>' % (gx0, gy, gx1, gy, BORDER))
        L.append('<text x="%d" y="%.1f" font-family="Verdana,Segoe UI,sans-serif" font-size="11" fill="%s" text-anchor="end">%d</text>' % (gx0 - 8, gy + 4, SUB, int(vmax * i / 4)))
    pts = []
    for i, v in enumerate(weekly):
        px = gx0 + (gx1 - gx0) * (i / max(1, n - 1))
        py = gy1 - (gy1 - gy0) * (min(v, vmax) / vmax)
        pts.append((px, py))
    L.append('<path d="%s" fill="url(#g)" opacity="0.5"/>' % ("M %d %d " % (gx0, gy1) + " ".join("L %.1f %.1f" % p for p in pts) + " L %d %d Z" % (gx1, gy1)))
    L.append('<path d="%s" fill="none" stroke="%s" stroke-width="2" stroke-linejoin="round"/>' % ("M " + " ".join("L %.1f %.1f" % p for p in pts), ACC))
    last_pt = pts[-1]
    L.append('<circle cx="%.1f" cy="%.1f" r="4" fill="#FF4757"/>' % (last_pt[0], last_pt[1]))
    months, seen = [], -1
    for w in weeks:
        m = date.fromisoformat(w["firstDay"]).month
        if m != seen:
            months.append((w["firstDay"], m)); seen = m
    for i, (fd, m) in enumerate(months):
        frac = i / max(1, len(months) - 1)
        L.append('<text x="%.1f" y="258" font-family="Verdana,Segoe UI,sans-serif" font-size="11" fill="%s" text-anchor="middle">%s</text>' % (gx0 + (gx1 - gx0) * frac, SUB, date.fromisoformat(fd).strftime("%b")))
    L.append('<text x="974" y="290" font-family="Verdana,Segoe UI,sans-serif" font-size="11" fill="%s" text-anchor="end">last week: %d commits</text>' % (SUB, weekly[-1]))
save("graph.svg", L)

RANKS = [(0, "従卒", "FOLLOWER"), (50, "三席", "3RD SEAT"), (200, "副隊長", "LIEUTENANT"), (500, "隊長", "CAPTAIN"), (1000, "卍解", "BANKAI")]
commits = total_commits or 0
idx = max(i for i, (t, _, _) in enumerate(RANKS) if commits >= t)
thr_t, thr_kanji, thr_name = RANKS[idx]
next_thr = RANKS[idx + 1][0] if idx + 1 < len(RANKS) else None
W, H = 1000, 130
L = svg_open(W, H, USER + " - seireitei rank")
L.append('<text x="30" y="56" font-family="Verdana,Segoe UI,sans-serif" font-size="22" font-weight="bold" letter-spacing="2" fill="%s">SEIREITEI RANK</text>' % TITLE)
L.append('<text x="30" y="92" font-family="Verdana,Segoe UI,sans-serif" font-size="20" fill="%s">%s  %s</text>' % (PAPER, thr_kanji, thr_name))
bx0, bx1, by = 420, 960, 74
L.append('<rect x="%d" y="%d" width="%d" height="12" rx="6" fill="#161B22" stroke="%s"/>' % (bx0, by, bx1 - bx0, BORDER))
if next_thr:
    prev_thr = thr_t
    prog = min(1.0, (commits - prev_thr) / max(1, next_thr - prev_thr))
    label = "%d / %d commits to %s" % (commits, next_thr, RANKS[idx + 1][2])
else:
    prog = 1.0
    label = "%d commits — maximum rank" % commits
L.append('<rect x="%d" y="%d" width="%d" height="12" rx="6" fill="%s"/>' % (bx0, by, max(6, int((bx1 - bx0) * prog)), ACC))
L.append('<text x="%d" y="%d" font-family="Verdana,Segoe UI,sans-serif" font-size="12" fill="%s" text-anchor="end">%s</text>' % (bx1, by - 12, SUB, esc(label)))
save("rank.svg", L)
print("DONE")
