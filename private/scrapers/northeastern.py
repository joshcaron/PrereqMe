#! /usr/bin/python
"""
    Scrapes NEU course information.
"""

import json
import itertools
import os
import re
import sys
import threading
import traceback
import urllib
import urllib2

import lxml.html


# Regex for extracting course number from title
TITLE_INFO_REGEX = re.compile('.*([0-9]{4}).*-(.*)')
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

def iter_child_textnodes(elem, strip_whitespace=False, remove_empty=False):
    """
        Returns a generator which produces a list of the text contents of direct
        child nodes.
    """
    # Text nodes found after the first HTML child of this element are stored
    # in the tail properties of the child elements rather than in the list of
    # children.
    tail_iter = (c.tail for c in elem.iterchildren() if c.tail is not None)
    chained_iter = itertools.chain((elem.text,), tail_iter)
    if strip_whitespace:
        chained_iter = (s.strip() for s in chained_iter)
    if remove_empty:
        chained_iter = (s for s in chained_iter if s)
    return chained_iter

def splitstrip(text, separator):
    """
        Splits text on a separator, then strips white space from the resulting
        strings and only outputs non-empty strings.
    """
    return [t.strip() for t in text.split(separator) if t.strip()]

def parse_hours(text):
    hours = {}

    if "TO" in text:
        # range
        # TODO: Move to constant
        to_re = re.compile('([0-9]+\.[0-9]{3} TO +[0-9]+\.[0-9]{3})(.*)')
        groups = to_re.match(text).groups()
        hmin, hmax = [c.strip() for c in groups[0].split("TO")]
        hours['valueType'] = 'range'
        hours['min'] = hmin
        hours['max'] = hmax
        hours['hourType'] = groups[1].strip()
    elif "OR" in text:
        # options
        # TODO: Move to constant
        or_re = re.compile('([0-9]+\.[0-9]{3} OR +[0-9]+\.[0-9]{3})(.*)')
        groups = or_re.match(text).groups()
        options = [c.strip() for c in groups[0].split("OR")]
        hours['valueType'] = 'options'
        hours['options'] = options
        hours['hourType'] = groups[1].strip()
    else:
        # single
        # TODO: Move to constant
        spaces = re.compile(' +')
        split = spaces.split(text, 1)
        count = float(split[0])
        hour_type = split[1].strip()
        hours['valueType'] = 'single'
        hours['value'] = count
        hours['hourType'] = hour_type

    return hours

def parse_description(description):
    info = {}
    pieces = [a.strip() for a in description.itertext() if a.strip() != '']

    preNumbers = []
    numbers = []
    postNumbers = []
    foundNumbers = False
    # TODO: Move to constant
    double_re = re.compile("([0-9]+\.[0-9]{3})")
    for p in pieces:
        matched = double_re.match(p.strip())
        stripped = p.strip()
        if foundNumbers:
            if matched != None:
                numbers.append(stripped)
            else:
                postNumbers.append(stripped)
        elif matched != None:
            foundNumbers = True
            numbers.append(stripped)
        else:
            preNumbers.append(stripped)

    desc = " ".join(preNumbers)
    hasPrereq = 'Prereq.' in desc
    hasCoreq = 'Coreq.' in desc
    if hasPrereq and hasCoreq:
        desc_pieces = [r.strip() for r in desc.split('Prereq.') if r.strip() != '']
        info['description'] = desc_pieces[0]
        reqs = [r.strip() for r in desc_pieces[1].split('Coreq.') if r.strip() != '']
        info['prereq'] = reqs[0]
        info['coreq'] = reqs[1]
    elif hasPrereq:
        desc_pieces = [r.strip() for r in desc.split('Prereq.') if r.strip() != '']
        info['description'] = desc_pieces[0]
        info['prereq'] = desc_pieces[1]
        info['coreq'] = None
    elif hasCoreq:
        desc_pieces = [r.strip() for r in desc.split('Coreq.') if r.strip() != '']
        info['description'] = desc_pieces[0]
        info['prereq'] = None
        info['coreq'] = desc_pieces[1]
    else:
        info['description'] = desc
        info['prereq'] = None
        info['coreq'] = None

    hours = []
    for nums in numbers:
        hours.append(parse_hours(nums))
    info['hours'] = hours

    info['levels'] = [l.strip() for l in postNumbers[1].split(",")]
    info['schedules'] = [s.strip() for s in postNumbers[3].split(",")]
    info['department'] = postNumbers[4]
    # Some courses don't have attributes!??!
    try:
        comma_attributes = [
            'UG Col of Arts, Media & Design',
            'GS Col of Arts, Media & Design'
        ]
        attrs = postNumbers[6]
        info['attributes'] = re.findall("(" + "|".join(comma_attributes) + "|(?:\w+[\s|,])+)", attrs)
    except IndexError:
        info['attributes'] = []

    return info

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

def get_course_info_by_dept(depts, threadcount=10):
    """
        Gets a dictionary mapping departments to their course information
    """
    # Lock for department queue
    dlock = threading.Lock()
    output = {
        "school": "Northeastern University",
        "slug": "NEU",
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

def main():
    """
        Writes all course information to all_courses.json
    """
    dept_dict = get_course_info_by_dept(get_departments())
    with open('../schools/northeastern.json', 'w') as fobj:
        json.dump(dept_dict, fobj, indent=4, sort_keys=True)

if __name__ == '__main__':
    main()

