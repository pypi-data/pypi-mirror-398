# DictionarPy

An extensible offline dictionary application, in the terminal

The dictionary comes prepopulated with a little over 54,000 words and 119,000
definitions available for offline reference. It is also designed to be
added to and grow with your lexicon.

### Some things you can do:

1. Add and remove words, parts of speech, definitions, IPA transcriptions
2. Show random words
3. Get similar words
4. Reference the built-in IPA key
5. Search within definitions for a particular string
6. Find anagrams of words

### Statistics regarding this version's included dictionary

```sh
$ dpy -ns
Words:               54072
Definitions:         119844
IPA Transcriptions:  30028
Disk size:           10.70MB
───────────────────────────────────────────────────────
Parts of speech:
    adverb │ plural noun │ adjectif │ intransitive verb
    noun │ nom │ nom masculin commun │ abbreviation
    transitive/intransitive verb │ nom féminin │ article
    │ determiner │ idiom │ abréviation │ pronoun │ nom
    masculin │ phrase │ adjective │ auxiliary verb │ verb
    │ transitive verb │ ambitransitive verb │ definite
    article │ conjunction │ interjection │ verbe
    preposition
```

---

## Examples

- Add a word/definition to the database
  
  ```sh
  $ dpy -w "my new word" -p "my part of speech" -d "my definition!"
  ```

- Add or update the phonetic/phonemic transcription of a word

  ```sh
  $ dictionarpy -w "my new word" -i "/mj nu wɝd/"
  ```

- Show the definitions for a word (use `-n` to avoid ansi escape sequences)

  ```sh
  $ dictionarpy -n "my new word"                                                
  ┌──────────────────────┐
  │     my new word      │
  │     /mj nu wɝd/      │
  ├──────────────────────┤
  │ 1. my part of speech │
  │    my definition!    │
  └──────────────────────┘
  ```

- Remove a definition from the database

  ```sh
  $ dictionarpy -r 1 "my new word"
  ```

- Remove an entry from the database

  ```sh
  $ dictionarpy -R "remove_this_word"
  ```

- Learn a random word!

  ```sh
  $ dpy "$(dpy -z)"
  ```

For help and additional functionality:

```sh
$ dpy -h
usage: dpy [-h] [-n] [-e] [-s] [-0] [-t [N]] [-g [IPA SYMBOL]] [-c]
           [-z [PART OF SPEECH]] [-a] [-r INDEX] [-R] [-f STRING]
           [-w ADD_WORD] [-p ADD_POS] [-d ADD_DEF] [-i ADD_IPA] [-P N] [-D N]
           [-I] [-v]
           [word]

Offline dictionary

positional arguments:
  word                  Word to be defined

options:
  -h, --help            show this help message and exit
  -n, --no-ansi         Don't use ansi escape sequences
  -e, --no-stemming     Don't use Porter Stemming on a word if it's not found
  -s, --stats           Show database statistics
  -0, --empty           Show words that do not possess definitions
  -t, --tail [N]        Show last N words added to the database. N=10 if left
                        empty
  -g, --ipa-guide [IPA SYMBOL]
                        Show ipa guide (empty for all)
  -c, --ipa-charts      Show ipa charts
  -z, --random [PART OF SPEECH]
                        Return a random word
  -a, --anagrams        Show anagrams for word
  -r, --remove-def INDEX
                        Remove a definition specified by its index
  -R, --remove-word     Remove a word
  -f, --find-in-defs STRING
                        Show entries which contain STRING in definitions
  -w, --add-word ADD_WORD
                        Word to add/word to add to
  -p, --add-pos ADD_POS
                        Part of speech to add
  -d, --add-def ADD_DEF
                        Definition to add
  -i, --add-ipa ADD_IPA
                        Pronunciation to add
  -P, --show-pos N      Only show word's part of speech at Nth index
  -D, --show-def N      Only show word's definition at Nth index
  -I, --show-ipa        Only show word's pronunciation
  -v, --version         Show version
```
