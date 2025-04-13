import time
import os
import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import pandas as pd
from utils.agent_names import agent_name_list, prefix_name, is_agent
from utils.agent_checker import check_link_null, seeker_renter_split, add_status

class FacebookAutoScrapper:
    def __init__(self, session_file="facebook_state.json", config=None):
        """
        Initialize FacebookScrapper with configuration
        """
        load_dotenv()
        
        self.config = {
            "base_url": "https://www.facebook.com",
            "email": os.getenv('EMAIL'),
            "password": os.getenv('PASSWORD'),
            "posts_count": 3,
            "agent_author_path": ".//csv_files/facebook/agent_names_from_renter.csv",
            "renter_file_path": ".//csv_files/facebook/room_renter.csv",
            "seeker_file_path": ".//csv_files/facebook/room_seeker.csv",
            "group_ids": [
                "1396145167522075",
                "1093378301215297",
                "417449789872854",
            ]
        }
        if config:
            self.config.update(config)

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.session_file = session_file
        self.use_existing_session = os.path.exists(self.session_file)

    def start_browser(self, headless=False):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.context = self.browser.new_context(
            storage_state=self.session_file if self.use_existing_session else None,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        )
        self.page = self.context.new_page()
        return self.page, self.context
    
    def close_browser(self):
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def login(self, page, context):
        """
        Login to Facebook
        """
        try:
            # ========================== Login codes =================================
            print("Logging into Facebook...")
            page.goto(self.config['base_url'])

            try: # Accept cookies if prompted
                cookie_button = page.wait_for_selector(
                    '[data-testid="cookie-policy-dialog"] button[data-testid="cookie-policy-manage-dialog-accept-button"]',
                    timeout=3000
                )
                if cookie_button:
                    cookie_button.click()
            except Exception:
                print("No cookie prompt detected, continuing...")
            
            try:
                email_field = page.wait_for_selector("#email", timeout=3000)
                if email_field:
                    page.fill("#email", self.config['email'])
                    time.sleep(1)
                    page.fill("#pass", self.config['password'])
                    time.sleep(1)
                    page.click("button[name='login']")

                    # Save session state
                    context.storage_state(path=self.session_file)
                    print("Successfully logged in!, New session saved! =============================")
            except Exception as e:
                print(f"Already logged in using saved session")
        except Exception as e:
            print(f"An error occurred during execution login method: {e}")
            return False
        return True

    def extract_post_data(self, post_element):
        try:
            try:
                see_more = post_element.query_selector("div[role='button']:has-text('ดูเพิ่มเติม')")
                if see_more:
                    see_more.click()
                    time.sleep(0.5)
            except Exception as e:
                print(f"Note: Could not expand 'See more' content: {e}")

            shared_author = None
            shared_author_element = post_element.query_selector_all("div[data-ad-rendering-role='profile_name']")
            if len(shared_author_element) >= 2:
                shared_author = shared_author_element[1].inner_text() if shared_author_element else None

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
                if not content:
                    content_div = post_element.query_selector("div[data-ad-rendering-role='story_message']")
                    content = content_div.inner_text() if content_div else ""

            post_id = post_element.evaluate("el => el.getAttribute('aria-describedby')")
            
            return {
                "date": datetime.datetime.now().strftime("%d/%m/%Y"),
                "author": author,
                "shared_author": shared_author,
                "content": content,
                "post_link": post_link,
                "post_id": post_id
            }
        except Exception as e:
            print(f"Error extracting post data {e}")
            return None
        

    def scrape_group_posts(self, page):
        all_posts = []
        # ========================== End Login codes =================================
        for i, group_id in enumerate(self.config["group_ids"]):
            print(f"Scrapping to group ID: {group_id} || from {i+1} of {len(self.config["group_ids"])} groups =============================")

            # Navigate to the group
            page.goto(f"{self.config['base_url']}/groups/{group_id}")

            # time.sleep(5)
            page.wait_for_selector("div[role='feed']")
            # time.sleep(2)

            posts = []
            last_height = page.evaluate("document.body.scrollHeight")
            agent_post_count = 1

            while len(posts) < self.config['posts_count']:
                post_elements = page.query_selector_all("div[role='article']")
                for post in post_elements:
                    if len(posts) >= self.config['posts_count']:
                        break
                        
                    post_data = self.extract_post_data(post)
                    if post_data['shared_author'] is not None:
                        if post_data['shared_author'].lower() in agent_name_list or is_agent(post_data['shared_author'], prefix_name):
                            print(f"    Found {agent_post_count} Agent's post: {post_data['shared_author']}")
                            agent_post_count += 1
                            continue
                    if post_data['author'].lower() in agent_name_list or is_agent(post_data['author'], prefix_name):
                        print(f"    Found {agent_post_count} Agent's post: {post_data['author']}")
                        agent_post_count += 1
                        continue
                    # Check post_id if it duplicated
                    if post_data and post_data['post_id']:
                        if any(p.get('post_id') == post_data['post_id'] for p in posts):
                            continue
                            
                        posts.append(post_data)
                        print(f"    Collected post {len(posts)}/{self.config['posts_count']}")
                
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

            all_posts.extend(posts)

        return all_posts
 
    def process_posts(self, posts):
        fb_posts_df = pd.DataFrame(posts)

        # Optional: save raw data for debugging
        # fb_posts_df.to_csv("./csv_files/facebook/facebook_posts.csv")

        fb_posts_df = check_link_null(fb_posts_df)
        seeker_df, renter_df = seeker_renter_split(fb_posts_df)
        renter_df = add_status(renter_df)

        # Export new agent name list to csv
        agent_author = renter_df[renter_df['status'] == "agent"]['author'].value_counts()
        pd.Series(agent_author).to_csv(self.config['agent_author_path'])

        # Export processed data to csv
        seeker_df.to_csv(self.config['seeker_file_path'])
        renter_df.to_csv(self.config['renter_file_path'])

    def run(self):
        """
        Main execution flow
        """
        try:
            page, context = self.start_browser(headless=False)
            login_success = self.login(page=page, context=context)
            if not login_success:
                print("Logging in failed !!!")
                return False
            posts = self.scrape_group_posts(page=page)
            self.process_posts(posts)
        finally:
            self.close_browser()

def main():
    scrapper = FacebookAutoScrapper()
    scrapper.run()

if __name__ == "__main__":
    main()
        