"""
Based on SmBe19's RedditBots BotSkeleton
Requires an oauth.txt file to function
Written by /u/risos
"""

import re
import os
import time
import praw
import OAuth2Util
import ast

# Used for extracting the scramble from the webpage
from bs4 import BeautifulSoup
from urllib.request import urlopen

# Contains URLs that will go in the comment
from botConfig import *

USERAGENT = 'rubiks v0.2 by /u/risos'
SUBREDDIT = 'cubers'

# Number of posts to try before stopping
# Only useful for when AutoModerator breaks or something
POST_LIMIT = 30

def get_scramble():
    """
    Fetches the scramble from gyroninja's site
    """

    html = urlopen(SCRAMBLE_URL).read()
    # The page contains just the scramble so there is very little cleaning up to do
    text = BeautifulSoup(html, 'html.parser')
    text = text.get_text()
    # text is holding json data as a string so we need to convert it to a dictionary
    text = ast.literal_eval(text)

    return text['scramble']

def scramble_to_url(scramble):
    """
    Parse the scramble and generate the alg.cubing.net url for it
    """
    
    url = 'https://alg.cubing.net/?setup='
    for i in scramble:
        if i == '\'':
            url += '-'
        elif i == ' ':
            url += '_'
        else:
            url += i

    return url

def run_bot():
    """
    Main function
    """

    # Get the scramble and parse it
    scramble = get_scramble()
    scramble_url = scramble_to_url(scramble)

    # Reddit stuff
    r = praw.Reddit(USERAGENT)
    o = OAuth2Util.OAuth2Util(r)
    sub = r.get_subreddit(SUBREDDIT)

    posted = False

    print('Starting bot for subreddit', SUBREDDIT, '\n')

    # Main body
    o.refresh()

    # Read the scramble day from the scramble_day.txt file which just holds an integer number
    with open('scramble_day.txt', 'r') as f:
        SCRAMBLE_DAY = f.read()
        SCRAMBLE_DAY = SCRAMBLE_DAY.strip('\n')

    if not os.path.isfile('posts_replied_to.txt'):
        posts_replied_to = []

    else:
        with open('posts_replied_to.txt', 'r') as f:
            posts_replied_to = f.read()
            posts_replied_to = posts_replied_to.split('\n')
            posts_replied_to = list(filter(None, posts_replied_to))

    # Stop after 30 tries
    tries = 0

    # For each new submission in chronological order (newest to oldest)
    for submission in sub.get_new():
        tries += 1
        if tries > POST_LIMIT:
            print(str(POST_LIMIT) + " post limit reached. Stopping bot.")
            break

        try:
            if submission.id not in posts_replied_to:
                if re.search('daily discussion thread -', submission.title, re.IGNORECASE):
                    comment = '## Daily Scramble ' + str(SCRAMBLE_DAY) + '!\n\nScramble: [`' + scramble + '`](' + scramble_url + ')\n\nPlease count up your moves using [STM](' + STM_URL + ').\n'
                    postedComment = submission.add_comment(comment)
                    print('Sleeping for 1.5 seconds')
                    time.sleep(1.5)
                    posted = True
                    print('\nBot replying to:', submission.title)
                    print('\nText:', comment)

                    # We only want to post on the most recent daily thread which is today's
                    break
        except:
            # I doubt this will ever happen
            print('Ran out of posts')

        # Only allowed to send 1 request per second
        # Not sure if this really needs to be here, but better to be safe than sorry
        print('Checking post...')
        time.sleep(1.5)

    # So the bot doesn't post to the same daily thread twice
    if posted:
        posts_replied_to.append(submission.id)
        with open('posts_replied_to.txt', 'w') as f:
            for post_id in posts_replied_to:
                f.write(post_id + '\n')

        SCRAMBLE_DAY = str(int(SCRAMBLE_DAY) + 1)

        with open('scramble_day.txt', 'w') as f:
            f.write(SCRAMBLE_DAY + '\n')

    else:
        print('No comment was posted.')

if __name__ == '__main__':
    if not USERAGENT:
        print('Missing useragent')
    elif not SUBREDDIT:
        print('Missing subreddit')
    else:
        run_bot()
        print('Bot finished running.')
