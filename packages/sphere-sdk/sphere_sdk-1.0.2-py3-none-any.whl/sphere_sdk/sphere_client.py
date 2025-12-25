import sys
import ctypes
import os
import logging
from importlib.metadata import version, PackageNotFoundError 
from google.protobuf.json_format import MessageToDict
from . import sphere_sdk_types_pb2
from ctypes import (
    create_string_buffer
)


logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s (%(module)s): %(message)s')
logger = logging.getLogger(__name__)

class TradingClientError(Exception):
    """Base exception for TradingClientSDK errors."""
    pass

class SDKInitializationError(TradingClientError):
    """Error during SDK initialization (e.g., DLL loading)."""
    pass

class LoginFailedError(TradingClientError):
    """Error during login."""
    pass

class NotLoggedInError(TradingClientError):
    """Error when an action requiring login is attempted without being logged in."""
    pass

class TradeOrderFailedError(TradingClientError):
    """Error during a trade order submission."""
    pass

class CreateOrderFailedError(TradingClientError):
    """Error during a create order submission."""
    pass

class UpdateOrderFailedError(TradingClientError):
    """Error during a update order submission."""
    pass

class CancelOrderFailedError(TradingClientError):
    """Error during a cancel order submission."""
    pass

class GetInstrumentsFailedError(TradingClientError):
    """Failed to retrieve the list of instruments."""
    pass

class GetExpiriesFailedError(TradingClientError):
    """Failed to retrieve expiries for the specified instrument."""
    pass

class GetBrokersFailedError(TradingClientError):
    """Failed to retrieve the list of brokers."""
    pass

class GetClearingOptionsFailedError(TradingClientError):
    """Failed to retrieve the available clearing options."""
    pass


OrderEventCallbackType = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.c_int
)

TradeEventCallbackType = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.c_int
)

