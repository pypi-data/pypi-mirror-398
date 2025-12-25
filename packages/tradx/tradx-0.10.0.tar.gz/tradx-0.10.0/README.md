# Changelog

## [v0.1.2] - *Released: 09-Jan-2025*  
### Changes:
- **examples/example1.py**  
  - Refactored code for improved readability and efficiency.  
- **examples/example2.log** *(New)*  
  - Log file for the second example script.  
- **examples/example2.py** *(New)*  
  - Added a script demonstrating two example algorithmic trading strategies using the `tradx` library.  
- **src/tradx/baseClass/baseAlgo.py**  
  - Added functionality to track orders and positions at the strategy level.  
  - Implemented the ability to square off individual strategy positions intraday without disrupting others.  
- **src/tradx/baseClass/order.py** *(New)*  
  - Introduced a Pydantic class to manage strategy-level orders.  
- **src/tradx/baseClass/orderEvent.py**  
  - Fixed a bug in attribute types for 'OrderAverageTradedPrice' and 'OrderAverageTradedPriceAPI.'  
- **src/tradx/baseClass/position.py** *(New)*  
  - Introduced a Pydantic class to manage strategy-level positions.  
- **src/tradx/interactiveEngine.py**  
  - Refactored code for better maintainability.  
  - Added functionality to cancel individual orders.

---

## [example1 Added] - *Released: 08-Jan-2025*  
### Changes:
- **examples/example1.log** *(New)*  
  - Log file for the first example script.  
- **examples/example1.py** *(New)*  
  - Example script showcasing basic functionality of the `tradx` library.

---

## [v0.1.1] - *Released: 08-Jan-2025*  
### Changes:
- **algoContainer.py**  
  - Fixed the broadcast function to work with the new Pydantic class for candle data.  
- **baseClass/baseAlgo.py**  
  - Added virtual functions for `unsubscribe`, `initialize`, and `deinitialize`.  
- **baseClass/index.py** *(New)*  
  - Implemented a separate Pydantic class for index data management.  
- **marketDataEngine.py**  
  - Made the `subscribe` and `unsubscribe` functions functional.  
  - Updated `loadMaster` function to fetch options and futures master data.  
  - Fixed bugs in `on_event_candle_data_full`.

---

## Initial Commit - *Released: 07-Jan-2025*  
### Changes:  
- Introduced the `tradx` package.  

---

This changelog provides a clear and organized view of the changes across different versions.