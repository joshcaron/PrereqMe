#! /usr/bin/python
"""
    Scrapes Northeastern University course information.
"""

import json
import itertools
import re
import threading
import traceback
import urllib
import urllib2
import lxml.html

####################################
# Compiled Regexes                 #
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

# URL used for getting the available semesters
SEMESTER_OPTIONS_URL = 'https://wl11gp.neu.edu/udcprod8/bwckctlg.p_disp_dyn_ctlg'

# URL used for getting all the department options
DEPARTMENT_OPTIONS_URL = 'https://wl11gp.neu.edu/udcprod8/bwckctlg.p_disp_cat_term_date'

# Required parameters for getting departments
DEPARTMENT_OPTIONS_PARAMS = {
    "call_proc_in": "bwckctlg.p_disp_dyn_ctlg",
    "cat_term_in": None
}

# URL used for the course listing for a department
COURSES_URL = 'https://wl11gp.neu.edu/udcprod8/bwckctlg.p_display_courses'

# Required parameters for the course listing page
REQUIRED_COURSES_PARAMS = {
    "sel_subj": "",
    "sel_levl": "",
    "sel_schd": "",
    "sel_coll": "",
    "sel_divs": "",
    "sel_dept": "",
    "sel_attr": ""
}

####################################
# Northeastern Information         #
####################################

NORTHEASTERN_INFO = {
    "school": "Northeastern University",
    "slug": "Northeastern",
    "location": {
        "street": "360 Huntington Ave",
        "city": "Boston",
        "state": "MA",
        "country": "USA",
    },
    "website": "http://www.northeastern.edu/",
}


####################################
# Main                             #
####################################

def main():
    """
        After selecting a semester and department, gather all the course
        information and save it as json
    """
    print "Getting available semesters:"
    semester = get_semester_choice()
    print "\nGetting departments for %s:" % semester["name"]

    departments = get_department_choices(semester["value"])
    fetched = thread_departments(departments, semester["value"])

    northeastern = NORTHEASTERN_INFO.copy()
    northeastern["departments"] = fetched

    path = raw_input("Save as (example.json): ")
    with open(path, 'w') as fobj:
        json.dump(northeastern, fobj, indent=4, sort_keys=True)


####################################
# Semester Selection               #
####################################

def get_semester_options():
    """
        Gets all the available semesters, except for CPS and Law
    """
    dom = get_dom(SEMESTER_OPTIONS_URL)
    select = dom.cssselect('select[name="cat_term_in"]')[0]
    semesters = get_options(select)
    filtered = []
    for semester in semesters:
        name = semester["name"]
        if "Law" not in name and "CPS" not in name and "None" not in name:
            filtered.append(semester)
    return filtered


def get_semester_choice():
    """
        Out of the available semesters, gets the user's choice
    """
    semesters = get_semester_options()
    for index, semester in enumerate(semesters):
        print "(%d) %s" % (index+1, semester["name"])

    choice = raw_input("\nChoice: ")
    try:
        return semesters[int(choice)-1]
    except ValueError:
        print "Please enter a number.\n"
        get_semester_choice()
    except IndexError:
        print "Out of range.\n"
        get_semester_choice()


####################################
# Department Selection             #
####################################

def get_department_options(term_id):
    """
        Gets all the available departments
    """
    params = DEPARTMENT_OPTIONS_PARAMS.copy()
    params['cat_term_in'] = term_id
    url = DEPARTMENT_OPTIONS_URL + '?' + urllib.urlencode(params)
    dom = get_dom(url)
    select = dom.cssselect('select[name="sel_subj"]')[0]
    return get_options(select)


def get_department_choices(term_id):
    """
        Out of the available departments, gets the user's choice
    """
    departments = get_department_options(term_id)
    print "(0) All"
    # for index, d in enumerate(departments):
    #   print "(%d) %s" % (index+1, d["name"])

    choice = raw_input("\nChoice: ")
    try:
        if int(choice) == 0:
            return departments
        else:
            print "Choosing individual departments is not currently supported.\n"
            get_department_choices(term_id)
    except ValueError:
        print "Please enter a number.\n"
        get_department_choices(term_id)


