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

# Search configurations
searches = [
    {"query": "horror movies", "output": "horror.json"},
    {"query": "comedy movies", "output": "comedy.json"},
    {"query": "romance movies", "output": "romance.json"},
    {"query": "thriller movies", "output": "thriller.json"},
    {"query": "south korean movies", "output": "sk.json"},
    {"query": "depressing movies", "output": "sad.json"}
]

timeframe = "week"
limit = 15  # Top 15 posts

# Function to fetch search results
def fetch_genre_posts(query):
    content = ""
    def write_line(text):
        nonlocal content
        content += text + '\n'
    
    # Search across all subreddits
    url = f"https://oauth.reddit.com/search?q={query}&sort=relevance&t={timeframe}&limit={limit}"
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
            write_line(f"## {i}. {post_data['title']} (from r/{post_data['subreddit']})")
            write_line("")
            write_line(f"**Score:** {post_data['score']}")
            write_line(f"**URL:** {post_data['url']}")
            if post_data.get('selftext'):
                write_line(f"**Body:** {post_data['selftext']}")
            write_line("")
            
            # Fetch top 10 comments for this post
            post_id = post_data['id']
            subreddit = post_data['subreddit']
            comments_url = f"https://oauth.reddit.com/r/{subreddit}/comments/{post_id}.json?limit=20&depth=25"
            comments_response = requests.get(comments_url, headers=headers)
            
            if comments_response.status_code == 200:
                comments_data = comments_response.json()
                comments = comments_data[1]['data']['children'] if len(comments_data) > 1 else []
                write_line(f"### Top {min(20, len(comments))} comments and their replies (up to depth 25)")
                write_line("")
                
                def write_comment(comment, depth=0, max_depth=25):
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
                
                for j, comment in enumerate(comments[:20], 1):
                    write_comment(comment, 0)
                write_line("")
            else:
                write_line(f"**Error fetching comments:** {comments_response.status_code}")
                write_line("")
        
        write_line("---")
        write_line("")
    else:
        write_line(f"**Error in search:** {response.status_code} - {response.text}")
    
    return content

# Process all searches
for search in searches:
    print(f"Fetching data for: {search['query']}")
    
    # Fetch content for this search
    content = fetch_genre_posts(search['query'])
    
    # Save to JSON
    with open(search['output'], 'w', encoding='utf-8') as f:
        json.dump({"content": content}, f)
    
    print(f"Results saved to {search['output']}")

print("All genre searches completed!")