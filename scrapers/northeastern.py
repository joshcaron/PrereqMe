#! /usr/bin/python
"""
    Scrapes NEU course information.
"""

import json
import itertools
import os
import re
import threading
import traceback
import urllib
import urllib2
import lxml.html

####################################
# Compiled Regexs                  #
####################################

# Extract course number and title
TITLE_INFO_REGEX = re.compile(r'[\sa-zA-Z]+(\d+)\s?-\s?(.*)')

# Extract hour range
HOURS_TO_REGEX = re.compile(r'([0-9]+\.[0-9]{3} TO +[0-9]+\.[0-9]{3})(.*)')

# Extract hour options
HOURS_OR_REGEX = re.compile(r'([0-9]+\.[0-9]{3} OR +[0-9]+\.[0-9]{3})(.*)')

# Match one or more spaces
SPACES_REGEX = re.compile(r' +')

# Matches a floating point number that has 3 decimal places
DOUBLE_REGEX = re.compile(r'([0-9]+\.[0-9]{3})')

# Known attributes that have commas in them
COMMA_ATTRIBUTES = [
    'UG Col of Arts, Media & Design',
    'GS Col of Arts, Media & Design'
]
ATTRIBUTES_REGEX = re.compile('(' + '|'.join(COMMA_ATTRIBUTES) + r'|(?:[\w\s-])+)')

# Matches a department string followed by a course number
COURSES_REGEX = re.compile(r'(\w+ \d+)')


####################################
# URLs and Parameter data          #
####################################

# Base URL for the course display page
DISPLAY_COURSES_URL = 'https://wl11gp.neu.edu/udcprod8/bwckctlg.p_display_courses?'
# Default parameters for the course display page
DEFAULT_COURSES_PARAMS = {
    "sel_levl": "dummy",
    "call_proc_in": "",
    "sel_to_cred": "",
    "sel_crse_strt": "",
    "sel_from_cred": "",
    "sel_divs": "dummy",
    "sel_schd": "dummy",
    "sel_attr": "dummy",
    "term_in": "201530",
    "sel_coll": "dummy",
    "sel_dept": "",
    "sel_crse_end": "",
    "sel_title": ""
}


####################################
# Main                             #
####################################

def main():
    """
        Writes all course information to all_courses.json
    """
    dept_dict = get_course_info_by_dept(get_departments())
    with open('../schools/northeastern.json', 'w') as fobj:
        json.dump(dept_dict, fobj, indent=4, sort_keys=True)


def get_course_info_by_dept(depts, threadcount=10):
    """
        Gets a dictionary mapping departments to their course information
    """
    # Lock for department queue
    dlock = threading.Lock()
    output = {
        "school": "Northeastern University",
        "slug": "Northeastern",
        "location": {
            "street": "360 Huntington Ave",
            "city": "Boston",
            "state": "MA",
            "country": "USA",
        },
        "website": "http://www.northeastern.edu/",
        "departments": []
    }
    depts = itertools.tee(depts, 1)[0]
    errors = []

    def threadfunc():
        """
            Runs inside of the threads. Gets information for departments in
            a loop and returns when no deparments remain in the queue
        """
        while True:
            try:
                dlock.acquire()
                try:
                    dept = depts.next()
                    print 'Getting: %s' % dept['name']
                except StopIteration:
                    return
                finally:
                    dlock.release()
                info = get_course_info(dept['abbreviation'])
                data = {
                    "name": dept['name'],
                    "abbreviation": dept['abbreviation'],
                    "courses": info
                }
                output['departments'].append(data)
            except Exception, err:
                errors.append((err, traceback.format_exc()))
                return
    threads = [threading.Thread(target=threadfunc) for i in xrange(threadcount)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    if errors:
        errstr = '\n'.join('%s\n%s' % pair for pair in errors)
        raise Exception('Errors occurred fetching data:\n%s' % errstr)
    return output


####################################
# DOM Parsing                      #
####################################

def get_dom(url, data=None):
    """
        Performs an HTTP request on the url and returns an LXML DOM of the HTML
        response.
    """
    response = urllib2.urlopen(url, data=data)
    try:
        return lxml.html.parse(response).getroot()
    finally:
        response.close()


def get_course_page(department):
    """
        Gets the courses list for the given department
    """
    params = DEFAULT_COURSES_PARAMS.copy()
    params["sel_subj"] = department
    # For some reason, sel_sub is required twice.
    url = DISPLAY_COURSES_URL + 'sel_subj=dummy&' + urllib.urlencode(params)
    return get_dom(url)


def get_departments():
    """
        Returns a list of department strings
    """
    # XXX: Do this by scraping.
    print 'Getting departments (fake)'
    curdir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(curdir, 'northeastern_departments.json'), 'r') as fobj:
        return json.load(fobj)


def elems_to_content(elems):
    """
        Takes a list of LXML elements and returns a list of their text content 
    """
    return [elem.text_content() for elem in elems]


####################################
# Course Information Parsing       #
####################################

def get_course_info(dept):
    """
        Takes a department and returns a dictionary mapping course numbers to
        dicts containing their information
    """
    dom = get_course_page(dept)
    titles = elems_to_content(dom.cssselect('td.nttitle'))
    descriptions = dom.cssselect('td.ntdefault')[:len(titles)]
    course_array = []
    for title, description in zip(titles, descriptions):
        course_num, title = TITLE_INFO_REGEX.match(title).groups()
        course_num = int(course_num)
        title = title.strip()
        info = parse_description(description)
        info['title'] = title
        info['number'] = course_num
        course_array.append(info)
    return course_array


