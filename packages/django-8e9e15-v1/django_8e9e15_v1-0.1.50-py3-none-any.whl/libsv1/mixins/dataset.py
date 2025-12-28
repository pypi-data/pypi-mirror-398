import random

class DatasetMixin:
    @classmethod
    def get_random_id(cls):
        data = cls.data()
        if not data:
            return -1
        return random.choice(data)['id']

    @classmethod
    def first(cls, id=None, name=None):
        if id:
            return cls.first_by_id(id)
        elif name:
            return cls.first_by_name(name)
        return None

    @classmethod
    def first_by_id(cls, id):
        for item in cls.data():
            if item['id'] == id:
                return item
        return None

    @classmethod
    def first_by_name(cls, name):
        for item in cls.data():
            if item['name'] == name:
                return item
        return None

    @classmethod
    def name_by_id(cls, id):
        for item in cls.data():
            if item['id'] == id:
                return item['name']
        return None

    @classmethod
    def id_by_name(cls, name):
        for item in cls.data():
            if item['name'] == name:
                return item['id']
        return None

    @classmethod
    def field_by_id(cls, id, field):
        for item in cls.data():
            if item['id'] == id:
                return item.get(field)
        return None

    @classmethod
    def field_by_name(cls, name, field):
        for item in cls.data():
            if item['name'] == name:
                return item.get(field)
        return None

    @classmethod
    def get(cls, where=None, exclude_fields=None, only_fields=None, return_as_list=None):
        data = cls.data()
        if where:
            data = [item for item in data if item.get(where[0]) == where[1]]
        if exclude_fields:
            data = [
                {key: value for key, value in item.items() if key not in exclude_fields}
                for item in data
            ]
        if only_fields:
            data = [
                {key: value for key, value in item.items() if key in only_fields}
                for item in data
            ]

        if return_as_list:
            return [item.get(return_as_list) for item in data if return_as_list in item]

        return data

    @classmethod
    def data(cls):
        return [
            {'id': value, 'name': value.capitalize() if isinstance(value, str) else key.lower().capitalize()}
            for key, value in cls.__dict__.items()
            if (isinstance(value, (str, int)) and not key.startswith('__') and not callable(value))
        ]
