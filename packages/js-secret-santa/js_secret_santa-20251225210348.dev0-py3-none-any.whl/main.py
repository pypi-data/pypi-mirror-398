import datetime
import json
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
import os

import pandas as pd

from src.logger import logger


def matcher(people, person_filter: dict = None):
    while True:
        matches = []
        giftees = people.copy()
        random.shuffle(giftees)
        gifters = people.copy()
        random.shuffle(gifters)
        for i in range(0, len(people)):
            skip = False
            # Check if gifter and giftee are the same person
            if (
                gifters[i]["First Name"] + gifters[i]["Last Name"]
                == giftees[i]["First Name"] + giftees[i]["Last Name"]
            ):
                logger.warning(
                    f"Same person: {gifters[i]['First Name']} {gifters[i]['Last Name']}-> {giftees[i]['First Name']} {giftees[i]['Last Name']}"
                )
                break
            # Check if gifter and giftee are in the same family (same last name)
            if gifters[i]["Last Name"] == giftees[i]["Last Name"]:
                logger.warning(
                    f"Same family: {gifters[i]['First Name']} {gifters[i]['Last Name']}-> {giftees[i]['First Name']} {giftees[i]['Last Name']}"
                )
                break
            if person_filter:
                for person in person_filter:
                    if (
                        person is not None
                        and gifters[i]["Email"] in person.keys()
                        and giftees[i]["Email"] in person[gifters[i]["Email"]]
                    ):
                        logger.warning(
                            f"Person Filter: {gifters[i]['Email']} -> {giftees[i]['Email']}"
                        )
                        skip = True
                        break
            if skip:
                break
            matches.append(
                {
                    "Gifter": {
                        "Name": gifters[i]["First Name"]
                        + " "
                        + gifters[i]["Last Name"],
                        "Email": gifters[i]["Email"],
                    },
                    "Giftee": {
                        "Name": giftees[i]["First Name"]
                        + " "
                        + giftees[i]["Last Name"],
                        "Gifts": [
                            giftees[i]["Amazon link to Gift #1 ($30 max)"],
                            giftees[i]["Amazon link to Gift #2 ($30 max)"],
                            giftees[i]["Amazon link to Gift #3 ($30 max)"],
                        ],
                    },
                }
            )
        if len(matches) == len(people):
            break
    return matches


def send_email(secret_santa, debug):
    sender_email = os.getenv("SMTP_SENDER_EMAIL")
    receiver_email = secret_santa["Gifter"]["Email"]
    password = os.getenv("SMTP_PASSWORD")
    message = MIMEMultipart("alternative")
    current_year = datetime.datetime.now().year
    message["Subject"] = f"Your Secret Santa has Arrived for {current_year}!"
    message["From"] = sender_email
    message["To"] = receiver_email

    logger.debug(
        f"Creating email with subject: {message['Subject']}, from: {message['From']}, and to: {message['To']}"
    )

    text = f"""
    Hello {secret_santa["Gifter"]["Name"]},
    You are shopping for {secret_santa["Giftee"]["Name"]}.
    There requested gists are
    1. {secret_santa["Giftee"]["Gifts"][0]}
    2. {secret_santa["Giftee"]["Gifts"][1]}
    3. {secret_santa["Giftee"]["Gifts"][2]}
    Please let me know if you have any questions.
    Love, Jack
    """

    html = f"""\
    <html>
        <body>
            <p> Hello {secret_santa["Gifter"]["Name"]},<br>
                You are shopping for {secret_santa["Giftee"]["Name"]}.<br>
                There requested gifts are<br><br>
                1. <a href={secret_santa["Giftee"]["Gifts"][0]}>{secret_santa["Giftee"]["Gifts"][0]}</a><br>
                2. <a href={secret_santa["Giftee"]["Gifts"][1]}>{secret_santa["Giftee"]["Gifts"][1]}</a><br> 
                3. <a href={secret_santa["Giftee"]["Gifts"][2]}>{secret_santa["Giftee"]["Gifts"][2]}</a><br> 
                <br>
                Please let me know if you have any questions.<br>
                Love, Jack
            </p>
        </body>
    </html>
    """
    logger.info(f"Sending email to {secret_santa['Gifter']['Name']} -> {message['To']}")
    if not debug:
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)
        with smtplib.SMTP(
            os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT"))
        ) as server:
            server.starttls()
            server.login(os.getenv("SMTP_USERNAME"), password)
            server.sendmail(sender_email, receiver_email, message.as_string())
    else:
        logger.info(text)


def writer(secret_santa):
    with open("secret-santa.json", "w") as convert_file:
        convert_file.write(json.dumps(secret_santa, indent=4))


# Main function that runs the program
def main():
    interactive_mode: bool = (
        True if os.getenv("INTERACTIVE_MODE", str(True)).lower() == "true" else False
    )
    debug = True

    if not interactive_mode:
        logger.info("Running in non-interactive mode")
        debug: bool = (
            True if os.getenv("DRY_RUN", str(True)).lower() == "true" else False
        )
        csv_file = os.getenv("FILE_PATH", "secret_santa.csv")
        logger.info("CSV File Path: {}".format(csv_file))
        logger.info("Debug Mode: {}".format(debug))
    else:
        csv_file = input("Provide Full path to CSV file: ")
        debug_question = input("Enable debug mode (Y/n): ")
        if debug_question.lower() == "no" or debug_question.lower() == "n":
            debug = False

    # specify columns with datatypes for pandas
    columns = {
        "First Name": str,
        "Last Name": str,
        "Email": str,
        "Amazon link to Gift #1 ($30 max)": str,
        "Amazon link to Gift #2 ($30 max)": str,
        "Amazon link to Gift #3 ($30 max)": str,
    }

    people = pd.read_csv(
        f"./{csv_file}", usecols=list(columns.keys()), dtype=columns
    ).to_dict(orient="records")

    secret_santa = matcher(people)
    writer(secret_santa)
    for i in range(0, len(secret_santa)):
        send_email(secret_santa[i], debug)


if __name__ == "__main__":
    load_dotenv()
    main()
