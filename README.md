# BGG.CON 2023 Badge Availability Checker

This is a small Python program that checks the tabletop.events API for badge availability to BGG.CON 2023. The program polls the API every 10 seconds and sends a message to Discord if badges are available.

## Installation

To run the program, you will need to have Python 3 installed on your system. You can download Python from the official website: https://www.python.org/downloads/

You will also need to install the `requests` package, which can be installed using pip:

```
pip install requests
```

## Usage

To use the program, you will need to set the `WEBHOOK_URL` environment variable to the URL of your Discord webhook. You can do this by setting the environment variable before running the program:

```
export WEBHOOK_URL=<webhook-url>
```

Replace `<webhook-url>` with the URL of your Discord webhook.

Once you have set the `WEBHOOK_URL` environment variable, you can run the program using the following command:

```
python bgg.py
```

The program will poll the tabletop.events API every 10 seconds and send a message to Discord if badges are available.