def parse_description(description):
    """
        Takes a course description and returns a dictionary of all the various
        pieces of information that can be extracted from it
    """
    info = {}
    pre_numbers, numbers, post_numbers = get_pieces(description)

    description, prereq, coreq = split_requisites(pre_numbers)
    info['description'] = description
    info['prereqstr'] = prereq
    info['prerequisites'] = parse_prereqs(prereq)
    info['corequisites'] = parse_coreqs(coreq)

    hours = parse_hours(numbers)
    info['hours'] = hours

    levels, schedules, department, attributes = after_hours(post_numbers)
    info['levels'] = levels
    info['schedules'] = schedules
    info['department'] = department
    info['attributes'] = attributes

    return info


def get_pieces(description):
    """
        Takes a description of a course and returns a tuple of the various
        pieces organized as follows:
            - Before the course hours
            - The course hours
            - After the course hours
    """
    pieces = [a.strip() for a in description.itertext() if a.strip() != '']
    pre_numbers = []
    numbers = []
    post_numbers = []
    found_numbers = False
    for p in pieces:
        matched = DOUBLE_REGEX.match(p.strip())
        stripped = p.strip()
        if found_numbers:
            if matched != None:
                numbers.append(stripped)
            else:
                post_numbers.append(stripped)
        elif matched != None:
            found_numbers = True
            numbers.append(stripped)
        else:
            pre_numbers.append(stripped)

    return (pre_numbers, numbers, post_numbers)


def split_requisites(description_pieces):
    desc = " ".join(description_pieces)
    has_prereq = 'Prereq.' in desc
    has_coreq = 'Coreq.' in desc
    description = ''
    prereq_str = ''
    coreq_str = ''

    if has_prereq and has_coreq:
        desc_pieces = [r.strip() for r in desc.split('Prereq.') if r.strip() != '']
        description = desc_pieces[0]
        reqs = [r.strip() for r in desc_pieces[1].split('Coreq.') if r.strip() != '']
        prereq_str = reqs[0]
        coreq_str = reqs[1]
    elif has_prereq:
        desc_pieces = [r.strip() for r in desc.split('Prereq.') if r.strip() != '']
        description = desc_pieces[0]
        prereq_str = desc_pieces[1]
        coreq_str = ''
    elif has_coreq:
        desc_pieces = [r.strip() for r in desc.split('Coreq.') if r.strip() != '']
        description = desc_pieces[0]
        prereq_str = ''
        coreq_str = desc_pieces[1]
    else:
        description = desc
        prereq_str = ''
        coreq_str = ''

    return (description, prereq_str, coreq_str)


def parse_prereqs(prereq_str):
    prereqs = []
    pieces = [p.strip() for p in prereq_str.split(";")]
    try:
        has_course = COURSES_REGEX.search(pieces[0])
        if has_course:
            # extract all courses
            if "(a)" in pieces[0]:
                # Ands and Ors, oh dear god why
                ands = pieces[0].split("and")
                for a in ands:
                    ors = [make_prereq_course(o) for o in COURSES_REGEX.findall(a)]
                    prereqs.append(ors)
            elif " or " in pieces[0]:
                # ors
                ors = [make_prereq_course(o) for o in COURSES_REGEX.findall(pieces[0])]
                prereqs.append(ors)
            elif " and " in pieces[0]:
                ands = [[make_prereq_course(a)] for a in COURSES_REGEX.findall(pieces[0])]
                for a in ands:
                    prereqs.append(a)
            elif "concurrently" in pieces[0]:
                prereqs.append([make_prereq_course(pieces[0], True)])
            else:
                prereqs.append([make_prereq_course(pieces[0])])
            # any more data?
            prereqs.append([pieces[1]])
        else:
            # No course information, just text
            if prereq_str != '':
                prereqs.append([pieces[0]])
    except IndexError:
        pass

    return prereqs


def parse_coreqs(coreq_str):
    coreqs = []
    try:
        coreqs = [make_coreq_course(a) for a in COURSES_REGEX.findall(coreq_str)]
    except IndexError:
        pass

    return coreqs


def make_prereq_course(course_str, concurrent=False):
    pieces = course_str.split(" ")
    course = {
        "department": pieces[0],
        "number": pieces[1],
        "concurrent": concurrent
    }
    return course


def make_coreq_course(course_str):
    pieces = course_str.split(" ")
    course = {
        "department": pieces[0],
        "number": pieces[1]
    }
    return course


def parse_hours(numbers):
    all_hours = []
    for text in numbers:
        hours = {}

        if "TO" in text:
            # range
            groups = HOURS_TO_REGEX.match(text).groups()
            hmin, hmax = [c.strip() for c in groups[0].split("TO")]
            hours['valueType'] = 'range'
            hours['min'] = hmin
            hours['max'] = hmax
            hours['hourType'] = groups[1].strip()
        elif "OR" in text:
            # options
            groups = HOURS_OR_REGEX.match(text).groups()
            options = [c.strip() for c in groups[0].split("OR")]
            hours['valueType'] = 'options'
            hours['options'] = options
            hours['hourType'] = groups[1].strip()
        else:
            # single
            # TODO: Move to constant
            split = SPACES_REGEX.split(text, 1)
            count = float(split[0])
            hour_type = split[1].strip()
            hours['valueType'] = 'single'
            hours['value'] = count
            hours['hourType'] = hour_type
        all_hours.append(hours)

    return all_hours


def after_hours(post_numbers):
    levels = []
    schedules = []
    department = ''
    attributes = []

    levels = [l.strip() for l in post_numbers[1].split(",")]
    schedules = [s.strip() for s in post_numbers[3].split(",")]
    department = post_numbers[4]
    # Some courses don't have attributes!??!
    try:
        attrs = post_numbers[6]
        attributes = [a.strip() for a in ATTRIBUTES_REGEX.findall(attrs)]
    except IndexError:
        pass

    return (levels, schedules, department, attributes)


if __name__ == '__main__':
    main()

