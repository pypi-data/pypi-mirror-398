import os
import subprocess
import pathlib
import argparse
import mpd
import logging
from pylyr.crawler import Crawler

import gobject
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import pympris


class PyLyr:
    def __init__(self, artist=None, title=None):
        if artist is not None and title is not None:
            logging.info('Song and artist manually specified')

            self.source = 'manual'
            self.artist = artist
            self.title = title

        else:
            logging.info('Connecting to mpd to determine song and artist')

            self.source = 'mpd'
            self.client = mpd.MPDClient()
            try:
                self.client.connect("localhost", 6600)
            except ConnectionRefusedError as e:
                logging.info(e)
                logging.info('mpd server is inactive or does not exist')
                self.source = 'mpris'

            if self.source == 'mpd':
                current_song = self.client.currentsong() 
            else:
                current_song = None

            if current_song:
                self.artist = current_song['artist']
                self.title = current_song['title']

            # cannot find active title associated w/ mpd server
            # -> look for active MPRIS enabled clients
            else:
                logging.info('Cannot find title via mpd; trying MPRIS')
                dbus_loop = DBusGMainLoop()
                bus = dbus.SessionBus(mainloop=dbus_loop)

                # get unique ids for all available players
                players_ids = list(pympris.available_players())

                if not len(players_ids):
                    print('Cannot detect any active mpd or MPRIS servers')
                    exit(1)

                mp = pympris.MediaPlayer(players_ids[0], bus)

                metadata = mp.player.Metadata
                self.artist, = metadata.get('xesam:artist')
                self.title = metadata.get('xesam:title')

        self.artist = self.artist.replace('/', '')
        self.title = self.title.replace('/', '')

        lyrics_dir = pathlib.Path.home() / '.local/share/lyrics'
        lyrics_dir.mkdir(parents=True, exist_ok=True)
        self.lyrics_file = lyrics_dir / f"{self.artist} - {self.title}.txt"
        logging.info(f'Lyrics file: {self.lyrics_file}')


    def get_lyrics(self) -> str:
        if (not os.path.exists(self.lyrics_file) or
            os.path.getsize(self.lyrics_file) == 0):

            logging.info('Local lyrics file does not exist or is empty')

            with Crawler(self.artist, self.title) as crawler:
                lyrics = crawler.get_lyrics()
            if lyrics:
                with open(self.lyrics_file, 'w') as f:
                    f.write(lyrics)
            else:
                logging.info("Could not find lyrics")
                return '' 

        header = f'{self.artist} - {self.title}'
        with open(self.lyrics_file, 'r') as f:
            return f'{header}\n{"─" * len(header)}\n{f.read()}'


    def open_in_editor(self) -> None:
        logging.info('Opening lyrics file in default editor')
        editor = os.environ.get('EDITOR', 'vi')
        subprocess.run([editor, self.lyrics_file])


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.source == 'mpd':
            self.client.close()
            self.client.disconnect()
