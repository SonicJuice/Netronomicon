import socket, base64
from urllib.request import Request, urlopen, HTTPError, URLError
from urllib.parse import urlparse
from http import client as httplib


class UrlFetcher:
    def __init__(self, config):
        """
        initialises a UrlFetcher object which retrieves linked URLs according to the config file
        RETURNS: None
        """
        self.config = config

    def fetch_url(self, url, depth, url_manager, retry=0):
        """
        sends a request for a URL to be crawled before examining its contents
        RETURNS: bool
        """
        url_req = Request(url, None, {"User-Agent" : self.config.USER_AGENT_STRING})
        parsed = urlparse(url) 
        if parsed.hostname in self.config.get_authentication_data():
            username, password = self.config.get_authentication_data()[parsed.hostname]
            base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
            url_req.add_header("Authorization", "Basic %s" % base64string)
        try:    
            url_data = urlopen(url_req, timeout = self.config.URL_FETCH_TIMEOUT)
            try:
                size = int(url_data.info().getheaders("Content-Length")[0])
            except AttributeError:
                fail_object = None
                size_str = url_data.info().get("Content-Length", fail_object)
                if size_str:
                    size = int(size_str)
                else:
                    size = -1
            except IndexError:
                size = -1

            return size < self.config.MAX_PAGE_SIZE and url_data.code > 199 and url_data.code < 300 \
                   and self.__process_url_data(url, url_data.read(), depth, url_manager)
        except HTTPError:
            return False
        except URLError:
            return False
        except httplib.HTTPException:
            return False
        except socket.error:
            if (retry == self.config.MAX_FETCH_RETRIES):
                return False
            return self.fetch_url(url, depth, url_manager, retry + 1)
        except Exception as e:
            print(type(e).__name__ + " occurred during URL Fetching.")
            return False

    def __process_url_data(self, url, html_data, depth, url_manager):
        """
        extracts information from the URL, adding the text data, html data and url are added to the output buffer.
        The URLs found on the page are sent add to the frontier.
        RETURNS: bool
        """
        text_data = self.config.get_text_data(html_data, for_url=url)
        url_manager.add_output({"html": html_data, "text": text_data, "url": url}) # send relevant information to the output writing function

        links = []
        if (self.config.extract_next_links(url, html_data, links)):
            for link in links:
                url_manager.add_to_frontier(link, depth + 1)
            return True
        return False 
