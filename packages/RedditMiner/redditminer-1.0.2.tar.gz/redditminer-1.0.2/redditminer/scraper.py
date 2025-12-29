import requests
import http.cookiejar
import time
from datetime import datetime, timezone

class RedditImageScraper:
    def __init__(self, cookie_file):
        self.cookie_file = cookie_file
        self.session = requests.Session()
        self.load_cookies()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

    def load_cookies(self):
        cj = http.cookiejar.MozillaCookieJar(self.cookie_file)
        cj.load(ignore_discard=True, ignore_expires=True)
        self.session.cookies = cj

    def get_subreddit_posts(self, subreddit, limit=100, sort='new', with_comment=False):
        print(f"\n📸 Extracting Images from r/{subreddit}...")
        print(f"   (Sort: {sort}, Target: {limit} posts)")
        posts_collected = []
        after = None
        while len(posts_collected) < limit:
            url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit=100"
            if after:
                url += f"&after={after}"
            response = self.session.get(url, headers=self.headers)
            if response.status_code != 200:
                if response.status_code == 429:
                    print("❌ Error: 429 (Too Many Requests) - You are being rate limited by Reddit.\n   Slowing down requests and retrying in 60 seconds...")
                    time.sleep(60)
                    continue  # Retry the same request after waiting
                elif response.status_code == 403:
                    print("❌ Error: 403 (Forbidden) - Access denied. Your cookies may be invalid, expired, or lack permission for this subreddit.")
                elif response.status_code == 401:
                    print("❌ Error: 401 (Unauthorized) - Authentication failed. Check your cookies.txt file.")
                elif response.status_code == 404:
                    print("❌ Error: 404 (Not Found) - The subreddit or resource could not be found.")
                else:
                    print(f"❌ Error: {response.status_code} - Unexpected HTTP error.")
                break
            data = response.json()
            children = data.get("data", {}).get("children", [])
            if not children:
                break
            for p in children:
                p_data = p.get("data", {})
                image_url = p_data.get("url", "")
                is_image = any(image_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])
                gallery_urls = []
                if "is_gallery" in p_data and p_data["is_gallery"]:
                    media_metadata = p_data.get("media_metadata", {})
                    for item_id in media_metadata:
                        s = media_metadata[item_id].get("s", {})
                        if "u" in s:
                            gallery_urls.append(s["u"].replace("&amp;", "&"))
                # Always keep both fields, at least one will be non-null if available
                if is_image or gallery_urls:
                    post = {
                        "title": p_data.get("title"),
                        "author": p_data.get("author"),
                        "created_utc": datetime.fromtimestamp(p_data.get("created_utc", 0), timezone.utc).isoformat(),
                        "permalink": f"https://www.reddit.com{p_data.get('permalink')}",
                        "image_url": image_url if is_image else None,
                        "gallery_images": gallery_urls if gallery_urls else None
                    }
                    # Fetch comments if requested
                    if with_comment:
                        permalink = p_data.get('permalink')
                        if permalink:
                            comments_url = f"https://www.reddit.com{permalink}.json?limit=1"
                            try:
                                comments_resp = self.session.get(comments_url, headers=self.headers)
                                if comments_resp.status_code == 200:
                                    comments_data = comments_resp.json()
                                    if len(comments_data) > 1:
                                        comment_list = []
                                        for c in comments_data[1].get("data", {}).get("children", []):
                                            c_data = c.get("data", {})
                                            if c.get("kind") == "t1" and c_data.get("author") != "AutoModerator":
                                                comment_list.append({
                                                    "author": c_data.get("author"),
                                                    "body": c_data.get("body"),
                                                    "score": c_data.get("score"),
                                                    "created_utc": datetime.fromtimestamp(c_data.get("created_utc", 0), timezone.utc).isoformat()
                                                })
                                        post["comments"] = comment_list
                                else:
                                    post["comments"] = []
                            except Exception as e:
                                post["comments"] = []
                    posts_collected.append(post)
                if len(posts_collected) >= limit:
                    break
            after = data.get("data", {}).get("after")
            if not after:
                break
            print(f"   ...found {len(posts_collected)} images so far...")
            time.sleep(1)
        return posts_collected[:limit]
