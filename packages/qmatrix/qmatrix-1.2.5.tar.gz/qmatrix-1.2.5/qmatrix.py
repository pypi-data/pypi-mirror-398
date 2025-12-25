import curses
import random
import time
import sys
import argparse
import json
import threading
import queue
import os
import queue
import requests

# Terminal detection
IS_KITTY = "KITTY_WINDOW_ID" in os.environ
IS_GHOSTTY = "GHOSTTY_BIN_DIR" in os.environ or "GHOSTTY_RESOURCES_DIR" in os.environ
IS_SEXY_TERM = IS_KITTY or IS_GHOSTTY

from constants import ANTONYMS, QUOTES, KATAKANA

# Configuration
CONFIG_PATH = os.path.expanduser("~/.config/qmatrix/config.json")

DEFAULT_CHARSETS = {
    'matrix': KATAKANA + "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*()_+-=[]{}|;:,.<>?/",
    'horror': "†‡☠☢☣☠⚰⚡︎⚓︎⚛⚕⚚⚜⚘⚙⚗⚖⚔⚙⛓⚰⚱⚲⚳⚴⚵⚶⚷⚸⚹⚺⚻⚼⚽︎⚾︎⛄︎⛅︎⛈⛎⛏⛑⛓⛔︎⛩⛪︎⛲︎⛳︎⛵︎⏳⌛︎⏰⏱⏲⏳"
}

