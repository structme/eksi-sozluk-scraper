# Ekşi Sözlük Entry Scraper

This is a Python script that allows you to scrape entries from Ekşi Sözlük (eksisozluk.com) topics. It collects usernames, entry contents, dates, and favorite counts.

## Features

- Scrapes all entries from a given Ekşi Sözlük topic URL
- Handles pagination automatically
- Collects username, content, date, and favorite count for each entry
- Saves data to CSV file
- Includes anti-bot detection measures
- Provides detailed logging
- Handles errors gracefully

## Requirements

- Python 3.6+
- Required packages listed in `requirements.txt`

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/eksi-sozluk-scraper.git
cd eksi-sozluk-scraper
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the script with a topic URL as argument:

```bash
python eksi_scraper.py "https://eksisozluk.com/your-topic-url"
```

The script will:
1. Fetch all pages of the topic
2. Extract entries with their metadata
3. Save everything to `entries.csv` file

## Output Format

The script creates a CSV file with the following columns:
- username (index)
- entry (content)
- date
- favorites (count)

## Notes

- Please be mindful of the website's terms of service and rate limits
- Add reasonable delays between requests to avoid overwhelming the server
- The script might need updates if the website structure changes

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
