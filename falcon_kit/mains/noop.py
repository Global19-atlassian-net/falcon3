import sys

def run(prog, *args):
    print("{} on {!r}".format(prog, args))

def main(argv=sys.argv):
    run(*argv)

if __name__ == '__main__':  # pragma: no cover
    main()
