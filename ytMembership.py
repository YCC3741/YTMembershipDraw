import random
import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import json

# CLIENT_SECRETS_FILE變數指定包含此應用程式的OAuth 2.0資訊的文件名稱，包括client_id和client_secret。
CLIENT_SECRETS_FILE = "credentials.json"

# 這個OAuth 2.0訪問範圍允許只讀訪問已認證用戶的帳戶，但不允許其他類型的帳戶訪問。
SCOPES = ["https://www.googleapis.com/auth/youtube.channel-memberships.creator"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

def get_authenticated_service():
    # 自動化認證過程
    if os.path.exists('token.json'):
        credentials = google.oauth2.credentials.Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
    #UCRCAtC_t-Z8GTK7vcRUONRA

    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_local_server(port=0)
    # 保存認證令牌
    with open('token.json', 'w') as token:
        token.write(credentials.to_json())
    
    #credentials = google.oauth2.credentials.Credentials('4/0ATx3LY4q1AB3sD8nKhQqul6RPqmVstzcmoHhVyqGhOFCMma1zXuiFXXI1YwJbCnHKQTquA', 'my-user-agent/1.0')
    
    return googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

def get_members(youtube, channel_id):
    members = []
    request = youtube.members().list(
        part="snippet",
        filterByMemberChannelId=channel_id,
        maxResults=1000
    )
    print(request)
    response = request.execute()
    
    while response:
        for item in response['items']:
            members.append(item['snippet']['displayName'])
        
        if 'nextPageToken' in response:
            request = youtube.members().list(
                part="snippet",
                filterByMemberChannelId=channel_id,
                pageToken=response['nextPageToken'],
                maxResults=100
            )
            response = request.execute()
        else:
            break

    return members

def pick_winner(members):
    return random.choice(members)

if __name__ == "__main__":

    youtube = get_authenticated_service()

    if youtube:
        channel_id = input("請輸入你的頻道ID: ")

        try:
            members = get_members(youtube, channel_id)
            if members:
                winner = pick_winner(members)
                print(f"獲獎者是: {winner}")
            else:
                print("該頻道沒有找到會員。")
        except googleapiclient.errors.HttpError as e:
            print(f"\n!!!!!!!!!有問題: {e}")
    else:
        print("認證失敗，無法建立 YouTube API 服務。")

