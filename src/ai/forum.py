import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from threading import Lock
import copy
import logging
import pickle

logger = logging.getLogger(__name__)

topic_id_regex = re.compile('topic=(\d+)')
message_id_regex = re.compile('\.msg(\d+)')
datetime_format = '%a, %d %b %Y %H:%M:%S %Z'

MIN_TIMESTAMP_KEY = ""


class ForumMessage:
    def __init__(self, message_id, link, pub_timestamp, description):
        self.message_id = message_id
        self.link = link
        self.pub_timestamp = pub_timestamp
        self.description = description


class ForumTopic:
    def __init__(self, topic_id, category, title):
        self.id = topic_id
        self.category = category
        self.title = title
        self.messages = dict()

    @property
    def earliest_message_link(self):
        ts = None
        link = None
        for message in self.messages:
            if ts is None or ts > message.pub_timestamp:
                link = message.link
        return link

    @property
    def last_update_timestamp(self):
        ts = 0
        for message in self.messages.values():
            ts = max(ts, message.pub_timestamp)
        return ts


class Forum:
    def __init__(self, forum_rss_url, redis_storage):
        self._lock = Lock()
        self._storage = redis_storage
        self._forum_rss_url = forum_rss_url
        self._min_timestamp = 0.0
        if self._storage:
            self._min_timestamp = self._storage.get(MIN_TIMESTAMP_KEY)
            if self._min_timestamp is None:
                self._min_timestamp = 0.0
            else:
                self._min_timestamp = 0.0
                # self._min_timestamp = pickle.loads(self._min_timestamp)
        logging.info(f"AI Forum created, min_timestamp {self._min_timestamp}")
        self.forum_data = dict()

    def get_fresh_topics(self):
        with self._lock:
            result = (copy.deepcopy(t) for t in self.forum_data.values())
            result = sorted(result,
                            key=lambda x: x.last_update_timestamp,
                            reverse=True)
            return result

    def reset_to_timestamp(self, timestamp):
        with self._lock:
            old_forum_data = self.forum_data.values()
            self.forum_data = dict()

            for topic in old_forum_data:
                messages = dict(
                    (k, v) for k, v in topic.messages.items() if v.pub_timestamp > timestamp)
                if messages:
                    topic.messages = messages
                    self.forum_data[topic.id] = topic
            self._min_timestamp = timestamp
            if self._storage:
                self._storage.set(MIN_TIMESTAMP_KEY, pickle.dumps(self._min_timestamp))

    def gather_updates(self):
        with self._lock:
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

                if pub_timestamp <= self._min_timestamp:
                    continue

                topic_id = topic_id_regex.search(link).group(1)
                message_id = message_id_regex.search(link).group(1)
                if topic_id not in self.forum_data:
                    topic = ForumTopic(topic_id, category, title)
                    self.forum_data[topic_id] = topic
                else:
                    topic = self.forum_data[topic_id]
                    topic.category = category
                    topic.title = title
                if message_id not in topic.messages:
                    topic.messages[message_id] = ForumMessage(message_id, link, pub_timestamp,
                                                              description)
