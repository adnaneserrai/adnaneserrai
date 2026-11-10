"""Generate assets/stats.svg and assets/langs.svg from the GitHub GraphQL API."""
import json, os, urllib.request
from html import escape

USER = os.environ.get("GH_USER", "adnaneserrai")
TOKEN = os.environ["GH_TOKEN"]
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")

Q = """query($u:String!){user(login:$u){
  contributionsCollection{totalCommitContributions totalPullRequestContributions
    totalIssueContributions totalRepositoryContributions restrictedContributionsCount}
  repositoriesContributedTo(first:1,contributionTypes:[COMMIT,PULL_REQUEST,ISSUE]){totalCount}
  repositories(first:100,ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC){totalCount nodes{
    stargazerCount languages(first:10,orderBy:{field:SIZE,direction:DESC}){
      edges{size node{name color}}}}}}}"""

req = urllib.request.Request("https://api.github.com/graphql",
    data=json.dumps({"query": Q, "variables": {"u": USER}}).encode(),
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})
u = json.load(urllib.request.urlopen(req))["data"]["user"]
c = u["contributionsCollection"]
repos = u["repositories"]["nodes"]

FONT = "JetBrains Mono,Fira Code,Consolas,monospace"
HEAD = f"""<svg xmlns="http://www.w3.org/2000/svg" width="440" height="190" viewBox="0 0 440 190">
<rect x=".5" y=".5" width="439" height="189" rx="6" fill="#0a0a0a" stroke="#2a2a2a"/>
<rect x="24" y="22" width="22" height="3" fill="#ff1a1a"/>
<text x="24" y="46" font-family="{FONT}" font-size="15" font-weight="700" fill="#ececec">{{title}}</text>"""

rows = [("commits · last year", c["totalCommitContributions"] + c["restrictedContributionsCount"]),
        ("public repos", u["repositories"]["totalCount"]),
        ("contributed to", u["repositoriesContributedTo"]["totalCount"]),
        ("stars earned", sum(r["stargazerCount"] for r in repos))]
s = HEAD.replace("{title}", "footprint")
for i, (k, v) in enumerate(rows):
    y = 80 + i * 22
    s += (f'<text x="24" y="{y}" font-family="{FONT}" font-size="12" fill="#5f5f5f">&gt;</text>'
          f'<text x="40" y="{y}" font-family="{FONT}" font-size="12" fill="#9a9a9a">{k}</text>'
          f'<text x="416" y="{y}" text-anchor="end" font-family="{FONT}" font-size="13" font-weight="700" fill="#ececec">{v}</text>')
open(os.path.join(OUT, "stats.svg"), "w", encoding="utf-8").write(s + "</svg>")

SKIP = {"HTML", "CSS", "SCSS", "Makefile", "CMake", "Batchfile", "Shell"}
sizes = {}
for r in repos:
    for e in r["languages"]["edges"]:
        if e["node"]["name"] in SKIP: continue
        sizes[e["node"]["name"]] = sizes.get(e["node"]["name"], 0) + e["size"]
total = sum(sizes.values()) or 1
top = sorted(sizes.items(), key=lambda x: -x[1])[:6]
reds = ["#ff1a1a", "#d41414", "#a80f0f", "#7d0909", "#5e0505", "#420202"]
s = HEAD.replace("{title}", "written in")
for i, (name, size) in enumerate(top):
    y, pct = 80 + i * 22, size / total
    s += (f'<text x="24" y="{y}" font-family="{FONT}" font-size="12" fill="#cfcfcf">{escape(name)}</text>'
          f'<rect x="150" y="{y-8}" width="210" height="6" rx="3" fill="#1c1c1c"/>'
          f'<rect x="150" y="{y-8}" width="{max(3, 210*pct):.1f}" height="6" rx="3" fill="{reds[i]}"/>'
          f'<text x="416" y="{y}" text-anchor="end" font-family="{FONT}" font-size="11" fill="#9a9a9a">{pct*100:.1f}%</text>')
open(os.path.join(OUT, "langs.svg"), "w", encoding="utf-8").write(s + "</svg>")
print("ok", rows, top)
