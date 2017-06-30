# Googlefit To FitLegit syncing

Sync your google fit calories and weight to fitlegit to calculate your **actual** TDEE.

# Installation

1. `mkvirtualenv googlefit_to_fitlegit`
2. `pip install -r requirements.txt`
3. Hit the [Google Dev Console](https://console.developers.google.com/flows/enableapi?apiid=fitness). Depending on how many google accounts you auth with, you may have to specify the user in the URL parameters. ie. `&authuser=1` for the second authenticated user.
4. Click `Continue`. Then select `Go to credentials` and select `Client ID`
5. Under `Where will you be calling the API from?`, select `Other UI`, under `What data will you be accessing?`, select `User data`, and hit `What credentials will I need?`
6. Name your client, `googlefit_to_fitlegit` works.
6. Under `Set up the OAuth 2.0 consent screen`, select your email address, and pick a product name to show, `googlefit_to_fitlegit` works. Hit `Continue`.
8. Note your `client id`. Download the `.json` file with your creds. Hit `Done`.
3. Authenticate with your google account with the info you just downloaded. This is an interactive authentication that spins up a browser window. This process will generate a `google.json` file with an access and refresh token. The python client will take care of refreshing your access token whenever you run it. The implication is that it runs just fine in a scheduled and unattended job after first auth.
    `./auth.py <client id> <secret>`

# Usage

1. set `FITLEGIT_USER` and `FITLEGIT_PASS` environment variables with any method that suites you.
2. `./sync.py`
3. Enjoy!

# Scheduled Jobs

If you want to schedule a job within *nix, use cron. If you want to do the same within OS X, you'll have to use launchctl. I've included a `googlefit_to_fitlegit.plist` template file to get you started. You'll need to:

1. Modify `googlefit_to_fitlegit.plist` to suit your paths and run time.
2. Create a `googlefit_to_fitlegit.sh` file that the plist file executes that runs `./sync` with the appropriate python/system environment.
2. Place the file in `~/Library/LaunchAgents`
3. Load it via `launchctl load ~/Library/LaunchAgents/googlefit_to_fitlegit.plist`
4. Fire it up via `launchctl start googlefit_to_fitlegit`
