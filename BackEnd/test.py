import argparse
import os
import re

import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow


# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = 'credentials.json'

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

RATINGS = ('like', 'dislike', 'none')

# Authorize the request and store authorization credentials.
def get_authenticated_service():
  flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
  credentials = flow.run_local_server(port=9527, open_browser=False)
  return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)

# Add the video rating. This code sets the rating to 'like,' but you could
# also support an additional option that supports values of 'like' and
# 'dislike.'
def like_video(youtube, args):
  youtube.videos().rate(
    id=args.videoId,
    rating=args.rating
  ).execute()

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--videoId', default='OE63BYWdqC4',
    help='ID of video to like.')
  parser.add_argument('--rating', default='like',
    choices=RATINGS,
    help='Indicates whether the rating is "like", "dislike", or "none".')
  args = parser.parse_args()

  youtube = get_authenticated_service()
  try:
    like_video(youtube, args)
  except (HttpError, e):
    print( 'An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))
  else:
    print ('The %s rating has been added for video ID %s.' %
           (args.rating, args.videoId))




from flask import Flask, redirect, request, session, url_for
from google_auth_oauthlib.flow import Flow
import os
import googleapiclient.discovery

app = Flask(__name__)
app.secret_key = 'YOUR_SECRET_KEY'

CLIENT_SECRETS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
REDIRECT_URI = 'http://localhost:5000/oauth2callback'  # 注意這個 URI 要與你的實際部署匹配

@app.route('/')
def index():
    # 創建 OAuth 流程對象
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    authorization_url, state = flow.authorization_url(
        access_type='offline', include_granted_scopes='true')
    
    # 將 state 保存到 session 以供回調使用
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    # 指定的 state 要從 session 中獲取
    state = session['state']

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state, redirect_uri=REDIRECT_URI)
    flow.fetch_token(authorization_response=request.url)

    if not flow.credentials:
        return 'Failed to authenticate.', 401

    session['credentials'] = flow.credentials.to_json()  # 將憑證存儲在 session 中

    return redirect(url_for('youtube_data'))

@app.route('/youtube_data')
def youtube_data():
    credentials = google.oauth2.credentials.Credentials(
        **session['credentials'])
    
    youtube = googleapiclient.discovery.build(
        'youtube', 'v3', credentials=credentials)

    request = youtube.channels().list(
        part='snippet,contentDetails,statistics',
        mine=True
    )
    response = request.execute()
    return str(response)

if __name__ == '__main__':
    app.run('localhost', 5000)
