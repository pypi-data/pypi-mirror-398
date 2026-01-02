import logging
import os
import json

from html.parser import HTMLParser

_logger = logging.getLogger(__name__) 

class FactHTMLParser(HTMLParser):
    start_tags = []    
    def handle_starttag(self, tag, attrs):
        self.start_tags.append(tag)