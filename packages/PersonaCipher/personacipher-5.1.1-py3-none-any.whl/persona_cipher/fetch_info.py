import requests
from bs4 import BeautifulSoup

def fetch_wikipedia_infobox(username=None, language='en'):
    url = f"https://{language}.wikipedia.org/wiki/{username}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 404:
            print(f"Sorry, no Wikipedia page found for {username} in {language}.")
        else:
            print(f"HTTP error occurred: {err}")
        return False 
    
    soup = BeautifulSoup(response.text, 'html.parser')

    infobox = soup.find('table', {'class': 'infobox'})

    if not infobox:
        print(f"No infobox found on Wikipedia for {username} in {language}.")
        return False

    labels = []
    values = []
    for row in infobox.find_all('tr'):
        th = row.find('th')
        td = row.find('td')

        if th and td:
            label = th.get_text(strip=True)
            value = td.get_text(strip=True)

            if label and value:
                if any(keyword in label.lower() for keyword in ['website', 'medal record', 'signature']):
                    continue
                value = ''.join(BeautifulSoup(value, 'html.parser').findAll(text=True)).strip()
                labels.append(label)
                values.append(value)

    if not labels:
        print(f"No relevant data found for {username} in {language}.")
        return False

    print(f"\n{'Label':<30} {'Value'}")
    print('-' * 50)

    for label, value in zip(labels, values):
        print(f"{label:<30} {value}")

    return True

def get_language_descriptions():
    languages = {
        "en": "English",
        "sv": "Swedish",
        "da": "Danish",
        "de": "German",
        "fi": "Finnish",
        "no": "Norwegian",
        "it": "Italian",
        "fr": "French",
        "pl": "Polish",
    }
    return languages

def main():

    person_detected = input("Enter the name of the detected person, country, content, etc: ")

    languages = get_language_descriptions()
    print("\nAvailable languages for fetching infobox:")
    for lang_code, lang_desc in languages.items():
        print(f"{lang_code}: {lang_desc}")

    language = input("\nEnter the language code (e.g., en for English, sv for Swedish, etc.): ").strip().lower()

    if not language or language not in languages:
        language = 'en'
        print("Invalid or empty input. Defaulting to English (en).")

    print(f"\nFetching infobox for {person_detected} in {languages[language]}...")

    if fetch_wikipedia_infobox(person_detected, language):
        print(f"\nInfobox data for {person_detected} in {languages[language]} fetched successfully!")
    else:
        print(f"\nNo relevant data found for {person_detected} in {languages[language]}.")
        print("Falling back to English (en)...")
        if fetch_wikipedia_infobox(person_detected, 'en'):
            print(f"\nInfobox data for {person_detected} in English fetched successfully!")

if __name__ == "__main__":
    main()
