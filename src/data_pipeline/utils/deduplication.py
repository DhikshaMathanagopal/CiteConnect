def deduplicate_papers(papers):
    seen, unique = set(), []
    for p in papers:
        t = p.get("title", "").strip().lower()
        if t and t not in seen:
            seen.add(t)
            unique.append(p)
    return unique
