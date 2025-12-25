import socket, threading
from classmods import ENVMod, suppress_errors
from typing import List, Literal, Optional, Self, Type, Union, cast
from ._exeptions import AMIExceptions


EXCEPTED_OS_ERROR = 'An operation was attempted on something that is not a socket'


class AMIClient:
    from .operation import Operation, Response
    @ENVMod.register(section_name='AMIClient', cast={'events': str})
    def __init__(
            self,
            host: Optional[str] = None,
            port: Optional[int] = None,
            username: Optional[str] = None,
            secret: Optional[str] = None,
            auth_type: Optional[Literal['plain', 'MD5']] = None,
            key: Optional[str] = None,
            events: Optional[Union[Literal['on', 'off'], list[str]]] = None,
            timeout: Optional[int] = None,
            socket_buffer: Optional[int] = None,
        ) -> None:
        """
        A client for interacting with the Asterisk Manager Interface (AMI) over a socket connection.

        Handles authentication, event listening in a background thread, and provides methods
        to manage the connection and interaction lifecycle.

        Attributes:
            registry (Registry): Registry object used to manage and dispatch AMI operations.

        Args:
            host (str): Hostname or IP address of the AMI server.
            port (int): TCP port to connect to.
            username (Optional[str]): AMI username.
            secret (Optional[str]): AMI password.
            auth_type (Optional[Literal['plain', 'MD5']]): Authentication method.
            key (Optional[str]): Challenge key, used for MD5 authentication.
            events (Optional[Union[Literal['on', 'off'], list[str]]]): Event subscriptions or list.
            timeout (int): Socket connection timeout in seconds.
            socket_buffer (int): Size of buffer for reading socket data.
        """
        self._host = host or '127.0.0.1'
        self._port = port or 5038
        self._username = username
        self._secret = secret
        self._auth_type = auth_type
        self._key = key
        self._events = events
        self._timeout = timeout or 10
        self._socket_buffer = socket_buffer or 2048

        from ._registry import Registry
        self.registry = Registry()


    def connect(self) -> None:
        """
        Establish a TCP connection to the AMI server and start the listener thread.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self._timeout)
        self.listen_thread = threading.Thread(target=self.listen_loop, daemon=True)

        self.socket.connect((self._host, self._port))
        self.listen_thread.start()

    def disconnect(self) -> None:
        """
        Close the socket connection and stop the listening thread safely.
        Also logs out if authenticated.
        """
        if self.is_authenticated():
            self.logout()

        self.socket.close()

        if not threading.current_thread() == self.listen_thread:
            self.listen_thread.join()

    def listen_loop(self) -> None:
        """
        Internal method that runs in a separate thread to continuously receive and
        decode messages from the AMI server.

        This method handles:
            - Receiving and buffering raw AMI data
            - Splitting complete messages by `\r\n\r\n`
            - Passing parsed messages to the registry
            - Handling benign socket errors and controlled timeouts
        """
        buffer = b''

        while self.is_connected():
            try: 
                data = self.socket.recv(self._socket_buffer)
            ## This error excepted if no event triggers in server for `self._timeout` amount of time.
            except TimeoutError: continue
            except OSError as e:
                ## This error message is excepted sometimes and this line prevents random crashes
                if EXCEPTED_OS_ERROR in str(e): continue
                else:
                    self.disconnect()
                    raise e

            try:
                buffer += data
                while b'\r\n\r\n' in buffer:
                    raw_operation, buffer = buffer.split(b'\r\n\r\n', 1)
                    self.registry._register_new_operation(raw_operation.decode())

            ## Ignore Operation Errors
            ## TODO: This is a temporary solution. This will be fixed in logging integration.
            except AMIExceptions.ClientError.OperationError: continue
            except Exception as e:
                self.disconnect()
                raise e


    def login(self) -> Response:
        """
        Authenticate with the AMI server using the provided credentials.

        Returns:
            Response: The response received from the server after login attempt.
        """
        from .operation import Response
        from .operation.action import Login

        response = Login(
            Username = self._username,
            Secret = self._secret,
            AuthType = cast(Optional[Literal['plain', 'MD5']], self._auth_type),
            Key = self._key,
            Events = cast(Optional[Union[Literal['on', 'off'], list[str]]], self._events),
        ).send(self)

        return cast(Response, response)

    def logout(self) -> Response | None:
        """
        Send a logoff command to the AMI server if currently authenticated.

        Returns:
            Response | None: The logoff response or None if not authenticated.
        """
        if not self.is_authenticated():
            from .operation.action import Logoff
            return Logoff().send(self)


    @suppress_errors(False)
    def is_connected(self) -> bool:
        """
        Check whether the client socket is still connected.

        Returns:
            bool: True if connected, False if any socket error occurs.
        """
        if hasattr(socket, 'MSG_DONTWAIT'): self.socket.send(b'', socket.MSG_DONTWAIT)  # type: ignore
        else: self.socket.send(b'')
        return True

    @suppress_errors(False)
    def is_authenticated(self) -> bool:
        """
        Check whether the client is authenticated with the AMI server.

        Returns:
            bool: True if authenticated, False otherwise.
        """
        from .operation.action import Ping
        Ping().send(self, check_connection=True, check_authentication=False)
        return True


    def add_whitelist(self, items: List[Type]) -> None:
        """
        Add item types to the whitelist.

        Args:
            items (List[Type]): A list of operation types to allow.
        """
        for item in items:
            self.registry.whitelist.add(item)

    def add_blacklist(self, items: List[Type]) -> None:
        """
        Add item types to the blacklist.

        Args:
            items (List[Type]): A list of operation types to block.
        """
        for item in items:
            self.registry.blacklist.add(item)


    def remove_whitelist(self, items: List[Type]) -> None:
        """
        Remove item types from the whitelist.

        Args:
            items (List[Type]): A list of operation types to remove.
        """
        for item in items:
            self.registry.whitelist.remove(item)

    def remove_blacklist(self, items: List[Type]) -> None:
        """
        Remove item types from the blacklist.

        Args:
            items (List[Type]): A list of operation types to remove.
        """
        for item in items:
            self.registry.whitelist.remove(item)


    def __enter__(self) -> Self:
        """
        Enter the runtime context and automatically connect and log in.

        Returns:
            Self: The connected and authenticated client instance.
        """
        self.connect()
        self.login()
        return self

    def __exit__(self, type, value, traceback) -> None:
        """
        Exit the runtime context, logging out and disconnecting from the AMI server.

        Args:
            type: The exception type (if any).
            value: The exception value (if any).
            traceback: The traceback object (if any).
        """
        self.logout()
        self.disconnect()