# oauth.py

from authlib.integrations.flask_client import OAuth
from config import Config
oauth = OAuth()

# 設定各種 OAuth 提供者
twitter = oauth.register(
    name='twitter',
    client_id=Config.TWITTER_CLIENT_ID,
    client_secret=Config.TWITTER_CLIENT_SECRET,
    authorize_url='https://api.twitter.com/oauth/authenticate',
    authorize_params=None,
    request_token_url='https://api.twitter.com/oauth/request_token',
    request_token_params=None,
    access_token_url='https://api.twitter.com/oauth/access_token',
    access_token_params=None,
    refresh_token_url=None,
    redirect_uri='/twitter/authorized',
    client_kwargs=None
)