class QuoteManager:
    def __init__(self, local_file):
        self.quotes = []
        self.local_file = local_file
        self.fetch_queue = queue.Queue()
        self.load_local()
        self.start_fetcher()

    def load_local(self):
        try:
            with open(self.local_file, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.quotes = [item.get('quoteText', item.get('text', '')) for item in data if item.get('quoteText') or item.get('text')]
                print(f"Loaded {len(self.quotes)} local quotes.")
        except Exception as e:
            self.quotes = QUOTES # Fallback
            print(f"Error loading local quotes: {e}")

    def start_fetcher(self):
        if requests is None:
            return

        def fetcher():
            while True:
                try:
                    # Fetch from a public API
                    response = requests.get("https://type.fit/api/quotes", timeout=10)
                    if response.status_code == 200:
                        new_quotes = response.json()
                        texts = [item.get('text', '') for item in new_quotes if item.get('text')]
                        for t in texts:
                            if t and t not in self.quotes:
                                self.quotes.append(t)
                    # Also try another one for variety
                    response = requests.get("https://zenquotes.io/api/random", timeout=10)
                    if response.status_code == 200:
                        item = response.json()[0]
                        q = item.get('q')
                        if q and q not in self.quotes:
                            self.quotes.append(q)
                except Exception:
                    pass
                time.sleep(300) # Fetch every 5 minutes

        t = threading.Thread(target=fetcher, daemon=True)
        t.start()

    def get_random(self):
        if not self.quotes:
            return random.choice(QUOTES)
        return random.choice(self.quotes)

def load_config(custom_path=None):
    path = custom_path if custom_path else CONFIG_PATH
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
    return {}

class Column:
    def __init__(self, x, height, charset, speed_factor=0.2, tail_min=6, tail_max=None):
        self.x = x
        self.height = height
        self.charset = charset
        self.speed = random.uniform(0.5, 1.5) * speed_factor
        self.counter = 0.0
        # Variable tail: 6 +/- 5 (range 1 to 11)
        self.tail_min = tail_min
        self.tail_max = tail_max if tail_max else tail_min + 5
        self.active_chars = [] # [(y, char, brightness)]
        self._reset_tail()

    def _reset_tail(self):
        # Variable tail: 6 +/- 5 (range 1 to 11)
        low = max(3, self.tail_min - 5)
        high = self.tail_min + 5
        self.tail_len = random.randint(low, high)
        dark_tail_len = 8
        total_len = self.tail_len + dark_tail_len
        
        # Start above screen so we fall in
        self.head_y = -random.randint(total_len, total_len + self.height)
        
        self.active_chars = []
        # Generate the full snake relative to head_y
        # Head is at head_y. Tail trails up (negative direction).
        for i in range(total_len):
            y = self.head_y - i
            char = random.choice(self.charset)
            # Brightness is determined by position (i)
            # 0=Head, >0=Trail
            # We assign placeholder brightness here, update calculates real color
            br = 0 
            self.active_chars.append([y, char, br])

    def update(self):
        self.counter += self.speed
        if self.counter >= 1.0:
            self.counter -= 1.0
            self.head_y += 1 # Track head for reference
            
            # SLIDING PHYSICS: Move every character down
            for item in self.active_chars:
                item[0] += 1
                
                # Randomly mutate chars in the stream ("Digital Rain" effect)
                if random.random() < 0.05:
                     item[1] = random.choice(self.charset)

            # Pruning / Reset
            # Since we slide, we just check if the whole snake is off screen
            # The last item is the top-most (lowest y value originally, now highest index? No, list order)
            # List order: Head(i=0) -> Trail(i=N). 
            # So Head has highest Y. Tail (last item) has lowest Y.
            # If Tail (last item) > height, we are done.
            if self.active_chars[-1][0] > self.height:
                 self._reset_tail()
                 return

            # Assign Colors/Brightness based on index
            # Index 0 is Head.
            dark_tail_len = 8
            body_len = len(self.active_chars) - dark_tail_len
            
            for i, item in enumerate(self.active_chars):
                 if i == 0:
                     item[2] = 3 # Head (White)
                 elif i <= body_len:
                     # Body
                     if i % 2 == 0:
                         item[2] = 2 # Sushi
                     else:
                         item[2] = 1 # Normal
                     
                     if random.random() < 0.1:
                         item[2] = 3 # Sparkle
                 else:
                     # Dark Tail
                     item[2] = 1 # Dim

    def draw(self, stdscr):
        for y, char, br in self.active_chars:
            if 0 <= y < self.height:
                try:
                    attr = 0
                    if br == 3: # Head/Sparkle
                        attr = curses.color_pair(9) | curses.A_BOLD
                    elif br == 2: # Sushi (Primary Body)
                        attr = curses.color_pair(2) 
                    elif br == 1: # Dark/Normal
                         attr = curses.color_pair(1) | curses.A_DIM
                    
                    stdscr.addch(y, self.x, char, attr)
                except curses.error:
                    pass

class QuoteColumn(Column):
    def __init__(self, x, height, charset, speed_factor=0.2, horror_mode=False, quote_manager=None, 
                 persist=True, glitch_rate=0.005, tail_min=6, tail_max=None):
        # Quotes fall slightly more predictably
        q_speed = random.uniform(0.6, 1.2) * speed_factor
        super().__init__(x, height, charset, q_speed, tail_min=tail_min, tail_max=tail_max)
        self.horror_mode = horror_mode
        self.quote_manager = quote_manager
        self.quote_manager = quote_manager
        self.persist = persist
        self.glitch_rate = glitch_rate
        self.quote = self.quote_manager.get_random() if self.quote_manager else random.choice(QUOTES)
        
        # Adjust tail length to accommodate the quote so it doesn't get erased while typing
        # "Rain dropping" feel: The tail must be at least the quote length + leader
        # We add some random trail after the quote too
        self.base_tail_min = tail_min # Keep the user pref for normal resets
        self._adjust_tail_for_quote()
        
        # Ensure quote is not too long for the screen height
        if len(self.quote) > height - 10:
            self.quote = self.quote[:height-13] + "..."
        self.quote = self.quote.upper()
        
        self.quote_idx = 0
        self.is_glitching = False
        self.glitch_timer = 0
        self.original_quote = self.quote
        
        self.char_colors = []
        self._setup_colors()
        
        # State for stationary behavior
        self.holding = False
        self.hold_timer = 0
        self.raining = False

    def _reset_tail(self):
        # QuoteColumn handles its own tail/content generation
        pass
    
    def _reset_quote(self):
        self.quote = self.quote_manager.get_random() if self.quote_manager else random.choice(QUOTES)
        # Ensure quote fits
        if len(self.quote) > self.height - 10:
             self.quote = self.quote[:self.height-13] + "..."
        self.quote = self.quote.upper()
        
        self.head_y = -random.randint(0, 10)
        self.active_chars = []
        self.quote_idx = 0
        self.is_glitching = False
        self.holding = False
        self.hold_timer = 0
        self.raining = False # New state for sliding down
        
        self.original_quote = self.quote
        self._adjust_tail_for_quote()
        if self.persist:
            self._setup_colors()

    def _adjust_tail_for_quote(self):
        # Calculate needed length: Leader(2) + Quote + Padding
        needed = 2 + len(self.quote) + random.randint(1, 6)
        self.tail_len = max(needed, self.base_tail_min)

    def _setup_colors(self):
        self.words = self.quote.split()
        # "Tmatrix" Aesthetic: Mostly Green/White
        # 2 = Normal Green, 3 = Bright Green
        # 9 = White (Head color, used for emphasis)
        # Exotic colors (4-8) kept rare
        if random.random() < 0.8: # 80% chance of pure matrix look
             colors = [2, 2, 2, 3, 3]
        else:
             colors = [2, 3, 4, 5, 6, 7, 8]
             
        self.word_colors = [random.choice(colors) for _ in self.words]
        self.char_colors = []
        for i, word in enumerate(self.words):
            color = self.word_colors[i]
            for _ in word:
                self.char_colors.append(color)
            if i < len(self.words) - 1:
                self.char_colors.append(color)
    
    def draw(self, stdscr):
        for y, char, br, char_idx in self.active_chars:
            if 0 <= y < self.height:
                try:
                    if br == 3: # White Head
                        attr = curses.color_pair(9) | curses.A_BOLD
                    else:
                        color_idx = 2
                        if char_idx < len(self.char_colors):
                            color_idx = self.char_colors[char_idx]
                        
                        attr = curses.color_pair(color_idx)
                        if br == 1:
                            attr |= curses.A_BOLD
                        else:
                            attr |= curses.A_DIM
                    
                    stdscr.addch(y, self.x, char, attr)
                except curses.error:
                    pass

    def update(self):
        # Handle Stationary Hold
        if self.holding:
            self.hold_timer -= 1
            if self.hold_timer <= 0:
                self.holding = False
                # Hybrid Choice: 90% Rain Down, 10% Vanish
                if random.random() < 0.1:
                    self._reset_quote()
                else:
                    self.raining = True
            return

        self.counter += self.speed
        if self.counter >= 1.0:
            self.counter -= 1.0
            self.head_y += 1
            
            # If raining (sliding down after hold)
            if self.raining:
                # True Sliding Physics: Move every character down by 1
                for item in self.active_chars:
                    item[0] += 1
                
                # Remove chars that have fallen off screen
                self.active_chars = [item for item in self.active_chars if item[0] < self.height]
                
                # If block is gone, reset
                if not self.active_chars:
                    self._reset_quote()
                    return # Done
            
            # Glitch logic - Rare anomalies
            if self.horror_mode:
                if random.random() < self.glitch_rate and not self.is_glitching:
                    self.is_glitching = True
                    self.glitch_timer = random.randint(30, 60)
                    # Word swap
                    for word, ant in ANTONYMS.items():
                        if word in self.quote:
                            self.quote = self.quote.replace(word, ant)
                            self._setup_colors() # Update colors for new word
                            break
                    
                    # Shattering effect: randomly insert symbols or remove chars
                    if random.random() < 0.5:
                        new_quote = ""
                        for char in self.quote:
                            if random.random() < 0.2:
                                new_quote += random.choice(DEFAULT_CHARSETS['horror'])
                            elif random.random() < 0.1:
                                new_quote += " "
                            else:
                                new_quote += char
                        self.quote = new_quote
            
            if self.is_glitching:
                self.glitch_timer -= 1
                if self.glitch_timer <= 0:
                    self.is_glitching = False
                    self.quote = self.original_quote
                    self._setup_colors()

            # Rain leader logic: 2 chars of rain before the quote starts
            leader_offset = 2
            
            if self.raining:
                pass # Already handled above, skip typing logic
            
            # If still typing...
            elif self.quote_idx < len(self.quote) + leader_offset:
                if self.quote_idx < leader_offset:
                    char = random.choice(DEFAULT_CHARSETS['matrix'])
                    char_idx = -1 
                else:
                    char = self.quote[self.quote_idx - leader_offset]
                    char_idx = self.quote_idx - leader_offset
                    if self.is_glitching and random.random() < 0.1:
                        char = random.choice(DEFAULT_CHARSETS['horror'])
                
                # Head logic
                self.active_chars.insert(0, [self.head_y, char, 3, char_idx])
                self.quote_idx += 1
            else:
                # Finished typing. Enter HOLD mode.
                self.holding = True
                self.hold_timer = random.randint(40, 100) # Persist for a few seconds (approx 2-4s at 20fps)
                return # Stop processing this frame (freeze)

            # Process tail (pruning)
            # We want total length = Body (self.tail_len) + Dark Tail (8)
            total_allowed = self.tail_len + 8
            if len(self.active_chars) > total_allowed:
                self.active_chars.pop()

            # Fading - Quotes stay bright longer in persist mode
            # But we still want a gradient for the trail part
            for i, item in enumerate(self.active_chars):
                if i == 0: 
                    item[2] = 2 # Head (leader)
                    continue
                
                if self.horror_mode and random.random() < 0.01:
                    item[1] = random.choice(DEFAULT_CHARSETS['horror'])
                
                # Fading gradient
                # 3-shade Green Gradient for Quotes too
                # Because quotes slide, we base it on index relative to the full block length
                # But for simplicity and look, we can just use the index
                
                if i < 2:
                    item[2] = 3 # Bright head/lead
                elif i < len(self.quote) + 2:
                    # The quote itself is usually bright/normal for readability
                    # Let's keep the quote text mostly in the "Bright" and "Normal" range
                    # Use random variation slightly to make it shimmer? No, readable first.
                    item[2] = 2 # Keep actual quote text Bright Green
                else:
                    # The trail after the quote follows the gradient
                    # Calculate position in the trail part
                    trail_idx = i - (len(self.quote) + 2)
                    trail_len_est = 15 # estimate trail length
                    if trail_idx < trail_len_est :
                        # Body of quote trail
                        if trail_idx % 2 == 0:
                             item[2] = 2 # Sushi
                        else:
                             item[2] = 4 # Bright Sparkle
                    else:
                        item[2] = 1 # Dark Tip

            # Reset if head is off screen (failsafe) or empty
            # If raining, we handle reset above when list empty. Failsafe here.
            if self.raining and not self.active_chars:
                 self._reset_quote()
            elif self.head_y > self.height + self.tail_len + 20 and not self.raining:
                # Failsafe for non-raining modes
                if not self.holding:
                     self._reset_quote()

def main(stdscr, args):
    # Check if we should override sexy mode
    global IS_SEXY_TERM
    if args.sexy:
        IS_SEXY_TERM = True

    curses.curs_set(0)
    # Use timeout for non-blocking wait. Reference base is 20 FPS (50ms).
    # We want higher FPS for smoothness, so we must SCALE motion speed down.
    target_fps = args.fps
    ms_per_frame = 1000 // target_fps
    stdscr.timeout(ms_per_frame)
    
    # Physics scaling: If we run 3x faster (60fps vs 20fps), we move 1/3 as much per frame.
    speed_scale = 20.0 / target_fps
    
    curses.start_color()
    
    quote_manager = QuoteManager("/home/rex/Documents/exmatrix/quotes.json")
    
    # Advanced Color Support (256 Colors)
    # Mapping: (Dim, Normal, Bright)
    EXTENDED_COLORS = {
        'green': (22, 40, 82), # Neon Green shades
        'red': (52, 124, 196),
        'blue': (18, 21, 33),
        'white': (242, 250, 255),
        'cyan': (24, 37, 51),
        'magenta': (53, 126, 201),
        'yellow': (58, 142, 226),
    }
    
    bg = curses.COLOR_BLACK
    
    # Background Logic
    if args.transparent:
        curses.use_default_colors()
        bg = -1
    elif args.bg_color and args.bg_color.lower() != 'black':
        bg_name = args.bg_color.lower()
        if curses.COLORS >= 256 and bg_name in EXTENDED_COLORS:
             # Use the darkest/dim shade for background to keep text readable
             bg = EXTENDED_COLORS[bg_name][0]
        elif bg_name in ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']:
             bg = getattr(curses, f"COLOR_{bg_name.upper()}", curses.COLOR_BLACK)

    color_choice = args.color.lower()
    
    if curses.COLORS >= 256 and color_choice in EXTENDED_COLORS:
        c_dim, c_norm, c_bright = EXTENDED_COLORS[color_choice]
        
        # User requested #86ab48 (RGB 134, 171, 72)
        # We try to define a custom color index 100 for this "Sushi Green"
        custom_sushi = 100
        if curses.can_change_color():
            # scale 0-255 to 0-1000
            curses.init_color(custom_sushi, 525, 670, 282) 
        else:
            # Fallback to closest xterm color if terminal locks palette
            custom_sushi = 107 # r:135, g:175, b:95 (Approx match)

        # Sexy terminal optimization: slightly shifted hues or higher contrast
        if color_choice == 'green':
            # Use specific overrides for green to match request perfectly
            curses.init_pair(1, 22, bg) # Dark Green
            curses.init_pair(2, custom_sushi, bg) # PRIMARY BODY COLOR
            curses.init_pair(3, 46, bg) # Bright Green
            curses.init_pair(9, 231 if color_choice != 'white' else 255, bg) # Head White (moved to 9)
        else:
            curses.init_pair(1, c_dim, bg)
            curses.init_pair(2, custom_sushi if color_choice == 'green' else c_norm, bg)
            curses.init_pair(3, c_bright, bg)
            curses.init_pair(9, curses.COLOR_WHITE, bg) # Head
        
        # Exotic words
        
        # Exotic words
        curses.init_pair(4, 201, bg) # Magenta
        curses.init_pair(5, 226, bg) # Yellow
        curses.init_pair(6, 196, bg) # Red
        curses.init_pair(7, 51, bg)  # Cyan
        curses.init_pair(8, 33, bg)  # Blue
    else:
        # Fallback to basic 8 colors
        BASIC_COLORS = {
            'green': curses.COLOR_GREEN,
            'red': curses.COLOR_RED,
            'blue': curses.COLOR_BLUE,
            'white': curses.COLOR_WHITE,
            'cyan': curses.COLOR_CYAN,
            'magenta': curses.COLOR_MAGENTA,
            'yellow': curses.COLOR_YELLOW,
        }
        fg = BASIC_COLORS.get(color_choice, curses.COLOR_GREEN)
        curses.init_pair(1, fg, bg) # Dim (via A_DIM)
        curses.init_pair(2, fg, bg) # Normal
        curses.init_pair(3, curses.COLOR_WHITE, bg) # Head
        
        # Exotic pairs
        curses.init_pair(4, curses.COLOR_MAGENTA, bg)
        curses.init_pair(5, curses.COLOR_YELLOW, bg)
        curses.init_pair(6, curses.COLOR_RED, bg)
        curses.init_pair(7, curses.COLOR_CYAN, bg)
        curses.init_pair(7, curses.COLOR_CYAN, bg)
        curses.init_pair(8, curses.COLOR_BLUE, bg)

    # Global Background Setting
    # If a specific background logic is active (bg != 0), we must ensure the whole window uses it.
    if bg != curses.COLOR_BLACK:
        # Define a specific pair for the background (Pair 10)
        # Foreground doesn't matter much for empty space, but use dim green or white for safety
        curses.init_pair(10, curses.COLOR_WHITE, bg)
        stdscr.bkgd(' ', curses.color_pair(10))

    sh, sw = stdscr.getmaxyx()
    columns = []
    
    def create_columns():
        cols = []
        # Dynamic density using args.density
        step = max(1, args.density)
        for x in range(0, sw, step):
            if random.random() < args.mix:
                cols.append(QuoteColumn(x, sh, DEFAULT_CHARSETS['matrix'], args.speed * speed_scale, args.horror, 
                                        quote_manager, args.persist, args.glitch_rate, args.tail_min, args.tail_max))
            else:
                cols.append(Column(x, sh, DEFAULT_CHARSETS['matrix'], args.speed * speed_scale, args.tail_min, args.tail_max))
        return cols

    columns = create_columns()

    while True:
        try:
            # Safe loop wait using curses timeout
            key = stdscr.getch()
            
            # Handle various exit keys
            if key == ord('q') or key == ord('Q') or key == 27: # 27 is ESC
                stdscr.clear()
                stdscr.refresh()
                break
                
            if key == curses.KEY_RESIZE:
                new_sh, new_sw = stdscr.getmaxyx()
                if new_sh != sh or new_sw != sw:
                    sh, sw = new_sh, new_sw
                    columns = create_columns()

            stdscr.erase()
            for col in columns:
                col.update()
                col.draw(stdscr)

            stdscr.refresh()
            # No manual sleep needed, getch waits 50ms
            
        except KeyboardInterrupt:
            stdscr.clear()
            stdscr.refresh()
            break
        except curses.error:
            pass # Ignore resize errors generally

    # Valid exit point (end of main)

def main_wrapper():
    parser = argparse.ArgumentParser(description="QMatrix - High-Performance Matrix Rain TUI")
    parser.add_argument("-s", "--speed", type=float, default=0.2, help="Fall speed factor")
    parser.add_argument("-c", "--color", type=str, default="green", help="Color (green, red, blue, white, cyan)")
    parser.add_argument("-m", "--mix", type=float, default=0.15, help="Mix ratio for quotes (0.0 to 1.0)")
    parser.add_argument("-d", "--density", type=int, default=1, help="Column spacing (higher = lower density)")
    parser.add_argument("--horror", action="store_true", help="Enable horror glitch effects")
    parser.add_argument("--tail-min", type=int, default=25, help="Minimum tail length")
    parser.add_argument("--tail-max", type=int, default=50, help="Maximum tail length")
    parser.add_argument("--persist", action="store_true", default=True, help="Keep quotes on screen as they drop (typing effect)")
    parser.add_argument("--no-persist", action="store_false", dest="persist", help="Disable persistent quotes")
    parser.add_argument("--glitch-rate", type=float, default=0.005, help="Rate of horror glitches (0.0 to 1.0)")
    parser.add_argument("--sexy", action="store_true", help="Force high-end terminal optimizations (Kitty/Ghostty)")
    parser.add_argument("--fps", type=int, default=None, help="Target FPS (Default: 60 for Sexy, 20 Standard)")
    parser.add_argument("--bg-color", type=str, default="black", help="Background color (black, red, blue, etc) or use --transparent")
    parser.add_argument("--transparent", action="store_true", help="Use terminal transparent background (for images/wallpapers)")
    parser.add_argument("--config", type=str, help="Path to custom config file")
    # Pre-parse to get config path without preventing help message
    temp_args, _ = parser.parse_known_args()
    
    # Load config and use it to update DEFAULTS, so CLI flags still override
    config = load_config(temp_args.config)
    if config:
        parser.set_defaults(**config)
    
    # Final parse
    args = parser.parse_args()
    
    # FPS Defaults
    if args.fps is None:
        # Check IS_SEXY_TERM again properly (since main does it too, but we need it here for default)
        # Or just let main handle None? No, argparse needs a value or we pass None to main.
        # Let's do it in main logic or here.
        # Re-check detection simple here
        is_sexy = "KITTY_WINDOW_ID" in os.environ or "GHOSTTY_BIN_DIR" in os.environ or "GHOSTTY_RESOURCES_DIR" in os.environ or args.sexy
        args.fps = 60 if is_sexy else 20

    if args.speed >= 2.0:
        print("WARNING: Speed values >= 2.0 may cause unreadability and visual artifacts.")
        time.sleep(2)
        
    curses.wrapper(main, args)

if __name__ == "__main__":
    main_wrapper()
