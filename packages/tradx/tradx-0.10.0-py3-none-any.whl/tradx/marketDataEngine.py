from xts_api_client.market_data_socket_client import MarketDataSocketClient
from xts_api_client.market_data_socket import MDSocket_io
from xts_api_client.xts_connect_async import XTSConnect
import xts_api_client.helper.helper as helper
from typing import Any, List, Dict
from tradx.logger.logger import *
from tradx.baseClass.baseAlgo import BaseAlgo
from tradx.baseClass.market.candleData import CandleData
from tradx.baseClass.market.marketDepthData import MarketDepthData
from tradx.baseClass.market.marketStatusData import MarketStatusData
from tradx.baseClass.market.openInterestData import OpenInterestData
from tradx.baseClass.market.ltpData import LtpData
from tradx.baseClass.market.touchLineData import TouchLineData
from tradx.baseClass.market.index import Index
from tradx.baseClass.market.optionsInstrument import OptionManager, OptionsInstrument
from tradx.baseClass.interactive.tradeEvent import TradeEvent
from tradx.algoContainer import SubcribeContainer
from datetime import datetime
import json
import pandas
import asyncio
import pandas as pd
import math
from decimal import Decimal
from io import StringIO


def cm_master_string_to_df(cm_master_result: str) -> pd.DataFrame:
    """
    Converts the response of cm_master API to a pandas DataFrame.

    This function takes a string response from the cm_master API, which contains data separated by the '|' character,
    and converts it into a pandas DataFrame. The DataFrame will have predefined column headers.

    Parameters:
        cm_master_result (str): The string response from the cm_master API.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the parsed data from the cm_master_result string.
    """
    col_header = [
        "ExchangeSegment",
        "ExchangeInstrumentID",
        "InstrumentType",
        "Name",
        "Description",
        "Series",
        "NameWithSeries",
        "InstrumentID",
        "PriceBand_High",
        "PriceBand_Low",
        "FreezeQty",
        "TickSize",
        "LotSize",
        "Multiplier",
        "DisplayName",
        "ISIN",
        "PriceNumerator",
        "PriceDenominator",
        "DetailedDescription",
        "ExtendedSurvlndicator",
        "Cautionlndicator",
        "GSMIndicator",
    ]
    _dtype = {
        "ExchangeSegment": str,
        "ExchangeInstrumentID": int,
        "InstrumentType": int,
        "Name": str,
        "Description": str,
        "Series": str,
        "NameWithSeries": str,
        "InstrumentID": int,
        "LotSize": int,
        "Multiplier": int,
        "DisplayName": str,
        "ISIN": str,
        "PriceNumerator": int,
        "PriceDenominator": int,
        "DetailedDescription": str,
        "ExtendedSurvlndicator": int,
        "Cautionlndicator": int,
        "GSMIndicator": int,
    }
    _converters = {
        "PriceBand_High": Decimal,
        "PriceBand_Low": Decimal,
        "TickSize": Decimal,
        "FreezeQty": float,  # Define FreezeQty as float first
    }

    cm_master_df = pd.read_csv(
        StringIO(cm_master_result),
        sep="|",
        low_memory=False,
        header=None,
        names=col_header,
        dtype=_dtype,
        converters=_converters,
    )

    cm_master_df["FreezeQty"] = cm_master_df["FreezeQty"].apply(
        lambda x: int(math.floor(x))
    )  # Floor and convert to int

    return cm_master_df


