from abc import ABC, abstractmethod


class AntidetectAdapter(ABC):

    @abstractmethod
    def list_profiles(self) -> list[dict]:
        """
        Trả về danh sách profiles.
        Mỗi item: { "id": str, "name": str, "status": "running"|"stopped" }
        """

    @abstractmethod
    def get_debug_address(self, profile_name: str) -> str:
        """
        Nhận profile_name, trả về debug address dạng "127.0.0.1:PORT".
        Tự start profile nếu chưa chạy.
        """
