from typing import Dict, Set, Any
from tradx.baseClass.baseAlgo import BaseAlgo
from tradx.baseClass.market.candleData import CandleData
from tradx.baseClass.market.touchLineData import TouchLineData
import asyncio


class AlgoContainer:
    """
    AlgoContainer is a container class that maps algorithms to their subscriptions and allows broadcasting messages.
    Attributes:
        subscriptions (Dict[int, Set[BaseAlgo]]): A dictionary mapping subscription keys to sets of algorithm instances.
    Methods:
        __init__():
            Initializes the AlgoContainer with an empty subscription map.
        subscribe(key: int, algo: BaseAlgo):
            Subscribes an algorithm to a specific key.
                key (int): The subscription key.
                algo (BaseAlgo): The algorithm instance subscribing.
        unsubscribe(key: int, algo: BaseAlgo):
            Unsubscribes an algorithm from a specific key.
                key (int): The subscription key.
                algo (BaseAlgo): The algorithm instance unsubscribing.
        broadcast(key: int, message: str, dataType: str):
            Broadcasts a message to all algorithms subscribed to a given key.
                key (int): The key to broadcast the message for.
                dataType (str): The type of data being broadcasted (e.g., "bar").
    """

    def __init__(self) -> None:
        """
        Initializes the algoContainer instance.

        Attributes:
            subscriptions (Dict[int, Set[BaseAlgo]]):
                A dictionary mapping an integer key (e.g., a topic or identifier)
                to a set of algorithm instances (BaseAlgo).
        """
        self.subscriptions: Dict[int, Set[BaseAlgo]] = {}

    def subscribe(self, key, algo: BaseAlgo) -> None:
        """
        Subscribes an algorithm to a given key.
        Args:
            key: The key to subscribe the algorithm to.
            algo (BaseAlgo): The algorithm to be subscribed.
        Raises:
            None
        Returns:
            None
        """

        if key not in self.subscriptions:
            self.subscriptions[key] = set()
        self.subscriptions[key].add(algo)

    def unsubscribe(self, key, algo: BaseAlgo) -> None:
        """
        Unsubscribe an algorithm from a given key.
        This method removes the specified algorithm from the list of
        subscriptions associated with the given key. If no more algorithms
        are subscribed to the key after removal, the key is deleted from
        the subscriptions.
        Args:
            key: The key from which the algorithm should be unsubscribed.
            algo (BaseAlgo): The algorithm instance to be unsubscribed.
        """

        if key in self.subscriptions and algo in self.subscriptions[key]:
            self.subscriptions[key].remove(algo)

            # Remove the key if no more algorithms are subscribed
            if not self.subscriptions[key]:
                del self.subscriptions[key]

    async def broadcast(self, message: Any) -> None:
        """
        Broadcast a message to all algorithms subscribed to a given key.

        Args:
            key (str): The key to broadcast the message for.
            message (str): The message to broadcast.
        """
        if message.ExchangeInstrumentID in self.subscriptions:
            if isinstance(message, CandleData):
                for algo in self.subscriptions[message.ExchangeInstrumentID]:
                    asyncio.ensure_future(algo.on_barData(message))
            if isinstance(message, TouchLineData):
                for algo in self.subscriptions[message.ExchangeInstrumentID]:
                    asyncio.ensure_future(algo.on_touchLineData(message))


class SubcribeContainer:
    """
    AlgoContainer is a container class that maps algorithms to their subscriptions and allows broadcasting messages.
    Attributes:
        subscriptions (Dict[int, Set[BaseAlgo]]): A dictionary mapping subscription keys to sets of algorithm instances.
    Methods:
        __init__():
            Initializes the AlgoContainer with an empty subscription map.
        subscribe(key: int, algo: BaseAlgo):
            Subscribes an algorithm to a specific key.
                key (int): The subscription key.
                algo (BaseAlgo): The algorithm instance subscribing.
        unsubscribe(key: int, algo: BaseAlgo):
            Unsubscribes an algorithm from a specific key.
                key (int): The subscription key.
                algo (BaseAlgo): The algorithm instance unsubscribing.
        broadcast(key: int, message: str, dataType: str):
            Broadcasts a message to all algorithms subscribed to a given key.
                key (int): The key to broadcast the message for.
                dataType (str): The type of data being broadcasted (e.g., "bar").
    """

    def __init__(self) -> None:
        """
        Initializes the algoContainer instance.

        Attributes:
            subscriptions (Dict[int, Set[BaseAlgo]]):
                A dictionary mapping an integer key (e.g., a topic or identifier)
                to a set of algorithm instances (BaseAlgo).
        """
        self.subscriptions: Dict[int, Set[str]] = {}

    def subscribe(self, exchangeInstrumentID, xtsMessageCode, uuid: str) -> None:
        """
        Subscribes an algorithm to a given key.
        Args:
            key: The key to subscribe the algorithm to.
            algo (BaseAlgo): The algorithm to be subscribed.
        Raises:
            None
        Returns:
            None
        """
        key = (exchangeInstrumentID, xtsMessageCode)
        if key not in self.subscriptions:
            self.subscriptions[key] = set()
        self.subscriptions[key].add(uuid)

    def unsubscribe(self, exchangeInstrumentID, xtsMessageCode, uuid: str) -> None:
        """
        Unsubscribe an algorithm from a given key.
        This method removes the specified algorithm from the list of
        subscriptions associated with the given key. If no more algorithms
        are subscribed to the key after removal, the key is deleted from
        the subscriptions.
        Args:
            key: The key from which the algorithm should be unsubscribed.
            algo (BaseAlgo): The algorithm instance to be unsubscribed.
        """
        key = (exchangeInstrumentID, xtsMessageCode)
        if key in self.subscriptions and uuid in self.subscriptions[key]:
            self.subscriptions[key].remove(uuid)

            # Remove the key if no more algorithms are subscribed
            if not self.subscriptions[key]:
                del self.subscriptions[key]

    def ifExists(self, exchangeInstrumentID, xtsMessageCode) -> bool:
        """
        Check if a subscription exists for the given exchangeInstrumentID and xtsMessageCode.
        Args:
            exchangeInstrumentID: The exchange instrument ID to check.
            xtsMessageCode: The XTS message code to check.
        Returns:
            bool: True if the subscription exists, False otherwise.
        """
        return (exchangeInstrumentID, xtsMessageCode) in self.subscriptions
