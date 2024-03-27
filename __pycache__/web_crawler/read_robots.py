import urllib.robotparser as robotparser
from urllib.parse import urlparse


class ReadRobots:
    def __init__(self, config):
        """
        initialises a ReadRobots object which stores the rules specified by robots.txt
        according to the config file
        RETURNS: None
        """
        self.RULE_DICT = {}
        self.config = config    

    def allowed(self, url):
        """
        parses through robots.txt to determine if the webpage can be fetched
        RETURNS: bool
        """
        try:
            parsed = urlparse(url)
            port = ""
            if (parsed.port):
                port = ":" + str(parsed.port)
        except ValueError:
            print("ValueError: " + url)

        robot_url = ""
        try:
            robot_url = parsed.scheme + "://" + parsed.hostname + port + "/robots.txt"
        except TypeError:
            print(parsed)
        if robot_url not in self.RULE_DICT:
            self.RULE_DICT[robot_url] = robotparser.RobotFileParser(robot_url)
            try:
                self.RULE_DICT[robot_url].read()
            except IOError:
                del self.RULE_DICT[robot_url]
                return True
        try:
            return self.RULE_DICT[robot_url].can_fetch(self.config.USER_AGENT_STRING, url)
        except KeyError:
            print ("Keyerror: " + url)
            return True
