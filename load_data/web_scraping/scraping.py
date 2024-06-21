import requests
from bs4 import BeautifulSoup
import re
import json

def soupify(url):
    """
    Parse the HTML and return a Beautiful Soup object with parsed content
    """
    response = requests.get(url)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')

    return soup

def get_read_more_links(soup):
    """
    Take in some parsed soup and return a list with the URLs
    that are attached "Read More" links
    """
    read_more_links = []
    # Look at all the <a> tags
    for a_tag in soup.find_all('a', href=True):
        # See if the given <a> tag is followed by <span>Read More</span>
        span_tag = a_tag.find('span', string='Read More')
        # If said span tag exists, create the URL and add to return list
        if span_tag:
            read_more_links.append('https://centerforautism.com' + a_tag['href'])
    # filter out unnecessary links
    excluded_links = ['https://centerforautism.com/parent-resources/insurance-accepted/']
    read_more_links = [link for link in read_more_links if link not in excluded_links]

    return read_more_links


soup = soupify(url="https://centerforautism.com/parent-resources/new-diagnosis/")
read_more_links = get_read_more_links(soup)

# Instantiate a list to save the results to
document_list = list()

# Get regex to find the relevant <div>
pattern = re.compile(r'elementor-element .* elementor-widget-text-editor')

# Iterate through the links, extract the text, load into a dictionary, and append
# to output list
for link in read_more_links:
    # Instantiate a dict to organize the results
    document_dict = dict()

    soup = soupify(link)
    # Find the div with the relevant text
    content_div = soup.find('div', class_=lambda x: x and pattern.match(x))

    title_text = ''
    article_text = ''

    # Find and concatenate the first h2 and h3 tags
    first_h2 = content_div.find('h2')
    if first_h2:
        title_text += first_h2.get_text(separator=' ', strip=True) + ' '
        
    first_h3 = content_div.find('h3')
    if first_h3:
        title_text += first_h3.get_text(separator=' ', strip=True)

    # Extract the article text
    for tag in content_div.find_all():
        article_text += tag.get_text(separator=' ', strip=True) + ' '

    # Strip any extra whitespace from the text
    title_text = title_text.strip()
    article_text = article_text.strip()

    # Write results to dict
    document_dict["url"] = link
    document_dict["title"] = title_text
    document_dict["article"] = article_text

    # Append to the output list
    document_list.append(document_dict)

with open('scraped_autism_articles.json', mode='w') as file:
    json.dump(document_list, file)





