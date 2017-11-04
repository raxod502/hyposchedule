#!/usr/bin/env python3

import json
import pprint
import re

def days_to_str(days):
    return ''.join(sorted(days, lambda day: 'MTWRF'.index(day)))

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

    def __str__(self):
        return str(self.hours) + ':' + str(self.minutes)

    def __repr__(self):
        return 'HourMinute({}, {}, {})'.format(self.hours, self.minutes, False)

class TimeBlock:
    def __init__(self, days, begin, end):
        self.days = days
        self.begin = begin
        self.end = end

    def conflicts_with(self, other):
        return self.days & other.days and not (self.end <= other.begin or self.begin >= other.end)

    def __str__(self):
        return str(self.begin) + ' - ' + str(self.end) + ' on ' + days_to_str(self.days)

    def __repr__(self):
        return 'TimeBlock({}, {}, {})'.format(self.days, self.begin, self.end)

class Course:
    def __init__(self, data):
        self.data = data

    def __getitem__(self, attr):
        return self.data[attr]

    def matches(self, pattern):
        department, course_code, school, section_number = re.match(
            r'([a-z]+)?\s*(?:([0-9]+)|\s)\s*(?:(hm|po|jm)|\s)\s*([0-9+])',
            pattern.lower())
        if section_number:
            section_number = int(section_number)
        return not (department and department != self.department or
                    course_code and course_code != self.course_code or
                    school and school != self.school or
                    section_number and section_number != self.section_number)

def parse_course_data(courses_filename):
    with open(courses_filename) as courses_file:
        courses_data = json.load(courses_file)
    courses = []
    for course_data in courses_data:
        course_name = course_data['name']
        data_blob = course_data['times']
        sections = []
        for line in data_blob.splitlines():
            line_match = re.match(
                r'([A-Z]+)\s*([0-9A-Z]+)\s*(HM|PO|JM)-([0-9]+)\s+\(([^\)]+)\):\s+(.+)',
                line)
            assert line_match, "Couldn't match line: " + line
            department, course_code, school, section_number, instructor, times_blob = line_match.groups()
            section_number = int(section_number)
            assert section_number >= 1
            time_matches = re.finditer(
                r'([MTWRF]+)\s+([0-9]+):([0-9]+)\s*(AM|PM)?\s+-\s+([0-9]+):([0-9]+)\s+(AM|PM);\s+([^,]+),\s+([^,]+),\s+([^,]+)',
                times_blob)
            assert time_matches, "Couldn't match times: " + times_blob
            meetings = []
            for time_match in time_matches:
                days, hours_begin, minutes_begin, ampm_begin, hours_end, minutes_end, ampm_end, campus, building, room = time_match.groups()
                days = set(days)
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
                'department': department,
                'course_code': course_code,
                'school': school,
                'section_number': section_number,
                'instructor': instructor,
                'meetings': meetings
            }
            sections.append(section)
        course = {
            'course_name': course_name,
            'sections': sections,
        }
        courses.append(course)
    return courses

def parse_user_file(user_filename):
    try:
        with open(user_filename, 'r') as user_file:
            return user_file.readlines()
    except FileNotFoundError:
        return []

def filter_courses(all_courses, selected_patterns, blacklisted_patterns):
    selected_courses = []
    for selected_pattern in selected_patterns:
        matched_courses = []
        for course in all_courses:
            if course.matches(selected_pattern):
                matched_courses.append(course)
        if len(matched_courses) > 1:
            raise AssertionError('Selected pattern {} matches ambiguously: {}'
                                 .format(selected_pattern, matched_courses))
        if len(matched_courses) < 1:
            raise AssertionError('Selected pattern {} matches no courses'
                                 .format(selected_pattern))
        selected_courses.extend(matched_courses)
    blacklisted_courses = []
    for blacklisted_pattern in blacklisted_patterns:
        matched_courses = []
        for course in all_courses:
            if course.matches(selected_pattern):
                matched_courses.append(course)
        if not matched_courses:
            raise AssertionError('Blacklisted pattern {} matches no courses'
                                 .format(blacklisted_pattern))
        blacklisted_courses.extend(matched_courses)
    courses = []
    for course in all_courses:
        if course in blacklisted_courses:
            continue
        conflicts = False
        for selected_course in selected_courses:
            if course.conflicts_with(selected_course):
                conflicts = True
                break
        if not conflicts:
            courses.append(course)
    return courses

all_courses = parse_course_data('courses.json')
selected_patterns = parse_user_file('selected.txt')
blacklisted_patterns = parse_user_file('blacklisted.txt')
courses = filter_courses(all_courses, selected_patterns, blacklisted_patterns)

pprint.pprint(courses)
