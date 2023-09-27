from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import PySimpleGUI as sg
import requests, sys, os, time

#PARALLELIZE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# Define a function to scrape scientific articles
def scrape(base_site, search_selector, article_selector, next_page_selector, pdf_container_selector):
    download_folder = 'downloads'

    # Check if a search term is provided as a command-line argument, otherwise prompt the user
    search_term = sys.argv[1] if len(sys.argv) == 2 else None
    if not search_term:
        search_term = sg.popup_get_text("Enter Search Term:", title="Webscraper Search Term")
    if not search_term:
        raise SystemExit()


    # Perform the initial search and get the results URL
    url = perform_search(base_site, search_term,  search_selector)

    # Create the download folder if it doesn't exist
    if not os.path.exists(download_folder):
        os.mkdir(download_folder)

    i = 0
    while True:
        print(url)
        html_text = get_data(url)

        # Iterate through the articles on the current page
        for art_link in get_articles(html_text, base_site, article_selector):
            i += 1
            art_name = get_article_name(art_link)
            print(i, art_name)
            download_pdf(art_link, art_name, base_site, download_folder, pdf_container_selector)

        # Get the URL of the next page of results, if available
        url = get_next_page(html_text, next_page_selector)
        if not url:
            break
        else:
            url = base_site + url

# Function to retrieve HTML data from a URL using requests and BeautifulSoup
def get_data(url):
    data = requests.get(url)
    html_text = BeautifulSoup(data.text, 'html.parser')
    return html_text

# Function to get the URL of the next page of results
def get_next_page(html_text, next_page_selector):
    pagination = html_text.find(*next_page_selector[0])
    next_page_link = pagination.find(*next_page_selector[1])

    if not next_page_link:
        return None

    return str(next_page_link['href'])

# Function to extract article links from the current page
def get_articles(html_text, base_site, article_selector):
    articles_list = html_text.find(*article_selector[0])
    articles = articles_list.find_all(*article_selector[1])

    article_links = [article.find('a', {"class": "c-card__link u-link-inherit"})['href'] for article in articles]
    article_links = [link for link in article_links if link is not None]
    final_article_links = [base_site + link for link in article_links]

    return final_article_links

# Function to get the name of an article from its link
def get_article_name(art_link):
    page_data = get_data(art_link)
    art_name = str(page_data.h1.contents[0]).replace("<i>", "").replace("</i>", "").replace("/", " ").replace("-", "")
    return art_name

# Function to download a PDF article
def download_pdf(art_link, art_name, base_site, download_folder, pdf_container_selector):
    page_data = get_data(art_link)
    download_button_div = page_data.find(*pdf_container_selector[0])
    if download_button_div and art_name is not None:
        download_button_link = download_button_div.find(*pdf_container_selector[1])['href']
        res = requests.get(base_site + download_button_link)

        if res.status_code == 200 and art_name is not None:
            pdf_path = os.path.join(download_folder, f"{art_name[:25]}.pdf")

            with open(pdf_path, 'wb') as pdf:
                pdf.write(res.content)
        else:
            print("FAILED TO DOWNLOAD")

# Function to perform a search and return the search results URL using Selenium
def perform_search(base_site, search_term, search_selector):
    # Use Selenium to perform a search and get the search results URL
    driver = webdriver.Chrome()  # You need to have ChromeDriver installed and in your PATH
    driver.maximize_window()
    driver.get(base_site)
    search_box = driver.find_element(By.CSS_SELECTOR, search_selector[0])
    search_box.click()
    search_box = driver.find_element(By.CSS_SELECTOR, search_selector[1])
    search_box.send_keys(search_term)
    search_box.send_keys(Keys.RETURN)
    
    # Wait for the search results page to load
    #time.sleep(.1)
    
    # Get the current URL, which is the search results URL
    search_results_url = driver.current_url
    driver.quit()
    
    return search_results_url


# Define journal-specific selectors (modify as needed)
nature_search_selector = ["a[role='button'][class='c-header__link']", "input[class='c-header__input'][id='keywords']"]
nature_article_selector = [['ul', {"class": "app-article-list-row"}], ['li', {"class": "app-article-list-row__item"}]]
nature_next_page_selector = ['ul[class="c-pagination"]', ['a', {"class": "c-pagination__link"}]]
nature_pdf_container_selector = [['div', {"class": "c-pdf-container"}] , ['a', {"class": "u-button u-button--full-width u-button--primary u-justify-content-space-between c-pdf-download__link"}]]

# Call the main scraping function for a specific journal (Nature.com in this example)
scrape('https://www.nature.com', nature_search_selector, nature_article_selector, nature_next_page_selector, nature_pdf_container_selector)
