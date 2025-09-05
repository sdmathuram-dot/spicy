import requests
import json
import re
import os
import sys

# Add logging
print("Starting ranking.py...")

# Get API key from environment variable
api_key = os.getenv('OPENROUTER_API_KEY')
if not api_key:
    print("Error: OPENROUTER_API_KEY environment variable not set")
    sys.exit(1)

print(f"API key found: {api_key[:10]}...")

def process_file(input_file, output_file):
    print(f"Processing {input_file} -> {output_file}")

    # Read the Reddit output file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            reddit_content = data['content']
        print(f"Read {len(reddit_content)} characters from {input_file}")
    except Exception as e:
        print(f"Error reading {input_file}: {e}")
        return

    # Construct the prompt
    prompt = f"""
Based on the following Reddit discussions from movie subreddits, analyze the posts and comments to identify the most recommended or discussed movies.

Create a ranked list of the top 20 movies mentioned and dont mention the year, in JSON format with the following structure:
{{
  "ranked_movies": [
    {{
      "rank": 1,
      "title": "Movie Title",
      "reason": "Why it's recommended or why have you ranked it such rank"
    }},
    ...
  ]
}}

Reddit Discussions:
{reddit_content}
"""

    print(f"Sending API request for {input_file}...")

    try:
        response = requests.post(
          url="https://openrouter.ai/api/v1/chat/completions",
          headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",

          },
          data=json.dumps({
            "model": "deepseek/deepseek-chat-v3.1:free",
            "messages": [
              {
                "role": "user",
                "content": prompt
              }
            ],

          })
        )

        print(f"API response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("API response successful")

            if 'choices' in data and data['choices']:
                content = data['choices'][0]['message']['content']
                print(f"AI response length: {len(content)}")

                try:
                    # Try to extract JSON from code block
                    start = content.find('```json')
                    if start != -1:
                        start += len('```json')
                        end = content.find('```', start)
                        if end != -1:
                            json_str = content[start:end].strip()
                            ranked_data = json.loads(json_str)
                            print("Extracted JSON from code block")
                        else:
                            ranked_data = json.loads(content)
                            print("Parsed JSON directly (no closing ```)")
                    else:
                        # Fallback to direct parse if no code block
                        ranked_data = json.loads(content)
                        print("Parsed JSON directly")

                    # Save to file
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(ranked_data, f, indent=4)
                    print(f"Saved rankings to {output_file}")

                except json.JSONDecodeError as e:
                    print(f"Failed to parse AI response as JSON: {e}")
                    print(f"AI response preview: {content[:500]}...")

            else:
                print("No choices in API response")
                print(f"Response data: {data}")

        else:
            print(f"API request failed: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"Error during API call: {e}")

# Process today
print("Processing today's data...")
process_file('rectoday.json', 'todayranked.json')

# Process month
print("Processing month's data...")
process_file('recmonth.json', 'monthranked.json')

# Process genres
print("Processing comedy data...")
process_file('comedy.json', 'comedyranked.json')

print("Processing sad data...")
process_file('sad.json', 'sadranked.json')

print("Processing horror data...")
process_file('horror.json', 'horrorranked.json')

print("Processing romance data...")
process_file('romance.json', 'romanceranked.json')

print("Processing thriller data...")
process_file('thriller.json', 'thrillerranked.json')

print("Processing south korean data...")
process_file('sk.json', 'skranked.json')

print("ranking.py completed")