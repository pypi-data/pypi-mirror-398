"""Almanac Bot module"""

import json
import logging
import logging.config
import os
import sys
import time
from typing import List

from babel import Locale, UnknownLocaleError
import schedule

from almanacbot import config, constants
from almanacbot.ephemeris import Ephemeris
from almanacbot.postgresql_client import PostgreSQLClient
from almanacbot.twitter_client import TwitterClient

logger = logging.getLogger("almanacbot")


class AlmanacBot:
    """Almanac Bot class"""

    def __init__(self):
        self.conf: config.Configuration = None
        self.twitter_client: TwitterClient = None
        self.postgresql_client: PostgreSQLClient = None

        # configure logger
        self._setup_logging()

        # read configuration
        logger.info("Initializing Almanac Bot...")
        try:
            self.conf = config.Configuration(constants.CONFIG_FILE_NAME)
        except ValueError:
            logger.exception("Error getting configuration.")
            sys.exit(1)

        # setup locale
        try:
            self.locale: Locale = Locale.parse(self.conf.config["language"]["locale"])
            logger.info(f"Locale set to: {self.locale}")
        except (ValueError, UnknownLocaleError):
            logger.exception("Error setting up locale.")
            sys.exit(1)

        # setup Twitter API client
        try:
            self._setup_twitter()
        except ValueError:
            logger.exception("Error setting up Twitter API client.")
            sys.exit(1)

        # setup PostgreSQL client
        try:
            self._setup_postgresql()
        except ValueError:
            logger.exception("Error setting up PostgreSQL client.")
            sys.exit(1)

        logger.info("Almanac Bot properly initialized.")

    def _setup_logging(
        self,
        path="logging.json",
        log_level=logging.DEBUG,
        env_key=constants.CONFIG_ENVVAR,
    ) -> None:
        env_path: str = os.getenv(env_key, None)
        if env_path:
            path = env_path
        if os.path.exists(path):
            with open(path, "rt", encoding="UTF-8") as f:
                log_conf = json.load(f)
                logging.config.dictConfig(log_conf)
                logger.debug(f"Loaded logging configuration:\n{log_conf}")
        else:
            logging.basicConfig(level=log_level)
            logger.debug("Default logging configuration applied.")

    def _setup_twitter(self) -> None:
        logger.info("Setting up Twitter API client...")
        self.twitter_client = TwitterClient(
            bearer_token=self.conf.config["twitter"]["bearer_token"],
            consumer_key=self.conf.config["twitter"]["consumer_key"],
            consumer_secret=self.conf.config["twitter"]["consumer_secret"],
            access_token_key=self.conf.config["twitter"]["access_token_key"],
            access_token_secret=self.conf.config["twitter"]["access_token_secret"],
            locale=self.locale,
        )
        logger.info("Twitter API client set up.")

    def _setup_postgresql(self) -> None:
        logger.info("Setting up PostgreSQL client...")
        self.postgresql_client: PostgreSQLClient = PostgreSQLClient(
            user=self.conf.config["postgresql"]["user"],
            password=self.conf.config["postgresql"]["password"],
            hostname=self.conf.config["postgresql"]["hostname"],
            database=self.conf.config["postgresql"]["database"],
            ephemeris_table=self.conf.config["postgresql"]["ephemeris_table"],
            logging_echo=bool(self.conf.config["postgresql"]["logging_echo"]),
        )
        logger.info("PostgreSQL client set up.")

    def next_ephemeris(self) -> None:
        """This method obtains the next Epehemeris and publishes it arrived the moment"""
        logger.info("Getting today's ephemeris...")
        today_ephs: List[Ephemeris] = self.postgresql_client.get_today_ephemeris()
        logger.debug(f"Today's ephemeris: {today_ephs}")

        # tweet ephemeris
        logger.info("Tweeting ephemeris...")
        for today_eph in today_ephs:
            self.twitter_client.tweet_ephemeris(today_eph)


if __name__ == "__main__":
    ab: AlmanacBot = AlmanacBot()

    # schedule the daily job
    logger.info("Scheduling job...")
    schedule.every(1).days.do(ab.next_ephemeris)
    logger.info("Job scheduled.")

    # loop over ephemeris
    logger.info("Running all jobs...")
    schedule.run_all()
    logger.info("All jobs run.")
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except (KeyboardInterrupt, SystemExit):
            logger.warning("Waiting time has been interrupted. Exiting!")
            del ab
            sys.exit(0)
