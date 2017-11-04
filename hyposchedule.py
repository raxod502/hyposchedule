#!/usr/bin/env python3

import json
import pprint
import re

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

class TimeBlock:
    def __init__(self, begin, end):
        self.begin = begin
        self.end = end

    def conflicts_with(self, other):
        return not (self.end <= other.begin or self.begin >= other.end)

def parse_course_data(courses_filename):
    courses_data = json.load(courses_filename)
    courses = []
    for course_data in courses_data:
        course_name = course_data['name']
        data_blob = course_data['times']
        sections = []
        for line in data_blob.splitlines():
            line_match = re.match(r'([A-Z]+)([0-9A-Z]+)\s+([A-Z]+)-([0-9]+)\s+\(([^\)]+)\):\s+(.+)')
            assert line_match, "Couldn't match line: " + line
            department, course_code, school, section_number, instructor, times_blob = line_match.groups()
            section_number = int(section_number)
            assert section_number >= 1
            time_matches = times_blob.findall('([MTWRF]+)\s+([0-9]+):([0-9]+)\s*(AM|PM)\s+([0-9]+):([0-9]+)\s+(AM|PM);\s+([^,]+),\s+([^,]+),\s+([^,]+)')
            meetings = []
            for time_match in time_matches:
                days, hours_begin, minutes_begin, ampm_begin, hours_end, minutes_end, ampm_end, campus, building, room = time_match.groups()
                days = set(days)
                hours_begin = int(hours_begin)
                minutes_begin = int(minutes_begin)
                hours_end = int(hours_end)
                minutes_end = int(minutes_end)
                pm_begin = ampm_begin == 'PM'
                pm_end = ampm_end == 'PM'
                assert 1 <= hours_begin <= 12
                assert 0 <= minutes_begin <= 59
                assert 1 <= hours_end <= 12
                assert 0 <= minutes_end <= 59
                begin = HourMinute(hours_begin, minutes_begin, pm_begin)
                end = HourMinute(hours_end, minutes_end, pm_end)
                block = TimeBlock(begin, end)
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

pprint.pprint(parse_course_data('courses.json'))
