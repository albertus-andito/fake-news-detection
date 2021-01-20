import json
import pprint


class Triple:

    def __init__(self, subject=None, relation=None, objects=None):
        self.subject = subject
        self.relation = relation
        self.objects = objects

    def __eq__(self, other):
        if isinstance(other, Triple):
            return self.subject == other.subject and self.relation == other.relation \
                   and sorted(self.objects) == sorted(other.objects)
        return False

    def __str__(self):
        return self.to_json()

    def __repr__(self):
        return self.to_json()

    def __hash__(self):
        return hash((self.subject, self.relation, tuple(self.objects)))

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)


if __name__ == '__main__':
    triple = Triple('UV rays', 'cure', ['abc', 'COVID 19'])
    triple2 = Triple('UV rays', 'cure', ['COVID 19', 'abc'])
    triple3 = Triple()
    pprint.pprint(triple.to_json())
    print(triple.__eq__(triple2))