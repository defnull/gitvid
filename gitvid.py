import pygments
import pygments.lexers
from pygments.token import Token
import PIL, PIL.Image, PIL.ImageFont, PIL.ImageDraw
from PIL.ImageColor import getrgb
import sys, os
import subprocess, re

font = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'font.pil')

class StyleDict(dict):
    ''' Store color information based on pygments token types. '''
    
    def __init__(self):
        self["fg"] = '#000000'
        self["bg"] = '#ffffff'

    def __missing__(self, token):
        ''' Search the token hierarchy for missing tokens. Default to
            foregrount color. '''
        for t in reversed(token.split()):
            if t in self:
                self[token] = self[t]
                return self[token]
        self[token] = self["fg"]
        return self[token]
        
    def __setitem__(self, key, value):
        ''' Auto-convert CSS/HTML color hashes (e.g. #112233) '''
        if isinstance(value, str):
            value = getrgb(value)
        dict.__setitem__(self, key, value)


def _c_blend(c1,c2,f=0.5):
    ''' Blend two colors together. '''
    return (int(c1[0]*f + c2[0]*(1-f)),
            int(c1[1]*f + c2[1]*(1-f)),
            int(c1[2]*f + c2[2]*(1-f)))

class Renderer:
    def __init__(self, git_path, filename, out="out.flv",
            pygments_style="default", fps=60, size=(1280, 720), quality=90):
        self.git_path = git_path
        self.filename = filename
        self.width, self.height = size
        self.border = 15
        self.lexer = pygments.lexers.get_lexer_for_filename(self.filename)
        self.video_out = out
        self.style = StyleDict()
        self.fps = fps
        self.quality = quality
        self.font = PIL.ImageFont.load(font)

        self.do_highlight = False

        if pygments_style:
            self.do_highlight = True
            self.load_pygments_style(pygments_style)
            
    def load_pygments_style(self, name):
        from pygments.styles import get_style_by_name
        style = get_style_by_name(name)
        self.style["bg"] = style.background_color
        self.style["fg"] = [255-c for c in self.style["bg"]]
        for token, value in list(style.styles.items()):
            rules = value.split()
            for rule in rules:
                if rule.startswith('#'):
                    self.style[token] = rule
                if rule.startswith('bg:#'):
                    self.style[token] = rule[3:]
                    break # 
            if 'bold' not in rules or 'unbold' in rules:
                self.style[token] = _c_blend(self.style[token], self.style["bg"], 0.8)

    def sh(self, *cmd):
        return subprocess.check_output(cmd, cwd=self.git_path).decode('utf8').splitlines()

    def run(self):
    
        self.video_prog = subprocess.Popen(
              ['ffmpeg', '-loglevel', 'panic', '-y',
               '-f', 'image2pipe', '-vcodec', 'mjpeg', '-r', str(self.fps), '-i', '-',
               '-vcodec', 'libx264', '-r', str(self.fps), self.video_out],
              stdin=subprocess.PIPE,
              stdout = open("/dev/null", 'wb'))
        self.video_out = self.video_prog.stdin
        
        self.image = PIL.Image.new("RGB", (self.width, self.height), self.style["bg"])
        self.draw  = PIL.ImageDraw.Draw(self.image)
        
        try:
            self.last_sha = self.last_msg = None
            log = self.sh('git','log','--reverse','--pretty=oneline','--', self.filename)
            for i, line in enumerate(log):
                self.next_sha, self.next_msg = line.split(None, 1)

                if not self.last_sha:
                    self.last_sha = self.next_sha
                    self.last_msg = self.next_msg
                    continue

                print('(%d/%d) %s %s' % (i, len(log), self.next_sha[:8], self.next_msg))
     
                self.render_diff()
                
                self.last_sha = self.next_sha
                self.last_msg = self.next_msg
        finally:
            self.video_out.close()
            self.video_prog.wait()

    def render_diff(self):
        src = self.sh('git','show', '%s:%s' % (self.last_sha, self.filename))
        for op, ln, line in self.sha_diff():
            sys.stdout.write(op)
            sys.stdout.flush()
            if op == '+':
                src.insert(ln, line)
            elif op == '-':
                del src[ln]
            self.render(src)
        sys.stdout.write('\n')

    def sha_diff(self):
        lines = self.sh('git','diff','--minimal', self.last_sha, self.next_sha, '--', self.filename)
        while lines[0][0] != '@':
            del lines[0]

        ln_old, ln_new = 0, 0
        for line in lines:
            if line[0] == '@':
                ln_old, ln_new = list(map(int, re.match('@@ -(\\d+),\\d+ \\+(\\d+),\\d+ @@.*', line).groups()))
            elif line[0] == '+':
                yield '+', ln_new-1, line[1:]
                ln_new += 1
            elif line[0] == '-':
                yield '-', ln_new-1, line[1:]
                ln_old += 1
            else:
                ln_old += 1
                ln_new += 1

    def render(self, src):
        self.draw.rectangle((0,0,self.width, self.height), self.style['bg'])
            
        row = self.border
        col = -1
        offset = self.border
        maxcol = 0
        
        if self.do_highlight:
            tokens = pygments.lex('\n'.join(src), self.lexer)
        else:
            tokens = [(Token.Text, '\n'.join(src))]
        
        for token, text in tokens:
            color = self.style[token]
            points = []
            for c in text:
                col += 1
                if c == '\n':
                    row += 1
                    maxcol = max(maxcol, col)
                    col = -1
                    if row >= self.height - (self.border*2):
                        row = self.border
                        offset += maxcol + self.border
                    continue
                if c == ' ':
                    continue
                if c == '\t':
                    col += 3
                    continue

                points.extend((col + offset, row))

            self.draw.point(points, color)

        text = '%s %s' % (self.next_sha[:8], self.next_msg)
        self.draw.text((0, 0), text, font=self.font, fill=(0,0,0,255))

        self.image.save(self.video_out, 'JPEG', quality=self.quality)


