import json


class Triple:
    """
    Class representation of a Triple, consisting  of Subject, Relation, and Objects.

    :param subject: Subject of the triple
    :type subject: str
    :param relation: Relation or predicate of the triple
    :type relation: str
    :param objects: list of Objects of the triple
    :type objects: list

    """

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
        """
        Returns a JSON representation of the Triple.

        :return: JSON representation of the Triple
        :rtype: str
        """
        return json.dumps(self, default=lambda o: o.__dict__)

    @staticmethod
    def from_json(json_data):
        """
        Creates a Triple object from the given JSON string.

        :param json_data: JSON string representation of a triple '{"subject":..., "relation":..., "objects": [...]}'
        :type json_data: str
        :return: the Triple object
        :rtype: triple.Triple
        """
        return Triple.from_dict(json.loads(json_data))

    def to_dict(self):
        """
        Returns a dictionary representation of the Triple.

        :return: dictionary representation of the Triple
        :rtype: dict
        """
        return {'subject': self.subject, 'relation': self.relation, 'objects': self.objects}

    @staticmethod
    def from_dict(dic):
        """
        Creates a Triple object from the given dictionary.

        :param dic: dictionary representation of a triple {"subject":..., "relation":..., "objects": [...]}
        :type dic: dict
        :return: the Triple object
        :rtype: triple.Triple
        """
        return Triple(dic["subject"], dic["relation"], dic["objects"])
