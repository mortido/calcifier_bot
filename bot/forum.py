import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime

import storage

id_regex = re.compile('topic=(\d+)')
datetime_format = '%a, %d %b %Y %H:%M:%S %Z'


class Forum:
    def __init__(self, forum_rss_url, storage_file_name):
        self._storage_file_name = storage_file_name
        self._forum_rss_url = forum_rss_url
        self.forum_data = storage.load_from_file(self._storage_file_name, {})

        # In case if user data already exist and bot should show updates from last start.
        self._gather_info()

    def check_updates(self):
        self._gather_info()

    def reset_changes(self):
        # TODO: resets status of 'notified previously' for all subscribers at once.
        for v in self.forum_data.values():
            v['last_notify'] = v['pub_timestamp']
        storage.save_to_file(self._storage_file_name, self.forum_data)

    def get_updates(self, max_count=10):
        return sorted((v for v in self.forum_data.values() if v['last_notify'] < v['pub_timestamp']),
                      key=lambda x: x['pub_timestamp'], reverse=True)[:max_count]

    def _gather_info(self):
        page = requests.get(self._forum_rss_url)
        root = ET.fromstring(page.text)

        for item in root.iter('item'):
            title = None
            link = None
            pub_timestamp = None
            category = None
            description = None

            for field in item:
                if field.tag == 'pubDate':
                    pub_timestamp = datetime.strptime(field.text, datetime_format).timestamp()
                elif field.tag == 'title':
                    title = field.text
                    if title.startswith('Re: '):
                        title = title[4:]
                elif field.tag == 'link':
                    link = field.text
                elif field.tag == 'category':
                    category = field.text
                elif field.tag == 'description':
                    description = field.text

            topic_id = id_regex.search(link).group(1)
            topic = self.forum_data.get(topic_id, {'last_notify': 0})
            topic['category'] = category
            topic['description'] = description
            topic['link'] = link
            topic['pub_timestamp'] = pub_timestamp
            topic['title'] = title
            self.forum_data[topic_id] = topic

        storage.save_to_file(self._storage_file_name, self.forum_data)
