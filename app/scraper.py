import requests
from bs4 import BeautifulSoup


def scrape():
    
    url = 'https://www.vlr.gg'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    print(soup)



if __name__ == '__main__':
    scrape()