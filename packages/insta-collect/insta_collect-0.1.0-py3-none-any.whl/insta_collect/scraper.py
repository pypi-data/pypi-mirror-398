from playwright.sync_api import sync_playwright
import json
import time
import random

def get_post_details(page, url):
    """
    Mengambil detail post dengan strategi berlapis (Selectors -> Meta Tags)
    """
    data = {
        "caption": None,
        "username": None,
        "timestamp": None,
        "is_video": False # Flag untuk filtering video
    }
    
    try:
        print(f"   [..] Visiting: {url}")
        page.goto(url, wait_until="domcontentloaded")
        
        if "login" in page.url:
            print("   [!] Terlempar ke halaman Login. Skip.")
            return data

        try:
            page.wait_for_selector("article", timeout=5000)
        except:
            pass 


        try:
            meta_desc = page.locator('meta[property="og:description"]').get_attribute("content")
            if meta_desc:
                if ": " in meta_desc:
                    parts = meta_desc.split(": ", 1)
                    if len(parts) > 1:
                        raw_caption = parts[1].strip().strip('"').strip("'")
                        data["caption"] = raw_caption
        except:
            pass


        try:
            meta_title = page.locator('meta[property="og:title"]').get_attribute("content")
            if meta_title and "(@" in meta_title:
                start = meta_title.find("(@") + 2
                end = meta_title.find(")", start)
                data["username"] = meta_title[start:end]
        except:
            pass

        if not data["caption"]:
            try:
                selectors = ["h1", "span._aacl", "div[data-testid='post-comment-root'] span"]
                for sel in selectors:
                    if page.locator(sel).count() > 0:
                        text = page.locator(sel).first.inner_text()
                        if text:
                            data["caption"] = text
                            break
            except:
                pass

        if not data["username"]:
            try:
                # Cari link profil di dalam header yang memiliki role='link'
                username_element = page.locator("header a[role='link']").first 
                if username_element.count() > 0:
                    data["username"] = username_element.inner_text()

                    if not data["username"]:
                        href = username_element.get_attribute('href')
                        if href:
                             data["username"] = href.strip('/').split('/')[-1]
            except:
                pass


        try:
            time_el = page.locator("time").first
            if time_el.count() > 0:
                data["timestamp"] = time_el.get_attribute("datetime")
        except:
            pass


        try:
            # Jika elemen video atau Reels container ada, set is_video = True
            if page.locator("video").count() > 0 or page.locator("div[role='presentation'][tabindex='-1']").count() > 0:
                data["is_video"] = True
        except:
            pass

    except Exception as e:
        print(f"   [!] Error scraping details: {e}")

    return data

def scrape_hashtag(hashtag, limit=10, cookies_file=None):
    results = []
    photo_results = [] 

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        if cookies_file:
            try:
                with open(cookies_file, "r") as f:
                    cookies = json.load(f)
                    context.add_cookies(cookies)
                    print(f"[INFO] Loaded cookies")
            except:
                pass

        page = context.new_page()


        print(f"[1/2] Scanning hashtag #{hashtag}...")
        url = f"https://www.instagram.com/explore/tags/{hashtag}/"
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(3)

        collected_links = set()
        
        while len(collected_links) < limit * 1.5: 
            nodes = page.locator("a[href*='/p/']").all()
            
            for node in nodes:
                href = node.get_attribute("href")
                if href:
                    full_url = f"https://www.instagram.com{href}"
                    collected_links.add(full_url)
                    if len(collected_links) >= limit * 1.5:
                        break
            
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1.5)

        print(f"[INFO] Berhasil dapat {len(collected_links)} link. Sekarang ambil detail...")


        for index, link in enumerate(collected_links):
            print(f"[2/2] Scraping {index+1}/{len(collected_links)}: {link}")
            
            details = get_post_details(page, link)
            

            post_data = {
                "url": link,
                "caption": details["caption"],
                "username": details["username"],
                "timestamp": details["timestamp"],
                "is_video": details["is_video"], # Simpan flag video
                "source_tag": hashtag
            }
            results.append(post_data)
        
        browser.close()


    print(f"[3/3] Mulai filtering hasil (Hanya ambil foto)...")
    for post in results:

        if not post["is_video"] and len(photo_results) < limit:
            # Hapus flag is_video dari output akhir
            del post["is_video"]
            photo_results.append(post)

    print(f"[DONE] Total Foto yang diambil setelah filter: {len(photo_results)} dari {limit} target.")
    return photo_results
