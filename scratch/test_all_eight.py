import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrape_jobs import (
    fetch_linkedin_playwright_jobs,
    fetch_bdjobs_jobs,
    fetch_indeed_bd_jobs,
    fetch_jobicy_jobs,
    fetch_remotive_jobs,
    fetch_remoteok_jobs,
    fetch_arbeitnow_jobs,
    fetch_weworkremotely_jobs,
)

print("=" * 60)
print("COMPREHENSIVE ALL-SOURCES TEST")
print("=" * 60)

# 1. BDjobs
print("\n[1/8] Testing BDjobs...")
bd = fetch_bdjobs_jobs(["react", "developer"], max_hours=192)
print(f" -> BDjobs found: {len(bd)} jobs")
for j in bd[:2]:
    print(f"    * {j['title']} at {j['company']} ({j['location']})")

# 2. Indeed BD
print("\n[2/8] Testing Indeed BD...")
ind = fetch_indeed_bd_jobs(["software developer"], max_hours=192)
print(f" -> Indeed BD found: {len(ind)} jobs")
for j in ind[:2]:
    print(f"    * {j['title']} at {j['company']} ({j['location']})")

# 3. WeWorkRemotely
print("\n[3/8] Testing WeWorkRemotely...")
wwr = fetch_weworkremotely_jobs(max_hours=192)
print(f" -> WeWorkRemotely found: {len(wwr)} jobs")
for j in wwr[:2]:
    print(f"    * {j['title']} at {j['company']} ({j['location']})")

# 4. Jobicy
print("\n[4/8] Testing Jobicy...")
jbc = fetch_jobicy_jobs("react", max_hours=192)
print(f" -> Jobicy found: {len(jbc)} jobs")
for j in jbc[:2]:
    print(f"    * {j['title']} at {j['company']}")

# 5. Remotive
print("\n[5/8] Testing Remotive...")
rem = fetch_remotive_jobs(max_hours=192)
print(f" -> Remotive found: {len(rem)} jobs")
for j in rem[:2]:
    print(f"    * {j['title']} at {j['company']}")

# 6. RemoteOK
print("\n[6/8] Testing RemoteOK...")
rok = fetch_remoteok_jobs("javascript", max_hours=192)
print(f" -> RemoteOK found: {len(rok)} jobs")
for j in rok[:2]:
    print(f"    * {j['title']} at {j['company']}")

# 7. Arbeitnow
print("\n[7/8] Testing Arbeitnow...")
arb = fetch_arbeitnow_jobs(max_hours=192)
print(f" -> Arbeitnow found: {len(arb)} jobs")
for j in arb[:2]:
    print(f"    * {j['title']} at {j['company']}")

# 8. LinkedIn
print("\n[8/8] Testing LinkedIn...")
li = fetch_linkedin_playwright_jobs([("React Developer", "Bangladesh")], timeframe="week")
print(f" -> LinkedIn found: {len(li)} jobs")
for j in li[:2]:
    print(f"    * {j['title']} at {j['company']} ({j['location']})")

print("\n" + "=" * 60)
print("TEST SUMMARY:")
print(f"BDjobs:         {len(bd)} jobs")
print(f"Indeed:         {len(ind)} jobs")
print(f"WeWorkRemotely: {len(wwr)} jobs")
print(f"Jobicy:         {len(jbc)} jobs")
print(f"Remotive:       {len(rem)} jobs")
print(f"RemoteOK:       {len(rok)} jobs")
print(f"Arbeitnow:      {len(arb)} jobs")
print(f"LinkedIn:       {len(li)} jobs")
print("=" * 60)
