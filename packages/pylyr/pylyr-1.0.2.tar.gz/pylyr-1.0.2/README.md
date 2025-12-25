# PyLyr

Get lyrics of a song playing through mpd via api requests and webscraping

- Lyrics are cached in `~/.lyrics/` to avoid repeated requests for the same song
  - A nice corollary is that song titles can be determined with a `grep`
  command:
    ```sh
    grep -ri 'lyric string' ~/.lyrics
    ```

## Usage

Run `pylyr -h` to see an overview of command flags

- Output is to stdout by default to allow for easy manipulation

--------------------------------------------------------------------------------

## Examples

Downloading lyrics for all of a specific artist's songs:

    ARTIST="<artist>"
    mpc -f 'pylyr -v -t "%title%" -a "%artist%"' search artist "$ARTIST" \
    | while read line
    do
        sh -c "$line"
    done

Downloading lyrics for your entire library:

    mpc -f 'if \[ ! -f ~/.lyrics/"%artist% - %title%.txt" \]; \
    then pylyr -v -t "%title%" -a "%artist%"; fi' listall | while read line
    do
        sh -c "$line"
    done
