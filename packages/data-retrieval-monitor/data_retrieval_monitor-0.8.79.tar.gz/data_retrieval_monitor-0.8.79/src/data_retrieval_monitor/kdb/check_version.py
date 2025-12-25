import sys
from collections import defaultdict, deque
from importlib.metadata import distribution, version, PackageNotFoundError
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.markers import default_environment
from packaging.version import Version

if len(sys.argv) < 2:
    print("Usage: python - <your_library_name>")
    raise SystemExit(2)

ROOT = canonicalize_name(sys.argv[1])
env = default_environment()
env["extra"] = ""  # base install (no extras)

def dist_requires(pkg_name):
    d = distribution(pkg_name)
    reqs = []
    for s in (d.requires or []):
        r = Requirement(s)
        if r.marker is None or r.marker.evaluate(env):
            reqs.append(r)
    return reqs

def installed_ver(pkg_name):
    try:
        return version(pkg_name)
    except PackageNotFoundError:
        return None

# Collect dependency closure + constraints (child -> list of (parent, Requirement))
parents = defaultdict(list)
seen = set()
q = deque([ROOT])

while q:
    parent = q.popleft()
    if parent in seen:
        continue
    seen.add(parent)

    try:
        reqs = dist_requires(parent)
    except PackageNotFoundError:
        continue

    for r in reqs:
        child = canonicalize_name(r.name)
        parents[child].append((parent, r))
        if child not in seen:
            q.append(child)

# Print direct requirements of ROOT
print(f"\nDirect requirements of {ROOT}:")
try:
    for r in dist_requires(ROOT):
        print("  ", str(r))
except PackageNotFoundError:
    print(f"  ERROR: {ROOT} is not installed in this environment.")
    raise SystemExit(1)

# Print exhaustive transitive list with installed version + all constraints + status
print(f"\nExhaustive dependency closure (installed version vs required constraints):")
all_deps = sorted([p for p in seen if p != ROOT])

def status(installed, reqs):
    if installed is None:
        return "MISSING"
    v = Version(installed)
    for _, r in reqs:
        if r.specifier and not r.specifier.contains(v, prereleases=True):
            return "VIOLATES"
    return "OK"

for dep in all_deps:
    inst = installed_ver(dep)
    req_list = parents.get(dep, [])
    st = status(inst, req_list)

    print(f"\n{dep}=={inst if inst else 'NOT INSTALLED'}  [{st}]")
    if req_list:
        for parent, r in sorted(req_list, key=lambda x: x[0]):
            spec = str(r.specifier) if str(r.specifier) else "any"
            print(f"  required by {parent}: {spec}")
    else:
        print("  (no recorded parent constraint)")

# Also highlight only the problems
problems = []
for dep in all_deps:
    inst = installed_ver(dep)
    req_list = parents.get(dep, [])
    st = status(inst, req_list)
    if st in ("MISSING", "VIOLATES"):
        problems.append((dep, inst, st, req_list))

print("\n\n=== Problems only ===")
if not problems:
    print("None detected for this library's dependency closure.")
else:
    for dep, inst, st, req_list in problems:
        print(f"\n{dep}=={inst if inst else 'NOT INSTALLED'}  [{st}]")
        for parent, r in sorted(req_list, key=lambda x: x[0]):
            spec = str(r.specifier) if str(r.specifier) else "any"
            print(f"  required by {parent}: {spec}")