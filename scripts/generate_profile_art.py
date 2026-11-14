#!/usr/bin/env python3
"""Render theme-aware animated profile art from GitHub's contribution calendar."""
from __future__ import annotations
import datetime as dt, html, json, os, pathlib, urllib.request
ROOT = pathlib.Path(__file__).resolve().parents[1]
USER = os.getenv("GH_PROFILE_USER", "aarit88")
OUT = ROOT / "assets" / "animated"
DATA = ROOT / "data" / "contributions.json"
QUERY = """query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){followers{totalCount} repositories(privacy:PUBLIC,ownerAffiliations:OWNER,first:1){totalCount} contributionsCollection(from:$from,to:$to){totalCommitContributions totalIssueContributions totalPullRequestContributions contributionCalendar{totalContributions weeks{firstDay contributionDays{date contributionCount contributionLevel}}}}}}"""
PALETTES = {
 "dark": {"bg":"#0a101f","panel":"#111b2e","line":"#26364e","text":"#e2e8f0","muted":"#94a3b8","cyan":"#22d3ee","purple":"#a78bfa","green":"#34d399","levels":["#172338","#123f4a","#0e7490","#22d3ee","#a5f3fc"]},
 "light": {"bg":"#f8fafc","panel":"#ffffff","line":"#dbe4ef","text":"#0f172a","muted":"#475569","cyan":"#0369a1","purple":"#6d28d9","green":"#059669","levels":["#e2e8f0","#bae6fd","#7dd3fc","#0284c7","#1e3a8a"]},
}
def esc(value): return html.escape(str(value), quote=True)
def svg_open(width,height,p,title):
 return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc"><title id="title">{esc(title)}</title><desc id="desc">Animated {esc(title.lower())} for Aarit Gupta.</desc><defs><linearGradient id="accent"><stop stop-color="{p["cyan"]}"/><stop offset="1" stop-color="{p["purple"]}"/></linearGradient></defs>'
def write(name,body): (OUT/name).write_text(body+"</svg>\n",encoding="utf-8")
def text(x,y,value,size=14,color=None,weight=400,spacing=None):
 style=f' font-family="Inter,Segoe UI,Arial,sans-serif" font-size="{size}" font-weight="{weight}" fill="{color or "#e2e8f0"}"'
 if spacing: style+=f' letter-spacing="{spacing}"'
 return f'<text x="{x}" y="{y}"{style}>{esc(value)}</text>'
def get_data():
 now=dt.datetime.now(dt.timezone.utc); start=now-dt.timedelta(days=364); token=os.getenv("GITHUB_TOKEN")
 if token:
  payload={"query":QUERY,"variables":{"login":USER,"from":start.isoformat().replace("+00:00","Z"),"to":now.isoformat().replace("+00:00","Z")}}
  request=urllib.request.Request("https://api.github.com/graphql",data=json.dumps(payload).encode(),headers={"Authorization":f"Bearer {token}","Content-Type":"application/json","User-Agent":"aarit88-profile-art"})
  with urllib.request.urlopen(request,timeout=25) as response: result=json.load(response)
  if result.get("errors"): raise RuntimeError("GitHub GraphQL query failed: "+str(result["errors"]))
  user=result["data"]["user"]
  if not user: raise RuntimeError(f"GitHub user {USER} not found")
  c=user["contributionsCollection"]; calendar=c["contributionCalendar"]
  days=[{"date":day["date"],"count":day["contributionCount"],"level":day["contributionLevel"]} for week in calendar["weeks"] for day in week["contributionDays"]]
  info={"user":USER,"updated":now.isoformat(),"total":calendar["totalContributions"],"commits":c["totalCommitContributions"],"issues":c["totalIssueContributions"],"pull_requests":c["totalPullRequestContributions"],"followers":user["followers"]["totalCount"],"repositories":user["repositories"]["totalCount"],"days":days}
  DATA.parent.mkdir(parents=True,exist_ok=True); DATA.write_text(json.dumps(info,indent=2)+"\n",encoding="utf-8"); return info
 if DATA.exists(): return json.loads(DATA.read_text(encoding="utf-8"))
 return {"user":USER,"total":None,"commits":None,"issues":None,"pull_requests":None,"reviews":None,"followers":None,"repositories":None,"days":[]}
def render_meta(p):
 body=svg_open(1100,118,p,"About Aarit Gupta")+f'<rect width="1100" height="118" rx="18" fill="{p["panel"]}" stroke="{p["line"]}"/>'
 chips=[("B.TECH CSE","Dr. Ambedkar Institute of Technology"),("2023—2027","Bengaluru, India"),("FOCUS","AI · Robotics · Full-Stack")]
 for i,(head,sub) in enumerate(chips):
  x=30+i*360; body+=text(x,45,head,12,p["cyan"],700,"1.5")+text(x,76,sub,16,p["text"],600)
  if i<2: body+=f'<path d="M{x+330} 24v70" stroke="{p["line"]}"/>'
 return write(f"about-meta-{theme}.svg",body)
