import asyncio
import os
from playwright.async_api import async_playwright
import time
import random
from dotenv import load_dotenv
from utils.post_contents import GROUP_IDS, CONTRACT, MESSAGES
from utils.helper_functions import get_images_by_room, get_rooms_name, format_time
import datetime

IMAGE_PATH = "./images" # Image directory
 
class FacebookAutoPoster:
    def __init__(self, group_ids, contract, message, rooms_images=None):
        """
        Initialize the Facebook Auto Poster
        """
        load_dotenv()

        self.base_url = "https://www.facebook.com"
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.group_ids = group_ids
        self.contract = contract
        self.message = message or []
        self.rooms_images = rooms_images or [] # Its value is [List[List[str]]]

    async def run(self):
        """
        Main method to run the Facebook Auto Poster
        """
        print("Starting Facebook Auto Poster...")
        start = datetime.datetime.now()
        session_file = "facebook_state.json"
        use_existing_session = os.path.exists(session_file)
         
        async with async_playwright() as p:
            # Launch the browser
            browser = await p.chromium.launch(
                headless=False,  # Set to True in production
                # slow_mo=1000  # Slow down operations for visibility during testing
            )
            context = await browser.new_context(
                storage_state=session_file if use_existing_session else None,
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
            )
            page = await context.new_page()

            try:
                # ========================== Login codes =================================
                # Login to Facebook
                print("Logging into Facebook...")
                await page.goto(self.base_url)

                try: # Accept cookies if prompted
                    cookie_button = await page.wait_for_selector(
                        '[data-testid="cookie-policy-dialog"] button[data-testid="cookie-policy-manage-dialog-accept-button"]',
                        timeout=5000
                    )
                    if cookie_button:
                        await cookie_button.click()
                except Exception:
                    print("No cookie prompt detected, continuing...")
                
                try:
                    email_field = await page.wait_for_selector("#email", timeout=3000)
                    if email_field:
                        await page.fill("#email", self.email)
                        time.sleep(1)
                        await page.fill("#pass", self.password)
                        time.sleep(1)
                        await page.click("button[name='login']")

                        # Save session state
                        await context.storage_state(path="facebook_state.json")
                        print("Successfully logged in!, New session saved! =============================")
                except Exception as e:
                    print(f"Already logged in using saved session")
                    
                # ========================== End Login codes =================================
                for number_of_rooms in range(len(self.rooms_images)):
                    print(f"\n***** Posting room {sorted(get_rooms_name(IMAGE_PATH))[number_of_rooms]} *****")

                    for i, group_id in enumerate(self.group_ids):
                        print(f"    Posting to group ID: {group_id} || from {i+1} of {len(self.group_ids)} =============================")

                        # ============ Add waiting to mimic humans behavior =============
                        # Add this before any navigation
                        await page.wait_for_timeout(random.randint(2000, 4000))
                        # Scroll the page occasionally
                        await page.mouse.wheel(0, random.randint(300, 700))
                        await page.wait_for_timeout(random.randint(1000, 3000))
                        # ============ End Add waiting to mimic humans behavior =============
                        
                        # Navigate to the group
                        await page.goto(f"{self.base_url}/groups/{group_id}")

                        # Random delay to mimic human behavior
                        await asyncio.sleep(random.uniform(2, 5))
                        
                        try: # Try, In case reach post pending limit
                            # Click on the post creation area
                            post_box = page.locator('div[data-pagelet="GroupInlineComposer"]')
                            await post_box.get_by_role("button", name="เขียนอะไรสักหน่อย").click()
                            
                            # Upload images if provided
                            if self.rooms_images and len(self.rooms_images) > 0:
                                # Click on the photo/video button
                                photo_button = page.locator('div[role="button"][aria-label="รูปภาพ/วิดีโอ"]')
                                await photo_button.click()
                                
                                # Get the file input element and upload the images
                                file_input =  page.locator("form").filter(has_text="สร้างโพสต์").locator("input[type=\"file\"]")
                                
                                # Verify image paths exist
                                valid_image_paths = []
                                for img_path in self.rooms_images[number_of_rooms]:
                                    if os.path.exists(img_path):
                                        valid_image_paths.append(img_path)
                                    else:
                                        print(f"        Warning: Image file not found: {img_path}")
                                
                                if valid_image_paths:
                                    print(f"        Uploading {len(self.rooms_images[number_of_rooms])} images...")
                                    await file_input.set_input_files(valid_image_paths)
                                    await asyncio.sleep(2)
                                    print("        Images uploaded successfully!")
                           
                            # Type the message
                            await asyncio.sleep(1)
                            post_text_div = page.locator("form").filter(has_text="สร้างโพสต์").locator("div[role='presentation']")
                            post_text_area = post_text_div.locator('div[contenteditable="true"][role="textbox"]')
                            await post_text_area.click()
                            await post_text_area.fill(sorted(self.message)[number_of_rooms] + self.contract)
                            
                            # Click the post button
                            post_button = page.locator('div[role="button"][aria-label="โพสต์"]')
                            await post_button.click()
                            
                            # Wait for the post to be published
                            await asyncio.sleep(13)
                            print(f"        Successfully posted to group {group_id}!")
                            
                            # Random delay between groups
                            await asyncio.sleep(random.uniform(3, 5))
                        except Exception as e:
                            print(f"Reached pending posts limit!!! : {e}")
                
                print("All posts have been published successfully! ================================")
                
            except Exception as e:
                print(f"An error occurred during execution: {e}")
            finally:
                # Close the browser
                duration = datetime.datetime.now() - start
                await browser.close()
                print(f"Browser closed. Process completed in {format_time(duration)} hour.")

async def main():
    """
    usage of the FacebookAutoPoster class
    """
    poster = FacebookAutoPoster(
        group_ids=GROUP_IDS,
        contract=CONTRACT,
        message=MESSAGES,
        rooms_images=get_images_by_room(IMAGE_PATH)
    )
    await poster.run()

if __name__ == "__main__":
    asyncio.run(main())