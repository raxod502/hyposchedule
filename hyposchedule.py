#!/usr/bin/env python3

import collections
import json
import operator
import re

def days_to_str(days):
    return ''.join(sorted(days, key=lambda day: 'MTWRFSU'.index(day)))

class HourMinute:
    def __init__(self, hours, minutes, pm):
        self.hours = hours % 12
        self.minutes = minutes
        if pm:
            self.hours += 12

    def compare(self, other):
        if self.hours < other.hours:
            return -1
        elif self.hours > other.hours:
            return 1
        elif self.minutes < other.minutes:
            return -1
        elif self.minutes > other.minutes:
            return 1
        else:
            return 0

    def __eq__(self, other):
        return self.compare(other) == 0

    def __ne__(self, other):
        return self.compare(other) != 0

    def __lt__(self, other):
        return self.compare(other) < 0

    def __gt__(self, other):
        return self.compare(other) > 0

    def __le__(self, other):
        return self.compare(other) <= 0

    def __ge__(self, other):
        return self.compare(other) >= 0

    def __hash__(self):
        return hash((self.hours, self.minutes))

    def __str__(self):
        human_hours = ((self.hours - 1) % 12) + 1
        pm = self.hours >= 12
        return '{}:{:02d} {}'.format(human_hours, self.minutes, 'PM' if pm else 'AM')

    def __repr__(self):
        return 'HourMinute({}, {}, {})'.format(self.hours, self.minutes, False)

class TimeBlock:
    def __init__(self, days, begin, end):
        self.days = days
        self.begin = begin
        self.end = end

    def conflicts_with(self, other):
        return self.days & other.days and not (self.end <= other.begin or self.begin >= other.end)

    def compare(self, other):
        if self.begin < other.begin:
            return -1
        elif self.begin > other.begin:
            return 1
        elif self.end < other.end:
            return -1
        elif self.end > other.end:
            return 1
        else:
            for day in 'MWTRFSU':
                if day in self.days and day not in other.days:
                    return -1
                elif day in other.days and day not in self.days:
                    return 1
            return 0

    def __eq__(self, other):
        return self.compare(other) == 0

    def __ne__(self, other):
        return self.compare(other) != 0

    def __lt__(self, other):
        return self.compare(other) < 0

    def __gt__(self, other):
        return self.compare(other) > 0

    def __le__(self, other):
        return self.compare(other) <= 0

    def __ge__(self, other):
        return self.compare(other) >= 0

    def __hash__(self):
        return hash((self.days, self.begin, self.end))

    def __str__(self):
        return '{} from {} to {}'.format(days_to_str(self.days), self.begin, self.end)

    def __repr__(self):
        return 'TimeBlock({}, {}, {})'.format(repr(self.days), repr(self.begin), repr(self.end))

class Section:
    def __init__(self, data):
        self.data = data

    def __getitem__(self, attr):
        return self.data[attr]

    def __getattr__(self, attr):
        if attr == 'data':
            return self.data
        try:
            return self.data[attr]
        except KeyError:
            return self.data.__getattribute__(attr)

    def matches(self, pattern):
        department, course_code, school, section_number = re.match(
            r'([a-z]+)?\s*(?:([0-9]+)|\s)\s*(?:(hm|po|jm)|\s)(?:\s*|-)([0-9+])',
            pattern.lower())
        if section_number:
            section_number = int(section_number)
        return not (department and department != self.department or
                    course_code and course_code != self.course_code or
                    school and school != self.school or
                    section_number and section_number != self.section_number)

    def blocks(self):
        return [meeting['block'] for meeting in self.meetings]

    def conflicts_with(self, other):
        for my_meeting in self.meetings:
            for other_meeting in other.meetings:
                if my_meeting['block'].conflicts_with(other_meeting['block']):
                    return False
        return True

    def compare(self, other):
        if self.department < other.department:
            return -1
        elif self.department > other.department:
            return 1
        elif self.course_code < other.course_code:
            return -1
        elif self.course_code > other.course_code:
            return 1
        elif self.school < other.school:
            return -1
        elif self.school > other.school:
            return 1
        elif self.section_number < other.section_number:
            return -1
        elif self.section_number > other.section_number:
            return 1
        elif self.blocks() < other.blocks():
            return -1
        elif self.blocks() > other.blocks():
            return 1
        else:
            return 0

    def __eq__(self, other):
        return self.compare(other) == 0

    def __ne__(self, other):
        return self.compare(other) != 0

    def __lt__(self, other):
        return self.compare(other) < 0

    def __gt__(self, other):
        return self.compare(other) > 0

    def __le__(self, other):
        return self.compare(other) <= 0

    def __ge__(self, other):
        return self.compare(other) >= 0

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return 'Section({})'.format(repr(self.data))

class SectionBlock:
    def __init__(self, section, index):
        meeting = section.meetings[index]
        self.data = {**section, **meeting}
        self.data['index'] = index
        self.data['total'] = len(section.meetings)

    def __getitem__(self, attr):
        return self.data[attr]

    def __getattr__(self, attr):
        if attr == 'data':
            return self.data
        return self.data[attr]

    def blocks(self):
        return Section.blocks(self)

    def compare(self, other):
        num = Section.compare(self, other)
        if num == 0:
            if self.index < other.index:
                return -1
            elif self.index > other.index:
                return 1
            return 0
        else:
            return num

    def __eq__(self, other):
        return self.compare(other) == 0

    def __ne__(self, other):
        return self.compare(other) != 0

    def __lt__(self, other):
        return self.compare(other) < 0

    def __gt__(self, other):
        return self.compare(other) > 0

    def __le__(self, other):
        return self.compare(other) <= 0

    def __ge__(self, other):
        return self.compare(other) >= 0

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return 'SectionBlock({})'.format(repr(self.data))

