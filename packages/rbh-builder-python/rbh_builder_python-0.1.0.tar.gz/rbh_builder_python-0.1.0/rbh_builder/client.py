from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .exceptions import ApiError, AuthenticationError
from .transport import DEFAULT_BASE_URL, Transport, TransportConfig


@dataclass
class LoginResponse:
    access_token: str
    company_id: str


class RainbowClient:
    """
    High-level client for the Rainbow Hospitality Gateway REST API.
    """

    def __init__(
        self,
        *,
        access_token: str,
        company_id: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 10,
        username: str | None = None,
        password: str | None = None,
        debug: bool = False,
    ) -> None:
        self.company_id = company_id
        self._username = username
        self._password = password
        self._access_token = access_token
        self._debug = debug
        self.transport = Transport(
            config=TransportConfig(base_url=base_url, timeout=timeout),
            access_token=access_token,
        )

    class Builder:
        """
        Fluent builder to construct a client via /Login while retaining credentials for auto-refresh.
        """

        def __init__(self, *, base_url: str = DEFAULT_BASE_URL, timeout: int = 10) -> None:
            self._base_url = base_url
            self._timeout = timeout
            self._username: str | None = None
            self._password: str | None = None
            self._debug: bool = False

        def debug(self, enabled: bool = True) -> "RainbowClient.Builder":
            """Print request payloads (with masked password) before sending."""
            self._debug = enabled
            return self

        def with_credentials(self, *, username: str, password: str) -> "RainbowClient.Builder":
            self._username = username
            self._password = password
            return self

        def with_base_url(self, base_url: str) -> "RainbowClient.Builder":
            self._base_url = base_url
            return self

        def with_timeout(self, timeout: int) -> "RainbowClient.Builder":
            self._timeout = timeout
            return self

        def build(self) -> "RainbowClient":
            if not self._username or not self._password:
                raise ValueError("Username and password must be provided before build().")
            login = RainbowClient.login(
                username=self._username,
                password=self._password,
                base_url=self._base_url,
                timeout=self._timeout,
            )
            return RainbowClient(
                access_token=login.access_token,
                company_id=login.company_id,
                base_url=self._base_url,
                timeout=self._timeout,
                username=self._username,
                password=self._password,
                debug=self._debug,
            )

    @classmethod
    def builder(cls, *, base_url: str = DEFAULT_BASE_URL, timeout: int = 10) -> "RainbowClient.Builder":
        return cls.Builder(base_url=base_url, timeout=timeout)

    @property
    def access_token(self) -> str:
        return self._access_token

    @staticmethod
    def login(
        *,
        username: str,
        password: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 10,
        debug: bool = False,
    ) -> LoginResponse:
        transport = Transport(TransportConfig(base_url=base_url, timeout=timeout))
        body = {"Username": username, "Password": password}

        if debug:
            print("Login payload (json):", {"Username": body["Username"], "Password": "***"})
        payload = transport.request(
            "POST",
            "/Login",
            json_body=body,
            headers={"Content-Type": "application/json"},
        )
        # Accept case variations from the API.
        token = payload.get("AccessToken") or payload.get("accessToken")
        company_id = (
            payload.get("CompanID")
            or payload.get("CompanyID")
            or payload.get("companyID")
            or payload.get("companyId")
        )
        if not token or not company_id:
            raise ApiError(
                500,
                "Login response missing AccessToken or CompanyID",
                payload,
            )
        return LoginResponse(access_token=token, company_id=company_id)

    # ---------- Internal request helper with auto-refresh on 401 ----------
    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        try:
            return self.transport.request(method, path, **kwargs)
        except AuthenticationError as exc:
            if self._username and self._password:
                # Attempt one re-login then retry.
                refreshed = self.login(
                    username=self._username,
                    password=self._password,
                    base_url=self.transport.config.base_url,
                    timeout=self.transport.config.timeout,
                    debug=self._debug,
                )
                self.company_id = refreshed.company_id
                self._set_access_token(refreshed.access_token)
                return self.transport.request(method, path, **kwargs)
            raise exc

    def _set_access_token(self, token: str) -> None:
        self._access_token = token
        self.transport.set_access_token(token)

    # ---------- Rooms ----------
    def get_rooms(self, page_number: int = 1, page_size: int = 10) -> Dict[str, Any]:
        params = {
            "CompanyID": self.company_id,
            "pageNumber": page_number,
            "pageSize": page_size,
        }
        return self._request("GET", "/GetRooms", params=params)

    # ---------- Guests ----------
    def get_guests(self, page_number: int = 1, page_size: int = 10) -> Dict[str, Any]:
        params = {
            "CompanyID": self.company_id,
            "pageNumber": page_number,
            "pageSize": page_size,
        }
        return self._request("GET", "/GetGuests", params=params)

    def create_guest(self, **guest_fields: Any) -> Dict[str, Any]:
        body = {"CompanyID": self.company_id, **guest_fields}
        return self._request(
            "POST",
            "/CreateGuest",
            json_body=body,
            headers={"Content-Type": "application/json"},
        )

    def update_guest(self, guest_id: str, **guest_fields: Any) -> Dict[str, Any]:
        body = {"GuestId": guest_id, "CompanyID": self.company_id, **guest_fields}
        return self._request(
            "PUT",
            "/UpdateGuest",
            json_body=body,
            headers={"Content-Type": "application/json"},
        )

    def delete_guest(self, guest_id: str) -> Dict[str, Any]:
        body = {"GuestId": guest_id, "CompanyID": self.company_id}
        return self._request(
            "DELETE",
            "/DeleteGuest",
            json_body=body,
            headers={"Content-Type": "application/json"},
        )

    # ---------- Call logs ----------
    def get_call_logs(
        self,
        room_no: str,
        page_number: int = 1,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        params = {
            "CompanyID": self.company_id,
            "RoomNo": room_no,
            "pageNumber": page_number,
            "pageSize": page_size,
        }
        return self._request("GET", "/GetCallLogs", params=params)

    # ---------- Reservation flows ----------
    def checkin(
        self,
        *,
        room_id: str,
        checkout_date: str,
        first_name: str,
        last_name: str,
        barring: Optional[str] = None,
        guest_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "CompanyID": self.company_id,
            "RoomId": room_id,
            "CheckoutDate": checkout_date,
            "FirstName": first_name,
            "LastName": last_name,
        }
        if barring:
            body["Barring"] = barring
        if guest_id:
            body["GuestId"] = guest_id
        return self._request(
            "POST",
            "/Checkin",
            json_body=body,
            headers={"Content-Type": "application/json"},
        )

    def checkout(self, room_id: str, delete_guest: bool | None = None) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "CompanyID": self.company_id,
            "RoomId": room_id,
        }
        if delete_guest is not None:
            body["DeleteGuest"] = str(delete_guest).lower()
        return self._request(
            "POST",
            "/Checkout",
            json_body=body,
            headers={"Content-Type": "application/json"},
        )

    def move_room(self, room_id: str, new_room_id: str) -> Dict[str, Any]:
        body = {
            "CompanyID": self.company_id,
            "RoomId": room_id,
            "NewRoomId": new_room_id,
        }
        return self._request(
            "POST",
            "/MoveRoom",
            json_body=body,
            headers={"Content-Type": "application/json"},
        )

    # ---------- Wakeup calls ----------
    def create_wakeup_call(
        self,
        *,
        room_id: str,
        alarm_time: str,
        followup_time: str,
        frequency: str,
    ) -> Dict[str, Any]:
        body = {
            "CompanyId": self.company_id,
            "RoomId": room_id,
            "AlarmTime": alarm_time,
            "FollowupTime": followup_time,
            "Frequency": frequency,
        }
        return self._request(
            "POST",
            "/CreateWakeupCall",
            json_body=body,
            headers={"Content-Type": "application/json"},
        )

    def update_wakeup_call(
        self,
        *,
        wakeup_id: str,
        alarm_time: Optional[str] = None,
        followup_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"Id": wakeup_id}
        if alarm_time:
            body["AlarmTime"] = alarm_time
        if followup_time:
            body["FollowupTime"] = followup_time
        return self._request(
            "PUT",
            "/UpdateWakeupCall",
            json_body=body,
            headers={"Content-Type": "application/json"},
        )

    def delete_wakeup_call(self, wakeup_id: str) -> Dict[str, Any]:
        body = {"Id": wakeup_id}
        return self._request(
            "DELETE",
            "/DeleteWakeupCall",
            json_body=body,
            headers={"Content-Type": "application/json"},
        )

    def get_wakeup_calls(self, page_number: int = 1, page_size: int = 10) -> Dict[str, Any]:
        params = {
            "CompanyID": self.company_id,
            "pageNumber": page_number,
            "pageSize": page_size,
        }
        return self._request("GET", "/GetWakeupCalls", params=params)