class marketDataEngine(MarketDataSocketClient):
    """Class for market DATA API obj"""

    def __init__(
        self,
        api_key: str,
        api_password: str,
        source: str,
        root: str,
        user_logger: logging.Logger = None,
    ) -> None:
        """
        Initializes the MarketDataEngine object.
        Args:
            api_key (str): The API key for authentication.
            api_password (str): The API password for authentication.
            source (str): The data source.
            root (str): The root directory.
            user_logger (logging.Logger, optional): Logger for user-defined logging. Defaults to None.
        Raises:
            AssertionError: If any of the required arguments (api_key, api_password, source, root) are not provided.
        Attributes:
            _api_key (str): The API key for authentication.
            _api_password (str): The API password for authentication.
            _source (str): The data source.
            _root (str): The root directory.
            exchange_to_exchangeSegments (dict): Mapping of exchanges to exchange segments.
            index_to_exchangeSegmentId (DualHashMap): Mapping of index to exchange segment IDs.
            F_MASTER_DF (pandas.DataFrame): DataFrame for F_MASTER data.
            O_MASTER_DF (pandas.DataFrame): DataFrame for O_MASTER data.
            CM_MASTER_DF (pandas.DataFrame): DataFrame for CM_MASTER data.
            subscribe_manager (AlgoContainer): Manager for subscription algorithms.
            set_marketDataToken (str): Token for market data.
            set_userID (str): User ID.
            user_logger (logging.Logger): Logger for user-defined logging.
        """
        assert api_key, "API key is required"
        assert api_password, "API password is required"
        assert source, "Source is required"
        assert root, "Root is required"
        self.isConnected: bool = False
        self.isLive: bool = False
        self._api_key: str = api_key
        self._api_password: str = api_password
        self._source: str = source
        self._root: str = root
        self.exchange_to_exchangeSegments: dict = None
        self.index_list: List[Index] = []
        self.F_MASTER_DF: pandas.DataFrame = None
        self.option_manager: OptionManager = None
        self.CM_MASTER_DF: pandas.DataFrame = None
        self.subscribe_manager = SubcribeContainer()
        self.set_marketDataToken: str = None
        self.set_userID: str = None
        self.set_isInvestorClient: str = None
        self.user_logger = user_logger

        if self.user_logger:
            self.user_logger.info(
                "Market Data Engine Object initialized.",
                caller="marketDataEngine.__init__",
            )

    async def on_event_instrument_change_partial(self, data):
        """On receiving message code 1105:Instrument Change partial"""
        return

    async def initialize(self) -> None:
        """
        Asynchronously initializes the market data engine.
        This method performs the necessary setup by logging in and
        establishing a connection to the socket.
        Returns:
            None
        """
        await self.login()
        await self.socket.connect()

    async def initializeClient(self, response) -> None:
        self.xt = XTSConnect(
            self._api_key, self._api_password, self._source, self._root
        )
        self.isConnected = True
        self.xt._set_common_variables(
            response["token"], response["userID"], response["isInvestorClient"]
        )
        print("Initialized trade client.")

    async def on_event_candle_data_full(self, message: str) -> None:
        """
        Handles the full candle data event.
        This asynchronous method is triggered when a full candle data event is received.
        It processes the incoming message, converts it into a CandleData object, and
        broadcasts it to the subscribers.
        Args:
            message (str): The incoming message containing candle data in string format.
        Returns:
            None
        """
        __ = CandleData(message)
        if self.user_logger:
            self.user_logger.info(
                f"1505:Candle Data full;{__}",
                caller="marketDataEngine.on_event_candle_data_full",
            )
        asyncio.ensure_future(self.subscribe_manager.broadcast(__))

    async def on_event_market_data_full(self, data):
        """On receiving message code 1502:Market Data full"""
        __ = MarketDepthData(data)
        if self.user_logger:
            self.user_logger.info(
                f"1502:Market Data full;{__}",
                caller="marketDataEngine.on_event_market_data_full",
            )

    async def on_event_market_status_full(self, data):
        """On receiving message code 1507:Market Status full"""
        # __ = MarketStatusData(data)
        __ = data
        if self.user_logger:
            self.user_logger.info(
                f"1507:Market Status full;{__}",
                caller="marketDataEngine.on_event_market_status_full",
            )

    async def on_event_last_traded_price_full(self, data):
        """On receiving message code 1512:LTP full"""
        __ = LtpData(data)
        if self.user_logger:
            self.user_logger.info(
                f"1512:LTP full;{__}",
                caller="marketDataEngine.on_event_last_traded_price_full",
            )

    async def on_event_openinterest_full(self, data):
        """On receiving message code 1510:OpenInterest full"""
        __ = OpenInterestData(data)
        if self.user_logger:
            self.user_logger.info(
                f"1510:OpenInterest full;{__}",
                caller="marketDataEngine.on_event_openinterest_full",
            )

    async def on_event_touchline_full(self, data):
        """On receiving message code 1501:Touchline full"""
        __ = TouchLineData(data)
        if self.user_logger:
            self.user_logger.info(
                f"1501:Touchline full;{__}",
                caller="marketDataEngine.on_event_touchline_full",
            )
        asyncio.ensure_future(self.subscribe_manager.broadcast(__))

    async def on_connect(self) -> None:
        """
        Asynchronous method that handles actions to be performed upon successful connection to the market data socket.
        This method logs a message indicating that the market data socket has connected successfully.
        Returns:
            None
        """
        self.isConnected = True
        if self.user_logger:
            self.user_logger.info(
                "Market Data Socket connected successfully!",
                caller="marketDataEngine.on_connect",
            )

    async def reconnect(self):
        try:
            # Initialize and connect OrderSocket_io object
            self.socket = MDSocket_io(
                self.set_marketDataToken, self.set_userID, self._root, self
            )
            # Log successful login
            if self.user_logger:
                self.user_logger.info(
                    f"Login successful.", caller="marketDataEngine.reconnect"
                )

            await self.socket.connect()

        except Exception as e:
            if self.user_logger:
                self.user_logger.error(e, caller="marketDataEngine.reconnect")

    async def on_disconnect(self) -> None:
        """
        Handles the event when the market data socket gets disconnected.
        This method logs an informational message indicating that the market data
        socket has been disconnected. The log entry includes the caller information
        for easier traceability.
        Returns:
            None
        """
        self.isConnected = False
        if self.user_logger:
            self.user_logger.info(
                "Market Data Socket disconnected!",
                caller="marketDataEngine.on_disconnect",
            )
        current_time = datetime.now().time()
        cnt: int = 0
        if current_time < datetime.strptime("15:30", "%H:%M").time():
            while not self.isConnected and self.isLive:
                print(
                    "Attempting to reconnect as the time is before 3:30 PM and isConnected is False for market data socket."
                )
                if self.user_logger:
                    self.user_logger.info(
                        "Attempting to reconnect as the time is before 3:30 PM and isConnected is False.",
                        caller="marketDataEngine.on_disconnect",
                    )
                await self.reconnect()
                await asyncio.sleep(3)
                cnt += 1
                if not self.isConnected and self.user_logger:
                    print(
                        f"Reconnection attempt {cnt} failed for market data socket. Retrying..."
                    )
                    self.user_logger.warning(
                        f"Reconnection attempt {cnt} failed. Retrying...",
                        caller="marketDataEngine.on_disconnect",
                    )

    async def on_message(self, xts_message: Any) -> None:
        """
        Asynchronously handles incoming messages.
        This method is triggered when a new message is received. It parses the
        message from JSON format and logs the message if a user logger is available.
        Args:
            xts_message (Any): The incoming message in JSON format.
        Returns:
            None
        """
        if self.user_logger:
            self.user_logger.info(
                f"Received a message: {xts_message}",
                caller="marketDataEngine.on_message",
            )

    async def on_error(self, xts_message: Any) -> None:
        """
        Handles error messages received from the XTS system.
        Args:
            xts_message (Any): The error message received from the XTS system.
        Returns:
            None
        """
        if self.user_logger:
            self.user_logger.error(
                f"Received a error: {xts_message}", caller="marketDataEngine.on_error"
            )

    async def shutdown(self) -> None:
        """
        Asynchronously shuts down the market data engine.
        This method performs the following steps:
        1. Logs the entry into shutdown mode if a user logger is available.
        2. Disconnects the socket connection.
        3. Logs out from the market data service.
        4. Logs the successful logout and end of trading if a user logger is available.
        If an exception occurs during the shutdown process, it logs the error and re-raises the exception.
        Raises:
            Exception: If an error occurs during the shutdown process.
        """

        try:
            if self.user_logger:
                self.user_logger.info(
                    "Entering shut down mode.", caller="marketDataEngine.shutdown"
                )
            await self.socket.disconnect()
            await self.xt.marketdata_logout()
            if self.user_logger:
                self.user_logger.info(
                    f"Logged Out.",
                    caller="marketDataEngine.shutdown",
                )

        except Exception as e:
            if self.user_logger:
                self.user_logger.error(e, caller="marketDataEngine.shutdown")
            raise (e)

    async def login(self) -> None:
        """
        Asynchronously logs in to the market data engine and initializes necessary connections.
        This method performs the following steps:
        1. Initializes the XTSConnect object with the provided API credentials.
        2. Performs an interactive login to obtain the market data token and user ID.
        3. Initializes and connects the MDSocket_io object using the obtained token and user ID.
        4. Logs the successful login if a user logger is available.
        5. Retrieves and maps all exchange codes to their respective exchange segments.
        6. Retrieves and maps all index codes to their respective exchange instrument IDs.
        7. Logs the completion of the exchange and index mappings if a user logger is available.
        Raises:
            Exception: If any error occurs during the login process, it is logged and re-raised.
        Returns:
            None
        """

        try:
            # Initialize XTSConnect object
            self.xt = XTSConnect(
                self._api_key, self._api_password, self._source, self._root
            )

            # Perform interactive login
            response = await self.xt.marketdata_login()

            self.set_marketDataToken = response["result"]["token"]
            self.set_userID = response["result"]["userID"]
            self.set_isInvestorClient = False
            # Initialize and connect OrderSocket_io object
            self.socket = MDSocket_io(
                self.set_marketDataToken, self.set_userID, self._root, self
            )
            # Log successful login
            if self.user_logger:
                self.user_logger.info(
                    f"Login successful.", caller="marketDataEngine.login"
                )

            """Retrieve all exchange codes"""
            response = await self.xt.get_config()
            self.exchange_to_exchangeSegments = response["result"]["exchangeSegments"]
            if self.user_logger:
                self.user_logger.info(
                    f"Exchange to exchange segments mapping completed.",
                    caller="marketDataEngine.login",
                )

            """Retrieve all index codes"""
            for exchange in self.exchange_to_exchangeSegments:
                response = (
                    await self.xt.get_index_list(
                        exchangeSegment=self.exchange_to_exchangeSegments[exchange]
                    )
                )["result"]
                if "indexList" not in response:
                    continue
                index_list = response["indexList"]
                for index in index_list:
                    idx_name, idx_code = index.split("_")
                    self.index_list.append(
                        Index(
                            idx_name,
                            self.exchange_to_exchangeSegments[exchange],
                            idx_code,
                        )
                    )

            if self.user_logger:
                self.user_logger.info(
                    f"Index to exchange instrument id mapping completed.",
                    caller="marketDataEngine.login",
                )
        except Exception as e:
            if self.user_logger:
                self.user_logger.error(e, caller="marketDataEngine.login")
            raise (e)

    async def subscribe(
        self, Instruments: List[Dict], xtsMessageCode: int, uuid: str
    ) -> None:
        """
        Subscribes to market data for the given instruments.
        Args:
            Instruments (List[Dict]): A list of dictionaries, each containing 'exchangeSegment' and 'exchangeInstrumentID'.
            xtsMessageCode (int): The message code for the subscription. Must be one of [1501, 1502, 1505, 1507, 1512, 1105].
            algo (BaseAlgo): An instance of a class derived from BaseAlgo, representing the algorithm to be used for processing the market data.
        Raises:
            AssertionError: If any of the input arguments do not meet the required conditions.
            Exception: If an error occurs during the subscription process.
        Returns:
            None
        """
        assert Instruments, "Instruments list is required"
        assert isinstance(Instruments, list), "Instruments must be a list"
        assert isinstance(xtsMessageCode, int), "xtsMessageCode must be an integer"
        assert isinstance(
            uuid, str
        ), "uuid should be a string representing the strategy UUID"
        for instrument in Instruments:
            assert isinstance(instrument, dict), "Each instrument must be a dictionary"
            assert (
                "exchangeSegment" in instrument
            ), "Each instrument must have an 'exchangeSegment'"
            assert (
                "exchangeInstrumentID" in instrument
            ), "Each instrument must have an 'exchangeInstrumentID'"
        assert xtsMessageCode in [
            1501,
            1502,
            1505,
            1507,
            1512,
            1105,
        ], "Invalid message code"

        try:
            listToSubscribe: List = []
            for item in range(len(Instruments)):
                if not self.subscribe_manager.ifExists(
                    Instruments[item]["exchangeInstrumentID"], xtsMessageCode
                ):
                    listToSubscribe.append(item)
            if listToSubscribe:
                response = await self.xt.send_subscription(
                    Instruments=Instruments, xtsMessageCode=xtsMessageCode
                )

                if (
                    response["type"] == "error"
                    and response["description"] == "Instrument Already Subscribed !"
                ):
                    if self.user_logger:
                        self.user_logger.error(
                            f"Error in Subscribing Quantities: {Instruments} on request from {uuid} as {response}",
                            caller="marketDataEngine.subscribe",
                        )
                    # Avoid raising this error
                if response["type"] != "success":
                    if self.user_logger:
                        self.user_logger.error(
                            f"Error in Subscribing Quantities: {Instruments} on request from {uuid} as {response}",
                            caller="marketDataEngine.subscribe",
                        )
                    raise (response)
            for item in range(len(Instruments)):
                self.subscribe_manager.subscribe(
                    Instruments[item]["exchangeInstrumentID"], xtsMessageCode, uuid
                )

            if self.user_logger:
                self.user_logger.info(
                    f"Subscribed Quantities: {Instruments} on request from {uuid}",
                    caller="marketDataEngine.subscribe",
                )
        except Exception as e:
            if self.user_logger:
                self.user_logger.error(e, caller="marketDataEngine.subscribe")
            raise (e)

    async def loadMaster(self) -> None:
        """
        Asynchronously loads master data for different market segments and processes it.
        This method fetches master instruments data for NSE FO, BSE FO, NSE CM, and BSE CM market segments,
        converts the data into DataFrames, saves them as CSV files, and logs the fetched data.
        Raises:
            Exception: If there is an error during the fetching or processing of the master data.
        """

        try:
            """Get Master Instruments Request for NSE FO market segment"""
            exchangesegments = [self.xt.EXCHANGE_NSEFO, self.xt.EXCHANGE_BSEFO]
            response = await self.xt.get_master(exchangeSegmentList=exchangesegments)
            self.F_MASTER_DF, O_MASTER_DF, f_spread_df = helper.fo_master_string_to_df(
                response["result"]
            )
            O_MASTER_DF["UnderlyingIndexName"] = O_MASTER_DF[
                "UnderlyingIndexName"
            ].str.upper()
            O_MASTER_DF.to_csv(f"MASTER_O.csv", index=False)
            self.option_manager = OptionManager(O_MASTER_DF)
            self.F_MASTER_DF.to_csv(f"MASTER_F.csv", index=False)

            if self.user_logger:
                self.user_logger.info(
                    f"Options Contract Fetched: Sample - {O_MASTER_DF.head(1)}",
                    caller="marketDataEngine.loadMaster",
                )
            if self.user_logger:
                self.user_logger.info(
                    f"Futures Contract Fetched: Sample - {self.F_MASTER_DF.head(1)}",
                    caller="marketDataEngine.loadMaster",
                )

            """Get Master Instruments Request for NSE cash market segment"""
            exchangesegments = [self.xt.EXCHANGE_NSECM, self.xt.EXCHANGE_BSECM]
            response = await self.xt.get_master(exchangeSegmentList=exchangesegments)
            self.CM_MASTER_DF: pandas.DataFrame = cm_master_string_to_df(
                response["result"]
            )
            self.CM_MASTER_DF.to_csv(f"MASTER_CM.csv", index=False)

            if self.user_logger:
                self.user_logger.info(
                    f"Cash Market Contract Fetched: Sample - {self.CM_MASTER_DF.head(1)}",
                    caller="marketDataEngine.loadMaster",
                )
        except Exception as e:
            self.user_logger.error(e, caller="marketDataEngine.loadMaster")
            raise (e)

    async def loadMasterServer(self, directory: str = "") -> None:
        """
        Asynchronously loads master data for different market segments (NSE FO, BSE FO, NSE CM, BSE CM),
        and saves the results as compressed JSONL (.jsonl.gz) files.
        """
        try:
            # Fetch FO Master
            exchangesegments = [self.xt.EXCHANGE_NSEFO, self.xt.EXCHANGE_BSEFO]
            response = await self.xt.get_master(exchangeSegmentList=exchangesegments)
            FandO_response = response["result"]
            if self.user_logger:
                self.user_logger.info(
                    f"Futures and Options Contract file fetched.",
                    caller="marketDataEngine.loadMasterServer",
                )

            # Fetch CM Master
            exchangesegments = [self.xt.EXCHANGE_NSECM]
            response = await self.xt.get_master(exchangeSegmentList=exchangesegments)
            CM_response = response["result"]

            if self.user_logger:
                self.user_logger.info(
                    f"Cash Market Contract file fetched.",
                    caller="marketDataEngine.loadMasterServer",
                )

            # Save files as compressed JSON Lines

            # Save FO Master as simple JSON
            with open(directory + "FandO_master.txt", "w", encoding="utf-8") as f:
                f.write(FandO_response)  # assuming list of strings

            with open(directory + "CM_master.txt", "w", encoding="utf-8") as f:
                f.write(CM_response)  # assuming list of strings

            if self.user_logger:
                self.user_logger.info(
                    "Master files written to disk successfully.",
                    caller="marketDataEngine.loadMasterServer",
                )

        except Exception as e:
            self.user_logger.error(str(e), caller="marketDataEngine.loadMasterServer")
            raise (e)

    async def fetch_ltp(self, Instruments: List[Dict]) -> List[TouchLineData]:
        """
        Fetches the Last Traded Price (LTP) data for a list of instruments.
        Args:
            Instruments (List[Dict]): A list of dictionaries, each containing:
                - 'exchangeSegment' (str): The exchange segment of the instrument.
                - 'exchangeInstrumentID' (str): The exchange instrument ID.
        Returns:
            List[LtpData]: A list of LtpData objects containing the LTP data for each instrument.
        Raises:
            AssertionError: If the Instruments list is empty, not a list, or if any instrument
                            dictionary does not contain the required keys.
        """

        assert Instruments, "Instruments list is required"
        assert isinstance(Instruments, list), "Instruments must be a list"
        for instrument in Instruments:
            assert isinstance(instrument, dict), "Each instrument must be a dictionary"
            assert (
                "exchangeSegment" in instrument
            ), "Each instrument must have an 'exchangeSegment'"
            assert (
                "exchangeInstrumentID" in instrument
            ), "Each instrument must have an 'exchangeInstrumentID'"

        for instrument in Instruments:
            if isinstance(instrument["exchangeSegment"], str):
                instrument["exchangeSegment"] = self.exchange_to_exchangeSegments[
                    instrument["exchangeSegment"]
                ]
        response = await self.xt.get_quote(
            Instruments=Instruments,
            xtsMessageCode=1501,
            publishFormat="JSON",
        )
        _list: List[TouchLineData] = []
        for item in response["result"]["listQuotes"]:
            _list.append(TouchLineData(item))
        return _list

    async def fetch_option_quotes(self, instrument):
        response = await self.xt.get_quote(
            Instruments=instrument,
            xtsMessageCode=1502,
            publishFormat="JSON",
        )
        return json.loads(response["result"]["listQuotes"][0])

    async def unsubscribe(
        self, Instruments: List[Dict], xtsMessageCode: int, uuid: str
    ) -> None:
        """
        Unsubscribes from market data for the given instruments.
        Args:
            Instruments (List[Dict]): A list of dictionaries, each containing 'exchangeSegment' and 'exchangeInstrumentID'.
            xtsMessageCode (int): The message code for the unsubscription. Must be one of [1501, 1502, 1505, 1507, 1512, 1105].
            uuid (str): A string representing the strategy UUID.
        Raises:
            AssertionError: If any of the input arguments do not meet the required conditions.
            Exception: If an error occurs during the unsubscription process.
        Returns:
            None
        """
        assert Instruments, "Instruments list is required"
        assert isinstance(Instruments, list), "Instruments must be a list"
        assert isinstance(xtsMessageCode, int), "xtsMessageCode must be an integer"
        assert isinstance(
            uuid, str
        ), "uuid should be a string representing the strategy UUID"
        for instrument in Instruments:
            assert isinstance(instrument, dict), "Each instrument must be a dictionary"
            assert (
                "exchangeSegment" in instrument
            ), "Each instrument must have an 'exchangeSegment'"
            assert (
                "exchangeInstrumentID" in instrument
            ), "Each instrument must have an 'exchangeInstrumentID'"
        assert xtsMessageCode in [
            1501,
            1502,
            1505,
            1507,
            1512,
            1105,
        ], "Invalid message code"

        try:
            listToUnsubscribe: List = []
            for item in range(len(Instruments)):
                self.subscribe_manager.unsubscribe(
                    Instruments[item]["exchangeInstrumentID"], xtsMessageCode, uuid
                )
                if not self.subscribe_manager.ifExists(
                    Instruments[item]["exchangeInstrumentID"], xtsMessageCode
                ):
                    listToUnsubscribe.append(item)
            if listToUnsubscribe:
                response = await self.xt.send_unsubscription(
                    Instruments=Instruments, xtsMessageCode=xtsMessageCode
                )
                if response["type"] != "success":
                    if self.user_logger:
                        self.user_logger.error(
                            f"Error in unsubscribing Quantities: {Instruments} on request from {uuid} as {response}",
                            caller="marketDataEngine.unsubscribe",
                        )
                    raise (response)
            if self.user_logger:
                self.user_logger.info(
                    f"Unsubscribed Quantities: {Instruments} on request from {uuid}",
                    caller="marketDataEngine.unsubscribe",
                )

        except Exception as e:
            if self.user_logger:
                self.user_logger.error(e, caller="marketDataEngine.unsubscribe")
            raise (e)

    async def option_search_expiry_by_underline(self, underline: str) -> List[datetime]:
        """
        Searches for all contract expirations for a given underlying index name.
        Args:
            underline (str): The underlying index name to search for.
        Returns:
            List[datetime.datetime]: A sorted list of contract expirations.
        """
        return self.option_manager.search_expiry_by_underline(underline)

    async def option_search_all_underline(self) -> List[str]:
        """
        Retrieves all unique underlying index names.
        Returns:
            List[str]: A list of all unique underlying index names.
        """
        return self.option_manager.search_all_underline()

    async def option_search_by_underline(
        self, underline: str
    ) -> List[OptionsInstrument]:
        """
        Searches for all options instruments for a given underlying index name.
        Args:
            underline (str): The underlying index name to search for.
        Returns:
            List[OptionsInstrument]: A list of options instruments.
        """
        return self.option_manager.search_option_by_underline(underline)

    async def option_search_by_expiry_and_underline(
        self, underline: str, expiry: datetime
    ) -> List[OptionsInstrument]:
        """
        Searches for all options instruments for a given underlying index name and contract expiration.
        Args:
            underline (str): The underlying index name to search for.
            expiry (OptionsInstrument.ContractExpiration): The contract expiration to search for.
        Returns:
            List[OptionsInstrument]: A list of options instruments.
        """
        return self.option_manager.search_option_by_expiry_underline(underline, expiry)

    async def option_search(
        self,
        ExchangeSegment: str = None,
        ExchangeInstrumentID: int = None,
        InstrumentType: int = None,
        Name: str = None,
        Series: str = None,
        UnderlyingIndexName: str = None,
        ContractExpiration: datetime = None,
        StrikePrice: int = None,
        OptionType: int = None,
        minimumExpiry: bool = False,
    ) -> List[OptionsInstrument]:
        """
        Searches for options based on various criteria.
        Args:
            ExchangeSegment (str): Exchange segment to search for.
            ExchangeInstrumentID (int): Exchange instrument ID to search for.
            InstrumentType (int): Instrument type to search for.
            Name (str): Name to search for.
            Series (str): Series to search for.
            UnderlyingIndexName (str): Underlying index name to search for.
            ContractExpiration (datetime): Contract expiration to search for.
            StrikePrice (int): Strike price to search for.
            OptionType (int): Option type to search for.
            minimumExpiry (bool): If True, only return options with the minimum expiration date.
        Returns:
            pandas.DataFrame: DataFrame containing the search results.
        """
        return self.option_manager.search_option(
            ExchangeSegment=ExchangeSegment,
            ExchangeInstrumentID=ExchangeInstrumentID,
            InstrumentType=InstrumentType,
            Name=Name,
            Series=Series,
            UnderlyingIndexName=UnderlyingIndexName,
            ContractExpiration=ContractExpiration,
            StrikePrice=StrikePrice,
            OptionType=OptionType,
            minimumExpiry=minimumExpiry,
        )

    async def dummy_market_order(
        self,
        exchangeSegment: str,
        exchangeInstrumentID: int,
        productType: str,
        orderQuantity: int,
        orderUniqueIdentifier: str,
        baseAlgo: BaseAlgo,
    ):
        """
        Simulates a market order and generates a trade event.
        Args:
            exchangeSegment (str): The segment of the exchange where the order is placed.
            exchangeInstrumentID (int): The ID of the instrument being traded.
            productType (str): The type of product being traded.
            orderQuantity (int): The quantity of the order. Positive for buy, negative for sell.
            orderUniqueIdentifier (str): A unique identifier for the order.
            baseAlgo (BaseAlgo): An instance of the BaseAlgo class to handle the trade event.
        Returns:
            None
        This function fetches the last traded price (LTP) for the given instrument and creates a TradeEvent
        based on whether the order is a buy or sell. The TradeEvent is then passed to the baseAlgo's trade_
        method for further processing.
        """
        _list = await self.fetch_ltp(
            [
                {
                    "exchangeSegment": self.exchange_to_exchangeSegments[
                        exchangeSegment
                    ],
                    "exchangeInstrumentID": exchangeInstrumentID,
                }
            ]
        )
        _data = next(
            item for item in _list if item.ExchangeInstrumentID == exchangeInstrumentID
        )
        tradeEvent: TradeEvent = None
        if orderQuantity < 0:
            tradeEvent = TradeEvent(
                {
                    "LoginID": "ANSYM1",
                    "ClientID": "PR03",
                    "AppOrderID": 1110039096,
                    "OrderReferenceID": "",
                    "GeneratedBy": "TWSAPI",
                    "ExchangeOrderID": "1200000014332079",
                    "OrderCategoryType": "NORMAL",
                    "ExchangeSegment": exchangeSegment,
                    "ExchangeInstrumentID": exchangeInstrumentID,
                    "OrderSide": "Sell",
                    "OrderType": "Market",
                    "ProductType": productType,
                    "TimeInForce": "DAY",
                    "OrderPrice": 0,
                    "OrderQuantity": abs(orderQuantity),
                    "OrderStopPrice": 0,
                    "OrderStatus": "Filled",
                    "OrderAverageTradedPrice": _data.LastTradedPrice,
                    "LeavesQuantity": 0,
                    "CumulativeQuantity": abs(orderQuantity),
                    "OrderDisclosedQuantity": 0,
                    "OrderGeneratedDateTime": datetime.now(),
                    "ExchangeTransactTime": datetime.now(),
                    "LastUpdateDateTime": datetime.now(),
                    "CancelRejectReason": "",
                    "OrderUniqueIdentifier": orderUniqueIdentifier,
                    "OrderLegStatus": "SingleOrderLeg",
                    "LastTradedPrice": _data.LastTradedPrice,
                    "LastTradedQuantity": 0,
                    "LastExecutionTransactTime": "2025-01-06T10:14:40",
                    "ExecutionID": "402597456",
                    "ExecutionReportIndex": 4,
                    "IsSpread": False,
                    "OrderAverageTradedPriceAPI": _data.LastTradedPrice,
                    "OrderSideAPI": "SELL",
                    "OrderGeneratedDateTimeAPI": datetime.now(),
                    "ExchangeTransactTimeAPI": datetime.now(),
                    "LastUpdateDateTimeAPI": datetime.now(),
                    "OrderExpiryDateAPI": "01-01-1980 00:00:00",
                    "LastExecutionTransactTimeAPI": "06-01-2025 10:14:43",
                    "MessageSynchronizeUniqueKey": "PR03",
                    "MessageCode": 9005,
                    "MessageVersion": 4,
                    "TokenID": 0,
                    "ApplicationType": 146,
                    "SequenceNumber": 1583119016879540,
                    "TradingSymbol": "OBEROIRLTY",
                }
            )
        else:
            tradeEvent = TradeEvent(
                {
                    "LoginID": "ANSYM1",
                    "ClientID": "PR03",
                    "AppOrderID": 1110033460,
                    "OrderReferenceID": "",
                    "GeneratedBy": "TWSAPI",
                    "ExchangeOrderID": "1200000074343640",
                    "OrderCategoryType": "NORMAL",
                    "ExchangeSegment": exchangeSegment,
                    "ExchangeInstrumentID": exchangeInstrumentID,
                    "OrderSide": "Buy",
                    "OrderType": "Market",
                    "ProductType": productType,
                    "TimeInForce": "DAY",
                    "OrderPrice": 0,
                    "OrderQuantity": orderQuantity,
                    "OrderStopPrice": 0,
                    "OrderStatus": "Filled",
                    "OrderAverageTradedPrice": _data.LastTradedPrice,
                    "LeavesQuantity": 0,
                    "CumulativeQuantity": orderQuantity,
                    "OrderDisclosedQuantity": 0,
                    "OrderGeneratedDateTime": datetime.now(),
                    "ExchangeTransactTime": datetime.now(),
                    "LastUpdateDateTime": datetime.now(),
                    "CancelRejectReason": "",
                    "OrderUniqueIdentifier": orderUniqueIdentifier,
                    "OrderLegStatus": "SingleOrderLeg",
                    "LastTradedPrice": _data.LastTradedPrice,
                    "LastTradedQuantity": 0,
                    "LastExecutionTransactTime": "2025-01-15T15:09:56",
                    "ExecutionID": "409661490",
                    "ExecutionReportIndex": 3,
                    "IsSpread": False,
                    "OrderAverageTradedPriceAPI": _data.LastTradedPrice,
                    "OrderSideAPI": "BUY",
                    "OrderGeneratedDateTimeAPI": "15-01-2025 15:10:00",
                    "ExchangeTransactTimeAPI": "15-01-2025 15:09:56",
                    "LastUpdateDateTimeAPI": "15-01-2025 15:10:00",
                    "OrderExpiryDateAPI": "01-01-1980 00:00:00",
                    "LastExecutionTransactTimeAPI": "15-01-2025 15:10:00",
                    "MessageSynchronizeUniqueKey": "PR03",
                    "MessageCode": 9005,
                    "MessageVersion": 4,
                    "TokenID": 0,
                    "ApplicationType": 146,
                    "SequenceNumber": 1590913686126258,
                    "TradingSymbol": "MARUTI",
                }
            )
        asyncio.ensure_future(baseAlgo.trade_(tradeEvent))

    def loadMasterClient(
        self,
        index_list: None,
        exchange_to_exchangeSegments: None,
        fo_response: str = None,
        cm_response: str = None,
    ) -> None:
        if exchange_to_exchangeSegments:
            self.exchange_to_exchangeSegments = exchange_to_exchangeSegments

        if index_list:
            for index in index_list:
                self.index_list.append(
                    Index(
                        index["Name"],
                        index["ExchangeSegment"],
                        index["ExchangeInstrumentID"],
                    )
                )

        if fo_response:
            _, o_master_df, __ = helper.fo_master_string_to_df(fo_response)
            o_master_df["UnderlyingIndexName"] = o_master_df[
                "UnderlyingIndexName"
            ].str.upper()
            self.option_manager = OptionManager(o_master_df)

        if cm_response:
            self.CM_MASTER_DF = cm_master_string_to_df(cm_response)
