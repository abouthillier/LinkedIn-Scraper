import pandas as pd
from linkedin_scraper import Person, actions, Company
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
import time, csv
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD

driver = webdriver.Chrome()
print("Logging in...")
actions.login(driver, LINKEDIN_EMAIL, LINKEDIN_PASSWORD)

def scrape_posts(company_url):

    # TODO Get the date of the most recently scraped post
    
    print("Scraping posts")
    driver.get(company_url)

    # Toggle the Recent posts view
    # driver.find_element(By.CSS_SELECTOR, 'button.sort-dropdown-trigger').click()
    # driver.find_element(By.CSS_SELECTOR, 'button.sort-dropdown-trigger div.artdeco-dropdown__content-inner:nth-child(2)').click()

    print("Scrolling to some preset point to force the infinite scroll")
    # Scroll to some preset point to force the infinite scroll
    SCROLL_PAUSE_TIME = 3
    last_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(2):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    print("Toggling the 'See more' button to show the full post descriptions")
    # Toggle the "See more" button to show the full post descriptions
    driver.find_element(By.CSS_SELECTOR, 'body').send_keys(Keys.CONTROL + Keys.HOME)
    connect_buttons = driver.find_elements(By.CSS_SELECTOR, '.feed-shared-inline-show-more-text__see-more-less-toggle')
    for connect_button in connect_buttons:
        connect_button.click()

    # redefine page source to reflect the latest DOM (after scrolling)
    src = driver.page_source
    soup = BeautifulSoup(src, 'lxml')
    posts_data = pd.DataFrame(columns=['post_date', 'post_text'])

    master_data = soup.find_all('div', {'class': 'feed-shared-update-v2'})
    print(f"Total number of posts found: {len(master_data)}")

    print("Processing posts...")
    # Iterate through each post
    for post in master_data:
        print("\n" + "="*50)
        print(f"Processing post {master_data.index(post) + 1} of {len(master_data)}")
        
        # get post date
        post_date = post.find('span', {'class': 'update-components-actor__sub-description'})
        if post_date:
            # date in format: "12 hours ago", "1 day ago", "1 week ago", "1 month ago", "1 year ago"
            post_date_content = post_date.select('span.visually-hidden')[0].get_text().strip()

            # convert post date to datetime object
            # The post_date_content is in a relative format like "12 hours ago", "1 day ago", etc
            # Need to parse this relative time and convert it to an actual datetime
            now = datetime.now()
            
            if "hours ago" in post_date_content:
                hours = int(post_date_content.split()[0])
                post_date_datetime = now - timedelta(hours=hours)
            elif "day ago" in post_date_content or "days ago" in post_date_content:
                days = int(post_date_content.split()[0]) 
                post_date_datetime = now - timedelta(days=days)
            elif "week ago" in post_date_content or "weeks ago" in post_date_content:
                weeks = int(post_date_content.split()[0])
                post_date_datetime = now - timedelta(weeks=weeks)
            elif "month ago" in post_date_content or "months ago" in post_date_content:
                months = int(post_date_content.split()[0])
                post_date_datetime = now - relativedelta(months=months)
            elif "year ago" in post_date_content or "years ago" in post_date_content:
                years = int(post_date_content.split()[0])
                post_date_datetime = now - relativedelta(years=years)
            else:
                print(f"Unhandled date format: {post_date_content}")
                post_date_datetime = None
            print(f"Post date: {post_date_datetime}")
        else:
            print("No date content found in this post")

        # Get post text
        post_text = post.find('div', {'class': 'update-components-text'})
        if post_text:
            post_text_content = post_text.get_text().strip()
            print("Post content:")
            print(post_text_content)
        else:
            print("No text content found in this post")

        if post_date_datetime and post_text_content:
            # add the post data to the posts_data dataframe
            posts_data.loc[len(posts_data)] = [post_date_datetime, post_text_content]
        
        print("="*50 + "\n")

    return posts_data

# TODO NEXT:
# TODO: parse the post date and convert it to a datetime object
# TODO: log all data to csv
# TODO: log all posts into a csv and only scrape new posts

# TODO: develop a keyword search to find posts that mention specific keywords

SLUGS = [
    "hencove-marketing-llc"
]

URLS = [f"https://www.linkedin.com/company/{slug}/posts/?feedView=all" for slug in SLUGS]

for url in URLS:
    posts_data = scrape_posts(url)


# CSV file path
csv_file_path = 'output.csv'

# write the posts data to the csv file
with open(csv_file_path, 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile)
    for index, row in posts_data.iterrows():
        csv_writer.writerow([row['post_date'], row['post_text']])





driver.quit()
