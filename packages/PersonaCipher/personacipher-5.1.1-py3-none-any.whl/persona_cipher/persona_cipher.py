import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import face_recognition
import cv2
import numpy as np
import pyfiglet
from colorama import Fore, init
from .fetch_info import main as fetcher
from .mp4_downloader import main as mp4_downloader_main # Added import
import platform
import importlib.resources # Added import

init(autoreset=True)

# Global lists for known face encodings and names
known_face_encodings = []
known_face_names = []

# Define a base directory for user-generated data (e.g., known faces)
# For production, use a user-writable directory.
USER_DATA_BASE_DIR = os.path.join(os.path.expanduser('~'), '.PersonaCipher')
KNOWN_FACES_DIR = os.path.join(USER_DATA_BASE_DIR, 'known_faces')

def clear_screen():
    current_os = platform.system()
    if current_os in ["Linux", "Darwin"]:
        os.system("clear")
    elif current_os == "Windows":
        os.system("cls")

def create_ascii_art_with_author(project_name, author_name, author_description):
    project_ascii = pyfiglet.figlet_format(project_name, font="standard") # Changed font
    lines = project_ascii.split('\n')
    max_len = max(len(line) for line in lines) if lines else 0
    
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 80  # Default width if not in a proper terminal
    
    padding = (terminal_width - max_len) // 2 if terminal_width > max_len else 0

    for line in lines:
        print(" " * padding + Fore.RED + line)
    
    desc_padding = (terminal_width - len(author_description)) // 2 if terminal_width > len(author_description) else 0
    author_padding = (terminal_width - len(f"Author: {author_name}")) // 2 if terminal_width > len(f"Author: {author_name}") else 0

    print(" " * desc_padding + Fore.MAGENTA + author_description)
    print(" " * author_padding + Fore.RED + f"Author: {author_name}")

# Helper function to draw a sniper cross
def draw_sniper_cross(img, center_x, center_y, size, color, thickness):
    half_size = size // 2
    # Horizontal line
    cv2.line(img, (center_x - half_size, center_y), (center_x + half_size, center_y), color, thickness)
    # Vertical line
    cv2.line(img, (center_x, center_y - half_size), (center_x, center_y + half_size), color, thickness)
    # Center dot (optional, for aesthetics)
    cv2.circle(img, (center_x, center_y), thickness, color, -1)

# Helper function to draw a round sniper cross
def draw_round_sniper_cross(img, center_x, center_y, radius, color, thickness):
    # Outer circle
    cv2.circle(img, (center_x, center_y), radius, color, thickness)
    # Inner cross lines
    # Horizontal line
    cv2.line(img, (center_x - radius, center_y), (center_x + radius, center_y), color, thickness)
    # Vertical line
    cv2.line(img, (center_x, center_y - radius), (center_x, center_y + radius), color, thickness)
    # Center dot
    cv2.circle(img, (center_x, center_y), thickness * 2, color, -1)


# Load known faces from the dataset
def load_known_faces(dataset_dir=KNOWN_FACES_DIR): # Changed default to KNOWN_FACES_DIR
    if not os.path.exists(dataset_dir):
        print(f"Warning: Known faces directory not found at {dataset_dir}. Run create_dataset first.")
        return

    for person_name in os.listdir(dataset_dir):
        person_dir = os.path.join(dataset_dir, person_name)
        if not os.path.isdir(person_dir):
            continue
        for img_file in os.listdir(person_dir):
            img_path = os.path.join(person_dir, img_file)
            if os.path.isfile(img_path):  # Only proceed if it's a file
                image = face_recognition.load_image_file(img_path)
                face_encodings = face_recognition.face_encodings(image)
                if len(face_encodings) > 0:
                    known_face_encodings.append(face_encodings[0])
                    known_face_names.append(person_name)

    if known_face_encodings:
        print("Encoded faces for recognition.")
    else:
        print("No known faces found. Run create_dataset to generate known faces.")

# Recognize faces in a given image
def recognize_faces_in_image(image_path=None):
    # Default path for images
    if image_path is None:
        try:
            # Use importlib.resources for packaged assets
            default_image_path_obj = importlib.resources.files('persona_cipher').joinpath('assets/images')
            image_path = str(default_image_path_obj)
        except Exception as e:
            print(f"Error accessing packaged image assets: {e}")
            return
    
    # If the image is not found at the provided path, ask for the full path
    if not os.path.exists(image_path):
        print(f"Image not found at {image_path}. Please provide the full path.")
        image_path = input("Enter the full path of the image: ")

        # If the full path is still invalid, return with an error
        if not os.path.exists(image_path):
            print(f"Error: The image file '{image_path}' does not exist.")
            return

    try:
        # Load the image
        image_to_recognize = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image_to_recognize)

        if not face_locations:
            print("No faces found in the image.")
            return

        # Encode the faces
        face_encodings = face_recognition.face_encodings(image_to_recognize, face_locations)

        # Loop through faces and compare with known faces
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            # If a match is found and within the threshold, use the known name
            if matches[best_match_index] and face_distances[best_match_index] < 0.6:  # Adjust threshold as necessary
                name = known_face_names[best_match_index]

            # Draw a round sniper cross around the face (black color)
            center_x = (left + right) // 2
            center_y = (top + bottom) // 2
            radius = max(right - left, bottom - top) // 2
            draw_round_sniper_cross(image_to_recognize, center_x, center_y, radius, (0, 0, 0), 2) # Black color (BGR)
            cv2.putText(image_to_recognize, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1) # Black text

        # Convert to BGR for OpenCV display
        bgr_image = cv2.cvtColor(image_to_recognize, cv2.COLOR_RGB2BGR)
        cv2.imshow('Recognized Faces', bgr_image)
        cv2.waitKey(0)  # Wait for a key press to close the window
        cv2.destroyAllWindows()

    except Exception as e:
        print(f"An error occurred: {e}")

