import time
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import pandas as pd
from utils.agent_names import agent_name_list, prefix_name, is_agent

load_dotenv()

URL = "https://www.facebook.com"
GROUP = "https://www.facebook.com/groups/1396145167522075/"
email = os.getenv('EMAIL')
password = os.getenv('PASSWORD')
POST_COUNT = 30

playwright = sync_playwright().start()
browser = playwright.chromium.launch(headless=False)
page = browser.new_page()

def login_facebook(page):
    page.goto(GROUP, wait_until='load')
    # time.sleep(100)
    page.fill("input[type='text']", email)
    try:
        page.fill("#«r5»", password)
    except:
        try:
            page.fill("#«rd»", password)
        except:
            print("Could not find email field")
            return False
    page.click("div[aria-label='Accessible login button']")
    try:
        print("Login successful")
        return True
    except:
        print("Login failed")
        return False
    
def extract_post_data(post_element):
    try:
        try:
            see_more = post_element.query_selector("div[role='button']:has-text('ดูเพิ่มเติม')")
            if see_more:
                see_more.click()
                time.sleep(0.5)
        except Exception as e:
            print(f"Note: Could not expand 'See more' content: {e}")

        author_element = post_element.query_selector("h4 span a, h4 a, h3 span a, h3 a")
        author = author_element.inner_text() if author_element else "Unknown"

        post_link = None
        try:
            timestamp_element = post_element.query_selector("a[href*='/posts/'][role='link']")
            if timestamp_element:
                post_link = timestamp_element.get_attribute("href")
        except:
            pass

        content_element = post_element.query_selector("div[data-ad-comet-preview='message']")
        content = content_element.inner_text() if content_element else ""
        if not content:
            content_div = post_element.query_selector("div[data-ad-preview='message']")
            content = content_div.inner_text() if content_div else ""

        post_id = post_element.evaluate("el => el.getAttribute('aria-describedby')")

        return {
            "author": author,
            "content": content,
            "post_link": post_link,
            "post_id": post_id
        }

    except Exception as e:
        print(f"Error extracting post data {e}")
        return None
    
def scrape_group_posts(page, post_count):
    time.sleep(10)
    page.wait_for_selector("div[role='feed']")
    time.sleep(2)

    posts = []
    agent_posts = []
    last_height = page.evaluate("document.body.scrollHeight")

    while len(posts) < post_count:
        post_elements = page.query_selector_all("div[role='article']")
        for post in post_elements:
            if len(posts) >= post_count:
                break
                
            post_data = extract_post_data(post)

            if post_data['author'] in agent_name_list or is_agent(post_data['author'], prefix_name):
                print("Agent's post")
                agent_posts.append(post_data)
                continue
            if post_data and post_data['post_id']:
                if any(p.get('post_id') == post_data['post_id'] for p in posts):
                    # print("Duplicated post_id")
                    continue
                    
                posts.append(post_data)
                print(f"Collected post {len(posts)}/{post_count}")
        
        page.evaluate("window.scrollBy(0, 800)")
        time.sleep(3)

        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            page.evaluate("window.scrollBy(0, 800)")
            time.sleep(2)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                print("Reached end of page before collecting requested number of posts")
                break

        last_height = new_height    
    return posts, agent_posts

def main():
    try:
        login = login_facebook(page=page)
        if not login:
            page.close()
            browser.close()
            playwright.stop()
            exit(1)
        posts, agent_posts = scrape_group_posts(page=page, post_count=POST_COUNT)
        facebook_posts_df = pd.DataFrame(posts)
        facebook_agent_posts_df = pd.DataFrame(agent_posts)

        facebook_posts_df.to_csv("./csv_files/facebook_posts.csv")
        facebook_agent_posts_df.to_csv("./csv_files/facebook_agent_posts_df.csv")
            
    finally:
        page.close()
        browser.close()
        playwright.stop()

if __name__ == "__main__":
    main()