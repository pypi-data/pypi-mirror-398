import argparse
from dictionarpy.dictionarpy import DictionarPy


def main():
    parser = argparse.ArgumentParser(description='Offline dictionary')
    parser.add_argument('word', nargs='?', help='Word to be defined') 
    parser.add_argument('-n', '--no-ansi', action='store_true', 
        help="Don't use ansi escape sequences")
    parser.add_argument('-e', '--no-stemming', action='store_true', 
        help="Don't use Porter Stemming on a word if it's not found")
    parser.add_argument('-s', '--stats', action='store_true', 
        help='Show database statistics')
    parser.add_argument('-0', '--empty', action='store_true', 
        help='Show words that do not possess definitions')
    parser.add_argument('-t', '--tail', metavar='N', const=10, nargs='?',
        help='Show last N words added to the database. N=10 if left empty')
    parser.add_argument('-g', '--ipa-guide', const='all', metavar='IPA SYMBOL',
        nargs='?', help='Show ipa guide (empty for all)')
    parser.add_argument('-c', '--ipa-charts', action='store_true',
        help='Show ipa charts')
    parser.add_argument('-z', '--random', const='any', nargs='?', 
        metavar='PART OF SPEECH', 
        help='Return a random word')
    parser.add_argument('-a', '--anagrams', action='store_true',
        help='Show anagrams for word')
    parser.add_argument('-r', '--remove-def', type=int, metavar='INDEX',
        help='Remove a definition specified by its index')
    parser.add_argument('-R', '--remove-word', action='store_true',
        help='Remove a word')
    parser.add_argument('-f', '--find-in-defs', type=str, metavar='STRING',
        help='Show entries which contain STRING in definitions')
    parser.add_argument('-w', '--add-word', type=str, 
        help='Word to add/word to add to')
    parser.add_argument('-p', '--add-pos', type=str, 
        help='Part of speech to add')
    parser.add_argument('-d', '--add-def', type=str, 
        help='Definition to add')
    parser.add_argument('-i', '--add-ipa', type=str,
        help='Pronunciation to add')
    parser.add_argument('-P', '--show-pos', type=int, metavar='N',
        help="Only show word's part of speech at Nth index")
    parser.add_argument('-D', '--show-def', type=int, metavar='N',
        help="Only show word's definition at Nth index")
    parser.add_argument('-I', '--show-ipa', action='store_true',
        help="Only show word's pronunciation")
    parser.add_argument('-v', '--version', action='store_true', 
        help='Show version')
    args = parser.parse_args()

    if not args.add_word and (args.add_pos or args.add_def or args.add_ipa):
        parser.error('Missing -w/--add-word flag.')

    if args.stats:
        DictionarPy('', args.no_ansi, args.no_stemming).show_stats()
    elif args.empty:
        DictionarPy('', args.no_ansi, args.no_stemming).show_empty_words()
    elif args.version:
        DictionarPy('', args.no_ansi, args.no_stemming).show_versions()
    elif args.ipa_guide:
        DictionarPy('', args.no_ansi, args.no_stemming
                    ).show_ipa_guide(args.ipa_guide)
    elif args.ipa_charts:
        DictionarPy('', args.no_ansi, args.no_stemming).show_ipa_charts()
    elif args.tail:
        DictionarPy('', args.no_ansi, args.no_stemming
                    ).show_recent_words(args.tail)
    elif args.random:
        DictionarPy('', args.no_ansi, args.no_stemming
                    ).show_random_word(args.random)
    elif args.anagrams:
        if args.word is None:
            parser.error(
                'The -a/--anagrams flag requires a word to be specified.')
        DictionarPy(args.word, args.no_ansi, args.no_stemming
                    ).show_anagrams()
    elif args.remove_def:
        if args.word is None:
            parser.error(
                'The -r/--remove flag requires a word to be specified.')
        with DictionarPy(args.word, args.no_ansi, args.no_stemming) as dpy:
            dpy.remove_definition(args.remove_def)
    elif args.remove_word:
        with DictionarPy(args.word, args.no_ansi, args.no_stemming) as dpy:
            dpy.remove_word()
    elif args.find_in_defs:
        with DictionarPy('', args.no_ansi, args.no_stemming) as dpy:
            dpy.find_in_definitions(args.find_in_defs)
    elif args.add_word:
        if bool(args.add_pos) ^ bool(args.add_def):
            parser.error('The -p and -d flags are mutually dependent.')
        with DictionarPy('', args.no_ansi, args.no_stemming) as dpy:
            dpy.add_or_update_entry(
                args.add_word, args.add_pos, args.add_def, args.add_ipa)
    elif args.word is None:
        parser.print_help()
    else:
        with DictionarPy(args.word, args.no_ansi, args.no_stemming) as dpy:
            if args.show_pos and not (args.show_def or args.show_ipa):
                dpy.show_pos(args.show_pos)
            elif args.show_def and not (args.show_pos or args.show_ipa):
                dpy.show_definition(args.show_def)
            elif args.show_ipa and not (args.show_pos or args.show_def):
                dpy.show_ipa()
            else:
                dpy.show_entry()