def render_activity(p,info):
 days=info.get("days",[]); today=dt.date.today(); index={d["date"]:d["count"] for d in days}; series=[]
 for i in range(30,-1,-1):
  date=(today-dt.timedelta(days=i)).isoformat(); series.append(index.get(date,0))
 maxv=max(series or [0]) or 1; points=[]; bars=[]
 for i,val in enumerate(series):
  x=52+i*30; y=168-(val/maxv)*92; points.append(f"{x},{y:.1f}"); h=max(3,val/maxv*72); bars.append(f'<rect x="{x-5}" y="{218-h:.1f}" width="10" height="{h:.1f}" rx="4" fill="{p["cyan"]}" opacity=".45"><animate attributeName="opacity" values=".25;.85;.25" dur="3.4s" begin="{i*.025:.2f}s" repeatCount="indefinite"/></rect>')
 body=svg_open(1000,270,p,"GitHub activity over the last 31 days")+f'<rect width="1000" height="270" rx="18" fill="{p["panel"]}" stroke="{p["line"]}"/>'+text(32,36,"RECENT ACTIVITY",11,p["cyan"],700,"2")+text(32,61,"Daily contribution rhythm · last 31 days",17,p["text"],600)
 for y in (92,132,172,212): body+=f'<path d="M48 {y}H954" stroke="{p["line"]}" stroke-dasharray="3 7"/>'
 body+=''.join(bars)+f'<polyline points="{" ".join(points)}" fill="none" stroke="url(#accent)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="2400"><animate attributeName="stroke-dashoffset" values="2400;0;0;2400" dur="12s" repeatCount="indefinite"/></polyline>'
 for i in (0,10,20,30):
  x=52+i*30; y=168-(series[i]/maxv)*92; body+=f'<circle cx="{x}" cy="{y:.1f}" r="4" fill="{p["cyan"]}"><animate attributeName="r" values="3;6;3" dur="2.2s" begin="{i*.09:.1f}s" repeatCount="indefinite"/></circle>'
 return write(f"activity-graph-{theme}.svg",body)
def render_heatmap(p,info):
 days=info.get("days",[]); lookup={d["date"]:d for d in days}; today=dt.date.today(); start=today-dt.timedelta(days=363); start-=dt.timedelta(days=start.weekday())
 body=svg_open(1120,184,p,"Annual GitHub contribution heatmap")+f'<rect width="1120" height="184" rx="18" fill="{p["panel"]}" stroke="{p["line"]}"/>'+text(28,30,"ANNUAL CONTRIBUTION MAP",11,p["cyan"],700,"2")+text(28,50,"Daily activity · animated column reveal",13,p["muted"])
 cols=53; cell=12; gap=5
 for col in range(cols):
  date=start+dt.timedelta(days=col*7)
  if date.day<=7 and date.month in (1,3,5,7,9,11): body+=text(31+col*(cell+gap),72,date.strftime("%b"),9,p["muted"])
  for row in range(7):
   day=date+dt.timedelta(days=row); value=lookup.get(day.isoformat(),{}).get("count",0); lvl=0 if value==0 else min(4,1+int(value>=2)+int(value>=5)+int(value>=10)); delay=col*.035+row*.012
   body+=f'<rect x="{31+col*(cell+gap)}" y="{80+row*(cell+gap)}" width="{cell}" height="{cell}" rx="3" fill="{p["levels"][lvl]}" opacity=".65"><animate attributeName="opacity" values=".45;1;.65" dur="3.6s" begin="{delay:.2f}s" repeatCount="indefinite"/></rect>'
 body+=text(31,169,"Less",9,p["muted"])
 for i in range(5): body+=f'<rect x="70" y="158" width="11" height="11" rx="3" fill="{p["levels"][i]}"/>'
 body+=text(146,169,"More",9,p["muted"])
 return write(f"annual-heatmap-{theme}.svg",body)
def render_stats(p,info):
 def value(key): return f'{info[key]:,}' if isinstance(info.get(key),int) else "LIVE · READY"
 body=svg_open(1100,175,p,"Aarit Gupta developer activity overview")+f'<rect width="1100" height="175" rx="18" fill="{p["panel"]}" stroke="{p["line"]}"/>'+text(28,32,"DEVELOPER OVERVIEW",11,p["cyan"],700,"2")
 cards=[("CONTRIBUTIONS",value("total")),("COMMITS",value("commits")),("PUBLIC REPOS",value("repositories")),("FOLLOWERS",value("followers"))]
 for i,(label,val) in enumerate(cards):
  x=28+i*267; body+=f'<rect x="{x}" y="52" width="247" height="91" rx="13" fill="{p["bg"]}" stroke="{p["line"]}"/>'+text(x+17,79,label,10,p["muted"],700,"1.2")+text(x+17,119,val,24,p["text"],700)
  body+=f'<circle cx="{x+222}" cy="69" r="3" fill="{p["green"]}"><animate attributeName="opacity" values=".35;1;.35" dur="2.4s" repeatCount="indefinite"/></circle>'
 return write(f"developer-overview-{theme}.svg",body)
