"""Almanac Bot module"""

import argparse
import json
import logging
import logging.config
import os
import sys
from typing import List

from babel import Locale, UnknownLocaleError

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

    def run(self, dry_run: bool = False) -> int:
        """
        Execute once: get untweeted ephemeris for today, tweet them.

        Args:
            dry_run: If True, log what would be tweeted without actually tweeting.

        Returns:
            Number of tweets sent (or would be sent in dry-run mode).
        """
        logger.info("Getting today's untweeted ephemeris...")
        today_ephs: List[Ephemeris] = (
            self.postgresql_client.get_untweeted_today_ephemeris()
        )

        if not today_ephs:
            logger.info("No untweeted ephemeris for today.")
            return 0

        logger.debug(f"Found {len(today_ephs)} untweeted ephemeris entries.")

        tweets_sent = 0
        for eph in today_ephs:
            try:
                if dry_run:
                    text = TwitterClient._process_tweet_text(eph, self.locale)
                    logger.info(f"[DRY-RUN] Would tweet id={eph.id}: {text}")
                else:
                    logger.info(f"Tweeting ephemeris id={eph.id}...")
                    self.twitter_client.tweet_ephemeris(eph)
                    self.postgresql_client.mark_as_tweeted(eph.id)
                    logger.info(f"Successfully tweeted ephemeris id={eph.id}")
                tweets_sent += 1
            except Exception:
                logger.exception(f"Failed to tweet ephemeris id={eph.id}")

        mode = "would be sent" if dry_run else "sent"
        logger.info(f"Completed: {tweets_sent}/{len(today_ephs)} tweets {mode}.")
        return tweets_sent


def main() -> None:
    """Main entry point for one-shot execution."""
    parser = argparse.ArgumentParser(
        description="Almanac Bot - Tweet historical events"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log tweets without actually sending them",
    )
    args = parser.parse_args()

    logger.info("Starting Almanac Bot (one-shot mode)...")

    ab = AlmanacBot()
    tweets_sent = ab.run(dry_run=args.dry_run)

    mode = "would be" if args.dry_run else ""
    logger.info(f"Almanac Bot finished. Tweets {mode} sent: {tweets_sent}")
    sys.exit(0)


if __name__ == "__main__":
    main()
