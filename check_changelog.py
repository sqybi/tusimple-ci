#!/usr/bin/env python3

import argparse
import enum
import re
import urllib.request


# Changelog Data Structure

class ChangelogSectionType(enum.Enum):
    UNDEFINED = 0
    ADDED = 1
    CHANGED = 2
    DEPRECATED = 3
    REMOVED = 4
    FIXED = 5
    SECURITY = 6


class ChangelogSection(object):
    def __init__(self, changelog_type: str = "Undefined", text: str = ""):
        self.type = ChangelogSectionType[changelog_type.upper()]
        self.text = text

    def __eq__(self, other):
        if not isinstance(other, ChangelogSection):
            return NotImplemented
        return self.type == other.type and self.text == other.text


class ChangelogVersion(object):
    PARSER_PATTERN = r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(\-(?P<pre>[^\+]+))?(\+(?P<build>.+))?$"
    PARSER = re.compile(PARSER_PATTERN)

    def __init__(self, major: int = 0, minor: int = 0, patch: int = 0, pre: str = None, build: str = None):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.pre = pre
        self.build = build

    def __eq__(self, other):
        if not isinstance(other, ChangelogVersion):
            return NotImplemented
        return (self.major == other.major and self.minor == other.minor and self.patch == other.patch
                and self.pre == other.pre and self.build == other.build)

    def __lt__(self, other):
        if not isinstance(other, ChangelogVersion):
            return NotImplemented
        return (self.major < other.major or (self.major == other.major and self.minor < other.minor)
                or (self.major == other.major and self.minor == other.minor and self.patch < other.patch))

    def __gt__(self, other):
        if not isinstance(other, ChangelogVersion):
            return NotImplemented
        return (self.major > other.major or (self.major == other.major and self.minor > other.minor)
                or (self.major == other.major and self.minor == other.minor and self.patch > other.patch))

    def from_str(self, version: str):
        if version.upper() == "UNRELEASED":
            self.major = 0
            self.minor = 0
            self.patch = 0
            self.pre = None
            self.build = None
        else:
            match_obj = ChangelogVersion.PARSER.match(version)
            if match_obj is None:
                raise ValueError("Wrong Changelog version format")
            self.major = int(match_obj.group("major"))
            self.minor = int(match_obj.group("minor"))
            self.patch = int(match_obj.group("patch"))
            self.pre = match_obj.group("pre")
            self.build = match_obj.group("build")

    def __str__(self):
        if self.major == 0 and self.minor == 0 and self.patch == 0:
            return "Unreleased"
        base = "{}.{}.{}".format(self.major, self.minor, self.patch)
        if self.pre is not None:
            base = "{}-{}".format(base, self.pre)
        if self.build is not None:
            base = "{}+{}".format(base, self.build)
        return base


class ChangelogItem(object):
    def __init__(self):
        self.version = ChangelogVersion()
        self.date = None
        self.sections = []  # List of ChangelogSection

    def __eq__(self, other):
        if not isinstance(other, ChangelogItem):
            return NotImplemented
        return self.version == other.version and self.date == other.date and self.sections == other.sections


class Changelog(object):
    ITEM_PARSER_PATTERN = r"^##\s+\[(?P<version>[^\]]+)\](\s+\-\s+(?P<date>\S+))?$"
    ITEM_PARSER = re.compile(ITEM_PARSER_PATTERN)
    SECTION_PARSER_PATTERN = r"^###\s+(?P<type>\S+)$"
    SECTION_PARSER = re.compile(SECTION_PARSER_PATTERN)
    CHANGELOG_URL_PATTERN = "https://raw.githubusercontent.com/{}/{}/CHANGELOG.md"

    def __init__(self):
        self.items = []  # List of ChangelogItem

    def __eq__(self, other):
        if not isinstance(other, Changelog):
            return NotImplemented
        return self.items == other.items

    @staticmethod
    def parse(data: str):
        TestTool.test_log("Start parsing Changelog.")
        changelog = None
        for line in data.split("\n"):
            line = line.strip()
            if line == "":
                continue
            elif line.startswith("# "):
                # Only one title line allowed at first line
                if changelog is not None:
                    return None
                changelog = Changelog()
            elif line.startswith("## "):
                item = ChangelogItem()
                match_obj = Changelog.ITEM_PARSER.match(line)
                # Item line must match
                if match_obj is None:
                    return None
                item.version.from_str(match_obj.group("version"))
                item.date = match_obj.group("date")
                changelog.items.append(item)
            elif line.startswith("### "):
                # At least one item must be added before section
                if not changelog.items:
                    return None
                item = changelog.items[-1]
                section = ChangelogSection()
                match_obj = Changelog.SECTION_PARSER.match(line)
                # Section line must match
                if match_obj is None:
                    return None
                section.type = ChangelogSectionType[match_obj.group("type").upper()]
                item.sections.append(section)
            else:
                section = changelog.items[-1].sections[-1]
                section.text += line
                section.text += "\n"
        TestTool.test_log("Finished parsing Changelog.")
        return changelog

    @staticmethod
    def fetch(repo_name, commit_id, retry = 10):
        changelog_url = Changelog.CHANGELOG_URL_PATTERN.format(repo_name, commit_id)
        TestTool.test_log("Start fetching Changelog from: {}".format(changelog_url))
        changelog = None
        flag = False
        for _ in range(retry):
            try:
                data = urllib.request.urlopen(changelog_url).read().decode("utf-8")
                changelog = Changelog.parse(data)
                flag = True
            except Exception:
                changelog = None
            if flag:
                break
        if changelog is not None:
            changelog.items = changelog.items[::-1]
        TestTool.test_log("Finished fetching Changelog.")
        return changelog