video_size = {
    "8K": (8192, 4608),
    "WHUXGA": (7680, 4800),
    "4320p": (7680, 4320),
    "HUXGA": (6400, 4800),
    "WHSXGA": (6400, 4096),
    "HSXGA": (5120, 4096),
    "WHXGA": (5120, 3200),
    "HXGA": (4096, 3072),
    "4K": (4096, 2304),
    "2160p": (3840, 2160),
    "QUXGA": (3200, 2400),
    "WQSXGA": (3200, 2048),
    "QSXGA": (2560, 2048),
    "2K": (2048, 1152),
    "QWXGA": (2048, 1152),
    "WUXGA": (1920, 1200),
    "HD": (1920, 1080),
    "1080p": (1920, 1080),
    "UXGA": (1600, 1200),
    "900p": (1600, 900),
    "SXGA": (1280, 1024),
    "720p": (1280, 720),
    "WSVGA": (1024, 600),
    "PAL": (720, 576),
    "SVGA": (800, 600),
    "EGA": (640, 350),
    "VGA": (640, 480),
    "CGA": (320, 200)
}


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Visualize source code history')
    parser.add_argument('-o', '--out', metavar='OUT', default="gitvid.flv", help="Filename fo the target video file. (default: gitvid.flv)")
    parser.add_argument('--fps', default="60", type=int, help="Frames per second (default: 60)")
    parser.add_argument('--size', default="720p", help="Video resolution. Either [WIDTH]x[HEIGHT] or the name of a common resolution (e.g. 790p, 1080p, 4k, ...) (default: 790p)")
    parser.add_argument('--style', default=None, help="Pygments syntax highlighting style (default: No syntax highlighting)")
    parser.add_argument('--dry-run',  action='store_true', help="Run without actually generating a video.")
    parser.add_argument('SOURCE', help="Source folder (git repository)")
    parser.add_argument('PATH', help="Filenames to include in the visualization")

    args = parser.parse_args()
    
    if args.size in video_size:
        size = video_size[args.size]
    else:
        size = map(int, args.size.split('x', 1))
    
    r = Renderer(args.SOURCE, args.PATH, out=args.out, size=size, pygments_style=args.style, fps=args.fps)
    r.run()

if __name__ == "__main__":
    main()
    sys.exit(0)