def thread_departments(departments, term_id, threadcount=10):
    """
        Thread the course fetching for departments
    """
    dlock = threading.Lock()

    depts = itertools.tee(departments, 1)[0]
    fetched = []
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
                info = get_courses_for_department(dept['value'], term_id)
                data = {
                    "name": dept['name'],
                    "abbreviation": dept['value'],
                    "courses": info
                }
                fetched.append(data)
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

    return fetched

def get_courses_for_department(dept_id, term_id):
    """
        Get all of the courses for the given department in the given term
    """
    params = REQUIRED_COURSES_PARAMS.copy()
    params['term_in'] = term_id
    url = COURSES_URL + '?' + urllib.urlencode(params) + '&sel_subj=' + dept_id
    dom = get_dom(url)
    return parse_course_tree(dom)


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


def elems_to_content(elems):
    """
        Takes a list of LXML elements and returns a list of their text content
    """
    return [elem.text_content() for elem in elems]


def get_options(select):
    """
        Takes an LXML Select element and returns a list of dictionaries with
        each option's name and value
    """
    choices = []
    for child in select.getchildren():
        name = child.text.strip()
        value = child.values()[0]
        choices.append({"name": name, "value": value})
    return choices


####################################
# Course Information Parsing       #
####################################

def parse_course_tree(dom):
    """
        Returns a list of courses that have been extracted from the DOM
    """
    titles = elems_to_content(dom.cssselect('td.nttitle'))
    descriptions = dom.cssselect('td.ntdefault')[:len(titles)]
    courses = []
    for title, description in zip(titles, descriptions):
        course_num, title = TITLE_INFO_REGEX.match(title).groups()
        course_num = int(course_num)
        title = title.strip()
        course = get_course_info(description)
        course['title'] = title
        course['number'] = course_num
        courses.append(course)
    return courses


def get_course_info(description):
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
    for piece in pieces:
        matched = DOUBLE_REGEX.match(piece.strip())
        stripped = piece.strip()
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
    """
        Split up pieces of the description and return a tuple containing the
        description of the course, the prerequisite string of the course, and
        the corequisite string of the course
    """
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
    """
        Given a string that contains prerequisites of a course, return the
        parsed string as an array of arrays such that in order to fulfill the
        prerequisites for the course a prerequiste from each array in the
        returned array should be completed
    """
    prereqs = []
    pieces = [p.strip() for p in prereq_str.split(";")]
    try:
        has_course = COURSES_REGEX.search(pieces[0])
        if has_course:
            # extract all courses
            if "(a)" in pieces[0]:
                # Ands and Ors, oh dear god why
                ands = pieces[0].split("and")
                for option in ands:
                    ors = [make_prereq_course(o) for o in COURSES_REGEX.findall(option)]
                    prereqs.append(ors)
            elif " or " in pieces[0]:
                # ors
                ors = [make_prereq_course(o) for o in COURSES_REGEX.findall(pieces[0])]
                prereqs.append(ors)
            elif " and " in pieces[0]:
                ands = [[make_prereq_course(a)] for a in COURSES_REGEX.findall(pieces[0])]
                for option in ands:
                    prereqs.append(option)
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
    """
        Return the corequisites extracted from the given string
    """
    coreqs = []
    try:
        coreqs = [make_coreq_course(a) for a in COURSES_REGEX.findall(coreq_str)]
    except IndexError:
        pass

    return coreqs


def make_prereq_course(course_str, concurrent=False):
    """
        Return a dictionary of a course that contains the course information and
        whether or not the prerequiste can be taken concurrently
    """
    pieces = course_str.split(" ")
    course = {
        "department": pieces[0],
        "number": pieces[1],
        "concurrent": concurrent
    }
    return course


def make_coreq_course(course_str):
    """
        Return a dictionary of a course that contains the course information
    """
    pieces = course_str.split(" ")
    course = {
        "department": pieces[0],
        "number": pieces[1]
    }
    return course


def parse_hours(numbers):
    """
        Return all the hours information that is found
    """
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
            split = SPACES_REGEX.split(text, 1)
            count = float(split[0])
            hour_type = split[1].strip()
            hours['valueType'] = 'single'
            hours['value'] = count
            hours['hourType'] = hour_type
        all_hours.append(hours)

    return all_hours


def after_hours(post_numbers):
    """
        Return a tuple of information that is found found after the course hours
    """
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

