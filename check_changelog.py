#!/usr/bin/env python3

import argparse


test_result_code = 0


class TesterBase(object):
    def test(self):
        raise NotImplementedError


class TesterNoDelete(TesterBase):
    """Any deletion to Changelog.md is not allowed except it's a """

    def __init__(self, diff_url):
        self.diff_url = diff_url

    def test(self):
        return True, ""


def get_changelog_diff(diff_url):
    try:
        pass
    except:
        pass
    return "", ""


def test_fail(log_message):
    print(log_message)
    global test_result_code
    test_result_code = 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--diff", "-d", dest="diff_url", action="store", required=True)
    args = parser.parse_args()

    if not args.diff_url.endswith(".diff"):
        args.diff_url += ".diff"

    print args.diff_url

    #changelog_diff, log_message = get_changelog_diff(args.diff_url)
    #if changelog_diff is None:
    #    test_fail(log_message)

    #testers = [
    #    TesterNoDelete(changelog_diff),
    #]

    #for tester in testers:
    #    result, log_message = tester.test()
    #    if not result:
    #        test_fail(log_message)

    return 0


if __name__ == "__main__":
    try:
        main()
    except:
        test_fail("[E] Unexpected error.")
    finally:
        exit(test_result_code)
