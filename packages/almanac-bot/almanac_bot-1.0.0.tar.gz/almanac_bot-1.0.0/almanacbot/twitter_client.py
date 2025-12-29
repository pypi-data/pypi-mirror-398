import datetime
import logging
import string
# from typing import List

from babel import Locale
from babel.dates import format_date
import tweepy

from almanacbot.ephemeris import Ephemeris

logger = logging.getLogger(__name__)


class TwitterClient:
    """Class serving as Twitter API client"""

    def __init__(
        self,
        bearer_token: str,
        consumer_key: str,
        consumer_secret: str,
        access_token_key: str,
        access_token_secret: str,
        locale: Locale,
    ):
        self.locale = locale

        # Twitter API v2 client
        self._client_v2: tweepy.Client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token_key,
            access_token_secret=access_token_secret,
        )

        # Twitter API v1 client
        # self._client_v1: tweepy.API = tweepy.API(tweepy.OAuth2BearerHandler(bearer_token))

    def tweet_ephemeris(self, eph: Ephemeris) -> None:
        # tplace: tweepy.Place = None
        # no access to places using Twitter v1 API with free account
        # if eph.location:
        #     logger.info(f"Obtaining Place from ephemeris coordinates: {eph.location}")
        #     places: List[tweepy.Place] = self._client_v1.search_geo(
        #         lat=eph.location.latitude,
        #         lon=eph.location.longitude,
        #         max_results=1,
        #     )
        #     if len(places) > 0:
        #         tplace = places[0]

        # logger.info(f"Tweeting ephemeris: {eph}")
        # self._client_v2.create_tweet(
        #     text=TwitterClient._process_tweet_text(eph, self.locale),
        #     place_id=tplace[0] if tplace else None,
        # )

        # post tweet without place ID (geolocation)
        logger.info(f"Tweeting ephemeris: {eph}")
        self._client_v2.create_tweet(
            text=TwitterClient._process_tweet_text(eph, self.locale),
        )

    @staticmethod
    def _process_tweet_text(eph: Ephemeris, locale: Locale) -> str:
        today = datetime.datetime.now(datetime.timezone.utc)
        template = string.Template(eph.text)

        values = {
            "date": format_date(date=eph.date.date(), format="full", locale=locale),
            "years_ago": today.year - eph.date.year,
        }

        logger.debug(f"Processed ephemeris text: {template.substitute(values)}")

        return template.substitute(values)
