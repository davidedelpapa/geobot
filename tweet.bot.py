import time
import os
import logging
import tweepy
import requests


from config_tweepy import get_api


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def check_mentions(api, since_id):
    logger.info("Retrieving mentions")
    new_since_id = since_id
    for tweet in tweepy.Cursor(api.mentions_timeline,
        since_id=since_id).items():
        new_since_id = max(tweet.id, new_since_id)
        if tweet.in_reply_to_status_id is not None:
            continue
        logger.info(f"Answering to {tweet.user.name}")
        logger.info(f"{tweet.text}")
        
        # getting the API response
        response = requests.get(os.getenv("API_HTTPS"))
        
        # reply to mention
        api.update_status(
            status=f"@{tweet.user.screen_name} {response.text}",
            in_reply_to_status_id=tweet.id,
        )
        logger.info(f"Since_id: {new_since_id}")
    return new_since_id

def main():
    api = get_api()
    since_id = int(os.getenv("BOT_SINCEID"))
    while True:
        since_id = check_mentions(api, since_id)
        logger.info("Waiting...")
        time.sleep(30)

if __name__ == "__main__":
    main()