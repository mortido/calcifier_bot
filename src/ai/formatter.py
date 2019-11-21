def format_topic(topic):
    first_link = None
    ts = 0
    for message in topic.messages.values():
        if first_link is None or ts > message.pub_timestamp:
            ts = message.pub_timestamp
            first_link = message.link
    return f"- [{topic.title}]({first_link}) ({len(topic.messages)})"


def format_category(category, topics):
    return f'**{category}:**\n' + \
           '\n'.join(format_topic(topic) for topic in topics if topic.category == category)


def format_forum_updates(topics):
    categories = sorted(set(topic.category for topic in topics))
    result = []
    for category in categories:
        result.append(format_category(category, topics))
    return '\n\n'.join(result)

