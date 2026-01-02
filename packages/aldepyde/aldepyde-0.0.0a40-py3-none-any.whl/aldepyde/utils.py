import sys
import time

# I'm sorry tqdm. I love you too :(
# This is NOT meant to replace tqdm. Only bother using this if you are on
# a restrictive system that doesn't allow 3rd party resources
class ProgressBar():
    def __init__(self, itb=None, ascii=False, blength=30, total=None, minupdate=.1, fp=sys.stdout):
        self.itb = self.iterize(itb)
        self.ascii = ascii
        self.blength = blength
        self.minupdate = minupdate
        self._ascii_char = self.default_ascii()
        self._uni_char = self.default_uni()
        self._empty = self.default_empty()
        self._progress_printer = self._print_bar if total != 0 else self._print_current
        self.fp = fp
        self.description = ""
        self.current = 0
        self.start = -1


        if total is None:
            try:
                self.total = len(self.itb)
            except TypeError:
                self.total = 0
        else:
            self.total = total

    def load(self, itb):
        self.itb = self.iterize(itb)

    def set_total(self, total):
        self.total = total

    def __iter__(self):
        it = self.itb
        minupdate = self.minupdate
        self.start = last = time.perf_counter()
        current = 0
        pbar_type = self._print_current if self.total == 0 else self._print_bar
        fp = self.fp
        for item in iter(it):
            yield item
            current += 1
            self.current = current
            now = time.perf_counter()
            if now - last >= minupdate:
                last = now
                fp.write("".join(["\r", self.description, pbar_type(current)]))
        fp.write("".join(["\r", self.description , pbar_type(current)]))
        fp.write('\n')

    def update(self, current=1):
        self.current += 1
        if self.start == -1:
            self.start = time.perf_counter()
        if self.total == 0:
            self.sp.write("".join(["\r", self.description ,self._print_current(self.current)]))
        else:
            self.fp.write("".join(["\r",self.description ,self._print_bar(self.current)]))

    def _print_current(self, current:int) -> str:
        return "".join([str(current), self._get_meta_current(current)])

    def _get_meta_current(self, current):
        elapsed = time.perf_counter() - self.start
        eh, er = divmod(elapsed, 3600)
        em, es = divmod(er, 60)
        eh = int(eh)
        em = int(em)
        es = int(es)
        rate = round(current / elapsed)
        elp = "".join([str(eh).zfill(2), ':', str(em).zfill(2), ':', str(es).zfill(2)])
        return "".join(['|', '|ELP ' , elp, '|', str(rate), ' itr/sec'])

    def _print_bar(self, current:int) -> str:
        completed = current / self.total
        cycle = self._ascii_char if self.ascii else self._uni_char
        if len(cycle) == 1:
            return "".join([cycle[0]*round(completed*self.blength), self._empty*(self.blength - round(completed*self.blength)), self._get_meta_pbar(current)])
        else:
            full = min(len(cycle[-1] * int(completed * self.blength)), self.blength)
            empty = self.blength - full - 1
            bridge_index = round(((self.blength * completed)%1) * (len(cycle) - 1))
            bridge = "" if empty < 0 else cycle[bridge_index]
            return "".join( ['[', cycle[-1] * full, bridge, self._empty*empty, self._get_meta_pbar(current), ']'])


    def _get_meta_pbar(self, current):
        elapsed = time.perf_counter() - self.start
        eh, er = divmod(elapsed, 3600)
        em, es = divmod(er, 60)
        eh = int(eh)
        em = int(em)
        es = int(es)
        rate = round(current / elapsed)
        eta = (self.total - current) / (rate + 0.00001)
        h, r = divmod(eta, 3600)
        m, s = divmod(r, 60)
        h = int(h)
        m = int(m)
        s = int(s)
        rs = "".join([str(h).zfill(2), ':', str(m).zfill(2), ':', str(s).zfill(2)])
        elp = "".join([str(eh).zfill(2), ':', str(em).zfill(2), ':', str(es).zfill(2)])
        return "".join(['|', str(round(100*current/self.total)), '%|ETA ', rs, '|ELP ' , elp, '|', str(rate), ' itr/sec'])


    def iterize(self, itb):
        if isinstance(itb, int):
            return range(itb)
        else:
            try:
                iter(itb)
                return itb
            except TypeError:
                sys.stderr.write("The object loaded into the progress bar is not iterable")
                return None

    def default_empty(self):
        return '-'

    def set_empty(self, char: str):
        if len(char) != 1:
            raise ValueError("The empty character must only be one character")
        self._empty = char

    def default_ascii(self):
        return ('@')

    def set_ascii(self, progression : tuple):
        self._ascii_char = progression

    def default_uni(self):
        return ('░', '▒', '▓', '█')

    def set_uni(self, progression : tuple):
        self._uni_char = progression

    def set_description(self, desc):
        self.description = desc




