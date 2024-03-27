import re
from abc import *
from urllib.parse import urlparse
from lxml.html.clean import Cleaner
from lxml import html, etree


class Config(metaclass=ABCMeta):
    """
    abstract base class contains one or more abstract methods (which have no implementation in the ABC
    but must be implemented in any class that inherits from it)
    """
    def __init__(self):
        """
        initialises a Config object specifying crawling rules
        RETURNS: None
        """
        self.MAX_WORKER_THREADS = 8
        self.FRONTIER_TIMEOUT = 60 # seconds time out for trying to get the next url from the frontier
        self.WORKER_TIMEOUT = 60
        self.OUTPUT_QUEUE_TIMEOUT = 60 # seconds timeout of trying to get the data from the output queue
        self.URL_FETCH_TIMEOUT = 2 # seconds timeout for trying to get URL data
        self.__USER_AGENT_STRING = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
 # crawler's identifier
        self.RESUMABLE = True # allows fetching to resume from the last closure.
        self.MAX_FETCH_RETRIES = 5 # number of times to retry fetching a URL if it fails
        self.POLITENESS_DELAY = 300 # time delay between crawls
        self.PERSISTENT_FILE = "Persistent.shelve" # file stores the current state of crawler for resuming
        self.NO_OF_DOCS_TO_FETCH = -1
        self.MAX_DEPTH = -1
        self.MAX_PAGE_SIZE = 1048576 # in bytes (only works for websites that send Content-Length in the response header
        self.MAX_QUEUE_SIZE = 0
        self.REMOVE_JAVASCRIPT_AND_CSS = True

    @abstractmethod
    def get_seeds(self):
        """
        getter method for the first set of urls to start crawling from. It's abstract such that it has a declaration but not an implementation
        RETURNS: None
        """
        return ["Sample Url 1", "Sample Url 2", "Etc"]

    @abstractmethod
    def handle_url_data(self, parsed_data):
        """
        handles url data
        RETURNS: None
        """
        print (parsed_data["url"])
        return

    def allowed_schemes(self, scheme):
        """
        specifies valid schemes/protocols
        RETURNS: string
        """
        return scheme.lower() in set(["http", "https", "ftp", b"http", b"https", b"ftp"])

    @abstractmethod
    def valid_url(self, url):
        """
        determines if a url is valid and, therefore, fetchable
        RETURNS: bool
        """
        parsed = urlparse(url)
        try:
            return ".ics.uci.edu" in parsed.hostname \
                and not re.match(".*\.(css|js|bmp|gif|jpe?g|ico" + "|png|tiff?|mid|mp2|mp3|mp4"\
                + "|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf" \
                + "|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1" \
                + "|thmx|mso|arff|rtf|jar|csv"\
                + "|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
  
        except TypeError:
            print ("TypeError for ", parsed)

    def get_text_data(self, html_data, for_url='<Mising URL info>'):
        """
        extracts text from HTML data
        RETURNS: string
        """
        if self.remove_javascript:
          try:
            cleaner = Cleaner()
            cleaner.javascript = True
            cleaner.style = True
            html_data = cleaner.clean_html(html_data)
          except:
            print(f"Couldn't remove style and JS for {for_url}")
        try:
            return html.fromstring(html_data).text_content()
        except Exception as e:
            print(type(e).__name__  +f": Couldn't extract text for {for_url}")
            return ""

    def extract_linked_urls(self, url, raw_data, output_links):
        """
        extracts the next links to iterate over
        RETURNS: bool (if successful)
        """
        try:
            html_parse = html.document_fromstring(raw_data)
            html_parse.make_links_absolute(url)
        except etree.ParserError:
            print("Couldn't extract links from the url")
            return False
        except etree.XMLSyntaxError:
            print("Couldn't extract links from the url")
            return False

        for element, attribute, link, pos in html_parse.iterlinks():
            output_links.append(link)
        return True

    def get_authentication_data(self):
        """
        getter method for authentication as top_level_url : tuple(username, password)
        RETURNS: dict
        """
        return {}
