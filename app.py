#!/usr/bin/env python3
"""Static Python import graph, circular dependency detector and Mermaid exporter."""
import argparse, ast, json
from pathlib import Path
SKIP={".git",".venv","venv","__pycache__","node_modules","build","dist"}
def module_name(path,root):
    rel=path.relative_to(root).with_suffix("")
    parts=list(rel.parts)
    if parts[-1]=="__init__":parts.pop()
    return ".".join(parts)
def scan(root):
    root=Path(root).resolve();files=[p for p in root.rglob("*.py") if not (set(p.parts)&SKIP)]
    modules={module_name(p,root):p for p in files};edges={m:set() for m in modules};external=set();errors=[]
    for mod,path in modules.items():
        try:tree=ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
        except (OSError,SyntaxError,UnicodeError) as e:errors.append({"file":str(path),"error":str(e)});continue
        package=mod if path.name=="__init__.py" else mod.rpartition(".")[0]
        for node in ast.walk(tree):
            names=[]
            if isinstance(node,ast.Import):names=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom):
                base=node.module or ""
                if node.level:
                    bits=package.split(".") if package else []
                    keep=max(0,len(bits)-node.level+1)
                    base=".".join(bits[:keep]+([base] if base else []))
                names=[base] if base else []
                names += [base+"."+a.name for a in node.names if base and a.name!="*"]
            for name in names:
                match=next((x for x in modules if name==x or name.startswith(x+".")),None)
                if match:edges[mod].add(match)
                elif name and not name.startswith("."):external.add(name.split(".")[0])
    cycles=[];visiting=[];done=set()
    def visit(node):
        if node in visiting:
            cyc=visiting[visiting.index(node):]+[node]
            key=tuple(cyc)
            if key not in cycles:cycles.append(key)
            return
        if node in done:return
        visiting.append(node)
        for nxt in sorted(edges[node]):visit(nxt)
        visiting.pop();done.add(node)
    for node in sorted(edges):visit(node)
    return {"modules":sorted(modules),"edges":{k:sorted(v) for k,v in edges.items()},"external":sorted(external),"cycles":[list(x) for x in cycles],"errors":errors}
def mermaid(data):
    lines=["graph TD"]
    for node in data["modules"]:lines.append('  "'+node+'"')
    for src,targets in data["edges"].items():
        for dst in targets:lines.append('  "'+src+'" --> "'+dst+'"')
    return "\\n".join(lines)+"\\n"
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("path",nargs="?",default=".");p.add_argument("--json",action="store_true");p.add_argument("--mermaid",metavar="FILE");a=p.parse_args()
    root=Path(a.path)
    if not root.is_dir():p.error("path must be a directory")
    r=scan(root)
    if a.mermaid:Path(a.mermaid).write_text(mermaid(r),encoding="utf-8")
    if a.json:print(json.dumps(r,indent=2));return
    print(f"Modules: {len(r['modules'])} | external roots: {len(r['external'])} | cycles: {len(r['cycles'])} | parse errors: {len(r['errors'])}")
    for cyc in r["cycles"]:print("CYCLE: "+" -> ".join(cyc))
    if r["external"]:print("External imports: "+", ".join(r["external"]))
    for e in r["errors"]:print("ERROR:",e["file"],e["error"])
if __name__=="__main__":main()
