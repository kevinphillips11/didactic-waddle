import os
import random
import subprocess
import sys
import requests
from pytube import YouTube
import youtube_dl

def get_youtube_urls(query, num_results=20):
    youtube_urls = []
    try:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': True,
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f'ytsearch{num_results}:{query}', download=False)
            for result in search_results['entries']:
                if result:
                    youtube_urls.append(f'http://youtube.com/?v={result["url"]}')
    except Exception as e:
        print(f"An error occurred: {e}")

    return youtube_urls

def download_and_convert_to_mp3(url, output_path):
    try:
        yt = YouTube(url)
        video_stream = yt.streams.filter(file_extension='mp4', progressive=True).first()
        video_path = video_stream.download(output_path)

        mp3_path = os.path.splitext(video_path)[0] + ".mp3"
        subprocess.run(['ffmpeg', '-i', video_path, mp3_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        os.remove(video_path)

        return mp3_path
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def upload_to_transfer_sh(file_path):
    try:
        with open(file_path, 'rb') as file:
            response = requests.post('https://transfer.sh/', files={'file': file})
            if response.status_code == 200:
                return response.text.strip()
            else:
                print(f"Failed to upload to transfer.sh. Status code: {response.status_code}")
                return None
    except Exception as e:
        print(f"An error occurred while uploading to transfer.sh: {e}")
        return None

def remove_file(file_path):
    try:
        os.remove(file_path)
    except Exception as e:
        print(f"An error occurred while removing the file: {e}")

def update_index_html(audio_url):
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audio Player</title>
</head>
<body>

<h1>Audio Player</h1>

<audio controls>
    <source src="{audio_url}" type="audio/mp3">
    Your browser does not support the audio tag.
</audio>

</body>
</html>
"""
    with open('index.html', 'w') as html_file:
        html_file.write(html_content)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <artist_name>")
        sys.exit(1)

    artist_name = ' '.join(sys.argv[1:])
    output_path = os.path.join(os.getcwd(), "downloads")

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    youtube_urls = get_youtube_urls(artist_name, num_results=20)

    if not youtube_urls:
        print(f"No results found for {artist_name}")
        sys.exit(1)

    random_video_url = random.choice(youtube_urls)
    print(f"Downloading and converting a random song by {artist_name} from {random_video_url}")

    mp3_path = download_and_convert_to_mp3(random_video_url, output_path)

    if mp3_path:
        print("Uploading to transfer.sh...")
        transfer_sh_url = upload_to_transfer_sh(mp3_path)

        if transfer_sh_url:
            print(f"Audio file is uploaded to transfer.sh. You can listen to it here: {transfer_sh_url}")
            
            print("Updating index.html...")
            update_index_html(transfer_sh_url)
            
            print("Removing the local audio file...")
            remove_file(mp3_path)
            print("Local audio file removed.")
        else:
            print("Failed to upload to transfer.sh.")
    else:
        print("Failed to download and convert to MP3.")
