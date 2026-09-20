import os

file_path = "server.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# I want to replace the `Parallel multi-source fetch` block.
# Start marker: "# ── Parallel multi-source fetch"
# End marker: "print(f\">> Scraped {len(raw_target_jobs)} raw jobs"

start_str = "# ── Parallel multi-source fetch ───────────────────────────────────"
end_str = "print(f\">> Scraped {len(raw_target_jobs)} raw jobs"

start_idx = content.find(start_str)
end_idx = content.find(end_str)

if start_idx != -1 and end_idx != -1:
    new_code = """# ── Fetch using Apify ─────────────────────────────────────────────
            from scrape_jobs import fetch_jobs_via_apify, normalize_dedup
            all_raw_candidates = fetch_jobs_via_apify(loc_queries, timeframe=timeframe, location=loc_name, limit=50)

            print(f">> Fetched {len(all_raw_candidates)} raw candidates from Apify for '{loc_name}'")

            # ── Dedup across all sources and apply quality filters ─────────────
            raw_target_jobs = []
            target_seen = set()
            for item in all_raw_candidates:
                if is_within_timeframe(item.get("date_posted"), max_hours=max_hours) and is_tech_job(item.get("title", ""), item.get("description", "")):
                    u_key, t_key = normalize_dedup(item)
                    if (not u_key or u_key not in target_seen) and t_key not in target_seen:
                        if u_key:
                            target_seen.add(u_key)
                        target_seen.add(t_key)
                        raw_target_jobs.append(item)

            """
    
    new_content = content[:start_idx] + new_code + content[end_idx:]
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Successfully replaced server multi-source logic with Apify")
else:
    print("Markers not found")
