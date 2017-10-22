import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime

import storage

topic_id_regex = re.compile('topic=(\d+)')
message_id_regex = re.compile('\.msg(\d+)')

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
        for topic in self.forum_data.values():
            topic['unread_messages'].clear()
            topic['last_notify_timestamp'] = topic['last_message_timestamp']
        storage.save_to_file(self._storage_file_name, self.forum_data)

    def get_updates(self, max_count=10):
        return sorted((v for v in self.forum_data.values() if v['unread_messages']),
                      key=lambda x: x['last_message_timestamp'], reverse=True)[:max_count]

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

            topic_id = topic_id_regex.search(link).group(1)
            message_id = message_id_regex.search(link).group(1)
            if topic_id not in self.forum_data:
                topic = {'last_notify_timestamp': 0,  # time stamp of last sent message
                         'last_message_timestamp': 0,  # time stamp of last message
                         'unread_messages': {}}
            else:
                topic = self.forum_data[topic_id]

            if pub_timestamp <= topic['last_notify_timestamp']:
                continue

            # update just in case of update.
            topic['category'] = category
            topic['title'] = title
            topic['last_message_timestamp'] = max(topic['last_message_timestamp'], pub_timestamp)

            message = {'description': description,
                       'link': link,
                       'pub_timestamp': pub_timestamp}

            topic['unread_messages'][message_id] = message

            self.forum_data[topic_id] = topic

        storage.save_to_file(self._storage_file_name, self.forum_data)
