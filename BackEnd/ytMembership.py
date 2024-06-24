import random
import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import json
from datetime import datetime

from flask import Flask, redirect, request, session, url_for
from google_auth_oauthlib.flow import Flow


from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
import pytz

app = Flask(__name__)
app.secret_key = "ThankYou9527"

# 這些值應與你在 Google Cloud Console 註冊的設置相匹配
CLIENT_SECRETS_FILE = "credentials.json"
TEST_CHANNEL_ID = "UCdxCJxa4yZUx4gUCHYLzHaw"
SCOPES = ["https://www.googleapis.com/auth/youtube.channel-memberships.creator",
          "https://www.googleapis.com/auth/youtube",
          "https://www.googleapis.com/auth/youtube.readonly"]

REDIRECT_URI = "https://rufuit.com/oauth2callback"  # 注意這個 URI 要與你的實際部署匹配


@app.route("/")
def index():
    # 創建 OAuth 流程對象
    #print(os.getcwd())

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
    )

    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt='consent'
    )

    # 將 state 保存到 session 以供回調使用
    session["state"] = state

    return redirect(authorization_url)


@app.route("/oauth2callback")
def oauth2callback():
    # 指定的 state 要從 session 中獲取
    state = session["state"]
    

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state, redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(authorization_response=request.url)

    if not flow.credentials:
        return "Failed to authenticate.", 401

    session["credentials"] = flow.credentials.to_json()  # 將憑證存儲在 session 中

    return redirect(url_for("get_members"))


@app.route("/youtube_data")
def youtube_data():
    #print ( "!!!!!!!!!!!!!!!!!!!!!!",session["credentials"])
    
    # refresh_token, token_uri, client_id, and client_secret.

    newPac = json.loads(session["credentials"])
    newPac["expiry"] =  datetime.fromisoformat(newPac["expiry"])
    newPac["expiry"] = newPac["expiry"].replace(tzinfo=None)
    #print("!!!!!!!!!!!!!!!!!!!",newPac["expiry"])


    credentials = google.oauth2.credentials.Credentials( **newPac)

    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

    request = youtube.channels().list(
        part="snippet,contentDetails,statistics", mine=True
    )

    #print("!!!!!!!!!!!!!!!!!", request)

    response = request.execute()

    return str(response)


@app.route("/get_members")
def get_members(channel_id=TEST_CHANNEL_ID):
    members = []
    print(session["credentials"])

    newPac = json.loads(session["credentials"])
    newPac["expiry"] =  datetime.fromisoformat(newPac["expiry"])
    newPac["expiry"] = newPac["expiry"].replace(tzinfo=None)

    credentials = google.oauth2.credentials.Credentials( **newPac)

    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

    request = youtube.members().list(
        part="snippet", 
        #filterByMemberChannelId=channel_id, 
        maxResults=1000
    )
    #print(request)
    response = request.execute()

    while response:
        for item in response["items"]:
            members.append(item["snippet"]["displayName"])

        if "nextPageToken" in response:
            request = youtube.members().list(
                part="snippet",
                #filterByMemberChannelId=channel_id,
                pageToken=response["nextPageToken"],
                maxResults=100,
            )
            response = request.execute()
        else:
            break

    return members

if __name__ == "__main__":
    app.run('localhost', 9527)
