import storage


class Notifier:
    def __init__(self, subscriptions_file_name):
        self._subscriptions_file_name = subscriptions_file_name
        self._subscriptions = storage.load_from_file(self._subscriptions_file_name, {})

        self._subscriptions_by_chat = {}
        self._subscriptions_by_type = {}

        self._id_counter = 0

        for idx, sub in self._subscriptions.items():
            idx = int(idx)
            if idx > self._id_counter:
                self._id_counter = idx + 1
            self._add_sub_to_hash_tables(sub)

    def _add_sub_to_hash_tables(self, sub):
        chat_subs = self._subscriptions_by_chat.get(sub['chat_id'], [])
        chat_subs.append(sub)
        self._subscriptions_by_chat[sub['chat_id']] = chat_subs

        type_subs = self._subscriptions_by_type.get(sub['type'], [])
        type_subs.append(sub)
        self._subscriptions_by_type[sub['type']] = type_subs

    def _remove_subscription(self, sub):
        del self._subscriptions[sub['id']]
        self._subscriptions_by_chat[sub['chat_id']].remove(sub)
        self._subscriptions_by_type[sub['type']].remove(sub)
        storage.save_to_file(self._subscriptions_file_name, self._subscriptions)

    def add_subscription(self, chat_id, stype, data=None):
        sub = {
            'id': str(self._id_counter),
            'chat_id': chat_id,
            'type': stype,
            'data': data
        }
        self._id_counter += 1
        self._subscriptions[sub['id']] = sub
        self._add_sub_to_hash_tables(sub)
        storage.save_to_file(self._subscriptions_file_name, self._subscriptions)

    def remove_subscription_by_id(self, idx):
        if idx in self._subscriptions:
            self._remove_subscription(self._subscriptions[idx])

    def remove_subscription_by_chat_id(self, chat_id):
        if chat_id in self._subscriptions_by_chat:
            self._remove_subscription(self._subscriptions_by_chat[chat_id])

    def get_subscriptions_by_chat(self, chat_id):
        return self._subscriptions_by_chat.get(chat_id, [])

    def get_subscriptions_by_type(self, stype):
        return self._subscriptions_by_type.get(stype, [])

    def get_subscriptions_by_chat_and_type(self, chat_id, stype):
        return [sub for sub in self._subscriptions_by_chat.get(chat_id, []) if sub['type']==stype]
