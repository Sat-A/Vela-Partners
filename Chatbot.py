from openai import OpenAI
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set up your Bing Search API key
bing_api_key = os.getenv("BING_API_KEY")


def wide_search(query):
    query += " site:angel.co OR site:pitchbook.com OR site:cbinsights.com OR " \
             "site:techcrunch.com OR site:producthunt.com OR site:venturebeat.com OR " \
             "site:startupgrind.com OR site:blog.ycombinator.com"
    url = f"https://api.bing.microsoft.com/v7.0/search?q={query}&count=6"
    headers = {"Ocp-Apim-Subscription-Key": bing_api_key}
    response = requests.get(url, headers=headers)
    data = response.json()
    return data['webPages']['value']


def crunchbase_search(query):
    query += " site:www.crunchbase.com/organization"
    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {
        "Ocp-Apim-Subscription-Key": os.getenv("BING_API_KEY")
    }
    params = {
        "q": query,
        "count": 6  # Number of results to fetch
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


def extract_company_names(results):
    companies = []
    for result in results:
        url = result['url']
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        # You may need to customize this based on the structure of the website
        for tag in soup.find_all(['h1', 'h2', 'h3']):
            text = tag.get_text()
            companies.append(text.strip())
    return companies


# Function to get the response from ChatGPT
def get_chat_response(prompt, pre_prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system",
                   "content": "You are a research assistant application whose purpose is to provide results for queries"
                              "to the user. You only provide the answers without any explanations and introductions."
                              "For all the questions asked, return only the required values without other text."},
                  {"role": "user", "content": f"{pre_prompt} {prompt}"}],
        max_tokens=500
    )
    return response.choices[0].message.content


def find_crunchbase_url(company_names, api_key):
    search_results = {}

    for company_name in company_names:

        # Make a request to the Bing Web Search API for Crunchbase URL
        response_crunchbase = requests.get(
            "https://api.bing.microsoft.com/v7.0/search",
            params={"q": company_name + "company crunchbase" + " site:crunchbase.com/organization"},
            headers={"Ocp-Apim-Subscription-Key": api_key}
        )

        # Check if the request for Crunchbase URL was successful
        if response_crunchbase.status_code == 200:
            # Extract the top search result URL
            data = response_crunchbase.json()
            if "webPages" in data and "value" in data["webPages"] and data["webPages"]["value"]:
                crunchbase_url = data["webPages"]["value"][0]["url"]
            else:
                crunchbase_url = None
        else:
            crunchbase_url = None

        search_results[company_name] = crunchbase_url

    return search_results


def get_company_info(url):
    # Extract organization ID from the URL
    organization_id = url[40:].split('/')[0]
    API_KEY = os.getenv("CRUNCHBASE_API_KEY")
    # Base URL for the Entity Lookup API
    base_url = f"https://api.crunchbase.com/api/v4/entities/organizations/{organization_id}?card_ids=founders,fields&field_ids=website,linkedin,short_description&user_key={API_KEY}"

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


def Output_format(crunchbase_url):
    company_name, website, description, linkedin_url, founder_name, founder_description, funding_amt, funding_type = get_company_info(crunchbase_url)
    print(company_name)
    print(f"Website: {website}")
    gpt_description = get_chat_response(description, "Given is a description of a company. Rewrite this in up to 10"
                                                     "words, ensuring maximum information is retained: ")
    print(f"Description: {gpt_description}")
    print(f"Linkedin: {linkedin_url}")
    print(f"Funding: {funding_amt} USD, Type: {funding_type}")
    if founder_name:
        print(f"Founder Name: {founder_name}")
        gpt_founder_description = get_chat_response(founder_description, "Given is a description of the founder of a "
                                                                         "company. Rewrite this in 2 sentences, highlighting"
                                                                         "educational details if any mentioned. Return"
                                                                         "the description unchanged if you cannot "
                                                                         "rewrite it. Here is the description: ")
        print(f"Description: {gpt_founder_description}")
    else:
        print("Founder not found.")
    print()


# Main
user_input = input("Desired business sector: ")
search_query = get_chat_response(user_input, "Below, the user will enter a business sector. Use this business sector "
                                             "to generate an efficient bing search query to return the names of "
                                             "seed, pre-seed, and series-A startups (these are financial terms not"
                                             "agricultural) operating within this business "
                                             "sector. Make the output bing query precise and to the point for "
                                             "optimal results. Return only the simple search query, do not use advanced"
                                             "search filters such as 'site:', 'or', quotations, etc."
                                             "Do not add any other text to the output other than"
                                             "the final search query.")

updated_search_query = get_chat_response(search_query, f"Given is a simple search query generated for the input:"
                                                       f"{user_input}. If you think this search query is relevant to"
                                                       f"the user input, simply return the search query again. If not,"
                                                       f"make minor modifications and return the new search query. Do"
                                                       f"not make unnecessary changes. Search query:")
# print(search_query)
# print(updated_search_query)
results = wide_search(updated_search_query)
company_names = extract_company_names(results)
format_company_names_1 = get_chat_response(company_names, "Following is a block of text containing web-scraped data on"
                                                          "seed, pre-seed and series-A startup companies. From this text,"
                                                          "filter out only company names from the text and return the "
                                                          "names of top 5 startup companies in the form of a list."
                                                          "Remember, we are only looking for early stage startups and not for "
                                                          "big companies so filter them out from your response. The response"
                                                          "should be in the form of a python list. Your output should only"
                                                          " contain the list in plain text form, in the format:"
                                                          "[company_name_1, company_name_2, company_name_3,...]")

format_company_names = get_chat_response(format_company_names_1,
                                         "Given is a list that should contain the names of seed,"
                                         "pre-seed and series A startup companies. Remove anything from"
                                         "this list that does not meet this criteria, keeping only"
                                         "company names. Do not make unnecessary changes, returning the"
                                         "list in the same format as the output. This is the list:")
print("Searching the wider internet\n")

print(format_company_names)
format_company_names = eval(format_company_names)
wider_list = find_crunchbase_url(format_company_names, bing_api_key)

for url in wider_list:
    Output_format(wider_list[url])

print("Crunchbase results:\n")
search_results = crunchbase_search(search_query)

crunchbase_list = []
if search_results:
    for idx, url in enumerate(search_results[:10], start=1):
        crunchbase_list.append(url)
else:
    print("No search results found.")

for url in crunchbase_list:
    Output_format(url)
