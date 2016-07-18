# gitvid

Tool to visualize source code history

Based on this idea: https://github.com/drummyfish/gitviz 

## Dependencies

  * python3-imaging
  * python3-pygments
  * ffmpeg
  * git

## Usage

    usage: gitvid.py [-h] [-o OUT] [--size SIZE] [--style STYLE] [--dry-run] SOURCE PATH

    positional arguments:
      SOURCE             Source folder (git repository)
      PATH               Filenames to include in the visualization

    optional arguments:
      -h, --help         show this help message and exit
      -o OUT, --out OUT  Filename fo the target video file. (default: gitvid.flv)
      --size SIZE        Video resolution. Either [WIDTH]x[HEIGHT] or the name of
                         a common resolution (e.g. 790p, 1080p, 4k, ...) (default:
                         790p)
      --style STYLE      Pygments syntax highlighting style (default: bw)
      --dry-run          Run without actually generating a video.

## Example

    $ git clone https://github.com/defnull/gitvid.git
    $ cd gitvid
    $ python3 gitvid.py -o test.flv . gitvit.py 
