"""Dependency-free SVG renderer for Six Thinking Hats data; JupyterLite/Pyodide friendly."""
from html import escape
from textwrap import wrap

HAT_META = {
    "white": ("White Hat — Facts & Evidence", "#f7f7f7", "#5c6770"),
    "red": ("Red Hat — Feelings & Intuition", "#ffe9ed", "#e32636"),
    "black": ("Black Hat — Risks & Challenges", "#eeeeee", "#222222"),
    "yellow": ("Yellow Hat — Benefits & Opportunities", "#fff4bf", "#d99b00"),
    "green": ("Green Hat — Creativity & Alternatives", "#e7f8ea", "#169b45"),
    "blue": ("Blue Hat — Process & Next Steps", "#e4f1ff", "#1677d2"),
    "purple": ("Purple Hat — Orchestrator", "#efe4ff", "#6f2dbd"),
}
POSITIONS = {"white":(35,120),"red":(35,335),"black":(35,550),"yellow":(965,120),"green":(965,335),"blue":(965,550),"purple":(430,18)}

def _text(x,y,text,size=15,weight="normal",max_chars=48,line_height=20,anchor="start"):
    lines=[]
    for paragraph in str(text).split("\n"):
        lines.extend(wrap(paragraph,max_chars) or [""])
    spans=[]
    for i,line in enumerate(lines):
        spans.append(f'<tspan x="{x}" dy="{0 if i==0 else line_height}">{escape(line)}</tspan>')
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" font-family="Arial, sans-serif">{"".join(spans)}</text>'

def render_mind_map(data,width=1400,height=840,include_purple=True):
    hats=["white","red","black","yellow","green","blue"]
    if include_purple and data.get("purple"): hats.append("purple")
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">','<rect width="100%" height="100%" fill="#fff"/>','<circle cx="700" cy="430" r="178" fill="#f4f8ff" stroke="#2e6db4" stroke-width="4"/>']
    out.append(_text(700,372,data.get("title","Six Thinking Hats"),30,"bold",25,34,"middle"))
    if data.get("subtitle"): out.append(_text(700,470,data["subtitle"],17,"bold",36,22,"middle"))
    if data.get("question"): out.append(_text(700,535,data["question"],14,"normal",42,18,"middle"))
    for hat in hats:
        section=data.get(hat,{})
        if not section: continue
        label,fill,stroke=HAT_META[hat]; x,y=POSITIONS[hat]; w,h=((540,175) if hat=="purple" else (400,190))
        if hat=="purple": out.append(f'<path d="M 700 252 C 700 190, 700 210, 700 {y+h}" fill="none" stroke="{stroke}" stroke-width="5"/>')
        else:
            bx=x+(w if x<700 else 0); by=y+h/2; cx=525 if x<700 else 875
            out.append(f'<path d="M {cx} 430 C {(cx+bx)/2:.1f} 430, {(cx+bx)/2:.1f} {by}, {bx} {by}" fill="none" stroke="{stroke}" stroke-width="5"/>')
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="24" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        out.append(_text(x+18,y+32,section.get("label",label),18,"bold",45,20))
        yy=y+64
        for item in section.get("items",[])[:6]:
            lines=wrap(str(item),46)[:2]
            out.append(f'<circle cx="{x+22}" cy="{yy-5}" r="3.5" fill="{stroke}"/>')
            out.append(_text(x+34,yy,"\n".join(lines),13,"normal",46,16))
            yy += 20 + 16*(len(lines)-1)
    out.append('</svg>')
    return ''.join(out)