class SphereTradingClientSDK:
    _DLL_NAME_MAP = {
        'win32': 'Client.dll',
        'linux': 'Client.so',
        #'darwin': 'Client.dylib'
    }

    def __init__(self):
        """
        Initializes the Trading Client SDK.
        
        Raises:
            SDKInitializationError: If the DLL cannot be loaded or functions cannot be found.
        """
        self._client_dll = None
        self._login_func = None
        self._logout_func = None
        self._subscribe_orders_func = None
        self._subscribe_trades_func = None
        self._trade_order_func = None
        self._cancel_order_func = None
        self._create_trader_flat_order_func = None
        self._create_trader_spread_order_func = None
        self._create_trader_strip_order_func = None
        self._create_trader_fly_order_func = None
        self._update_trader_flat_order_func = None
        self._update_trader_spread_order_func = None
        self._update_trader_strip_order_func = None
        self._update_trader_fly_order_func = None
        self._get_instruments_func = None
        self._get_expiries_func = None
        self._get_brokers_func = None
        self._get_clearing_options_func = None
         
        self._c_order_event_callback_ptr = None
        self._user_order_callback = None
        self._c_trade_event_callback_ptr = None
        self._user_trade_callback = None
        self._is_logged_in = False

        dll_directory = os.path.dirname(os.path.abspath(__file__))

        dll_name = self._DLL_NAME_MAP.get(sys.platform)
        if not dll_name:


            raise SDKInitializationError(
                f"Unsupported operating system: {sys.platform}. "
            )

        dll_path = os.path.join(dll_directory, dll_name)
        
        logger.info(f"Attempting to load DLL from: {dll_path}")

        try:
            self._client_dll = ctypes.CDLL(dll_path)
            logger.info(f"Successfully loaded DLL: {dll_path}")
        except OSError as e:
            logger.error(f"Error loading DLL from {dll_path}: {e}")
            raise SDKInitializationError(
                f"Error loading DLL from {dll_path}: {e}. "
            ) from e

        self._load_functions()

        self._send_sdk_version()

        logger.info("SDK initialized successfully.")

    def _load_functions(self):
        """Loads function pointers from the DLL and sets their argtypes/restypes."""
        try:
            self._login_func = self._client_dll.login
            self._logout_func = self._client_dll.logout
            self._subscribe_orders_func = self._client_dll.subscribe_to_order_events
            self._subscribe_trades_func = self._client_dll.subscribe_to_trade_events
            self._trade_order_func = self._client_dll.trade_order
            self._cancel_order_func = self._client_dll.cancel_order
            self._create_trader_flat_order_func = self._client_dll.create_trader_flat_order
            self._create_trader_spread_order_func = self._client_dll.create_trader_spread_order
            self._create_trader_strip_order_func = self._client_dll.create_trader_strip_order
            self._create_trader_fly_order_func = self._client_dll.create_trader_fly_order
            self._update_trader_flat_order_func = self._client_dll.update_trader_flat_order
            self._update_trader_spread_order_func = self._client_dll.update_trader_spread_order
            self._update_trader_strip_order_func = self._client_dll.update_trader_strip_order
            self._update_trader_fly_order_func = self._client_dll.update_trader_fly_order
            self._get_instruments_func = self._client_dll.get_instruments
            self._get_expiries_func = self._client_dll.get_expiries_by_instrument_name
            self._get_brokers_func = self._client_dll.get_brokers
            self._get_clearing_options_func = self._client_dll.get_clearing_options

            try:
                self._set_sdk_version_func = self._client_dll.set_sdk_version
            except AttributeError:
                logger.warning("Native function 'set_sdk_version' not found. SDK version will not be tracked.")

        except AttributeError as e:
            logger.error("Could not access functions by name. Ensure DLL exports are correct.")
            raise SDKInitializationError(
                "Could not access functions by name. Ensure DLL exports are correct."
            ) from e

        self._login_func.restype = ctypes.c_int
        self._login_func.argtypes = [
            ctypes.c_char_p,      # usernamePtr
            ctypes.c_char_p,      # passwordPtr
            ctypes.c_int,         # passwordLength
            ctypes.c_void_p,      # resultBufferPtr
            ctypes.c_int          # resultBufferSize
        ]

        self._logout_func.restype = None
        self._logout_func.argtypes = []

        self._subscribe_orders_func.restype = None
        self._subscribe_orders_func.argtypes = [
            ctypes.c_void_p
        ]

        self._subscribe_trades_func.restype = None
        self._subscribe_trades_func.argtypes = [
            ctypes.c_void_p
        ]
        
        self._trade_order_func.restype = ctypes.c_int
        self._trade_order_func.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_int
        ]

        self._cancel_order_func.restype = ctypes.c_int
        self._cancel_order_func.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_int
        ]

        self._create_trader_flat_order_func.restype = ctypes.c_int
        self._create_trader_flat_order_func.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_int
        ]

        self._create_trader_spread_order_func.restype = ctypes.c_int
        self._create_trader_spread_order_func.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_int
        ]

        self._create_trader_strip_order_func.restype = ctypes.c_int
        self._create_trader_strip_order_func.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_int
        ]

        self._create_trader_fly_order_func.restype = ctypes.c_int
        self._create_trader_fly_order_func.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_int
        ]

        self._update_trader_flat_order_func.restype = ctypes.c_int
        self._update_trader_flat_order_func.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_int
        ]

        self._update_trader_spread_order_func.restype = ctypes.c_int
        self._update_trader_spread_order_func.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_int
        ]

        self._update_trader_strip_order_func.restype = ctypes.c_int
        self._update_trader_strip_order_func.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_int
        ]

        self._update_trader_fly_order_func.restype = ctypes.c_int
        self._update_trader_fly_order_func.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_int
        ]

        self._get_instruments_func.restype = ctypes.c_int
        self._get_instruments_func.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int
        ]
        
        self._get_expiries_func.restype = ctypes.c_int
        self._get_expiries_func.argtypes = [
            ctypes.c_char_p,
            ctypes.c_void_p,
            ctypes.c_int
        ]

        self._get_brokers_func.restype = ctypes.c_int
        self._get_brokers_func.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int
        ]

        self._get_clearing_options_func.restype = ctypes.c_int
        self._get_clearing_options_func.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int
        ]

        if self._set_sdk_version_func:
            self._set_sdk_version_func.restype = None
            self._set_sdk_version_func.argtypes = [ctypes.c_char_p]

        logger.debug("DLL functions loaded and configured.")

    def _send_sdk_version(self):
        """Retrieves the package version and sends it to the native C# client."""
        if not self._set_sdk_version_func:
            return

        try:
            sdk_version = version("sphere-sdk")
        except PackageNotFoundError:
            sdk_version = "0.0.0-dev"  # Fallback if package isn't installed via pip

        try:
            logger.info(f"Sending SDK Version to native client: {sdk_version}")
            self._set_sdk_version_func(sdk_version.encode('utf-8'))
        except Exception as e:
            logger.warning(f"Failed to send SDK version to native client: {e}")

    def login(self, username, password):
        """
        Logs into the trading service.

        Args:
            username (str): The username.
            password (str): The password.

        Raises:
            LoginFailedError: If the login attempt fails for any reason (e.g., bad credentials, network error).
        """
        if self._is_logged_in:
            logger.warning("Already logged in. Call logout first if you intend to re-login.")
            self.logout()


        username_bytes = username.encode('utf-8')
        password_bytes = password.encode('utf-8')

        logger.info(f"Attempting login for user: '{username}'...")

        bytes_needed_or_error = self._login_func(
            username_bytes,
            password_bytes,
            len(password_bytes),
            None,
            0
        )

        if bytes_needed_or_error >= 0:
            raise LoginFailedError(f"Login failed: Native function returned an unexpected positive value during size probe: {bytes_needed_or_error}")
        if bytes_needed_or_error == -1:
            raise LoginFailedError("Login failed: Invalid arguments passed to native function (e.g., null pointers).")
        if bytes_needed_or_error == -2:
            raise LoginFailedError("Login failed: An unhandled exception occurred.")

        required_size = -bytes_needed_or_error
        logger.debug(f"Native library requires a {required_size}-byte buffer for the login result.")

        result_buffer = ctypes.create_string_buffer(required_size)

        bytes_written = self._login_func(
            username_bytes,
            password_bytes,
            len(password_bytes),
            result_buffer,
            required_size
        )

        if bytes_written <= 0:
            raise LoginFailedError(f"Login failed: Native function failed on second call, return code: {bytes_written}")

        login_result_pb = sphere_sdk_types_pb2.SphereError()
        login_result_pb.ParseFromString(result_buffer.raw[:bytes_written])

        if login_result_pb.code == sphere_sdk_types_pb2.ErrorCode.ERROR_CODE_NONE:
            logger.info(f"Login successful for user: '{username}'.")
            self._is_logged_in = True
            return
        else:
            error_msg = login_result_pb.message or "No error message provided."
            try:
                error_name = sphere_sdk_types_pb2.ErrorCode.Name(login_result_pb.code)
            except ValueError:
                error_name = f"UNKNOWN_CODE_{login_result_pb.code}"
        
            logger.error(f"Login failed for user: '{username}'. Reason: {error_msg} (Code: {error_name})")
            raise LoginFailedError(f"Login failed: {error_msg}")

    def logout(self):
        """Logs out from the trading service."""
        if not self._is_logged_in:
            logger.warning("Not logged in, skipping logout call.")
            return

        logger.info("Calling logout function...")
        try:
            self._logout_func()
            logger.info("Logout process complete.")
        except Exception as e:
            logger.error(f"Exception during logout: {e}")
        finally:
            self._is_logged_in = False

    def _internal_on_order_event(self, order_details_protobuf_ptr, order_details_length):
        """
        This method deserializes the Protobuf data and calls the user's Python callback.
        """
        logger.debug(f"Internal callback received: ptr={order_details_protobuf_ptr}, len={order_details_length}")
        try:
            if not order_details_protobuf_ptr or order_details_length <= 0:
                logger.warning("Received order event with no data; ignoring.")
                return

            # Deserialize the wrapper message
            raw_bytes = ctypes.string_at(order_details_protobuf_ptr, order_details_length)
            order_result = sphere_sdk_types_pb2.OrderStacksResult()
            order_result.ParseFromString(raw_bytes)
            logger.debug(f"Deserialized order result: {order_result}")

            if order_result.error.code != sphere_sdk_types_pb2.ErrorCode.ERROR_CODE_NONE:
                try:
                    error_name = sphere_sdk_types_pb2.ErrorCode.Name(order_result.error.code)
                except ValueError:
                    error_name = f"UNKNOWN_CODE_{order_result.error.code}"
                error_msg = order_result.error.message or "No error message provided."
                raise TradingClientError(f"Order event stream reported an error: {error_msg} (Code: {error_name})")

            # If no error, pass the data payload to the SDK consumer's callback.
            if self._user_order_callback:
                try:
                    self._user_order_callback(order_result.data)
                except Exception as e_user_cb:
                    logger.error(f"User callback for order event threw an exception: {e_user_cb}", exc_info=True)
            else:
                logger.warning("Order event data received, but no user callback is registered to handle it.")

        except Exception as e_processing:
            logger.error(f"Failed to process incoming order event: {e_processing}", exc_info=True)

    def subscribe_to_order_events(self, user_callback):
        """
        Subscribes to order events. The provided callback will be invoked when new order events occur.

        Args:
            user_callback (callable): A Python function that accepts one argument:
                                      - The deserialized Protobuf order object.
                                        It will be None if the event had no data.
        Raises:
            NotLoggedInError: If not logged in.
            TradingClientError: If subscription fails for other reasons.
        """
        if not self._is_logged_in:
            raise NotLoggedInError("Cannot subscribe to order events: Not logged in.")
        if not callable(user_callback):
            raise ValueError("The provided callback must be a callable function.")

        logger.info("Subscribing to order events...")
        self._user_order_callback = user_callback

        if self._c_order_event_callback_ptr is None:
             self._c_order_event_callback_ptr = OrderEventCallbackType(self._internal_on_order_event)

        try:
            self._subscribe_orders_func(self._c_order_event_callback_ptr)
            logger.info("Subscription request sent.")
        except Exception as e:
            logger.error(f"Error subscribe function: {e}")
            self._user_order_callback = None
            raise TradingClientError(f"Failed to subscribe to order events: {e}") from e

    def unsubscribe_from_order_events(self):
        """Unsubscribes from order events."""
        if not self._is_logged_in:
            logger.warning("Cannot unsubscribe: Not logged in.")
            
        logger.info("Unsubscribing from order events...")
        try:
            self._subscribe_orders_func(None)
            logger.info("Unsubscription request sent.")
        except Exception as e:
            logger.error(f"Error calling unsubscribe function: {e}")
            raise TradingClientError(f"Failed to unsubscribe from order events: {e}") from e
        finally:
            self._user_order_callback = None
    
            
    def _internal_on_trade_event(self, trade_details_protobuf_ptr, trade_details_length):
        """
        This method deserializes the Protobuf data and calls the user's Python callback.
        """
        logger.debug(f"Internal callback received: ptr={trade_details_protobuf_ptr}, len={trade_details_length}")
        try:
            if not trade_details_protobuf_ptr or trade_details_length <= 0:
                logger.warning("Received trade event with no data; ignoring.")
                return

            # Deserialize the wrapper message
            raw_bytes = ctypes.string_at(trade_details_protobuf_ptr, trade_details_length)
            trade_result = sphere_sdk_types_pb2.TradeResult()
            trade_result.ParseFromString(raw_bytes)
            logger.debug(f"Deserialized trade result: {trade_result}")

            if trade_result.error.code != sphere_sdk_types_pb2.ErrorCode.ERROR_CODE_NONE:
                try:
                    error_name = sphere_sdk_types_pb2.ErrorCode.Name(trade_result.error.code)
                except ValueError:
                    error_name = f"UNKNOWN_CODE_{trade_result.error.code}"
                error_msg = trade_result.error.message or "No error message provided."
                raise TradingClientError(f"trade event stream reported an error: {error_msg} (Code: {error_name})")

            # If no error, pass the data payload to the SDK consumer's callback.
            if self._user_trade_callback:
                try:
                    self._user_trade_callback(trade_result.data)
                except Exception as e_user_cb:
                    logger.error(f"User callback for trade event threw an exception: {e_user_cb}", exc_info=True)
            else:
                logger.warning("trade event data received, but no user callback is registered to handle it.")

        except Exception as e_processing:
            logger.error(f"Failed to process incoming trade event: {e_processing}", exc_info=True)

    def subscribe_to_trade_events(self, user_callback):
        """
        Subscribes to trade events. The provided callback will be invoked when new trade events occur.

        Args:
            user_callback (callable): A Python function that accepts one argument:
                                      - The deserialized Protobuf trade object.
                                        It will be None if the event had no data.
        Raises:
            NotLoggedInError: If not logged in.
            TradingClientError: If subscription fails for other reasons.
        """
        if not self._is_logged_in:
            raise NotLoggedInError("Cannot subscribe to trade events: Not logged in.")
        if not callable(user_callback):
            raise ValueError("The provided callback must be a callable function.")

        logger.info("Subscribing to trade events...")
        self._user_trade_callback = user_callback

        if self._c_trade_event_callback_ptr is None:
             self._c_trade_event_callback_ptr = TradeEventCallbackType(self._internal_on_trade_event)

        try:
            self._subscribe_trades_func(self._c_trade_event_callback_ptr)
            logger.info("Subscription request sent.")
        except Exception as e:
            logger.error(f"Error subscribe function: {e}")
            self._user_trade_callback = None
            raise TradingClientError(f"Failed to subscribe to trade events: {e}") from e

    def unsubscribe_from_trade_events(self):
        """Unsubscribes from trade events."""
        if not self._is_logged_in:
            logger.warning("Cannot unsubscribe: Not logged in.")

        logger.info("Unsubscribing from trade events...")
        try:
            self._subscribe_trades_func(None)
            logger.info("Unsubscription request sent.")
        except Exception as e:
            logger.error(f"Error calling unsubscribe function: {e}")
            raise TradingClientError(f"Failed to unsubscribe from trade events: {e}") from e
        finally:
            self._user_trade_callback = None

    def trade_order(self, trade_request: sphere_sdk_types_pb2.TradeOrderRequestDto):
        """
        Submits a trade order.

        Args:
            trade_request (sphere_sdk_types_pb2.TradeOrderRequestDto): The Protobuf object 
                                      representing the trade request.

        Raises:
            NotLoggedInError: If not logged in.
            TradeOrderFailedError: If the trade order submission fails for any reason.
            ValueError: If the trade_request is not of the correct type.
        """

        if not isinstance(trade_request, sphere_sdk_types_pb2.TradeOrderRequestDto):
            raise ValueError("trade_request must be an instance of sphere_sdk_types_pb2.TradeOrderRequestDto")

        logger.info(f"Submitting trade order: {MessageToDict(trade_request)}")

        request_bytes = trade_request.SerializeToString()

        # First call to get the required buffer size
        bytes_needed_or_error = self._trade_order_func(
            request_bytes,
            len(request_bytes),
            None,
            0
        )

        # Handle native errors from the first call
        if bytes_needed_or_error >= 0:
            raise TradeOrderFailedError(f"Trade order failed: Native function returned an unexpected positive value during size probe: {bytes_needed_or_error}")
        if bytes_needed_or_error == -1:
            raise TradeOrderFailedError("Trade order failed: Invalid arguments passed to native function (e.g., null pointers).")
        if bytes_needed_or_error == -2:
            raise TradeOrderFailedError("Trade order failed: An unhandled exception occurred in the native library.")

        required_size = -bytes_needed_or_error
        logger.debug(f"Native library requires a {required_size}-byte buffer for the trade order result.")

        result_buffer = ctypes.create_string_buffer(required_size)

        # Second call to get the actual result
        bytes_written = self._trade_order_func(
            request_bytes,
            len(request_bytes),
            result_buffer,
            required_size
        )

        if bytes_written <= 0:
            raise TradeOrderFailedError(f"Trade order failed: Native function failed on second call, return code: {bytes_written}")

        result_pb = sphere_sdk_types_pb2.SphereError()
        result_pb.ParseFromString(result_buffer.raw[:bytes_written])

        if result_pb.code == sphere_sdk_types_pb2.ErrorCode.ERROR_CODE_NONE:
            logger.info("Trade order submitted successfully.")
            return result_pb
        else:
            error_msg = result_pb.message or "No error message provided."
            try:
                error_name = sphere_sdk_types_pb2.ErrorCode.Name(result_pb.code)
            except ValueError:
                error_name = f"UNKNOWN_CODE_{result_pb.code}"
        
            logger.error(f"Trade order submission failed. Reason: {error_msg} (Code: {error_name})")
            raise TradeOrderFailedError(f"Trade order failed: {error_msg}")

    def cancel_order(self, cancel_order_request: sphere_sdk_types_pb2.CancelOrderRequestDto):
        """
        Submits a cancel order.

        Args:
            cancel_order_request (sphere_sdk_types_pb2.CancelOrderRequestDto): The Protobuf object 
                                      representing the cancel order request.

        Raises:
            NotLoggedInError: If not logged in.
            CancelOrderFailedError: If the cancel order submission fails for any reason.
            ValueError: If the cancel_order_request is not of the correct type.
        """
        if not self._is_logged_in:
            raise NotLoggedInError("Cannot cancel order: Not logged in.")

        if not isinstance(cancel_order_request, sphere_sdk_types_pb2.CancelOrderRequestDto):
            raise ValueError("cancel_order_request must be an instance of sphere_sdk_types_pb2.CancelOrderRequestDto")

        logger.info(f"Submitting cancel order: {MessageToDict(cancel_order_request)}")

        request_bytes = cancel_order_request.SerializeToString()
        request_bytes_len = len(request_bytes)

        initial_buffer_size = 65536
        result_buffer = create_string_buffer(initial_buffer_size)
        bytes_returned = 0

        try:
            bytes_returned = self._cancel_order_func(
                request_bytes,
                request_bytes_len,
                result_buffer,
                initial_buffer_size
            )

            if bytes_returned < 0:
                if bytes_returned == -1:
                    raise CancelOrderFailedError("Native function reported invalid arguments during cancel order.")
                elif bytes_returned == -2:
                    raise CancelOrderFailedError("Native function reported an unhandled exception during cancel order.")
                else:
                    required_size = -bytes_returned
                    raise CancelOrderFailedError(
                        f"Native function requires a {required_size}-byte buffer, "
                        f"but the provided {initial_buffer_size}-byte buffer was insufficient. "
                        "Consider increasing the initial buffer size or re-introducing dynamic resizing."
                    )
        except Exception as e:
            raise CancelOrderFailedError(f"An unexpected Python error occurred during native call for cancel order: {e}") from e

        if bytes_returned == 0:
            raise CancelOrderFailedError("Native function returned 0 bytes, indicating no data or an unspecified error for cancel order.")

        result_pb = sphere_sdk_types_pb2.SphereError()
        result_pb.ParseFromString(result_buffer.raw[:bytes_returned])

        if result_pb.code == sphere_sdk_types_pb2.ErrorCode.ERROR_CODE_NONE:
            logger.info("Cancel order submitted successfully.")
            return result_pb
        else:
            error_msg = result_pb.message or "No error message provided."
            try:
                error_name = sphere_sdk_types_pb2.ErrorCode.Name(result_pb.code)
            except ValueError:
                error_name = f"UNKNOWN_CODE_{result_pb.code}"
        
            logger.error(f"Cancel order submission failed. Reason: {error_msg} (Code: {error_name})")
            raise CancelOrderFailedError(f"Cancel order failed: {error_msg}")

    def create_trader_flat_order(self, order_request: sphere_sdk_types_pb2.TraderFlatOrderRequestDto) -> sphere_sdk_types_pb2.OrderResult:
        """
        Submits a flat order request for a trader.

        Args:
            order_request (sphere_sdk_types_pb2.TraderFlatOrderRequestDto): The Protobuf object
                                      representing the order request.

        Returns:
            sphere_sdk_types_pb2.OrderResult: The full OrderResult object.

        Raises:
            NotLoggedInError: If not logged in.
            CreateOrderFailedError: If the order submission fails for any reason *before* a valid OrderResult
                                    can be parsed from the native call (e.g., native library errors).
            ValueError: If the order_request is not of the correct type.
        """
        if not self._is_logged_in:
            raise NotLoggedInError("Cannot create trader flat order: Not logged in.")

        if not isinstance(order_request, sphere_sdk_types_pb2.TraderFlatOrderRequestDto):
            raise ValueError("order_request must be an instance of sphere_sdk_types_pb2.TraderFlatOrderRequestDto")

        logger.info(f"Submitting create order: {MessageToDict(order_request)}")

        request_bytes = order_request.SerializeToString()
        request_bytes_len = len(request_bytes)

        initial_buffer_size = 4096
        result_buffer = create_string_buffer(initial_buffer_size)
        bytes_returned = 0

        try:
            bytes_returned = self._create_trader_flat_order_func(
                request_bytes,
                request_bytes_len,
                result_buffer,
                initial_buffer_size
            )

            if bytes_returned < 0:
                if bytes_returned == -1:
                    raise CreateOrderFailedError("Native function reported invalid arguments during create order.")
                elif bytes_returned == -2:
                    raise CreateOrderFailedError("Native function reported an unhandled exception during create order.")
                else:
                    required_size = -bytes_returned
                    logger.debug(f"Native library requires a {required_size}-byte buffer for create order. Resizing and retrying.")

                    result_buffer = create_string_buffer(required_size)
                    bytes_returned = self._create_trader_flat_order_func(
                        request_bytes,
                        request_bytes_len,
                        result_buffer,
                        required_size
                    )

                    if bytes_returned < 0:
                        if bytes_returned == -1:
                            raise CreateOrderFailedError("Native function reported invalid arguments during create order retry.")
                        elif bytes_returned == -2:
                            raise CreateOrderFailedError("Native function reported an unhandled exception during create order retry.")
                        else:
                            raise CreateOrderFailedError(f"Native function returned unexpected error code {bytes_returned} during create order retry.")
        except Exception as e:
            raise CreateOrderFailedError(f"An unexpected Python error occurred during native call for create order: {e}") from e

        if bytes_returned == 0:
            raise CreateOrderFailedError("Native function returned 0 bytes, indicating no data or an unspecified error for create order.")
        
        order_result_pb = sphere_sdk_types_pb2.OrderResult()
        order_result_pb.ParseFromString(result_buffer.raw[:bytes_returned])

        if order_result_pb.error.code == sphere_sdk_types_pb2.ErrorCode.ERROR_CODE_NONE:
            logger.info("Created order successfully.")
            return order_result_pb.data
        else:
            error_msg = order_result_pb.error.message or "No error message provided."
            try:
                error_name = sphere_sdk_types_pb2.ErrorCode.Name(order_result_pb.error.code)
            except ValueError:
                error_name = f"UNKNOWN_CODE_{order_result_pb.error.code}"
            logger.error(f"Create order failed internally. Reason: {error_msg} (Code: {error_name})")
            raise CreateOrderFailedError(f"Create order failed: {error_msg}")

    def create_trader_spread_order(self, order_request: sphere_sdk_types_pb2.TraderSpreadOrderRequestDto) -> sphere_sdk_types_pb2.OrderResult:
        """
        Submits a spread order request for a trader.

        Args:
            order_request (sphere_sdk_types_pb2.TraderSpreadOrderRequestDto): The Protobuf object
                                      representing the order request.

        Returns:
            sphere_sdk_types_pb2.OrderResult: The full OrderResult object.

        Raises:
            NotLoggedInError: If not logged in.
            CreateOrderFailedError: If the order submission fails for any reason *before* a valid OrderResult
                                    can be parsed from the native call (e.g., native library errors).
            ValueError: If the order_request is not of the correct type.
        """
        if not self._is_logged_in:
            raise NotLoggedInError("Cannot create trader spread order: Not logged in.")

        if not isinstance(order_request, sphere_sdk_types_pb2.TraderSpreadOrderRequestDto):
            raise ValueError("order_request must be an instance of sphere_sdk_types_pb2.TraderSpreadOrderRequestDto")

        logger.info(f"Submitting create order: {MessageToDict(order_request)}")

        request_bytes = order_request.SerializeToString()
        request_bytes_len = len(request_bytes)

        initial_buffer_size = 4096
        result_buffer = create_string_buffer(initial_buffer_size)
        bytes_returned = 0

        try:
            bytes_returned = self._create_trader_spread_order_func(
                request_bytes,
                request_bytes_len,
                result_buffer,
                initial_buffer_size
            )

            if bytes_returned < 0:
                if bytes_returned == -1:
                    raise CreateOrderFailedError("Native function reported invalid arguments during create order.")
                elif bytes_returned == -2:
                    raise CreateOrderFailedError("Native function reported an unhandled exception during create order.")
                else:
                    required_size = -bytes_returned
                    logger.debug(f"Native library requires a {required_size}-byte buffer for create order. Resizing and retrying.")

                    result_buffer = create_string_buffer(required_size)
                    bytes_returned = self._create_trader_spread_order_func(
                        request_bytes,
                        request_bytes_len,
                        result_buffer,
                        required_size
                    )

                    if bytes_returned < 0:
                        if bytes_returned == -1:
                            raise CreateOrderFailedError("Native function reported invalid arguments during create order retry.")
                        elif bytes_returned == -2:
                            raise CreateOrderFailedError("Native function reported an unhandled exception during create order retry.")
                        else:
                            raise CreateOrderFailedError(f"Native function returned unexpected error code {bytes_returned} during create order retry.")
        except Exception as e:
            raise CreateOrderFailedError(f"An unexpected Python error occurred during native call for create order: {e}") from e

        if bytes_returned == 0:
            raise CreateOrderFailedError("Native function returned 0 bytes, indicating no data or an unspecified error for create order.")
        
        order_result_pb = sphere_sdk_types_pb2.OrderResult()
        order_result_pb.ParseFromString(result_buffer.raw[:bytes_returned])

        if order_result_pb.error.code == sphere_sdk_types_pb2.ErrorCode.ERROR_CODE_NONE:
            logger.info("Created order successfully.")
            return order_result_pb.data
        else:
            error_msg = order_result_pb.error.message or "No error message provided."
            try:
                error_name = sphere_sdk_types_pb2.ErrorCode.Name(order_result_pb.error.code)
            except ValueError:
                error_name = f"UNKNOWN_CODE_{order_result_pb.error.code}"
            logger.error(f"Create order failed internally. Reason: {error_msg} (Code: {error_name})")
            raise CreateOrderFailedError(f"Create order failed: {error_msg}")

    def create_trader_strip_order(self, order_request: sphere_sdk_types_pb2.TraderStripOrderRequestDto) -> sphere_sdk_types_pb2.OrderResult:
        """
        Submits a strip order request for a trader.

        Args:
            order_request (sphere_sdk_types_pb2.TraderStripOrderRequestDto): The Protobuf object
                                      representing the order request.

        Returns:
            sphere_sdk_types_pb2.OrderResult: The full OrderResult object.

        Raises:
            NotLoggedInError: If not logged in.
            CreateOrderFailedError: If the order submission fails for any reason *before* a valid OrderResult
                                    can be parsed from the native call (e.g., native library errors).
            ValueError: If the order_request is not of the correct type.
        """
        if not self._is_logged_in:
            raise NotLoggedInError("Cannot create trader strip order: Not logged in.")

        if not isinstance(order_request, sphere_sdk_types_pb2.TraderStripOrderRequestDto):
            raise ValueError("order_request must be an instance of sphere_sdk_types_pb2.TraderStripOrderRequestDto")

        logger.info(f"Submitting create order: {MessageToDict(order_request)}")

        request_bytes = order_request.SerializeToString()
        request_bytes_len = len(request_bytes)

        initial_buffer_size = 4096
        result_buffer = create_string_buffer(initial_buffer_size)
        bytes_returned = 0

        try:
            bytes_returned = self._create_trader_strip_order_func(
                request_bytes,
                request_bytes_len,
                result_buffer,
                initial_buffer_size
            )

            if bytes_returned < 0:
                if bytes_returned == -1:
                    raise CreateOrderFailedError("Native function reported invalid arguments during create order.")
                elif bytes_returned == -2:
                    raise CreateOrderFailedError("Native function reported an unhandled exception during create order.")
                else:
                    required_size = -bytes_returned
                    logger.debug(f"Native library requires a {required_size}-byte buffer for create order. Resizing and retrying.")

                    result_buffer = create_string_buffer(required_size)
                    bytes_returned = self._create_trader_strip_order_func(
                        request_bytes,
                        request_bytes_len,
                        result_buffer,
                        required_size
                    )

                    if bytes_returned < 0:
                        if bytes_returned == -1:
                            raise CreateOrderFailedError("Native function reported invalid arguments during create order retry.")
                        elif bytes_returned == -2:
                            raise CreateOrderFailedError("Native function reported an unhandled exception during create order retry.")
                        else:
                            raise CreateOrderFailedError(f"Native function returned unexpected error code {bytes_returned} during create order retry.")
        except Exception as e:
            raise CreateOrderFailedError(f"An unexpected Python error occurred during native call for create order: {e}") from e

        if bytes_returned == 0:
            raise CreateOrderFailedError("Native function returned 0 bytes, indicating no data or an unspecified error for create order.")
        
        order_result_pb = sphere_sdk_types_pb2.OrderResult()
        order_result_pb.ParseFromString(result_buffer.raw[:bytes_returned])

        if order_result_pb.error.code == sphere_sdk_types_pb2.ErrorCode.ERROR_CODE_NONE:
            logger.info("Created order successfully.")
            return order_result_pb.data
        else:
            error_msg = order_result_pb.error.message or "No error message provided."
            try:
                error_name = sphere_sdk_types_pb2.ErrorCode.Name(order_result_pb.error.code)
            except ValueError:
                error_name = f"UNKNOWN_CODE_{order_result_pb.error.code}"
            logger.error(f"Create order failed internally. Reason: {error_msg} (Code: {error_name})")
            raise CreateOrderFailedError(f"Create order failed: {error_msg}")

    def create_trader_fly_order(self, order_request: sphere_sdk_types_pb2.TraderFlyOrderRequestDto) -> sphere_sdk_types_pb2.OrderResult:
        """
        Submits a fly order request for a trader.

        Args:
            order_request (sphere_sdk_types_pb2.TraderFlyOrderRequestDto): The Protobuf object
                                      representing the order request.

        Returns:
            sphere_sdk_types_pb2.OrderResult: The full OrderResult object.

        Raises:
            NotLoggedInError: If not logged in.
            CreateOrderFailedError: If the order submission fails for any reason *before* a valid OrderResult
                                    can be parsed from the native call (e.g., native library errors).
            ValueError: If the order_request is not of the correct type.
        """
        if not self._is_logged_in:
            raise NotLoggedInError("Cannot create trader fly order: Not logged in.")

        if not isinstance(order_request, sphere_sdk_types_pb2.TraderFlyOrderRequestDto):
            raise ValueError("order_request must be an instance of sphere_sdk_types_pb2.TraderFlyOrderRequestDto")

        logger.info(f"Submitting create order: {MessageToDict(order_request)}")

        request_bytes = order_request.SerializeToString()
        request_bytes_len = len(request_bytes)

        initial_buffer_size = 4096
        result_buffer = create_string_buffer(initial_buffer_size)
        bytes_returned = 0

        try:
            bytes_returned = self._create_trader_fly_order_func(
                request_bytes,
                request_bytes_len,
                result_buffer,
                initial_buffer_size
            )

            if bytes_returned < 0:
                if bytes_returned == -1:
                    raise CreateOrderFailedError("Native function reported invalid arguments during create order.")
                elif bytes_returned == -2:
                    raise CreateOrderFailedError("Native function reported an unhandled exception during create order.")
                else:
                    required_size = -bytes_returned
                    logger.debug(f"Native library requires a {required_size}-byte buffer for create order. Resizing and retrying.")

                    result_buffer = create_string_buffer(required_size)
                    bytes_returned = self._create_trader_fly_order_func(
                        request_bytes,
                        request_bytes_len,
                        result_buffer,
                        required_size
                    )

                    if bytes_returned < 0:
                        if bytes_returned == -1:
                            raise CreateOrderFailedError("Native function reported invalid arguments during create order retry.")
                        elif bytes_returned == -2:
                            raise CreateOrderFailedError("Native function reported an unhandled exception during create order retry.")
                        else:
                            raise CreateOrderFailedError(f"Native function returned unexpected error code {bytes_returned} during create order retry.")
        except Exception as e:
            raise CreateOrderFailedError(f"An unexpected Python error occurred during native call for create order: {e}") from e

        if bytes_returned == 0:
            raise CreateOrderFailedError("Native function returned 0 bytes, indicating no data or an unspecified error for create order.")
        
        order_result_pb = sphere_sdk_types_pb2.OrderResult()
        order_result_pb.ParseFromString(result_buffer.raw[:bytes_returned])

        if order_result_pb.error.code == sphere_sdk_types_pb2.ErrorCode.ERROR_CODE_NONE:
            logger.info("Created order successfully.")
            return order_result_pb.data
        else:
            error_msg = order_result_pb.error.message or "No error message provided."
            try:
                error_name = sphere_sdk_types_pb2.ErrorCode.Name(order_result_pb.error.code)
            except ValueError:
                error_name = f"UNKNOWN_CODE_{order_result_pb.error.code}"
            logger.error(f"Create order failed internally. Reason: {error_msg} (Code: {error_name})")
            raise CreateOrderFailedError(f"Create order failed: {error_msg}")

    def create_trader_strip_order(self, order_request: sphere_sdk_types_pb2.TraderStripOrderRequestDto) -> sphere_sdk_types_pb2.OrderResult:
        """
        Submits a strip order request for a trader.

        Args:
            order_request (sphere_sdk_types_pb2.TraderStripOrderRequestDto): The Protobuf object
                                      representing the order request.

        Returns:
            sphere_sdk_types_pb2.OrderResult: The full OrderResult object.

        Raises:
            NotLoggedInError: If not logged in.
            CreateOrderFailedError: If the order submission fails for any reason *before* a valid OrderResult
                                    can be parsed from the native call (e.g., native library errors).
            ValueError: If the order_request is not of the correct type.
        """
        if not self._is_logged_in:
            raise NotLoggedInError("Cannot create trader strip order: Not logged in.")

        if not isinstance(order_request, sphere_sdk_types_pb2.TraderStripOrderRequestDto):
            raise ValueError("order_request must be an instance of sphere_sdk_types_pb2.TraderStripOrderRequestDto")

        logger.info(f"Submitting create order: {MessageToDict(order_request)}")

        request_bytes = order_request.SerializeToString()
        request_bytes_len = len(request_bytes)

        initial_buffer_size = 4096
        result_buffer = create_string_buffer(initial_buffer_size)
        bytes_returned = 0

        try:
            bytes_returned = self._create_trader_strip_order_func(
                request_bytes,
                request_bytes_len,
                result_buffer,
                initial_buffer_size
            )

            if bytes_returned < 0:
                if bytes_returned == -1:
                    raise CreateOrderFailedError("Native function reported invalid arguments during create order.")
                elif bytes_returned == -2:
                    raise CreateOrderFailedError("Native function reported an unhandled exception during create order.")
                else:
                    required_size = -bytes_returned
                    logger.debug(f"Native library requires a {required_size}-byte buffer for create order. Resizing and retrying.")

                    result_buffer = create_string_buffer(required_size)
                    bytes_returned = self._create_trader_strip_order_func(
                        request_bytes,
                        request_bytes_len,
                        result_buffer,
                        required_size
                    )

                    if bytes_returned < 0:
                        if bytes_returned == -1:
                            raise CreateOrderFailedError("Native function reported invalid arguments during create order retry.")
                        elif bytes_returned == -2:
                            raise CreateOrderFailedError("Native function reported an unhandled exception during create order retry.")
                        else:
                            raise CreateOrderFailedError(f"Native function returned unexpected error code {bytes_returned} during create order retry.")
        except Exception as e:
            raise CreateOrderFailedError(f"An unexpected Python error occurred during native call for create order: {e}") from e

        if bytes_returned == 0:
            raise CreateOrderFailedError("Native function returned 0 bytes, indicating no data or an unspecified error for create order.")
        
        order_result_pb = sphere_sdk_types_pb2.OrderResult()
        order_result_pb.ParseFromString(result_buffer.raw[:bytes_returned])

        if order_result_pb.error.code == sphere_sdk_types_pb2.ErrorCode.ERROR_CODE_NONE:
            logger.info("Created order successfully.")
            return order_result_pb.data
        else:
            error_msg = order_result_pb.error.message or "No error message provided."
            try:
                error_name = sphere_sdk_types_pb2.ErrorCode.Name(order_result_pb.error.code)
            except ValueError:
                error_name = f"UNKNOWN_CODE_{order_result_pb.error.code}"
            logger.error(f"Create order failed internally. Reason: {error_msg} (Code: {error_name})")
            raise CreateOrderFailedError(f"Create order failed: {error_msg}")
    
    def update_trader_flat_order(self, order_update_request: sphere_sdk_types_pb2.TraderUpdateFlatOrderRequestDto) -> sphere_sdk_types_pb2.OrderResult:
        """
        Submits an update flat order request for a trader.

        Args:
            order_update_request (sphere_sdk_types_pb2.TraderUpdateFlatOrderRequestDto): The Protobuf object
                                      representing the update order request.

        Returns:
            sphere_sdk_types_pb2.OrderResult: The full OrderResult object, including data and error information.

        Raises:
            NotLoggedInError: If not logged in.
            UpdateOrderFailedError: If the update order submission fails for any reason.
            ValueError: If the order_update_request is not of the correct type.
        """
        if not self._is_logged_in:
            raise NotLoggedInError("Cannot update trader order: Not logged in.")

        if not isinstance(order_update_request, sphere_sdk_types_pb2.TraderUpdateFlatOrderRequestDto):
            raise ValueError("order_update_request must be an instance of sphere_sdk_types_pb2.TraderUpdateFlatOrderRequestDto")

        logger.info(f"Submitting update flat order request: {MessageToDict(order_update_request)}")

        request_bytes = order_update_request.SerializeToString()
        request_bytes_len = len(request_bytes)

        initial_buffer_size = 4096
        result_buffer = create_string_buffer(initial_buffer_size)
        bytes_returned = 0

        try:
            bytes_returned = self._update_trader_flat_order_func(
                request_bytes,
                request_bytes_len,
                result_buffer,
                initial_buffer_size
            )

            if bytes_returned < 0:
                if bytes_returned == -1:
                    raise UpdateOrderFailedError("Native function reported invalid arguments during update flat order.")
                elif bytes_returned == -2:
                    raise UpdateOrderFailedError("Native function reported an unhandled exception during update flat order.")
                else:
                    required_size = -bytes_returned
                    logger.debug(f"Native library requires a {required_size}-byte buffer for update flat order. Resizing and retrying.")

                    result_buffer = create_string_buffer(required_size)
                    bytes_returned = self._update_trader_flat_order_func(
                        request_bytes,
                        request_bytes_len,
                        result_buffer,
                        required_size
                    )

                    if bytes_returned < 0:
                        if bytes_returned == -1:
                            raise UpdateOrderFailedError("Native function reported invalid arguments during update flat order retry.")
                        elif bytes_returned == -2:
                            raise UpdateOrderFailedError("Native function reported an unhandled exception during update flat order retry.")
                        else:
                            raise UpdateOrderFailedError(f"Native function returned unexpected error code {bytes_returned} during update flat order retry.")
        except Exception as e:
            raise UpdateOrderFailedError(f"An unexpected Python error occurred during native call for update flat order: {e}") from e

        if bytes_returned == 0:
            raise UpdateOrderFailedError("Native function returned 0 bytes, indicating no data or an unspecified error for update order.")
        
        order_result_pb = sphere_sdk_types_pb2.OrderResult()
        order_result_pb.ParseFromString(result_buffer.raw[:bytes_returned])

        if order_result_pb.error.code == sphere_sdk_types_pb2.ErrorCode.ERROR_CODE_NONE:
            logger.info("Flat order updated successfully.")
            return order_result_pb.data
        else:
            error_msg = order_result_pb.error.message or "No error message provided."
            try:
                error_name = sphere_sdk_types_pb2.ErrorCode.Name(order_result_pb.error.code)
            except ValueError:
                error_name = f"UNKNOWN_CODE_{order_result_pb.error.code}"
            logger.error(f"Update order failed internally. Reason: {error_msg} (Code: {error_name})")
            raise UpdateOrderFailedError(f"Update flat order failed: {error_msg}")

    def update_trader_spread_order(self, order_update_request: sphere_sdk_types_pb2.TraderUpdateSpreadOrderRequestDto) -> sphere_sdk_types_pb2.OrderResult:
        """
        Submits an update spread order request for a trader.

        Args:
            order_update_request (sphere_sdk_types_pb2.TraderUpdateSpreadOrderRequestDto): The Protobuf object
                                      representing the update order request.

        Returns:
            sphere_sdk_types_pb2.OrderResult: The full OrderResult object, including data and error information.

        Raises:
            NotLoggedInError: If not logged in.
            UpdateOrderFailedError: If the update order submission fails for any reason.
            ValueError: If the order_update_request is not of the correct type.
        """
        if not self._is_logged_in:
            raise NotLoggedInError("Cannot update trader order: Not logged in.")

        if not isinstance(order_update_request, sphere_sdk_types_pb2.TraderUpdateSpreadOrderRequestDto):
            raise ValueError("order_update_request must be an instance of sphere_sdk_types_pb2.TraderUpdateSpreadOrderRequestDto")

        logger.info(f"Submitting update spread order request: {MessageToDict(order_update_request)}")

        request_bytes = order_update_request.SerializeToString()
        request_bytes_len = len(request_bytes)

        initial_buffer_size = 4096
        result_buffer = create_string_buffer(initial_buffer_size)
        bytes_returned = 0

        try:
            bytes_returned = self._update_trader_spread_order_func(
                request_bytes,
                request_bytes_len,
                result_buffer,
                initial_buffer_size
            )

            if bytes_returned < 0:
                if bytes_returned == -1:
                    raise UpdateOrderFailedError("Native function reported invalid arguments during update spread order.")
                elif bytes_returned == -2:
                    raise UpdateOrderFailedError("Native function reported an unhandled exception during update spread order.")
                else:
                    required_size = -bytes_returned
                    logger.debug(f"Native library requires a {required_size}-byte buffer for update spread order. Resizing and retrying.")

                    result_buffer = create_string_buffer(required_size)
                    bytes_returned = self._update_trader_spread_order_func(
                        request_bytes,
                        request_bytes_len,
                        result_buffer,
                        required_size
                    )

                    if bytes_returned < 0:
                        if bytes_returned == -1:
                            raise UpdateOrderFailedError("Native function reported invalid arguments during update spread order retry.")
                        elif bytes_returned == -2:
                            raise UpdateOrderFailedError("Native function reported an unhandled exception during update spread order retry.")
                        else:
                            raise UpdateOrderFailedError(f"Native function returned unexpected error code {bytes_returned} during update spread order retry.")
        except Exception as e:
            raise UpdateOrderFailedError(f"An unexpected Python error occurred during native call for update spread order: {e}") from e

        if bytes_returned == 0:
            raise UpdateOrderFailedError("Native function returned 0 bytes, indicating no data or an unspecified error for update order.")
        
        order_result_pb = sphere_sdk_types_pb2.OrderResult()
        order_result_pb.ParseFromString(result_buffer.raw[:bytes_returned])

        if order_result_pb.error.code == sphere_sdk_types_pb2.ErrorCode.ERROR_CODE_NONE:
            logger.info("Spread order updated successfully.")
            return order_result_pb.data
        else:
            error_msg = order_result_pb.error.message or "No error message provided."
            try:
                error_name = sphere_sdk_types_pb2.ErrorCode.Name(order_result_pb.error.code)
            except ValueError:
                error_name = f"UNKNOWN_CODE_{order_result_pb.error.code}"
            logger.error(f"Update order failed internally. Reason: {error_msg} (Code: {error_name})")
            raise UpdateOrderFailedError(f"Update spread order failed: {error_msg}")

    def update_trader_strip_order(self, order_update_request: sphere_sdk_types_pb2.TraderUpdateStripOrderRequestDto) -> sphere_sdk_types_pb2.OrderResult:
        """
        Submits an update strip order request for a trader.

        Args:
            order_update_request (sphere_sdk_types_pb2.TraderUpdateStripOrderRequestDto): The Protobuf object
                                      representing the update order request.

        Returns:
            sphere_sdk_types_pb2.OrderResult: The full OrderResult object, including data and error information.

        Raises:
            NotLoggedInError: If not logged in.
            UpdateOrderFailedError: If the update order submission fails for any reason.
            ValueError: If the order_update_request is not of the correct type.
        """
        if not self._is_logged_in:
            raise NotLoggedInError("Cannot update trader order: Not logged in.")

        if not isinstance(order_update_request, sphere_sdk_types_pb2.TraderUpdateStripOrderRequestDto):
            raise ValueError("order_update_request must be an instance of sphere_sdk_types_pb2.TraderUpdateStripOrderRequestDto")

        logger.info(f"Submitting update strip order request: {MessageToDict(order_update_request)}")

        request_bytes = order_update_request.SerializeToString()
        request_bytes_len = len(request_bytes)

        initial_buffer_size = 4096
        result_buffer = create_string_buffer(initial_buffer_size)
        bytes_returned = 0

        try:
            bytes_returned = self._update_trader_strip_order_func(
                request_bytes,
                request_bytes_len,
                result_buffer,
                initial_buffer_size
            )

            if bytes_returned < 0:
                if bytes_returned == -1:
                    raise UpdateOrderFailedError("Native function reported invalid arguments during update strip order.")
                elif bytes_returned == -2:
                    raise UpdateOrderFailedError("Native function reported an unhandled exception during update strip order.")
                else:
                    required_size = -bytes_returned
                    logger.debug(f"Native library requires a {required_size}-byte buffer for update strip order. Resizing and retrying.")

                    result_buffer = create_string_buffer(required_size)
                    bytes_returned = self._update_trader_strip_order_func(
                        request_bytes,
                        request_bytes_len,
                        result_buffer,
                        required_size
                    )

                    if bytes_returned < 0:
                        if bytes_returned == -1:
                            raise UpdateOrderFailedError("Native function reported invalid arguments during update strip order retry.")
                        elif bytes_returned == -2:
                            raise UpdateOrderFailedError("Native function reported an unhandled exception during update strip order retry.")
                        else:
                            raise UpdateOrderFailedError(f"Native function returned unexpected error code {bytes_returned} during update strip order retry.")
        except Exception as e:
            raise UpdateOrderFailedError(f"An unexpected Python error occurred during native call for update strip order: {e}") from e

        if bytes_returned == 0:
            raise UpdateOrderFailedError("Native function returned 0 bytes, indicating no data or an unspecified error for update order.")
        
        order_result_pb = sphere_sdk_types_pb2.OrderResult()
        order_result_pb.ParseFromString(result_buffer.raw[:bytes_returned])

        if order_result_pb.error.code == sphere_sdk_types_pb2.ErrorCode.ERROR_CODE_NONE:
            logger.info("Strip order updated successfully.")
            return order_result_pb.data
        else:
            error_msg = order_result_pb.error.message or "No error message provided."
            try:
                error_name = sphere_sdk_types_pb2.ErrorCode.Name(order_result_pb.error.code)
            except ValueError:
                error_name = f"UNKNOWN_CODE_{order_result_pb.error.code}"
            logger.error(f"Update order failed internally. Reason: {error_msg} (Code: {error_name})")
            raise UpdateOrderFailedError(f"Update strip order failed: {error_msg}")

    def update_trader_fly_order(self, order_update_request: sphere_sdk_types_pb2.TraderUpdateFlyOrderRequestDto) -> sphere_sdk_types_pb2.OrderResult:
        """
        Submits an update fly order request for a trader.

        Args:
            order_update_request (sphere_sdk_types_pb2.TraderUpdateFlyOrderRequestDto): The Protobuf object
                                      representing the update order request.

        Returns:
            sphere_sdk_types_pb2.OrderResult: The full OrderResult object, including data and error information.

        Raises:
            NotLoggedInError: If not logged in.
            UpdateOrderFailedError: If the update order submission fails for any reason.
            ValueError: If the order_update_request is not of the correct type.
        """
        if not self._is_logged_in:
            raise NotLoggedInError("Cannot update trader order: Not logged in.")

        if not isinstance(order_update_request, sphere_sdk_types_pb2.TraderUpdateFlyOrderRequestDto):
            raise ValueError("order_update_request must be an instance of sphere_sdk_types_pb2.TraderUpdateFlyOrderRequestDto")

        logger.info(f"Submitting update fly order request: {MessageToDict(order_update_request)}")

        request_bytes = order_update_request.SerializeToString()
        request_bytes_len = len(request_bytes)

        initial_buffer_size = 4096
        result_buffer = create_string_buffer(initial_buffer_size)
        bytes_returned = 0

        try:
            bytes_returned = self._update_trader_fly_order_func(
                request_bytes,
                request_bytes_len,
                result_buffer,
                initial_buffer_size
            )

            if bytes_returned < 0:
                if bytes_returned == -1:
                    raise UpdateOrderFailedError("Native function reported invalid arguments during update fly order.")
                elif bytes_returned == -2:
                    raise UpdateOrderFailedError("Native function reported an unhandled exception during update fly order.")
                else:
                    required_size = -bytes_returned
                    logger.debug(f"Native library requires a {required_size}-byte buffer for update fly order. Resizing and retrying.")

                    result_buffer = create_string_buffer(required_size)
                    bytes_returned = self._update_trader_fly_order_func(
                        request_bytes,
                        request_bytes_len,
                        result_buffer,
                        required_size
                    )

                    if bytes_returned < 0:
                        if bytes_returned == -1:
                            raise UpdateOrderFailedError("Native function reported invalid arguments during update fly order retry.")
                        elif bytes_returned == -2:
                            raise UpdateOrderFailedError("Native function reported an unhandled exception during update fly order retry.")
                        else:
                            raise UpdateOrderFailedError(f"Native function returned unexpected error code {bytes_returned} during update fly order retry.")
        except Exception as e:
            raise UpdateOrderFailedError(f"An unexpected Python error occurred during native call for update fly order: {e}") from e

        if bytes_returned == 0:
            raise UpdateOrderFailedError("Native function returned 0 bytes, indicating no data or an unspecified error for update order.")
        
        order_result_pb = sphere_sdk_types_pb2.OrderResult()
        order_result_pb.ParseFromString(result_buffer.raw[:bytes_returned])

        if order_result_pb.error.code == sphere_sdk_types_pb2.ErrorCode.ERROR_CODE_NONE:
            logger.info("Fly order updated successfully.")
            return order_result_pb.data
        else:
            error_msg = order_result_pb.error.message or "No error message provided."
            try:
                error_name = sphere_sdk_types_pb2.ErrorCode.Name(order_result_pb.error.code)
            except ValueError:
                error_name = f"UNKNOWN_CODE_{order_result_pb.error.code}"
            logger.error(f"Update order failed internally. Reason: {error_msg} (Code: {error_name})")
            raise UpdateOrderFailedError(f"Update fly order failed: {error_msg}")
    
    def get_instruments(self) -> sphere_sdk_types_pb2.InstrumentsResult:
        """
        Retrieves a list of all available instruments.

        Returns:
            An InstrumentsResult protobuf message containing the list of instruments or an error.

        Raises:
            NotLoggedInError: If the client is not logged in.
            TradingClientError: For general communication or library errors.
            GetInstrumentsFailedError: If unable to return instruments
        """
        if not self._is_logged_in:
            raise NotLoggedInError()

        required_size_or_error = self._get_instruments_func(None, 0)

        if required_size_or_error >= 0:
        # If 0, no data. If > 0, it's an error on a null buffer call.
            if required_size_or_error > 0:
                raise TradingClientError("get_instruments returned a positive size on a null buffer.")
            raise GetInstrumentsFailedError()

        buffer_size = -required_size_or_error
        buffer = create_string_buffer(buffer_size)
        
        bytes_written = self._get_instruments_func(buffer, buffer_size)

        if bytes_written < 0:
            raise TradingClientError(f"Failed to get instruments. Native call returned error code: {bytes_written}")

        result = sphere_sdk_types_pb2.InstrumentsResult()
        result.ParseFromString(buffer.raw[:bytes_written])

        if result.error.code == sphere_sdk_types_pb2.ErrorCode.ERROR_CODE_NONE:
            logger.info("Get Instruments retrieved successfully.")
            return result.data
        else:
            error_msg = result.error.message or "No error message provided."
            try:
                error_name = sphere_sdk_types_pb2.ErrorCode.Name(result.error.code)
            except ValueError:
                error_name = f"UNKNOWN_CODE_{result.error.code}"
        
            logger.error(f"Get Instruments failed. Reason: {error_msg} (Code: {error_name})")
            raise GetInstrumentsFailedError(f"Get Instruments failed: {error_msg}")


    def get_expiries_by_instrument_name(self, instrument_name: str) -> sphere_sdk_types_pb2.ExpiriesResult:
        """
        Retrieves a list of expiries for a given instrument name.

        Args:
            instrument_name: The name of the instrument (e.g., 'Naphtha MOPJ').

        Returns:
            An ExpiriesResult protobuf message containing the list of expiries or an error.

        Raises:
            NotLoggedInError: If the client is not logged in.
            TradingClientError: For general communication or library errors.
            GetExpiriesFailedError: If unable to return expiries for given instrument name
        """
        if not self._is_logged_in:
            raise NotLoggedInError()

        instrument_name_bytes = instrument_name.encode('utf-8')

        required_size_or_error = self._get_expiries_func(instrument_name_bytes, None, 0)
        
        if required_size_or_error >= 0:
            if required_size_or_error > 0:
                raise TradingClientError("get_expiries_by_instrument_name returned a positive size on a null buffer.")
            return GetExpiriesFailedError()

        buffer_size = -required_size_or_error
        buffer = create_string_buffer(buffer_size)
        
        bytes_written = self._get_expiries_func(instrument_name_bytes, buffer, buffer_size)

        if bytes_written < 0:
            raise TradingClientError(f"Failed to get expiries. Native call returned error code: {bytes_written}")

        result = sphere_sdk_types_pb2.ExpiriesResult()
        result.ParseFromString(buffer.raw[:bytes_written])

        if result.error.code == sphere_sdk_types_pb2.ErrorCode.ERROR_CODE_NONE:
            logger.info("Get Expiries by Instrument Name retrieved successfully.")
            return result.data
        else:
            error_msg = result.error.message or "No error message provided."
            try:
                error_name = sphere_sdk_types_pb2.ErrorCode.Name(result.error.code)
            except ValueError:
                error_name = f"UNKNOWN_CODE_{result.error.code}"
        
            logger.error(f"Get Expiries by Instrument Name failed. Reason: {error_msg} (Code: {error_name})")
            raise GetExpiriesFailedError(f"Get Expiries by Instrument Name failed: {error_msg}")

    def get_brokers(self) -> sphere_sdk_types_pb2.BrokersResult:
        """
        Retrieves a list of all brokers.

        Returns:
            An BrokersResult protobuf message containing the list of brokers or an error.

        Raises:
            NotLoggedInError: If the client is not logged in.
            TradingClientError: For general communication or library errors.
            GetBrokersFailedError: If unable to return brokers
        """
        if not self._is_logged_in:
            raise NotLoggedInError()

        required_size_or_error = self._get_brokers_func(None, 0)

        if required_size_or_error >= 0:
            if required_size_or_error > 0:
                raise TradingClientError("get_brokers returned a positive size on a null buffer.")
            return GetBrokersFailedError()

        buffer_size = -required_size_or_error
        buffer = create_string_buffer(buffer_size)
        
        bytes_written = self._get_brokers_func(buffer, buffer_size)

        if bytes_written < 0:
            raise TradingClientError(f"Failed to get brokers. Native call returned error code: {bytes_written}")

        result = sphere_sdk_types_pb2.BrokersResult()
        result.ParseFromString(buffer.raw[:bytes_written])
        
        if result.error.code == sphere_sdk_types_pb2.ErrorCode.ERROR_CODE_NONE:
            logger.info("Get Brokers retrieved successfully.")
            return result.data
        else:
            error_msg = result.error.message or "No error message provided."
            try:
                error_name = sphere_sdk_types_pb2.ErrorCode.Name(result.error.code)
            except ValueError:
                error_name = f"UNKNOWN_CODE_{result.error.code}"
        
            logger.error(f"Get Brokers failed. Reason: {error_msg} (Code: {error_name})")
            raise GetBrokersFailedError(f"Get Brokers failed: {error_msg}")

    def get_clearing_options(self) -> sphere_sdk_types_pb2.ClearingOptionsResult:
        """
        Retrieves a list of all clearing options.

        Returns:
            An ClearingOptionsResult protobuf message containing the list of clearing options or an error.

        Raises:
            NotLoggedInError: If the client is not logged in.
            TradingClientError: For general communication or library errors.
            GetClearingOptionsFailedError: If unable to return clearing options
        """
        if not self._is_logged_in:
            raise NotLoggedInError()

        required_size_or_error = self._get_clearing_options_func(None, 0)

        if required_size_or_error >= 0:
            if required_size_or_error > 0:
                raise TradingClientError("get_clearing_options returned a positive size on a null buffer.")
            return GetClearingOptionsFailedError()

        buffer_size = -required_size_or_error
        buffer = create_string_buffer(buffer_size)
        
        bytes_written = self._get_clearing_options_func(buffer, buffer_size)

        if bytes_written < 0:
            raise TradingClientError(f"Failed to get clearing options. Native call returned error code: {bytes_written}")

        result = sphere_sdk_types_pb2.ClearingOptionsResult()
        result.ParseFromString(buffer.raw[:bytes_written])
        
        if result.error.code == sphere_sdk_types_pb2.ErrorCode.ERROR_CODE_NONE:
            logger.info("Get Clearing Options retrieved successfully.")
            return result.data
        else:
            error_msg = result.error.message or "No error message provided."
            try:
                error_name = sphere_sdk_types_pb2.ErrorCode.Name(result.error.code)
            except ValueError:
                error_name = f"UNKNOWN_CODE_{result.error.code}"
        
            logger.error(f"Get Clearing Options failed. Reason: {error_msg} (Code: {error_name})")
            raise GetClearingOptionsFailedError(f"Get Clearing Options failed: {error_msg}")


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info("Exiting SDK context.")
        if self._is_logged_in:
            logger.info("Automatically logging out due to context exit...")
            if self._user_order_callback:
                try:
                    self.unsubscribe_from_order_events()
                except TradingClientError as e:
                    logger.warning(f"Could not unsubscribe from orders during context exit: {e}")
            if self._user_trade_callback:
                try:
                    self.unsubscribe_from_trade_events()
                except TradingClientError as e:
                    logger.warning(f"Could not unsubscribe from trades during context exit: {e}")
            self.logout()