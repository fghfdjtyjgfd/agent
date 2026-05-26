from pprint import pprint
import re
import time
import os
import openpyxl
from datetime import datetime, timedelta
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
            "posts_count": 100,
            "days_limit": 5, # Number of days to consider a post as recent
            "old_post_tolerance": 5, # Number of old posts allowed before stopping
            "agent_author_path": ".//csv_files/facebook/agent_names_from_renter.xlsx",
            "renter_file_path": ".//csv_files/facebook/room_renter.xlsx",
            "seeker_file_path": ".//csv_files/facebook/room_seeker.xlsx",
            "raw_posts_path": ".//csv_files/facebook/raw_posts.xlsx",
            "group_ids": [
                "385144122582004", # D condo hype เช่าคอนโด หอ ย่าน ม.กรุงเทพ มธ และ ม รังสิต
                "2334522046872720", # หาห้องพักย่านรังสิต 100,000+ คน
                "275678356775719", # แนะนำหอ ม.เกษตร
                "3286381871678927", # หาคอนโดให้เช่า สะพานใหม่ เกษตร หลักสี่ ดอนเมือง บางเขน รัชโยธิน ติด Bts
                "tucondo",
                "374078016708868" # Owner Post เจ้าของปล่อยเช่าคอนโด 业主出租群
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
                email_field = page.wait_for_selector("input[name='email']", timeout=7000)
                if email_field:
                    # page.fill("input[name='email']", self.config['email'])
                    # time.sleep(1)
                    # page.fill("input[name='pass']", self.config['password'])
                    # time.sleep(1)
                    # page.click("div[aria-label='เข้าสู่ระบบ']")
                    time.sleep(20)
                    # Save session state
                    context.storage_state(path=self.session_file)
                    print("Successfully logged in!, New session saved! =============================")
            except Exception as e:
                print(f"Already logged in using saved session")
        except Exception as e:
            print(f"An error occurred during execution login method: {e}")
            return False
        return True

    def parse_post_date(self, aria_label: str) -> str:
        now = datetime.now()
        if not aria_label:
            return now.strftime("%d/%m/%Y")

        thai_months = {
            'มกราคม': 1, 'กุมภาพันธ์': 2, 'มีนาคม': 3, 'เมษายน': 4,
            'พฤษภาคม': 5, 'มิถุนายน': 6, 'กรกฎาคม': 7, 'สิงหาคม': 8,
            'กันยายน': 9, 'ตุลาคม': 10, 'พฤศจิกายน': 11, 'ธันวาคม': 12
        }

        full_date_match = re.search(r'(\d+)\s+(\S+)\s+(\d{4})', aria_label)
        no_year_date_match = re.search(r'(\d+)\s+(\S+)', aria_label)
        # weeks_match = re.search(r'(\d+)\s*สัปดาห์', aria_label)
        days_match = re.search(r'(\d+)\s*วัน', aria_label)
        # hours_match = re.search(r'(\d+)\s*ชั่วโมง', aria_label)
        # minutes_match = re.search(r'(\d+)\s*นาที', aria_label)

        if full_date_match:
            day = int(full_date_match.group(1))
            month_name = full_date_match.group(2)
            year = int(full_date_match.group(3))
            month = thai_months.get(month_name)
            if month:
                return f"{day:02d}/{month:02d}/{year}"
        elif no_year_date_match:
            day = int(no_year_date_match.group(1))
            month_name = no_year_date_match.group(2)
            month = thai_months.get(month_name)
            if month:
                return f"{day:02d}/{month:02d}/{now.year}"
        # elif weeks_match:
        #     return (now - timedelta(weeks=int(weeks_match.group(1)))).strftime("%d/%m/%Y")
        elif days_match:
            return (now - timedelta(days=int(days_match.group(1)))).strftime("%d/%m/%Y")
        # elif hours_match or minutes_match:
        #     return now.strftime("%d/%m/%Y")

        return now.strftime("%d/%m/%Y")

    def extract_post_data(self, post_element):
        try:
            try:
                see_more = post_element.query_selector("div[role='button']:has-text('ดูเพิ่มเติม')")
                if see_more:
                    see_more.click()
                    time.sleep(1)
            except Exception as e:
                print(f"Note: Could not expand 'See more' content: {e}")

            shared_author = None
            shared_author_element = post_element.query_selector_all("div[data-ad-rendering-role='profile_name']")
            if len(shared_author_element) >= 2:
                shared_author = shared_author_element[1].inner_text() if shared_author_element else None

            author_element = post_element.query_selector("div[data-ad-rendering-role='profile_name']") #("h4 span a, h4 a, h3 span a, h3 a")
            author_element = author_element.query_selector('a[href*="/groups/"][role="link"]') if author_element else None
            author = author_element.inner_text() if author_element else "Unknown"

            post_link = None
            post_date_str = datetime.now().strftime("%d/%m/%Y")  # fallback
            timestamp_element = post_element.query_selector("a[href*='/posts/'][role='link']")
            if timestamp_element:
                post_link = timestamp_element.get_attribute("href")
                aria_label = timestamp_element.get_attribute("aria-label")
                post_date_str = self.parse_post_date(aria_label)

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
                "date": post_date_str,
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
        csv_fields = ["date", "author", "shared_author", "content", "post_link", "post_id"]
        raw_posts_path = self.config["raw_posts_path"]
        os.makedirs(os.path.dirname(raw_posts_path), exist_ok=True)

        # Load existing workbook or create a new one
        if os.path.exists(raw_posts_path):
            wb = openpyxl.load_workbook(raw_posts_path)
            ws = wb.active
        else:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(csv_fields)

        original_tolerance = self.config["old_post_tolerance"]
        try:
            # ========================== End Login codes =================================
            for i, group_id in enumerate(self.config["group_ids"]):
                print(f"Scrapping to group ID: {group_id} || from {i+1} of {len(self.config["group_ids"])} groups =============================")

                # Navigate to the group
                page.goto(f"{self.config['base_url']}/groups/{group_id}")

                time.sleep(2)
                page.wait_for_selector("div[role='feed']")
                # time.sleep(2)

                posts = []
                last_height = page.evaluate("document.body.scrollHeight")
                agent_post_count = 1
                stop_scraping = False
                self.config["old_post_tolerance"] = original_tolerance

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

                        # Check date of post if it's older than specified days
                        post_date = datetime.strptime(post_data['date'], "%d/%m/%Y")
                        if post_date < datetime.now() - timedelta(days=self.config['days_limit']):
                            self.config["old_post_tolerance"] -= 1
                            if self.config["old_post_tolerance"] <= 0:
                                print(f"    Post is older than {self.config['days_limit']} days, stopping...")
                                stop_scraping = True
                                break

                        # Check post_id if it duplicated
                        if post_data and post_data['post_link']:
                            if any(p.get('post_link') == post_data['post_link'] for p in posts):
                                continue

                            posts.append(post_data)
                            ws.append([post_data[f] for f in csv_fields])
                            wb.save(raw_posts_path)
                            print(f"    Collected post {len(posts)}/{self.config['posts_count']}")
                
                    if stop_scraping:
                        break

                    page.evaluate("window.scrollBy(0, 800)")
                    time.sleep(5)

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
        finally:
            wb.save(raw_posts_path)

        return all_posts
 
    def process_posts(self, posts):
        fb_posts_df = pd.DataFrame(posts)

        # Optional: save raw data for debugging
        # fb_posts_df.to_csv("./csv_files/facebook/facebook_posts.csv")

        fb_posts_df = check_link_null(fb_posts_df)
        seeker_df, renter_df = seeker_renter_split(fb_posts_df)
        renter_df = add_status(renter_df)

        # Export new agent name list to excel
        agent_author = renter_df[renter_df['status'] == "agent"]['author'].value_counts()
        pd.Series(agent_author).to_excel(self.config['agent_author_path'])

        # Export processed data to excel
        seeker_df.to_excel(self.config['seeker_file_path'])
        renter_df.to_excel(self.config['renter_file_path'])

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
        