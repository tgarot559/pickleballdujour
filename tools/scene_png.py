"""Render each tip's situation diagram to PNG (used by the RSS feed, the newsletter and social previews).
Usage: python3 tools/scene_png.py [--all]   (default: only missing files)"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scenes
from content.tips_fr import TIPS as TFR
from content.tips_en import TIPS as TEN
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "img", "scenes")

async def main():
    from playwright.async_api import async_playwright
    jobs = []
    for i, t in enumerate(TFR):
        for lang, tip in (("fr", t), ("en", TEN[i])):
            f = os.path.join(OUT, f"{t[0]}-{lang}.png")
            if "--all" in sys.argv or not os.path.exists(f):
                jobs.append((f, scenes.svg(t[0], lang, tip[1], tip[2])))
    if not jobs:
        print("nothing to render"); return
    async with async_playwright() as p:
        kw = {"executable_path": "/usr/bin/google-chrome"} if os.path.exists("/usr/bin/google-chrome") else {}
        b = await p.chromium.launch(**kw)
        pg = await b.new_page(device_scale_factor=2)
        for f, s in jobs:
            await pg.set_content(f'<html><head><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap" rel="stylesheet"></head><body style="margin:0;background:#fff"><div id="s" style="width:300px;display:inline-block">{s}</div></body></html>')
            await pg.wait_for_timeout(150)
            await (await pg.query_selector("#s svg")).screenshot(path=f, omit_background=True)
        await b.close()
    print(len(jobs), "rendered")
asyncio.run(main())
