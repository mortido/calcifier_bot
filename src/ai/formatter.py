def format_topic(topic):
    first_link = None
    ts = 0
    for message in topic['unread_messages'].values():
        if first_link is None or ts > message['pub_timestamp']:
            ts = message['pub_timestamp']
            first_link = message['link']
    return f"- [{topic['title']}]({first_link}) ({topic['unread_messages']})"


def format_category(category, topics):
    return f'**{category}:**\n' + \
           '\n'.join(format_topic(topic) for topic in topics if topic['category'] == category)


def format_forum_updates(updates):
    return '\n\n'.join(format_category(category, updates) for category in sorted(set(u['category'] for u in updates)))