def render_toolkit(p):
 groups=[("LANGUAGES","C++ · Python · TypeScript · SQL · Dart"),("AI & DATA","ML · NLP · OCR · Agent orchestration · PostgreSQL"),("WEB & BACKEND","React · Next.js · Node.js · FastAPI · WebSockets"),("ROBOTICS & OPS","ROS 2 · Gazebo · Docker · Kubernetes · Redis")]
 body=svg_open(1100,294,p,"Animated technical toolkit")+f'<rect width="1100" height="294" rx="18" fill="{p["panel"]}" stroke="{p["line"]}"/>'+text(28,34,"ENGINEERING TOOLKIT",11,p["cyan"],700,"2")
 for i,(title,items) in enumerate(groups):
  x=28+(i%2)*525;y=55+(i//2)*108;body+=f'<rect x="{x}" y="{y}" width="500" height="88" rx="14" fill="{p["bg"]}" stroke="{p["line"]}"/>'+text(x+18,y+31,title,11,p["cyan"],700,"1.4")+text(x+18,y+61,items,14,p["text"],550)+f'<circle cx="{x+473}" cy="{y+24}" r="4" fill="{p["purple"]}"><animate attributeName="r" values="3;6;3" dur="2.6s" begin="{i*.4}s" repeatCount="indefinite"/></circle>'
 return write(f"technical-toolkit-{theme}.svg",body)
def render_projects(p):
 cards=[("SWARMGRID","MULTI-ROBOT AMR","ROS 2 · Gazebo · A*",p["cyan"]),("SAKHI","WELLNESS PLATFORM","Next.js · Flutter · AI",p["purple"]),("SWARMNET","MULTI-AGENT SYSTEM","FastAPI · WebSockets",p["green"]),("BIOPODS","SELF-HEALING INFRA","Agents · Kubernetes",p["cyan"])]
 body=svg_open(1100,205,p,"Animated featured engineering projects")+f'<rect width="1100" height="205" rx="18" fill="{p["panel"]}" stroke="{p["line"]}"/>'+text(28,31,"SELECTED SYSTEMS",11,p["cyan"],700,"2")
 for i,(name,kind,stack,color) in enumerate(cards):
  x=28+i*267;body+=f'<rect x="{x}" y="51" width="247" height="124" rx="14" fill="{p["bg"]}" stroke="{p["line"]}"/><path d="M{x+18} 79h52" stroke="{color}" stroke-width="3" stroke-linecap="round"><animate attributeName="stroke-dasharray" values="0 80;52 80;0 80" dur="4s" begin="{i*.55}s" repeatCount="indefinite"/></path>'+text(x+18,109,name,16,p["text"],750)+text(x+18,132,kind,9,p["muted"],700,"1")+text(x+18,157,stack,11,color,550)
 return write(f"project-showcase-{theme}.svg",body)
def render_credentials(p):
 rows=[("QUALCOMM ACADEMY","AI Technical Foundation"),("QUALCOMM ACADEMY","Hands-on Development from Model to App"),("HACKATHONS","Adobe · AI for Bharat · ABB · SIH")]
 body=svg_open(1100,194,p,"Credentials and hackathon participation")+f'<rect width="1100" height="194" rx="18" fill="{p["panel"]}" stroke="{p["line"]}"/>'+text(28,32,"LEARNING & PARTICIPATION",11,p["cyan"],700,"2")
 for i,(org,title) in enumerate(rows):
  y=60+i*40;body+=f'<circle cx="38" cy="{y-4}" r="5" fill="{p["green"]}"><animate attributeName="r" values="4;6;4" dur="2.5s" begin="{i*.3}s" repeatCount="indefinite"/></circle>'+text(56,y,org,10,p["cyan"],700,"1.1")+text(256,y,title,14,p["text"],550)
 return write(f"credentials-{theme}.svg",body)
def main():
 global theme
 OUT.mkdir(parents=True,exist_ok=True); info=get_data()
 for theme,p in PALETTES.items():
  render_meta(p);render_activity(p,info);render_heatmap(p,info);render_stats(p,info);render_toolkit(p);render_projects(p);render_credentials(p)
 print(f"Rendered 14 animated SVG panels for @{USER}; contribution data: {info.get('updated','not yet fetched')}.")
if __name__=="__main__": main()
