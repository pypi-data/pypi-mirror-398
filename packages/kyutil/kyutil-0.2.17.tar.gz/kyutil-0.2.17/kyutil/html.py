# -*- coding: UTF-8 -*-
from playwright.sync_api import sync_playwright


def html_to_image(html_path, output_path="output.png", width=1920, height=1024):
    """使用前请先安装软件包，执行命令： playwright install """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(f"file://{html_path}")
        page.screenshot(path=output_path, full_page=True)
        browser.close()
