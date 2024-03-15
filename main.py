'''import requests
from dotenv import load_dotenv
import os

load_dotenv()
# Replace with your Crunchbase API key
API_KEY = os.getenv("CRUNCHBASE_API_KEY")

# Define the keyword to search for
keyword = "LLM Orchestration"

# Base URL for the Crunchbase API
url = f"https://api.crunchbase.com/v4/organizations?query={keyword}&user_key={API_KEY}"
print(url)
# Set headers with your API key
# headers = {"Authorization": f"Bearer {API_KEY}"}

# Send the GET request
response = requests.get(url)

# Check for successful response
if response.status_code == 200:
    # Parse the JSON data
    data = response.json()

    # Extract information about matching companies
    for company in data["data"]["items"]:
        print(f"Company Name: {company['properties']['name']}")
        # Access other company details using 'company['properties']' dictionary
        # Example: Website - company['properties']['website']
else:
    print("Error:", response.status_code, response.text)
'''

'''import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()

def search_bing(query):
    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {
        "Ocp-Apim-Subscription-Key": os.getenv("BING_API_KEY")
    }
    params = {
        "q": query,
        "count": 10  # Number of results to fetch
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx errors

        data = response.json()
        search_results = data.get('webPages', {}).get('value', [])

        return [result['url'] for result in search_results]
    except requests.exceptions.RequestException as e:
        print("Error fetching Bing search results:", e)
        return []

def main():
    query = input("Enter your search query: ")
    search_results = search_bing(query + " site:www.crunchbase.com/organization")

    if search_results:
        for idx, url in enumerate(search_results[:10], start=1):
            id = url[40:].split('/')[0]
            print(f"{idx}. {id}")
    else:
        print("No search results found.")


if __name__ == "__main__":
    main()'''

import requests
from dotenv import load_dotenv
import os

load_dotenv()
# Replace with your Crunchbase API key
API_KEY = os.getenv("CRUNCHBASE_API_KEY")


def search_bing(query):
    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {
        "Ocp-Apim-Subscription-Key": os.getenv("BING_API_KEY")
    }
    params = {
        "q": query,
        "count": 10  # Number of results to fetch
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx errors

        data = response.json()
        search_results = data.get('webPages', {}).get('value', [])

        return [result['url'] for result in search_results]
    except requests.exceptions.RequestException as e:
        print("Error fetching Bing search results:", e)
        return []


def get_company_info(url):
    # Extract organization ID from the URL
    organization_id = url[40:].split('/')[0]

    # Base URL for the Entity Lookup API
    base_url = f"https://api.crunchbase.com/api/v4/entities/organizations/{organization_id}?card_ids=founders,fields&field_ids=website,linkedin,short_description&user_key={API_KEY}"
    # print(base_url)

    try:
        # Send GET request with parameters
        response = requests.get(base_url)
        company_name = founder_name = founder_description = linkedin_url = website = description = funding_amt = funding_type = None
        # Check for successful response
        if response.status_code == 200:
            data = response.json()
            try:
                company_name = data["properties"]["identifier"]["value"]
                website = data["properties"]["website"]["value"]
                linkedin_url = data["properties"]["linkedin"]["value"]
                description = data["properties"]["short_description"]
                funding_amt = data['cards']['fields']['funding_total']['value_usd']
                funding_type = data['cards']['fields']['last_equity_funding_type']
                founder_name = data['cards']['founders'][0]['identifier']['value']
                founder_description = data['cards']['founders'][0]['description']
            except:
                pass

            return company_name, website, description, linkedin_url, founder_name, founder_description, funding_amt, funding_type
    except requests.exceptions.RequestException as e:
        print("Error:", e)

    return None


# Main
query = input("Enter your search query: ")
search_results = search_bing(query + " site:www.crunchbase.com/organization")

url_list = []
if search_results:
    for idx, url in enumerate(search_results[:10], start=1):
        url_list.append(url)
else:
    print("No search results found.")

# User input for the Crunchbase organization URL
# organization_url = input("Enter the Crunchbase organization URL: ")

for url in url_list:
    # Get founder name
    company_name, website, description, linkedin_url, founder_name, founder_description, funding_amt, funding_type = get_company_info(url)
    # print(id)
    print(company_name)
    print(f"Website: {website}")
    print(f"Description: {description}")
    print(f"Linkedin: {linkedin_url}")
    print(f"Funding: {funding_amt} USD, Type: {funding_type}")
    if founder_name:
        print(f"Founder Name: {founder_name}")
        print(f"Description: {founder_description}")
    else:
        print("Founder not found.")
    print()
