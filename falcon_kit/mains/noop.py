import sys

def run(prog, *args):
    print("{} on {!r}".format(prog, args))

def main(argv=sys.argv):
    run(*argv) # pylint: disable=no-value-for-parameter

if __name__ == '__main__':  # pragma: no cover
    main()