# Test cases

class TesterBase(object):
    TEST_CASE_START_LOG_PATTERN = "Started test case: {}"
    TEST_CASE_FINISH_LOG_PATTERN = "Finished test case: {}"

    @staticmethod
    def test(prev_changelog: Changelog, curr_changelog: Changelog) -> (bool, str):
        raise NotImplementedError


class TesterChangelogProperlyChanged(TesterBase):
    """Changelog.md is properly changed."""

    @staticmethod
    def test(prev_changelog: Changelog, curr_changelog: Changelog) -> (bool, str):
        TestTool.test_log(TesterBase.TEST_CASE_START_LOG_PATTERN.format("TesterChangelogProperlyChanged"))
        for i in range(len(prev_changelog.items)):
            if i >= len(curr_changelog.items):
                return False, "It is not allowed to remove items from changelog."
            if prev_changelog.items[i] != curr_changelog.items[i]:
                return False, "It is not allowed to modify items in changelog."
        TestTool.test_log(TesterBase.TEST_CASE_FINISH_LOG_PATTERN.format("TesterChangelogProperlyChanged"))
        return True, ""


class TesterNewChangelogItemsVersion(TesterBase):
    """Check if version of new items are increasing."""

    @staticmethod
    def test(prev_changelog: Changelog, curr_changelog: Changelog) -> (bool, str):
        assert len(prev_changelog.items) <= len(curr_changelog.items)
        TestTool.test_log(TesterBase.TEST_CASE_START_LOG_PATTERN.format("TesterNewChangelogItemsVersion"))
        start = len(prev_changelog.items)
        if start == 0:
            start = 1
        for i in range(len(curr_changelog.items) - start):
            item = curr_changelog.items[start + i]
            prev_item = curr_changelog.items[start + i - 1]
            if item.version < prev_item.version:
                return False, "Changelog items should have increasing versions."
        TestTool.test_log(TesterBase.TEST_CASE_FINISH_LOG_PATTERN.format("TesterNewChangelogItemsVersion"))
        return True, ""


class TesterNewChangelogItemsHasSection(TesterBase):
    """Check if there is at least one section for each new changelog item."""

    @staticmethod
    def test(prev_changelog: Changelog, curr_changelog: Changelog) -> (bool, str):
        assert len(prev_changelog.items) <= len(curr_changelog.items)
        TestTool.test_log(TesterBase.TEST_CASE_START_LOG_PATTERN.format("TesterNewChangelogItemsHasSection"))
        changelog_diff_items = curr_changelog.items[len(prev_changelog.items):]
        for item in changelog_diff_items:
            if len(item.sections) == 0:
                return False, "There must be at lease one section for each changelog item."
        TestTool.test_log(TesterBase.TEST_CASE_FINISH_LOG_PATTERN.format("TesterNewChangelogItemsHasSection"))
        return True, ""


class TesterNewChangelogSectionsHasText(TesterBase):
    """Empty section is not allowed."""

    @staticmethod
    def test(prev_changelog: Changelog, curr_changelog: Changelog) -> (bool, str):
        assert len(prev_changelog.items) <= len(curr_changelog.items)
        TestTool.test_log(TesterBase.TEST_CASE_START_LOG_PATTERN.format("TesterNewChangelogSectionsHasText"))
        changelog_diff_items = curr_changelog.items[len(prev_changelog.items):]
        for item in changelog_diff_items:
            assert len(item.sections) > 0
            for section in item.sections:
                if section.text == "":
                    return False, "Empty section is not allowed."
        TestTool.test_log(TesterBase.TEST_CASE_FINISH_LOG_PATTERN.format("TesterNewChangelogSectionsHasText"))
        return True, ""


# Test tools

class TestTool(object):
    failure_code = 0

    @staticmethod
    def test_fail(log_message: str, instant_fail = True):
        print("[FAIL] {}".format(log_message))
        TestTool.failure_code = 1
        if instant_fail:
            exit(TestTool.failure_code)

    @staticmethod
    def test_log(log_message: str):
        print("[LOG] {}".format(log_message))

    @staticmethod
    def test_finish():
        exit(TestTool.failure_code)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", dest="repo_name", action="store", required=True)
    parser.add_argument("--prev", dest="prev_commit_id", action="store", required=True)
    parser.add_argument("--curr", dest="curr_commit_id", action="store", required=True)
    args = parser.parse_args()

    # Get changelog objects
    prev_changelog = Changelog.fetch(args.repo_name, args.prev_commit_id)
    curr_changelog = Changelog.fetch(args.repo_name, args.curr_commit_id)
    if prev_changelog is None or curr_changelog is None:
        TestTool.test_fail("Cannot fetch changelog, or fetched wrong changelog format.")

    # Test cases
    testers = [
        TesterChangelogProperlyChanged,
        TesterNewChangelogItemsVersion,
        TesterNewChangelogItemsHasSection,
        TesterNewChangelogSectionsHasText,
    ]
    for tester in testers:
        try:
            result, log_message = tester.test(prev_changelog, curr_changelog)
            if not result:
                TestTool.test_fail(log_message, instant_fail=False)
        except AssertionError:
            # AssertionError means nothing to do because this situation should be covered by other test cases.
            pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        TestTool.test_log("Test finished by user interrupt (Ctrl-C).")
    except:
        TestTool.test_fail("Unexpected error.")
    finally:
        TestTool.test_finish()