class ProgressBar_dep():
    def __init__(self, itb=None, force_ascii=False, force_spinner=False, bar_length=10):
        self.itb = None
        self.iterator = None
        self.current = 0
        self.total = 0
        self.bar_length = bar_length
        self.description = ""
        self._force_ascii = force_ascii
        self.empty = ' '
        self.spinner = ['\\', '|', '/', '-']
        # TODO Make _quarters adjustable
        self._quarters = ['░', '▒', '▓', '█']
        self.set_quarters(self._quarters)
        self._force_spinner=force_spinner
        self.set_force_ascii(self._force_ascii)
        self.times = []
        if itb is None:
            return
        else:
            self.load(itb)

    # Mostly for debugging
    def set_force_spinner(self, force_spinner):
        self._force_spinner = force_spinner

    # Mostly for debugging
    def set_force_ascii(self, force_ascii):
        self._force_ascii = force_ascii
        if not force_ascii:
            self.spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        else:
            self.spinner = ['\\', '|', '/', '-']

    def set_quarters(self, quarters):
        self._quarters = [self.empty] + quarters

    def set_total(self, total):
        self.total = total

    def load(self, itb):
        if itb is not None:
            if isinstance(itb, int):
                itb = range(itb)
            try:
                iter(itb)
                self.current = 0
                self.description = ""
                self.itb = itb
                self.iterator = iter(self.itb)
                try:
                    self.total = len(itb)
                except TypeError:
                    self.total = 0

            except TypeError:
                print("The object loaded into the progress bar is not iterable", file=sys.stderr)


    def update(self, updates : int):
        self.current += updates

    def set_description(self, description):
        if description is None:
            description = ""
        self.description = description

    # TODO Toggle ETA
    def eta(self):
        if len(self.times) == 2:
            try:
                seconds = (self.times[1] - self.times[0]) * (self.total - self.current)
                hours, remainder = divmod(seconds, 3600)
                minutes, sec = divmod(remainder, 60)
                tstr = ""
                if hours >= 1:
                    tstr += f"{int(hours)}h "
                if minutes >= 1:
                    tstr += f"{int(minutes)}m "
                tstr += f"{round(sec)}s "
                return f" {{{tstr}}}"
            except ZeroDivisionError:
                return ""
        else:
            return ""

    def push_time(self, t):
        while len(self.times) >= 2:
            self.times.pop(0)
        self.times.append(t)

    def _progress_as_bar(self) -> str:
        return ""
        try:
            current_progress = self.current / self.total
        except ZeroDivisionError:
            return ""
        if self._force_ascii:
            current_progress = round(current_progress * self.bar_length)
            return '*' * current_progress + '-' * (self.bar_length - current_progress)
        else:
            current_progress = current_progress * self.bar_length
            whole_length = int(current_progress // 1)
            whole_portion = self._quarters[-1] * whole_length
            bp = round((current_progress%1) * 4)
            bridge = self._quarters[bp]
            decimal_portion = '-' * (self.bar_length - whole_length - 1)
            return whole_portion + bridge + decimal_portion

    def __iter__(self):
        return self

    def __next__(self):
        try:
            self.push_time(time())
            item = next(self.iterator)

            self.current += 1
            d = " | " + self.description if len(self.description) != 0 else ""
            return item

            progress_statement = f"{self.current}/{self.total}" if self.total != 0 and not self._force_spinner else f"{self.current} {self.spinner[self.current % len(self.spinner)]}"
            sys.stdout.write('\r' + self._progress_as_bar() + ' ' + progress_statement + d + self.eta())
            sys.stdout.flush()
            return item

        except StopIteration:
            print()
            raise