# Recognize faces in a given video
def recognize_faces_in_video(mp4_path=None):
    # Initialize variables to avoid UnboundLocalError
    frame_num = 0
    frame_skip_interval = 1 # Process every frame by default
    last_known_face_locations = []
    last_known_face_names = []
    found_match = False
    # Default path for videos
    if mp4_path is None:
        try:
            # Use importlib.resources for packaged assets
            default_video_path_obj = importlib.resources.files('persona_cipher').joinpath('assets/videos')
            mp4_path = str(default_video_path_obj)
        except Exception as e:
            print(f"Error accessing packaged video assets: {e}")
            return

    video_full_path = mp4_path

    if not os.path.exists(video_full_path):
        print(f"Video not found at {video_full_path}. Please provide the full path.")
        mp4_path = input("Enter the full path of the video: ")

        # Ensure the user-provided path is valid
        if not os.path.exists(mp4_path):
            print(f"Error: The video file '{mp4_path}' does not exist.")
            return

        video_full_path = mp4_path

    # Open the video file
    video_capture = cv2.VideoCapture(video_full_path)

    if not video_capture.isOpened():
        print(f"Error opening video file {video_full_path}")
        return

    try:
        # Process video frame by frame
        while True:
            ret, frame = video_capture.read()
            if not ret or frame is None:
                print("End of video or no frame.")
                break
            
            # Initialize current frame's face data
            current_face_locations = []
            current_face_names = []

            if frame_num % frame_skip_interval == 0:
                # Process this frame for face detection and encoding
                rgb_frame = frame[:, :, ::-1]
                small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.5, fy=0.5)
                face_locations_small = face_recognition.face_locations(small_frame, model="hog")
                face_encodings_small = face_recognition.face_encodings(small_frame, face_locations_small)

                # Scale locations back to original frame size
                for i, (top, right, bottom, left) in enumerate(face_locations_small):
                    top *= 2
                    right *= 2
                    bottom *= 2
                    left *= 2
                    current_face_locations.append((top, right, bottom, left))

                    # Recognize face
                    name = "Unknown"
                    if len(known_face_encodings) > 0 and len(face_encodings_small) > i: # Check if encoding exists for this face
                        matches = face_recognition.compare_faces(known_face_encodings, face_encodings_small[i])
                        face_distances = face_recognition.face_distance(known_face_encodings, face_encodings_small[i])
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index] and face_distances[best_match_index] < 0.6:
                            name = known_face_names[best_match_index]
                            found_match = True
                    current_face_names.append(name)

                # Store for skipped frames
                last_known_face_locations = current_face_locations
                last_known_face_names = current_face_names
            else:
                # Use stored face data for skipped frames
                current_face_locations = last_known_face_locations
                current_face_names = last_known_face_names

            # Draw on the frame
            for (top, right, bottom, left), name in zip(current_face_locations, current_face_names):
                # Draw a round sniper cross (black color)
                center_x = (left + right) // 2
                center_y = (top + bottom) // 2
                radius = max(right - left, bottom - top) // 2
                draw_round_sniper_cross(frame, center_x, center_y, radius, (0, 0, 0), 2) # Black color (BGR)
                cv2.putText(frame, name, (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2) # Black text

            # Display the frame with the recognized faces
            cv2.imshow('Video', frame)
            
            # Exit the video on pressing 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            frame_num += 1 # Increment frame number

    except KeyboardInterrupt:
        print("\nVideo playback interrupted by user.")
    except Exception as e:
        print(f"An error occurred during video playback: {e}")
    finally:
        # After processing all frames or on interrupt
        if found_match:
            print("Known faces detected.")
        else:
            print("No known faces detected.")

        # Release video capture and close OpenCV windows
        video_capture.release()
        cv2.destroyAllWindows()

def main_menu():
    project_name = "PersonaCipher"
    author_name = "cyb2rS2c"
    author_description = "Your face recognizer in images & videos."
    create_ascii_art_with_author(project_name, author_name, author_description)
    load_known_faces()

    try:
        while True:
            print("\nFace Recognition Menu")
            print("1. Recognize faces in an image")
            print("2. Recognize faces in a video")
            print("3. Get personal information summary about the detected person, country, etc (if available)")
            print("4. Download video from URL")
            print("5. Exit")

            choice = input("Select an option: ")

            if choice == '1':
                image_path = input("Enter the path of the image: ")
                recognize_faces_in_image(image_path)
            elif choice == '2':
                video_path = input("Enter the path of the video: ")
                recognize_faces_in_video(video_path)
            elif choice == '3':
                clear_screen()
                fetcher()
            elif choice == '4':
                clear_screen()
                mp4_downloader_main()
            elif choice == '5':
                print("Exiting the program.")
                clear_screen()
                break
            else:
                print("Invalid choice. Please select again.")
    except KeyboardInterrupt:
        print("\nExiting the program due to user interruption.")
        clear_screen()
            
if __name__ == "__main__":
    main_menu()

