from .model_base import ModelBase
from .user import User


class Organization(ModelBase):
    def __init__(self):
        self.name: str = None
        self.has_licence: bool = None
        self.credits: float = None
        self.registration_number: str = None
        self.address: str = None
        self.city: str = None
        self.postal_code: str = None
        self.country: str = None
        self.email: str = None
        self.phone_number: str = None
        self.is_limited: bool = None
        self.user_list: list[User] = list[User]()

    @staticmethod
    def _from_json(resp_json) -> "Organization":
        orga = Organization()

        orga.name = resp_json["name"]
        orga.has_licence = resp_json["has_licence"]
        orga.credits = resp_json["credits"]
        orga.registration_number = resp_json["registration_number"]
        orga.address = resp_json["address"]
        orga.city = resp_json["city"]
        orga.postal_code = resp_json["postal_code"]
        orga.country = resp_json["country"]
        orga.email = resp_json["email"]
        orga.phone_number = resp_json["phone_number"]
        orga.is_limited = resp_json["is_limited"]

        if "user_list" in resp_json:
            for analysis_resp in resp_json["user_list"]:
                orga.user_list.append(User._from_json(analysis_resp))

        return orga
