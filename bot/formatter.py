def format_forum_updates(updates):
    message = 'Новые сообщения на форуме\n'
    for category in sorted(set(u['category'] for u in updates)):
        message += '\n**' + category + ':**\n'
        for u in updates:
            if u['category'] == category:
                message += '- [{0}]({1})\n'.format(u['title'], u['link'])
    return message
