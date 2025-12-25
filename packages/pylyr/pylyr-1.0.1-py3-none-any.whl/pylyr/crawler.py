import urllib.parse
import requests
import re
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile


class Crawler:
    def __init__(self, artist: str, title: str):
        self.artist = artist
        self.title = title

        options = Options()
        options.add_argument('--headless')
        firefox_profile = FirefoxProfile()
        firefox_profile.set_preference('permissions.default.image', 2)
        firefox_profile.set_preference(
            'dom.ipc.plugins.enabled.libflashplayer.so', 'false')
        options.profile = firefox_profile
        self.driver = webdriver.Firefox(options=options)


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()


    def _get_soup(self, url: str) -> BeautifulSoup:
        self.driver.get(url)
        return BeautifulSoup(self.driver.page_source, 'html.parser')


    def get_lyrics(self):
        providers = [self._lrclib, self._genius, self._genius_from_search,
                     self._duckduckgo]

        lyrics = ''
        while providers:
            lyrics = providers.pop(0)()
            if lyrics:
                break

        return lyrics


    def _lrclib(self) -> str:
        '''
        Get lyrics directly from https://lrclib.net/ API
        '''
        logging.info('Requesting lyrics from lrclib') 

        base = 'https://lrclib.net/api/get?'
        artist = urllib.parse.quote_plus(self.artist)
        title = urllib.parse.quote_plus(self.title)

        url = f'{base}artist_name={artist}&track_name={title}'
        logging.info(f'Request URL: {url}')

        request = requests.get(url) 
        lyrics = request.json().get('plainLyrics')
        return lyrics


    def _duckduckgo(self) -> str:
        '''
        Prepare url and attributes for scraping duckduckgo.com
        then parse the returned html for lyrics
        '''
        logging.info('Scraping duckduckgo search results for lyrics')

        search_string = urllib.parse.quote_plus(
                    f'{self.artist} {self.title} lyrics')

        url = 'https://duckduckgo.com/?q=' + search_string \
                    + '&ia=web&iax=lyrics'
        logging.info(f'Using url: {url}')

        soup = self._get_soup(url)

        element = soup.find('div', attrs={'aria-label': 'Song lyrics'})

        if element is not None:
            for br in element.find_all('br'):
                br.replace_with('\n')

            lyrics = element.get_text()
            lyrics = '\n'.join(line.lstrip() 
                for line in lyrics.split('\n'))
            return lyrics
        return ''


    def _genius(self) -> str:
        '''
        Prepare url and attributes for scraping genius.com
        then parse the returned html for lyrics
        '''
        logging.info(
            'Scraping genius for lyrics, using url construction method')

        to_remove = r'( ?(\(|\[|\{).*(\)|\]|\}) ?)'
        artist = self.artist.replace(' ', '-')
        artist = re.sub(to_remove, '', artist)
        title = self.title.replace(' ', '-')
        title = re.sub(to_remove, '', title)

        url = f'https://genius.com/{artist}-{title}-lyrics'
        logging.info(f'Attempting to scrape constructed url: {url}')

        soup = self._get_soup(url)

        elements = soup.find_all('div', attrs={'data-lyrics-container': True})

        if elements != []:
            for element in elements:
                for br in element.find_all('br'):
                    br.replace_with('\n')
            return '\n'.join([element.get_text() 
                    for element in elements])
        return ''
    

    def _genius_from_search(self) -> str:
        '''
        Scrape genius.com lyrics page obtained via self._genius_search
        then parse the returned html for lyrics

        For this provider, there are two steps:

        1. Scrape genius' search page for suitable lyrics page urls
        2. Scrape the lyrics page url for the lyrics
        '''
        logging.info('Scraping genius for lyrics, using search method')

        similar, lyrics_page_url = self._genius_search(self.artist, self.title)
        if not similar:
            if 'the' in self.title.lower():
                logging.info(
                    "Trying removing 'the' from song's title in search query")
                title_sans_the = re.sub(r'^(T|t)he ', '', self.title)
                similar, lyrics_page_url = self._genius_search(self.artist,
                                                               title_sans_the)

        if not similar:
            if 'the' in self.artist.lower():
                logging.info(
                    "Trying removing 'the' from song's artist in search query")

                artist_sans_the = re.sub(r'^(T|t)he ', '', self.artist)
                similar, lyrics_page_url = self._genius_search(artist_sans_the,
                                                           self.title)

        # still can't find similar results, don't bother parsing lyrics page
        if not similar:
            return ''

        soup = self._get_soup(lyrics_page_url)

        elements = soup.find_all('div', attrs={'data-lyrics-container': True})

        if elements != []:
            for element in elements:
                for br in element.find_all('br'):
                    br.replace_with('\n')
            return '\n'.join([element.get_text() 
                    for element in elements])
        elif soup.body.find(string=re.compile('This song is an instrumental')):
            return '[Instrumental]'

        return ''

        
    def _genius_search(self, artist: str, title: str) -> tuple[bool, str]:
        '''
        Prepare a search query and then construct a url for the genius search
        results page.

        Extract the url of the first lyrics page from these results and
        determine if it is acceptably similar to the queried song

        Acceptability is acheived by the words in an song's title and
        artist information being either contained in those of lyrics page or 
        vice-versa
        This prevents the crawler from pulling lyrics from the wrong title
        '''
        search_results_url = 'https://genius.com/search?q=' + \
            urllib.parse.quote_plus(f'{artist} {title}')

        logging.info(f'Using search URL: {search_results_url}')

        soup = self._get_soup(search_results_url)

        lyrics_page_element = soup.find('a', attrs={'class': 'mini_card'})
        if not lyrics_page_element:
            logging.info('No lyrics page results found with search')
            return False, ''

        lyrics_page_url = lyrics_page_element.get('href')
        logging.info(f'Top result: {lyrics_page_url}')

        page_title = lyrics_page_element.find('div', 
            attrs={'class': 'mini_card-title'})
        if page_title is not None:
            page_title = page_title.text
        logging.info(f'{page_title = }')

        page_artist = lyrics_page_element.find('div',
            attrs={'class': 'mini_card-subtitle'})
        if page_artist is not None:
            page_artist = page_artist.text
        logging.info(f'{page_artist = }')

        return self._similar(page_title, page_artist), lyrics_page_url

    
    def _similar(self, actual_title: str, actual_artist: str) -> bool:
        if actual_title is None or actual_artist is None:
            return False

        to_remove = r"[,|'()\[\]\"’/\(\u200b\)]"

        actual_title = actual_title.lower().strip()
        actual_artist = actual_artist.lower().strip()
        actual = f'{actual_title} {actual_artist}'
        actual = re.sub(to_remove, '', actual)

        expected_title = self.title.lower()
        expected_artist = self.artist.lower()
        expected = f'{expected_title} {expected_artist}'
        expected = re.sub(to_remove, '', expected)

        logging.info(f'{actual = }')
        logging.info(f'{expected = }')

        actual = set(actual.split())
        expected = set(expected.split())

        logging.info(f'{actual = }')
        logging.info(f'{expected = }')

        similar = expected >= actual or expected <= actual
        logging.info(f'Results are similar to expected: {similar}')
        return similar
