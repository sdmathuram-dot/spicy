import requests
import sys
import json
import os

# Get credentials from environment variables
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
USERNAME = os.getenv('REDDIT_USERNAME')  # Changed to avoid system USERNAME conflict
PASSWORD = os.getenv('PASSWORD')

# Function to get a new access token
def get_new_token():
    auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    data = {
        'grant_type': 'password',
        'username': USERNAME,
        'password': PASSWORD,
        'duration': 'permanent'
    }
    headers = {'User-Agent': 'MovieRecApp/1.0'}
    
    response = requests.post('https://www.reddit.com/api/v1/access_token', auth=auth, data=data, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        if 'error' in token_data:
            print(f"Token Error: {token_data['error']}")
            return None
        return token_data.get('access_token')
    else:
        print(f"Failed to get token: {response.status_code}")
        return None

# Get a new token each time the script runs
token = get_new_token()
if not token:
    sys.exit("Could not obtain access token. Check credentials.")

# Set subreddits
subreddits = ["MovieSuggestions", "moviecritic", "TrueFilm"]

# Function to fetch and accumulate content
def fetch_content(timeframe):
    content = ""
    def write_line(text):
        nonlocal content
        content += text + '\n'
    
    for subreddit in subreddits:
        write_line(f"# Top 5 posts from r/{subreddit} {timeframe}")
        write_line("")
        
        # Make API call to get top 5 posts
        url = f"https://oauth.reddit.com/r/{subreddit}/top?t={timeframe}&limit=5"
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "MovieRecApp/1.0"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            posts = data['data']['children']
            
            for i, post in enumerate(posts, 1):
                post_data = post['data']
                write_line(f"## {i}. {post_data['title']}")
                write_line("")
                write_line(f"**Score:** {post_data['score']}")
                if post_data.get('selftext'):
                    write_line(f"**Body:** {post_data['selftext']}")
                write_line("")
                
                # Fetch top 10 comments for this post
                post_id = post_data['id']
                comments_url = f"https://oauth.reddit.com/r/{subreddit}/comments/{post_id}.json?limit=10&depth=10"
                comments_response = requests.get(comments_url, headers=headers)
                
                if comments_response.status_code == 200:
                    comments_data = comments_response.json()
                    comments = comments_data[1]['data']['children'] if len(comments_data) > 1 else []
                    write_line(f"### Top {min(10, len(comments))} comments and their replies (up to depth 10)")
                    write_line("")
                    
                    def write_comment(comment, depth=0, max_depth=10):
                        if depth > max_depth:
                            return
                        comment_data = comment['data']
                        body = comment_data.get('body', '[Deleted]')
                        author = comment_data.get('author', '[Deleted]')
                        if author == '[Deleted]' or body == '[Deleted]':
                            return  # Skip deleted comments
                        indent = "  " * depth
                        if depth == 0:
                            write_line(f"{j}. {body}")
                        else:
                            write_line(f"{indent}- {body}")
                        
                        # Recurse on replies
                        if 'replies' in comment_data and comment_data['replies'] and isinstance(comment_data['replies'], dict):
                            replies = comment_data['replies']['data']['children']
                            for reply in replies:
                                write_comment(reply, depth + 1, max_depth)
                    
                    for j, comment in enumerate(comments[:10], 1):
                        write_comment(comment, 0)
                    write_line("")
                else:
                    write_line(f"**Error fetching comments:** {comments_response.status_code}")
                    write_line("")
            
            write_line("---")
            write_line("")
        else:
            write_line(f"**Error for r/{subreddit}:** {response.status_code} - {response.text}")
            write_line("---")
            write_line("")
    
    return content

# Fetch for today
content_today = fetch_content("day")
with open('rectoday.json', 'w', encoding='utf-8') as f:
    json.dump({"content": content_today}, f)

# Fetch for month
content_month = fetch_content("month")
with open('recmonth.json', 'w', encoding='utf-8') as f:
    json.dump({"content": content_month}, f)

print("Output saved to rectoday.json and recmonth.json")
