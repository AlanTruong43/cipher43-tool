from abc import ABC, abstractmethod


class AntidetectAdapter(ABC):

    @abstractmethod
    def list_profiles(self) -> list[dict]:
        """
        Trả về danh sách profiles.
        Mỗi item: { "id": str, "name": str, "status": "running"|"stopped" }
        """
