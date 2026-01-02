import textwrap
import shutil
import re
from dictionarpy.utils import AnsiWrapperGenerator


class Box:
    def __init__(self, word: str, pronunciation: str|None, 
             defs_and_pos: list[tuple[str, str]], no_ansi: bool):

        self.bold = AnsiWrapperGenerator(
            no_ansi).genwrapper('\u001b[1m', '\u001b[0m')

        self.word = word
        self.pronunciation = pronunciation
        self.defs_and_pos = defs_and_pos or [('', '')]

        def_widths, pos_widths = zip(*[[len(i), len(j)] 
            for i, j in self.defs_and_pos])

        self.word_width = len(self.word)
        self.pronunciation_width = len(self.pronunciation) \
            if self.pronunciation else 0

        # width in columns
        self.inner_width = max(max(def_widths), 
                               max(pos_widths), 
                               self.word_width,
                               self.pronunciation_width) + 5

        # box would be bigger than terminal
        self.cols = shutil.get_terminal_size().columns
        if self.inner_width > self.cols - 2:
            self.inner_width = self.cols - 2


    def _get_padding(self, textlen:int) -> tuple[int, int]:
        '''
        Get the left and right spacing given the length of input text such that
        it is centered
        '''
        leftpad = (self.inner_width - textlen) // 2
        rightpad = self.inner_width - textlen - leftpad
        return leftpad, rightpad


    def _draw_header(self) -> None:
        '''
        Contains word and pronunciation lines
        '''
        for line in textwrap.wrap(self.word, width=self.inner_width - 2):
            leftpad, rightpad = self._get_padding(len(line))
            print('│', leftpad * ' ', self.bold(line), rightpad * ' ',
                  '│', sep='')

        if self.pronunciation:
            for line in textwrap.wrap(
                            self.pronunciation,
                            width=self.inner_width - 2):
                line = line.rstrip(',')
                leftpad, rightpad = self._get_padding(len(line))
                print('│', leftpad * ' ', line, rightpad * ' ',
                      '│', sep='')


    def _draw_hr(self, first, last) -> None:
        print(first, '─' * self.inner_width, last, sep='')


    def _draw_defs_and_pos(self) -> None:
        total_items = len(self.defs_and_pos)
        for i, (definition, pos) in enumerate(self.defs_and_pos, start=1):
            rightpad = (self.inner_width - len(pos) - 3 - len(str(i)))
            print('│ ', i, '. ', self.bold(pos), rightpad * ' ', '│', 
                  sep='')
            definition = textwrap.wrap(definition, width=self.inner_width - 6)

            # track these to avoid padding issues from nonprintable
            # chars in ansi escape codes
            bold_red = re.compile(r'(\x1b\[1;31m)|(\x1b\[0m)')
            start = re.compile(r'\x1b\[1;31m')
            end = re.compile(r'\x1b\[0m')
            for line in definition:
                # flatten list and discard empty strings
                matches = [match for pair in bold_red.findall(line) 
                           for match in pair if match]
                esc_seq_len = len(''.join(matches)) if matches else 0

                leftpad = len(str(i)) + 3
                rightpad = self.inner_width - len(line) + esc_seq_len - leftpad

                if start.search(line) and not end.search(line):
                    print('│', leftpad * ' ', line, rightpad * ' ', 
                          '\u001b[0m│', sep='')
                elif end.search(line) and not start.search(line):
                    print('│\u001b[1;31m', 
                          leftpad * ' ', line, rightpad * ' ', '│', sep='')
                else:
                    print('│', leftpad * ' ', line, rightpad * ' ', '│', sep='')

            if i < total_items:
                print('│', self.inner_width * ' ', '│', sep='')

    
    def draw(self):
        self._draw_hr('┌', '┐')
        self._draw_header()
        if self.defs_and_pos != [('', '')]:
            self._draw_hr('├', '┤')
            self._draw_defs_and_pos()
        self._draw_hr('└', '┘')