def parse_course_data(courses_filename):
    with open(courses_filename) as courses_file:
        courses_data = json.load(courses_file)
    sections = []
    for course_data in courses_data:
        course_name = course_data['name']
        data_blob = course_data['times']
        for line in data_blob.splitlines():
            line_match = re.match(
                r'([A-Z]+)\s*([0-9A-Z]+)\s*(AF|CH|CM|HM|JM|JP|PO|PZ|SC)-([0-9]+)\s+\(([^\)]+)\):\s+(.*)',
                line)
            assert line_match, "Couldn't match line: " + line
            department, course_code, school, section_number, instructor, times_blob = line_match.groups()
            section_number = int(section_number)
            assert section_number >= 1
            time_matches = re.finditer(
                r'([MTWRFSU]+)\s+([0-9]+):([0-9]+)\s*(AM|PM)?\s+-\s+([0-9]+):([0-9]+)\s+(AM|PM);\s+([^,]+),\s+([^,]+),\s+([^,]+)',
                times_blob)
            assert time_matches, "Couldn't match times: " + times_blob
            meetings = []
            for time_match in time_matches:
                days, hours_begin, minutes_begin, ampm_begin, hours_end, minutes_end, ampm_end, campus, building, room = time_match.groups()
                days = frozenset(days)
                hours_begin = int(hours_begin)
                minutes_begin = int(minutes_begin)
                hours_end = int(hours_end)
                minutes_end = int(minutes_end)
                pm_begin = (ampm_begin or ampm_end) == 'PM'
                pm_end = ampm_end == 'PM'
                assert 1 <= hours_begin <= 12
                assert 0 <= minutes_begin <= 59
                assert 1 <= hours_end <= 12
                assert 0 <= minutes_end <= 59
                begin = HourMinute(hours_begin, minutes_begin, pm_begin)
                end = HourMinute(hours_end, minutes_end, pm_end)
                block = TimeBlock(days, begin, end)
                meeting = {
                    'campus': campus,
                    'building': building,
                    'room': room,
                    'block': block,
                }
                meetings.append(meeting)
            section = {
                'course_name': course_name,
                'department': department,
                'course_code': course_code,
                'school': school,
                'section_number': section_number,
                'instructor': instructor,
                'meetings': sorted(meetings, key=lambda meeting: meeting['block'])
            }
            sections.append(Section(section))
    return sections

def parse_user_file(user_filename):
    try:
        with open(user_filename, 'r') as user_file:
            return user_file.readlines()
    except FileNotFoundError:
        return []

def filter_sections(all_sections, selected_patterns, blacklisted_patterns):
    selected_sections = []
    for selected_pattern in selected_patterns:
        matched_sections = []
        for section in all_sections:
            if section.matches(selected_pattern):
                matched_sections.append(section)
        if len(matched_sections) > 1:
            raise AssertionError('Selected pattern {} matches ambiguously: {}'
                                 .format(selected_pattern, matched_sections))
        if len(matched_sections) < 1:
            raise AssertionError('Selected pattern {} matches no sections'
                                 .format(selected_pattern))
        selected_sections.extend(matched_sections)
    blacklisted_sections = []
    for blacklisted_pattern in blacklisted_patterns:
        matched_sections = []
        for section in all_sections:
            if section.matches(selected_pattern):
                matched_sections.append(section)
        if not matched_sections:
            raise AssertionError('Blacklisted pattern {} matches no sections'
                                 .format(blacklisted_pattern))
        blacklisted_sections.extend(matched_sections)
    sections = []
    for section in all_sections:
        if section in blacklisted_sections:
            continue
        conflicts = False
        for selected_section in selected_sections:
            if section.conflicts_with(selected_section):
                conflicts = True
                break
        if not conflicts:
            sections.append(section)
    return sections

def sort_sections_by_block(sections):
    groups = {}
    for section in sections:
        blocks = section.blocks()
        for idx, block in enumerate(blocks):
            if block not in groups:
                groups[block] = []
            groups[block].append(SectionBlock(section, idx))
    for block in groups:
        groups[block].sort()
    return collections.OrderedDict(sorted(groups.items(), key=operator.itemgetter(0)))

def format_block(block):
    return '### {}'.format(block)

def format_section_block(section_block):
    return '* {} {} {}-{:02d} {}{}'.format(
        section_block.department,
        section_block.course_code.zfill(3),
        section_block.school,
        section_block.section_number,
        section_block.course_name,
        ' [{}/{}]'.format(section_block.index + 1, section_block.total)
        if section_block.total > 1 else '',)

def format_section_section(block, section_blocks):
    return (format_block(block) + '\n\n' +
            '\n'.join(format_section_block(section_block)
                      for section_block in section_blocks))

def format_section_sections(section_groups):
    return '\n\n'.join(
        format_section_section(*item) for item in section_groups.items())

all_sections = parse_course_data('courses.json')
selected_patterns = parse_user_file('selected.in')
blacklisted_patterns = parse_user_file('blacklisted.in')
sections = filter_sections(all_sections, selected_patterns, blacklisted_patterns)
section_groups = sort_sections_by_block(sections)

print(format_section_sections(section_groups))
