import os
import json
import asyncio
from playwright.async_api import async_playwright
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import time
from utils.post_contents import GROUP_IDS, POSTS_URL
import random

class FacebookAutomation:
    def __init__(self, group_ids, headless: bool = False, session_file="facebook_state.json"):
        """
        Initialize the FacebookAutomation class.
        
        Args:
            headless: Whether to run browser in headless mode
            slow_mo: Slow down operations by this amount of milliseconds
        """
        load_dotenv()

        self.base_url = "https://www.facebook.com"
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.group_ids = group_ids
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.session_file = session_file
        self.use_existing_session = os.path.exists(self.session_file)
    
    async def start_browser(self):
        """Start the browser and create a new context."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        # Check if we have a stored session
        self.context = await self.browser.new_context(storage_state=self.session_file if self.use_existing_session else None)
        self.page = await self.context.new_page()
        
    async def login(self):
        """
        Login to Facebook
        """
        try:
            if not self.page:
                await self.start_browser()
            # ========================== Login codes =================================
            print("Logging into Facebook...")
            await self.page.goto(self.base_url)

            try: # Accept cookies if prompted
                cookie_button = await self.page.wait_for_selector(
                    '[data-testid="cookie-policy-dialog"] button[data-testid="cookie-policy-manage-dialog-accept-button"]',
                    timeout=3000
                )
                if cookie_button:
                    cookie_button.click()
            except Exception:
                print("No cookie prompt detected, continuing...")
            
            try:
                email_field = await self.page.wait_for_selector("#email", timeout=3000)
                if email_field:
                    await self.page.fill("#email", self.email)
                    time.sleep(1)
                    await self.page.fill("#pass", self.password)
                    time.sleep(1)
                    await self.page.click("button[name='login']")

                    # Save session state
                    await self.context.storage_state(path=self.session_file)
                    print("Successfully logged in!, New session saved! =============================")
            except Exception as e:
                print(f"Already logged in using saved session")
        except Exception as e:
            print(f"An error occurred during execution login method: {e}")
            return False
        return True
    
    async def save_info(self, post_link: str) -> Dict[str, Any]:
        """
        Extract images and content from a Facebook post.
        
        Args:
            post_link: URL of the Facebook post (permalink)
            
        Returns:
            Dict containing 'content' and 'images' from the post
        """
        if not self.page:
            await self.start_browser()

        # Navigate to the post
        await self.page.goto(post_link)
        await asyncio.sleep(random.uniform(1, 2))

        post_dialog = await self.page.query_selector("div[role='dialog'][aria-labelledby='«R2imjbsmipapd5aq»']")
        # Find and extract the post content
        content = ""
        try:
            try:
                see_more = await post_dialog.query_selector("div[role='button']:has-text('ดูเพิ่มเติม')")
                if see_more:
                    await see_more.click()
                    time.sleep(0.5)
            except Exception as e:
                print(f"Note: Could not expand 'See more' content: {e}")

            content_element = await post_dialog.query_selector("div[data-ad-comet-preview='message']")
            content = await content_element.inner_text() if content_element else ""
            if not content:
                content_div = await post_dialog.query_selector("div[data-ad-preview='message']")
                content = await content_div.inner_text() if content_div else ""
                if not content:
                    content_div = await post_dialog.query_selector("div[data-ad-rendering-role='story_message']")
                    content = await content_div.inner_text() if content_div else ""
            print(f"Content: {content} \n")   
        except Exception as e:
            print(f"Error extracting post data {e}")
            return None
        
        # Find and download images
        images_url = []
        try:
            found_images = await post_dialog.query_selector_all('img') # ("a[href*='/photo'][role='link']")
            print(f"Found images {len(found_images)} : {found_images}")
            # Download each image
            for idx, img in enumerate(found_images):
                print("For loop found images")
                try:
                    src = await img.get_attribute('src')
                    if src and src.startswith('http') and "emoji" not in src and "profile" not in src:
                            images_url.append(src)
                            print(f"Saved image: {src}")
                except Exception as e:
                    print(f"Error downloading image {idx}: {e}")
        except Exception as e:
            print(f"Error extracting images: {e}")
        
        return {
            "content": content,
            "images": images_url
        }
    
    # async def post_to_page(self, page_url: str, content: str, images: List[str] = None) -> bool:
    #     """
    #     Post content and images to a Facebook page.
        
    #     Args:
    #         page_url: URL of the Facebook page
    #         content: Text content to post
    #         images: List of image file paths to upload
            
    #     Returns:
    #         bool: True if posting was successful, False otherwise
    #     """
    #     if not self.page or not await self.is_logged_in():
    #         print("Not logged in. Please login first.")
    #         return False
            
    #     try:
    #         # Navigate to the page
    #         await self.page.goto(page_url)
    #         await self.page.wait_for_load_state("networkidle")
            
    #         # Find and click the post creation area
    #         create_post_selectors = [
    #             'div[aria-label="Create Post"]',
    #             'div[role="button"][aria-label="Create Post"]',
    #             'span:has-text("Create Post")'
    #         ]
            
    #         clicked = False
    #         for selector in create_post_selectors:
    #             try:
    #                 await self.page.click(selector, timeout=5000)
    #                 clicked = True
    #                 break
    #             except:
    #                 continue
                    
    #         if not clicked:
    #             # Try another approach - look for the post composer
    #             await self.page.click('div[role="main"] div[role="button"]')
            
    #         # Wait for the post creation dialog
    #         await self.page.wait_for_selector('div[role="dialog"]', timeout=10000)
            
    #         # Fill in the post content
    #         await self.page.click('div[contenteditable="true"]')
    #         await self.page.fill('div[contenteditable="true"]', content)
            
    #         # Upload images if provided
    #         if images and len(images) > 0:
    #             # Look for the photo/video button
    #             photo_buttons = [
    #                 'div[aria-label="Photo/Video"]',
    #                 'div[aria-label="Add Photo or Video"]',
    #                 'input[type="file"][accept="image/*,image/heif,image/heic,video/*,video/mp4,video/x-m4v,video/x-matroska,.mkv"]'
    #             ]
                
    #             file_input = None
    #             for selector in photo_buttons:
    #                 try:
    #                     # Try to find the input element or click the button
    #                     if 'input' in selector:
    #                         file_input = await self.page.query_selector(selector)
    #                         if file_input:
    #                             break
    #                     else:
    #                         await self.page.click(selector)
    #                         # Now wait for file input to appear
    #                         file_input = await self.page.wait_for_selector('input[type="file"]', timeout=5000)
    #                         break
    #                 except:
    #                     continue
                
    #             if not file_input:
    #                 # Try to find any file input as a fallback
    #                 file_input = await self.page.query_selector('input[type="file"]')
                
    #             if file_input:
    #                 # Upload all images
    #                 await file_input.set_input_files(images)
    #                 # Wait for uploads to complete
    #                 await self.page.wait_for_load_state("networkidle")
    #             else:
    #                 print("Could not find file upload field")
            
    #         # Find and click the Post button
    #         post_button_selectors = [
    #             'div[aria-label="Post"]',
    #             'button:has-text("Post")',
    #             'div[role="button"]:has-text("Post")'
    #         ]
            
    #         for selector in post_button_selectors:
    #             try:
    #                 post_button = await self.page.wait_for_selector(selector, state="visible", timeout=5000)
    #                 if post_button:
    #                     await post_button.click()
    #                     break
    #             except:
    #                 continue
            
    #         # Wait for the post to be published
    #         await self.page.wait_for_load_state("networkidle")
    #         await asyncio.sleep(3)  # Additional wait to ensure the post is published
            
    #         print("Successfully posted to page!")
    #         return True
            
    #     except Exception as e:
    #         print(f"Error posting to page: {e}")
    #         return False
    
    async def post_to_groups(self, post_link: str, group_urls: List[str]) -> Dict[str, bool]:
        """
        Extract content from a post and share it to multiple Facebook groups.
        
        Args:
            post_link: URL of the source Facebook post
            group_urls: List of Facebook group URLs to post to
            
        Returns:
            Dict: Group URLs mapped to success status (True/False)
        """
        if not self.page or not await self.is_logged_in():
            print("Not logged in. Please login first.")
            return {group: False for group in group_urls}
        
        # First, extract the content and images from the source post
        post_info = await self.save_info(post_link)
        content = post_info["content"]
        images = post_info["images"]
        
        # Post to each group
        results = {}
        for group_url in group_urls:
            try:
                print(f"Posting to group: {group_url}")
                
                # Navigate to the group
                await self.page.goto(group_url)
                await self.page.wait_for_load_state("networkidle")
                
                # Find and click the post creation area
                create_post_selectors = [
                    'div[aria-label="Create Post"]',
                    'div[role="button"][aria-label="Create Post"]',
                    'span:has-text("Create Post")',
                    'div[role="button"]:has-text("What\'s on your mind")',
                    'div[role="main"] div[role="button"]'
                ]
                
                clicked = False
                for selector in create_post_selectors:
                    try:
                        await self.page.click(selector, timeout=5000)
                        clicked = True
                        break
                    except:
                        continue
                
                if not clicked:
                    print(f"Could not find post creation area in group: {group_url}")
                    results[group_url] = False
                    continue
                
                # Wait for the post creation dialog
                await self.page.wait_for_selector('div[role="dialog"]', timeout=10000)
                
                # Fill in the post content
                await self.page.click('div[contenteditable="true"]')
                await self.page.fill('div[contenteditable="true"]', content)
                
                # Upload images if available
                if images and len(images) > 0:
                    # Look for the photo/video button
                    photo_buttons = [
                        'div[aria-label="Photo/Video"]',
                        'div[aria-label="Add Photo or Video"]',
                        'input[type="file"][accept="image/*,image/heif,image/heic,video/*,video/mp4,video/x-m4v,video/x-matroska,.mkv"]'
                    ]
                    
                    file_input = None
                    for selector in photo_buttons:
                        try:
                            if 'input' in selector:
                                file_input = await self.page.query_selector(selector)
                                if file_input:
                                    break
                            else:
                                await self.page.click(selector)
                                file_input = await self.page.wait_for_selector('input[type="file"]', timeout=5000)
                                break
                        except:
                            continue
                    
                    if not file_input:
                        file_input = await self.page.query_selector('input[type="file"]')
                    
                    if file_input:
                        await file_input.set_input_files(images)
                        await self.page.wait_for_load_state("networkidle")
                    else:
                        print(f"Could not find file upload field in group: {group_url}")
                
                # Find and click the Post button
                post_button_selectors = [
                    'div[aria-label="Post"]',
                    'button:has-text("Post")',
                    'div[role="button"]:has-text("Post")'
                ]
                
                posted = False
                for selector in post_button_selectors:
                    try:
                        post_button = await self.page.wait_for_selector(selector, state="visible", timeout=5000)
                        if post_button:
                            await post_button.click()
                            posted = True
                            break
                    except:
                        continue
                
                if not posted:
                    print(f"Could not find post button in group: {group_url}")
                    results[group_url] = False
                    continue
                
                # Wait for the post to be published
                await self.page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)  # Additional wait
                
                print(f"Successfully posted to group: {group_url}")
                results[group_url] = True
                
                # Add a delay between posting to groups to avoid rate limiting
                await asyncio.sleep(10)
                
            except Exception as e:
                print(f"Error posting to group {group_url}: {e}")
                results[group_url] = False
        
        return results
    
    async def close(self):
        """Close the browser and clean up."""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None


# Example usage
async def main():
    fb = FacebookAutomation(headless=False, group_ids=GROUP_IDS)
    
    # Login
    logged_in = await fb.login()
    
    if logged_in:
        for url in POSTS_URL:
            post_info = await fb.save_info(url)
            # print(f"Extracted content: {post_info['content'][:100]}...")
            print(f"Found {len(post_info['images'])} images")
            print(post_info)
        
        # Example: Post to a page
        # await fb.post_to_page(
        #     "https://www.facebook.com/your_page",
        #     post_info["content"],
        #     post_info["images"]
        # )
        
        # Example: Post to multiple groups
        # group_urls = [
        #     "https://www.facebook.com/groups/group1",
        #     "https://www.facebook.com/groups/group2"
        # ]
        # results = await fb.post_to_groups("https://www.facebook.com/permalink.php?story_fbid=12345&id=67890", group_urls)
        
        # for group, success in results.items():
        #     print(f"Posted to {group}: {'Success' if success else 'Failed'}")
    
    # Always close the browser when done
    await fb.close()

if __name__ == "__main__":
    asyncio.run(main())