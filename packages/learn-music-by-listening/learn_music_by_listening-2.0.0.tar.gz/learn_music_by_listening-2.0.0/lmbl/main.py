#!/usr/bin/env python3
"""
Learn Music By Listening (lmbl)
Simple music player that displays educational facts while playing

Format: youtube_url, fact
One song per line

Usage: python -m lmbl.main playlist.txt
"""

import sys
import time
from pathlib import Path
from tempfile import gettempdir
import yt_dlp
import pygame
from plyer import notification
from pynput import keyboard


class MusicLearner:
    def __init__(self, playlist_file):
        self.playlist_file = playlist_file
        self.songs = []
        self.current_index = 0
        self.paused = False
        self.skip_requested = False
        self.quit_requested = False
        self.temp_dir = Path(gettempdir()) / "lmbl"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Parse playlist
        self.parse_playlist()
        
        # Setup keyboard listener
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()
    
    def parse_playlist(self):
        """Parse playlist file: url, fact"""
        with open(self.playlist_file, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Split on first comma
            if ',' in line:
                parts = line.split(',', 1)
                url = parts[0].strip()
                fact = parts[1].strip() if len(parts) > 1 else "No fact provided"
                
                if url.startswith('http'):
                    self.songs.append({
                        'url': url,
                        'fact': fact
                    })
        
        print(f"Loaded {len(self.songs)} songs")
    
    def show_fact(self, fact, song_number):
        """Show fact as system notification"""
        try:
            notification.notify(
                title=f"🎵 Song {song_number}/{len(self.songs)}",
                message=fact,
                app_name='Learn Music By Listening',
                timeout=15  # Show for 15 seconds
            )
        except Exception as e:
            print(f"Notification error: {e}")
    
    def on_key_press(self, key):
        """Handle keyboard input"""
        try:
            if key == keyboard.Key.space:
                self.toggle_pause()
            elif hasattr(key, 'char'):
                if key.char == 'n':
                    self.skip_requested = True
                    pygame.mixer.music.stop()
                elif key.char == 'q':
                    self.quit_requested = True
                    pygame.mixer.music.stop()
        except AttributeError:
            pass
    
    def toggle_pause(self):
        """Toggle pause/resume"""
        if pygame.mixer.music.get_busy() or self.paused:
            if self.paused:
                pygame.mixer.music.unpause()
                self.paused = False
                print(f"\n▶  RESUMED")
            else:
                pygame.mixer.music.pause()
                self.paused = True
                print(f"\n⏸  PAUSED")
    
    def download_audio(self, url, song_number):
        """Download audio using yt-dlp"""
        output_path = self.temp_dir / f"song_{song_number}.mp3"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(output_path.with_suffix('')),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }
        
        print(f"⬇  Downloading song {song_number}/{len(self.songs)}...")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return output_path
        except Exception as e:
            print(f"Download error: {e}")
            return None
    
    def play_song(self, song, song_number):
        """Play a single song and show its fact"""
        print(f"\n{'='*60}")
        print(f"Song {song_number}/{len(self.songs)}")
        print(f"Fact: {song['fact']}")
        print(f"{'='*60}")
        print("Controls: [SPACE]=Pause [N]=Next [Q]=Quit")
        
        # Download audio
        audio_file = self.download_audio(song['url'], song_number)
        if not audio_file or not audio_file.exists():
            print(f"Failed to download song {song_number}, skipping...")
            return
        
        # Show fact notification
        self.show_fact(song['fact'], song_number)
        
        # Play with pygame
        try:
            pygame.mixer.music.load(str(audio_file))
            pygame.mixer.music.play()
            
            self.skip_requested = False
            
            # Wait for song to finish or skip request
            while pygame.mixer.music.get_busy() and not self.skip_requested and not self.quit_requested:
                time.sleep(0.1)
            
            pygame.mixer.music.stop()
            
        except Exception as e:
            print(f"Playback error: {e}")
        finally:
            # Cleanup temp file
            try:
                audio_file.unlink()
            except:
                pass
    
    def play_all(self):
        """Play all songs in sequence"""
        print("\n🎵 LEARN MUSIC BY LISTENING 🎵")
        print(f"Loaded {len(self.songs)} songs\n")
        
        while self.current_index < len(self.songs) and not self.quit_requested:
            song = self.songs[self.current_index]
            self.play_song(song, self.current_index + 1)
            self.current_index += 1
            
            if not self.quit_requested and self.current_index < len(self.songs):
                print("\n⏭  Next song in 2 seconds...")
                time.sleep(2)
        
        print("\n✓ Playlist finished" if not self.quit_requested else "\n✓ Quit by user")
        self.listener.stop()
        pygame.mixer.quit()


def main():
    if len(sys.argv) < 2:
        print("Usage: lmbl <playlist_file>")
        print("\nPlaylist format (one per line):")
        print("  https://youtube.com/watch?v=..., This is a fact about music")
        print("  https://youtube.com/watch?v=..., Another interesting fact")
        return
    
    playlist_path = Path(sys.argv[1])
    
    if not playlist_path.exists():
        print(f"Error: {playlist_path} not found")
        return
    
    # Check dependencies
    try:
        import yt_dlp
        import pygame
        import plyer
        import pynput
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("\nInstall with:")
        print("pip install yt-dlp pygame plyer pynput --break-system-packages")
        return
    
    player = MusicLearner(playlist_path)
    player.play_all()


if __name__ == "__main__":
    main()