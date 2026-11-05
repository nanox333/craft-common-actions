"""Print a PR's reviews, review threads and conversation from the GraphQL JSON, markup stripped."""
import json, re, sys

d = json.load(open(sys.argv[1], encoding="utf-8-sig"))["data"]["repository"]["pullRequest"]
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 1800


def clean(body):
    body = re.sub(r"(?s)<details>.*?</details>|<!--.*?-->|<[^>]+>", "", body or "")
    return re.sub(r"\n{3,}", "\n\n", body).strip()


def show(text, indent):
    return clean(text)[:LIMIT].replace("\n", "\n" + indent)


state = "draft" if d["isDraft"] else "ready"
print(d["title"], "|", d["state"], state, d["mergeStateStatus"], "head", d["headRefOid"][:7], "updated", d["updatedAt"])
print("\n=== REVIEWS")
for r in d["reviews"]["nodes"]:
    print("-", r["author"]["login"], r["state"], r["submittedAt"], (r["commit"] or {}).get("oid", "")[:7])
    print("  " + show(r["body"], "  "))
print("\n=== THREADS")
for t in d["reviewThreads"]["nodes"]:
    flag = "RESOLVED" if t["isResolved"] else "OPEN"
    if t["isOutdated"]:
        flag += " (outdated)"
    print(f"--- {flag} {t['path']}:{t['line']}")
    for c in t["comments"]["nodes"]:
        print("  >", c["author"]["login"], c["createdAt"], c["databaseId"])
        print("    " + show(c["body"], "    "))
print("\n=== CONVERSATION")
for c in d["comments"]["nodes"]:
    print("-", c["author"]["login"], c["createdAt"])
    print("  " + show(c["body"], "  "))
