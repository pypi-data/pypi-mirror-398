import yt_dlp
import os

def download_youtube_video(url, download_path, video_quality="best"):
    # Ensure the download path exists
    os.makedirs(download_path, exist_ok=True)

    ydl_opts = {
        'format': video_quality,
        'outtmpl': f'{download_path}/%(title)s.%(ext)s',
        'concurrent_fragments': 4, 
        'noprogress': False,  # Changed to False so the user sees progress
        'quiet': False,  # Changed to False so the user sees output
        'merge_output_format': 'mp4', 
        'max_filesize': None,  
        'retry_sleep': 5,  
        'http_chunk_size': 1048576,  # 1MB chunks for faster download
        'external_downloader': 'aria2c', # Assuming aria2c is installed and available
    }

    try:
        print(f"Downloading video from {url} to {download_path} with quality {video_quality}...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("Download complete!")
    except Exception as e:
        print(f"Error during download: {e}")

def main(url=None, download_path=None, video_quality=None):
    if url is None:
        url = input("Enter the video URL: ")
    if download_path is None:
        # For production, use a user-writable directory.
        USER_DATA_BASE_DIR = os.path.join(os.path.expanduser('~'), '.PersonaCipher')
        DOWNLOAD_DIR = os.path.join(USER_DATA_BASE_DIR, 'videos')
        print(f"Default download path: {DOWNLOAD_DIR}")
        user_input_path = input("Enter the download path (press Enter for default): ")
        download_path = user_input_path if user_input_path else DOWNLOAD_DIR
        
    if video_quality is None:
        video_quality = input("Enter video quality ('best', 'worst', '720p', etc., press Enter for 'best'): ") or "best"
    
    # Check if download_path is still relative, and make it absolute if needed (for user input)
    if not os.path.isabs(download_path):
        download_path = os.path.abspath(download_path)

    download_youtube_video(url, download_path, video_quality)

if __name__ == "__main__":
    main()
