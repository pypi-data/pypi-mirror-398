import sqlite3
import subprocess
import pathlib
import os.path
import textwrap
import random
import shutil
import importlib.resources
import importlib.metadata
import itertools
from dictionarpy.box import Box
from dictionarpy.utils import AnsiWrapperGenerator
from dictionarpy.porter_stemmer import PorterStemmer


WIDTH = shutil.get_terminal_size().columns


class DictionarPy:
    def __init__(self, word: str, no_ansi: bool, no_stemming: bool):
        self.no_ansi = no_ansi
        self.no_stemming = no_stemming

        generator = AnsiWrapperGenerator(self.no_ansi)
        self.bold = generator.genwrapper('\u001b[1m', '\u001b[0m')
        self.underline = generator.genwrapper('\u001b[4m', '\u001b[24m')
        self.italic = generator.genwrapper('\u001b[3m', '\u001b[23m')

        self.search_string = ''
        self.red = generator.genwrapper('\u001b[1;31m', '\u001b[0m')

        self.word = word

        self.datadir = pathlib.Path.home() / '.local/share/dictionarpy'
        self.working_db_path = self.datadir / 'dictionary.db'
        self.datadir.mkdir(parents=True, exist_ok=True)

        with (importlib.resources.path('dictionarpy.data', 'dictionary.db') as
            packaged_dict):
            if self.working_db_path.is_file():
                installed_version = self._get_dictionary_version()
                packaged_version = self._get_dictionary_version(
                    db_path=packaged_dict)
                if packaged_version != installed_version:
                    mergeq = input('Installed and packaged databases are' +
                        ' of differing version number, merge them? [y/N] ')
                    if mergeq.lower() == 'y':
                        self._merge_databases(packaged_dict, packaged_version)
            else:
                shutil.copy2(packaged_dict, self.working_db_path)

        self.con = sqlite3.connect(self.working_db_path)
        self.cur = self.con.cursor()

    
    def _merge_databases(self, new_db_path, new_version) -> None:
        con = sqlite3.connect(self.working_db_path)
        cur = con.cursor()

        cur.execute('attach ? as dba', (str(new_db_path),))

        for tbl in ('words', 'definitions', 'pronunciations'):
            cur.execute(
                    f'insert or ignore into "{tbl}" select * from dba."{tbl}"')
        cur.execute(
            "update metadata set value = ? where key = 'version'",
            (new_version,))

        con.commit() 
        cur.execute('detach database dba')
        con.close()
         

    def _splash_display(self, title: str, items: set[str]) -> None:
        '''
        Print a delineated and wrapped 'splash' of the passed iterable's
        contents
        '''
        print('─' * (WIDTH // 2 + 2))
        output = ' │ '.join(items)

        print(self.bold(title))
        for line in textwrap.wrap(output, width=(WIDTH // 2)):
            if line[-2:] == ' │':
                line = line[:-2]
            print('   ', line)


    def _get_sim_words(self) -> set[str]:
        '''
        Try to return words in the database that contain the input word.
        This is used when a requested word is not found in the database
        '''
        sim_words_res = self.cur.execute(
            'select word from words where word like ?', 
            (f'%{self.word.lower()}%',)).fetchall()

        return {} if not sim_words_res else {i[0] for i in sim_words_res}


    def _get_word_id(self) -> int:
        '''
        Get the word id corresponding to the user requested word. If this fails,
        stem the word and retry. 
        (e.g. if `inverting` is not found, this will get `invert`)

        Following failure to get both requested and stemmed words, display
        similar words and exit program.
        '''
        word_id_res = self.cur.execute(
            'select id from words where word = ?', (self.word,)).fetchone()

        if not word_id_res:
            if not self.no_stemming:
                stemmer = PorterStemmer()
                og_word = self.word
                self.word = stemmer.stem(self.word)
                word_id_res = self.cur.execute(
                    'select id from words where word = ?', 
                    (self.word,)).fetchone()
            if not word_id_res:
                try: self.word = og_word
                except UnboundLocalError: pass
                print('Cannot find word in working database')
                sim_words = self._get_sim_words()
                if sim_words: self._splash_display('Similar:', sim_words)
                exit(1)

        word_id, = word_id_res
        return word_id


    def _get_definitions(self) -> list[tuple[str, str]]:
        '''
        Query database for definitions and parts of speech for a given word.

        E.g.
        word = happy
        returns
            [('enjoying or showing or marked by joy or pleasure', 'adjective'),
             ('marked by good fortune', 'adjective'), 
             ('eagerly disposed to act or to be of service', 'adjective'), 
             ('well expressed and to the point', 'adjective')]
        '''
        word_id = self._get_word_id()
        defs_and_pos = self.cur.execute(
            'select definition, pos from definitions where word_id = ?', 
            (word_id,)).fetchall()

        return defs_and_pos


    def _get_ipa(self) -> str|None:
        word_id = self._get_word_id()
        ipa_res = self.cur.execute(
            'select pronunciation from pronunciations where word_id = ?',
                (word_id,)).fetchone()

        if ipa_res is not None: 
            ipa, = ipa_res
            return ipa


    def show_ipa(self) -> None:
        ipa = self._get_ipa()
        print(ipa) if ipa else print(
            "No IPA transcription available for this word")

    
    def show_entry(self) -> None:
        '''
        Pretty print the "entry" in the dictionary corresponding to a given word
        '''
        defs_and_pos = self._get_definitions()
        if self.search_string:
            defs_and_pos = [
                    (d.replace(self.search_string, self.red(self.search_string)),
                     p) for d, p in defs_and_pos]
        ipa = self._get_ipa()

        box = Box(self.word, ipa, defs_and_pos, self.no_ansi)
        box.draw()


    def show_definition(self, n) -> None:
        '''
        Show the nth definition for a given word
        '''
        defs_and_pos = self._get_definitions()
        try: definition = defs_and_pos[n-1][0]
        except IndexError:
            print('No definition at this index')
            return
        print(definition)


    def show_pos(self, n) -> None:
        '''
        Show the nth part of speech for a given word
        '''
        defs_and_pos = self._get_definitions()
        try: pos = defs_and_pos[n-1][1]
        except IndexError:
            print('No part of speech at this index')
            return
        print(pos)


    def remove_definition(self, index: int) -> None:
        '''
        Remove a definition as specified by its display index.
        '''
        word_id = self._get_word_id()
        index -= 1

        definition_id = self.cur.execute(
            'select id from definitions where word_id = ? limit 1 offset ?',
                (word_id, index)).fetchone()
        if not definition_id:
            print('There is no definition at this index')
            return

        definition_id, = definition_id
        self.cur.execute(
            'delete from definitions where id = ?', (definition_id,))
        self.con.commit()


    def remove_word(self) -> None:
        '''
        Remove all traces of a word from the database (word, pronunciations,
        parts of speech and definitions)
        '''
        word_id = self._get_word_id()
        self.cur.execute(
            'delete from definitions where word_id = ?', (word_id,))
        self.cur.execute(
            'delete from pronunciations where word_id = ?', (word_id,))
        self.cur.execute('delete from words where id = ?', (word_id,))
        self.con.commit()


    def add_or_update_entry(self, addword: str, pos: str, definition: str, 
                            ipa: str) -> None:
        '''
        Create a word, [pos, definition, and pronunciation] if the word does not
        yet exist. 
        Otherwise add a pos, definition pair and/or pronunciation to an existing
        word.
        '''
        self.cur.execute(
            'insert or ignore into words (word) values (?)', (addword,))
        addword_id, = self.cur.execute(
            'select id from words where word = ?', (addword,)).fetchone()

        if pos and definition:
            self.cur.execute(
            'insert or ignore into definitions (word_id, definition, pos) \
                values (?, ?, ?)', (addword_id, definition, pos))
        if ipa:
            self.cur.execute(
            'insert or replace into pronunciations (word_id, pronunciation) \
                    values (?, ?)', (addword_id, ipa))
        self.con.commit()


    def _get_num_words(self) -> int:
        '''
        Return the number of words in the dictionary database
        '''
        return self.cur.execute(
            'select count(*) from words').fetchone()[0]


    def _get_num_defs(self, pos='*') -> int:
        '''
        Number of definitions in the dictionary. Optionally constrained to
        a specific part of speech
        '''
        return self.cur.execute(
            'select count(*) from definitions where pos glob ?', 
                (pos,)).fetchone()[0]


    def _get_db_size(self) -> float:
        '''
        Size of dictionary db in MB
        '''
        return os.path.getsize(self.working_db_path) / (1024 ** 2) 


    def _get_all_pos(self) -> set[str]:
        '''
        Return all the unique parts of speech in the dictioanry
        '''
        pos_res = self.cur.execute(
            'select distinct pos from definitions').fetchall()
        return {i[0] for i in pos_res}


    def _get_ipa_transcriptions(self) -> int:
        '''
        Return the number of IPA transcriptions in the dictionary database
        '''
        return self.cur.execute(
            'select count(*) from pronunciations').fetchone()[0]


    def show_stats(self) -> None:
        '''
        Print database information
        '''
        words = self._get_num_words()
        definitions = self._get_num_defs()
        transcriptions = self._get_ipa_transcriptions()
        size = self._get_db_size()

        print(f"{self.bold('Words:')}               {words}")
        print(f"{self.bold('Definitions:')}         {definitions}")
        print(f"{self.bold('IPA Transcriptions:')}  {transcriptions}")
        print(f"{self.bold('Disk size:')}           {size:.2f}MB")

        self._splash_display('Parts of speech:', self._get_all_pos())


    def _get_dictionary_version(self, db_path=None) -> str:
        if not db_path: db_path = self.working_db_path
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        version = cur.execute(
            "select value from metadata where key='version'").fetchone()[0]
        con.close() 
        return version 


    def _get_code_version(self) -> str:
        return importlib.metadata.version('dictionarpy')


    def show_versions(self) -> None:
        print(self.bold('Source code:'), self._get_code_version())
        print(self.bold('Dictionary: '), self._get_dictionary_version())


    def show_random_word(self, pos='any') -> None:
        '''
        Print a random word from the dictionary. Optionally constrained to a
        particular part of speech.

        Program exits if a nonexistent part of speech is passed.
        '''
        if pos == 'any':
            ind = random.randint(0, self._get_num_words() - 1)        
            word, = self.cur.execute(
                'select word from words limit 1 offset ?', (ind,)).fetchone()

        elif pos in self._get_all_pos():
            ind = random.randint(0, self._get_num_defs(pos) - 1)
            word, = self.cur.execute('select w.word from words as w \
                             join definitions as d on w.id = d.word_id \
                             where d.pos = ? limit 1 offset ?', 
                             (pos, ind)).fetchone()
        else:
            print('Part of speech not found in working database')
            exit(1)

        print(word)

    
    def find_in_definitions(self, string:str) -> None:
        '''
        Show entries where `string` is found in a definition.
        '''
        self.search_string = string

        word_ids_res = self.cur.execute(
            'select word_id from definitions where definition like ?',
            (f'%{string}%',)).fetchall()

        matches = {self.cur.execute(
                'select word from words where id = ?', word_id).fetchone()[0]
                   for word_id in word_ids_res}

        for match in sorted(matches):
            self.word = match
            self.show_entry()


    def show_recent_words(self, n:int) -> None:
        '''
        Display the last n words of the database
        '''
        words = self.cur.execute(
            'select word from words order by id desc limit ?', 
            (n,)).fetchall()

        i = 1
        for word, in words:
            print(f'{i}.\t{word}'.expandtabs(4))
            i += 1


    def show_empty_words(self) -> None:
        '''
        Show entries that do not contain definitions
        '''
        words = self.cur.execute(
            'select w.word from words w left join definitions d on' +
                    ' d.word_id = w.id where d.id is null').fetchall()

        i = 1
        for word, in words:
            print(f'{i}.\t{word}'.expandtabs(4))
            i += 1


    def show_ipa_guide(self, key:str='all') -> None:
        '''
        Display overview of IPA symbols. If an argument is passed, just the
        overview for that symbol.
        '''
        u = self.underline
        guide = {
            'b':  [[u('b') + 'ook',
                   'tu' + u('b')]],
            'd':  [[u('d') + 'esk',
                   'sa' + u('d')]],
            'f':  [[u('f') + 'amily',
                   'lea' + u('f'),
                   'lau' + u('gh'),
                   u('ph') + 'one']],
            'g':  [[u('g') + 'irl',
                   'bi' + u('g')]],
            'h':  [[u('h') + 'ead',
                   u('h') + 'and']],
            'j':  [[u('y') + 'awn',
                   u('y') + 'ogurt']],
            'k':  [[u('k') + 'ing',
                   u('c') + 'a' + u('k') + 'e',
                   u('r') + 'ock',
                   's' + u('ch') + 'ool']],
            'l':  [[u('l') + 'ion',
                   'penci' + u('l')]],
            'm':  [[u('m') + 'oon',
                   'ar' + u('m'),
                   'cli' + u('mb')]],
            'n':  [[u('n') + 'est',
                   'lio' + u('n')]],
            'p':  [[u('p') + 'en',
                   'ma' + u('p')]],
            'ɹ':  [[u('r') + 'un',
                    u('r') + 'oom',
                    'sta' + u('r')]],
            'ʁ':  [[u('r') + 'ega' + u('r') + 'der',
                    'nôt' + u('r') + 'e']],
            's':  [[u('s') + 'un',
                   'rut' + u('s'),
                   'fa' + u('c') + 'e']],
            't':  [[u('t') + 'en',
                   'goa' + u('t'),
                   'bu' + u('tt') + 'er',
                   'ki' + u('tt') + 'en']],
            'ɾ':  [['bu' + u('tt') + 'er'], 'flap between sonorants'],
            'ʔ':  [['ki' + u('tt') + 'en'], 'glottal stop before nasal'],
            'v':  [[u('v') + 'an',
                   'lo' + u('ve')]],
            'w':  [[u('w') + 'ater',
                   u('wh') + 'ale']],
            'ɥ':  [['h' + u('u') + 'it',
                   'P' + u('u') + 'y']],
            'z':  [[u('z') + 'ebra',
                   'qui' + u('z'),
                   'bean' + u('s'),
                   'cookie' + u('s')]],
            'ɲ':  [['ga' + u('gn') + 'er',
                   'champa' + u('gn') + 'e']],
            'ŋ':  [['wi' + u('ng'),
                   'runni' + u('ng')]],
            'ʒ':  [['mea' + u('s') + 'ure']],
            'dʒ': [[u('g') + 'ym',
                   'hu' + u('ge'),
                   u('j') + 'et']],
            'ʃ':  [[u('sh') + 'oes',
                   'fi' + u('sh'),
                   'mo' + u('ti') + 'on']],
            'tʃ': [[u('ch') + 'eese',
                   'lun' + u('ch')]],
            'θ':  [[u('th') + 'ree',
                   'mou' + u('th'),
                   u('th') + 'igh']],
            'ð':  [[u('th') + 'is',
                   'mo' + u('th') + 'er',
                   u('th') + 'y']],
            'ɑ':  [[u('o') + 'n',
                   'm' + u('o') + 'm']],
            'æ':  [[u('a') + 'pple',
                   'b' + u('a') + 'g',
                   'b' + u('a') + 'n'], 
                   '[ɛə] b' + u('a') + 'n (pre-nasal vowel)'],
            'aɪ': [['b' + u('i') + 'ke',
                   'sk' + u('y'),
                   'p' + u('ie'),
                   'h' + u('igh')]],
            'aʊ': [['m' + u('ou') + 'th',
                    'c' + u('o') + 'w']],
            'e': [['cl' + u('é'),
                   u('et'),
                   'l' + u('es'),
                   'ch' + u('ez'),
                   'all' + u('er'),
                   'pi' + u('ed'),
                   'journ' + u('é') + 'e' ]],
            'ɛ':  [[u('e') + 'gg',
                   't' + u('e') + 'n',
                   'br' + u('ea') + 'd']],
            'eɪ': [['g' + u('a') + 'me',
                   'r' + u('ai') + 'n',
                   'pl' + u('ay')]],
            'ɪ':  [[u('i') + 'n',
                   'b' + u('i') + 'g',
                   'f' + u('i') + 'fty,']],
            'i':  [[u('ea') + 't',
                   'sl' + u('ee') + 'p',
                   'happ' + u('y')]],
            'œ':  [['s' + u('œu') + 'r',
                    'j' + u('eu') + 'ne']],
            'ø':  [['c' + u('eu') + 'x',
                    'j' + u('eû') + 'ner',
                    'qu' + u('eue')]],
            'o':  [['s' + u('au') + 't',
                    'h' + u('au') + 't',
                    'bur' + u('eau'),
                    'ch' + u('o') + 'se',
                    't' + u('ô') + 't',
                    'c' + u('ô') + 'ne' ]],
            'oʊ': [['h' + u('o') + 'me',
                   'c' + u('o') + 'ld',
                   'r' + u('oa') + 'd',
                   'wind' + u('ow')]],
            'ɔ':  [['w' + u('a') + 'lk',
                   'y' + u('a') + 'wn',
                   u('Au') + 'gust']],
            'ɔɪ': [['c' + u('oi') + 'n',
                   'b' + u('oy')]],
            'ʊ':  [['b' + u('oo') + 'k',
                   'f' + u('oo') + 't',
                   'p' + u('u') + 't']],
            'u':  [['fl' + u('u') + 'te',
                   'bl' + u('ue'),
                   'fr' + u('ui') + 't',
                   'f' + u('oo') + 'd']],
            'y':  [['t' + u('u'),
                   's' + u('û') + 'r',
                   'r' + u('ue')]],
            'ʌ':  [[u('u') + 'p',
                   'r' + u('u') + 'n',
                   'one']],
            'ɝ':  [['sh' + u('ir') + 't',
                   u('Ear') + 'th',
                   'n' + u('ur') + 'se',
                   'w' + u('or') + 'k']],
            'ə':  [['b' + u('a') + 'lloon',
                   'cam' + u('e') + 'l',
                   'pr' + u('o') + 'tect',
                   'min' + u('u') + 's'], '"shwa", an unstressed vowel'],
            'ɚ':  [['fath' + u('er'),
                   'bak' + u('er')], 'unstressed rhotic vowel']}

        if key == 'all':
            for k, v in guide.items():
                print(self.bold('/' + k + '/'), end='\t')
                print(' │ '.join(v[0]))
                if len(v) == 2: print('\t' + self.italic(v[1]))
        elif key in guide.keys():
            v = guide.get(key)
            print(' │ '.join(v[0]))
            if len(v) == 2: print('\t' + self.italic(v[1]))


    def show_ipa_charts(self) -> None:
        charts = r'''
        - Vowels -
        ┌────────────┬───────┬─────────┬─────────┬────────┬──────┐
        │            │ Front │ N-front │ Central │ N-back │ Back │                     
        ├────────────┼───────┴─────────┴─────────┴────────┴──────┤ 
        │   Close    │    i•y ────────── ɨ•ʉ  ──────────── ɯ•u   │  
        ├────────────┤     \              \                 │    │  
        │ Near-close │      \      ɪ•ʏ     \        ʊ       │    │  
        ├────────────┤       \              \               │    │  
        │ Close-mid  │       e•ø ────────── ɘ•ɵ ────────── ɤ•o   │  
        ├────────────┤         \              \             │    │  
        │    Mid     │          \              ə            │    │  
        ├────────────┤           \              \           │    │  
        │  Open-mid  │           ɛ•œ  ───────── ɜ•ɞ ────── ʌ•ɔ   │  
        ├────────────┤             \              \         │    │  
        │ Near-open  │           æ  \              ɐ        │    │  
        ├────────────┤               \              \       │    │
        │    Open    │               a•ɶ ───────────────── ɑ•ɒ   │  
        └────────────┴───────────────────────────────────────────┘
        unrounded • rounded


        - Pulmonic Consonants -
        ┌────────────────┬──────────┬─────────────┬──────────────┬────────┬──────────┬──────────────┬───────────┬─────────┬───────┬────────┬─────────────┬─────────┐
        │                │ Bilabial │ Labiodental │ Linguolabial │ Dental │ Alveolar │ Postalveolar │ Retroflex │ Palatal │ Velar │ Uvular │ Pharyngeal/ │ Glottal │
        │                │          │             │              │        │          │              │           │         │       │        │  Epiglottal │         │
        ├────────────────┼──────────┼─────────────┼──────────────┼────────┼──────────┼──────────────┼───────────┼─────────┼───────┼────────┼─────────────┼─────────┤
        │    Plosive     │   p b    │             │              │        │    t d   │              │    ʈ ɖ    │   c ɟ   │  k g  │   q ɢ  │      ʡ      │    ʔ    │
        ├────────────────┼──────────┼─────────────┼──────────────┼────────┼──────────┼──────────────┼───────────┼─────────┼───────┼────────┼─────────────┼─────────┤
        │     Nasal      │    m     │      ɱ      │              │        │     n    │              │     ɳ     │    ɲ    │   ŋ   │    ɴ   │             │         │
        ├────────────────┼──────────┼─────────────┼──────────────┼────────┼──────────┼──────────────┼───────────┼─────────┼───────┼────────┼─────────────┼─────────┤
        │     Trill      │    ʙ     │             │              │        │     r    │              │           │         │       │    ʀ   │     ʜ ʢ     │         │
        ├────────────────┼──────────┼─────────────┼──────────────┼────────┼──────────┼──────────────┼───────────┼─────────┼───────┼────────┼─────────────┼─────────┤
        │   Tap or Flap  │          │      ⱱ      │              │        │     ɾ    │              │     ɽ     │         │       │        │             │         │
        ├────────────────┼──────────┼─────────────┼──────────────┼────────┼──────────┼──────────────┼───────────┼─────────┼───────┼────────┼─────────────┼─────────┤
        │  Lateral Tap   │          │             │              │        │     ɺ    │              │           │         │       │        │             │         │
        │    or Flap     │          │             │              │        │          │              │           │         │       │        │             │         │
        ├────────────────┼──────────┼─────────────┼──────────────┼────────┼──────────┼──────────────┼───────────┼─────────┼───────┼────────┼─────────────┼─────────┤
        │   Fricative    │   ɸ β    │     f v     │              │   θ ð  │    s z   │      ʃ ʒ     │    ʂ ʐ    │   ç ʝ   │  x ɣ  │   χ ʁ  │     ħ ʕ     │   h ɦ   │
        ├────────────────┼──────────┼─────────────┼──────────────┼────────┼──────────┼──────────────┼───────────┼─────────┼───────┼────────┼─────────────┼─────────┤
        │   Approximant  │          │      ʋ      │              │        │     ɹ    │              │     ɻ     │    j    │   ɰ   │        │             │         │
        ├────────────────┼──────────┼─────────────┼──────────────┼────────┼──────────┼──────────────┼───────────┼─────────┼───────┼────────┼─────────────┼─────────┤
        │    Lateral     │          │             │              │        │    ɬ ɮ   │              │           │         │       │        │             │         │
        │   Fricative    │          │             │              │        │          │              │           │         │       │        │             │         │
        ├────────────────┼──────────┼─────────────┼──────────────┼────────┼──────────┼──────────────┼───────────┼─────────┼───────┼────────┼─────────────┼─────────┤
        │    Lateral     │          │             │              │        │     l    │              │     ɭ     │    ʎ    │   ʟ   │        │             │         │
        │  Approximant   │          │             │              │        │          │              │           │         │       │        │             │         │
        └────────────────┴──────────┴─────────────┴──────────────┴────────┴──────────┴──────────────┴───────────┴─────────┴───────┴────────┴─────────────┴─────────┘
        unvoiced • voiced
        '''
        p = subprocess.Popen(['less', '-S'], stdin=subprocess.PIPE, text=True)
        p.communicate(charts)


    def _get_anagrams(self) -> set[str]:
        permutations = {''.join(p) 
            for p in itertools.permutations(self.word)} - {self.word}

        ids = {self.cur.execute(
            'select id from words where word = ?', (p,)).fetchone() 
               for p in permutations}
        ids = {i for i in ids if i != None}
        
        anagrams = {self.cur.execute(
                    'select word from words where id = ?', i).fetchone()[0] for i in ids}
        return anagrams
        

    def show_anagrams(self) -> None:
        i = 1
        for a in self._get_anagrams():
            print(f'{i}.\t{a}'.expandtabs(4))
            i += 1


    def __enter__(self):
        return self

    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()
