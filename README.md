# gitvid

Tool to visualize source code history

[![Example Video](http://img.youtube.com/vi/FBHdaYsWjk8/2.jpg)](http://www.youtube.com/watch?v=FBHdaYsWjk8)

Based on this idea: https://github.com/drummyfish/gitviz 

## TODO (Contributions welcomed)

  - [ ] Performance improvements
  - [ ] Fix large diffs on merge commits
  - [ ] Visualize multiple files at once
    - [ ] Add a way to include and exclude files based on file name globs (e.g. *.py)
  - [ ] Customize ffmpeg command options
  - [ ] Add live-preview with ffplay
  - [ ] Customize the commit message string
  - [ ] Add various verbosity flags (e.g. to show ffmpeg output)
  - [ ] Add a speedup factor (render a frame every N changes only)
  - [ ] Add a scaling factor (render images bigger than final video)

## Dependencies

GitVid is written for **Python3** and uses **pygments** for syntax highlighting and **PIL or Pillow** for image rendering. It calls **git** to fetch the history and **ffmpeg** to render the video. These commands must be installed and present in the current ``$PATH``.

Debian/Ubuntu:

    $ sudo apt-get install python3-imaging python3-pygments ffmpeg git

Max OSX:

    $ brew install ffmpeg
    $ brew install git
    $ pip install pygments Pillow

## Usage

    usage: gitvid.py [-h] [-o OUT] [--fps FPS] [--size SIZE] [--style STYLE]
                     [--fast] [--dry-run]
                     SOURCE PATH

    Visualize source code history

    positional arguments:
      SOURCE             Source folder (git repository)
      PATH               Filenames to include in the visualization

    optional arguments:
      -h, --help         show this help message and exit
      -o OUT, --out OUT  Filename fo the target video file. (default: gitvid.flv)
      --fps FPS          Frames per second (default: 60)
      --size SIZE        Video resolution. Either [WIDTH]x[HEIGHT] or the name of
                         a common resolution (e.g. 790p, 1080p, 4k, ...) (default:
                         790p)
      --style STYLE      Pygments syntax highlighting style (default: No syntax
                         highlighting)
      --fast             Do not visualize individual line additions and deletions,
                         but only full commits.

## Example

    $ git clone https://github.com/defnull/gitvid.git
    $ cd gitvid
    $ python3 gitvid.py -o test.flv . gitvit.py 
