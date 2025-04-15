# Brokerage Project

This is a Python-based brokerage calculation system that supports different types of trades including futures, options, delivery equity, and intraday equity.

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation Steps

1. Clone the repository
```bash
git clone https://github.com/Keerthanaashok1/brockerage.git
cd brockerage
```

2. Create a virtual environment
```bash
# On Windows
python -m venv venv
.\venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

## Running the Application

The system is divided into different modules for various types of trades. Choose the appropriate script based on your needs:

### For Futures Trading
```bash
python brockerage_ffutures.py
```
This script calculates brokerage for futures trading.

### For Options Trading
```bash
python brockerage_foptions.py
```
This script handles options trading brokerage calculations.

### For Delivery Equity
```bash
python brockerage_del_equity.py
```
Use this script for delivery-based equity trading calculations.

### For Intraday Equity
```bash
python brockerage_intra_equity.py
```
This script is specifically for intraday equity trading calculations.

## Input Files
- `Brokerage_calculator1_Input.xlsx`: Main input file containing trade details
- `NIFTY_parameter.xlsx`: Contains NIFTY-related parameters

## Output
The calculated results will be saved in the `OUTPUT` directory with appropriate timestamps.

## Project Structure
```
brockerage/
├── brockerage_ffutures.py    # Futures trading calculations
├── brockerage_foptions.py    # Options trading calculations
├── brockerage_del_equity.py  # Delivery equity calculations
├── brockerage_intra_equity.py# Intraday equity calculations
├── requirements.txt          # Python dependencies
├── INPUT/                    # Input files directory
├── OUTPUT/                   # Generated reports directory
└── doc/                      # Documentation files
