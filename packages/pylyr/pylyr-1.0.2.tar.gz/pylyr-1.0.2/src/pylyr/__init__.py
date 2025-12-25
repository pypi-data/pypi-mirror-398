import argparse
from pylyr.pylyr import PyLyr
import logging


def configure_logging(verbose: bool) -> None:
    if verbose:
        logging.basicConfig(level=logging.INFO)


def main():
    description = '''
        Display song lyrics. 

        If title and artist are not supplied, mpd or MPRIS APIs
        are used to try to ascertain the currently playing song.
        '''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-a', '--artist', help="Manually specify artist")
    parser.add_argument('-t', '--title', help="Manually specify title")
    parser.add_argument('-e', '--editor', action='store_true', 
        help='Open lyrics file in text editor') 
    parser.add_argument('-v', '--verbose', action='store_true', 
        help="Show verbose output")
    args = parser.parse_args()

    configure_logging(args.verbose)

    with PyLyr(args.artist, args.title) as pylr:
        if args.editor:
            pylr.open_in_editor()
        else:
            print(pylr.get_lyrics())
