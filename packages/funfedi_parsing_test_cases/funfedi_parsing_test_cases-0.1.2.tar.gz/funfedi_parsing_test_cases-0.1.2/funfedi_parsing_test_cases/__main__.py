import click

from . import activity_suite

from .suite.generate_doc import write_docs_for_sub_suites


@click.command("main")
def main():
    write_docs_for_sub_suites(activity_suite.sub_suites)


if __name__ == "__main__":
    main()
