from .cli import build_parser, run_from_CLI

def main():
    parser = build_parser()
    args = parser.parse_args() # args come from command line
    run_from_CLI(args)
    