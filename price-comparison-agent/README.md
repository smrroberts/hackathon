# Price Comparison Agent

## Overview
The Price Comparison Agent is a Python-based application designed to search for specific items across multiple e-commerce websites and perform price checks to identify the cheapest option available. This agent automates the process of comparing prices from various online retailers, making it easier for users to find the best deals.

## Features
- Search for items across multiple websites including Amazon, eBay, and Currys.
- Aggregate price information from different sources.
- Identify the cheapest item based on the search criteria.
- Utility functions for parsing and standardizing price formats.

## Project Structure
```
price-comparison-agent/
├── src/
│   ├── agent.py          # Main logic for the price comparison agent
│   ├── websites/         # Contains website-specific scraping modules
│   │   ├── __init__.py   # Initializes the websites package
│   │   ├── amazon.py     # Scraper for Amazon
│   │   ├── ebay.py       # Scraper for eBay
│   │   └── currys.py     # Scraper for Currys
│   ├── utils/            # Utility functions
│   │   └── price_parser.py # Functions for parsing prices
│   └── types/            # Type definitions
│       └── index.py      # Exports interfaces and types
├── requirements.txt       # Project dependencies
├── .env.example           # Example environment variables
└── README.md              # Project documentation
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd price-comparison-agent
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables by copying `.env.example` to `.env` and filling in the necessary values.

## Usage
To use the Price Comparison Agent, you can run the main script located in `src/agent.py`. You will need to specify the item you want to search for as a command-line argument.

Example:
```
python src/agent.py "wireless headphones"
```

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.