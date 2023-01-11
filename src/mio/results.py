# Copyright 2021-2023 Datum Technology Corporation
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
########################################################################################################################


from mio import cache
from mio import common
from mio import cfg
from mio import clean
from mio import cov
from mio import dox
from mio import sim

import yaml
from yaml.loader import SafeLoader
import os
import jinja2
from jinja2 import Template
import xml.etree.cElementTree as ET
from datetime import datetime
import re


uvm_warning_regex = "UVM_WARNING(?! \: )"
uvm_error_regex   = "UVM_ERROR(?! \: )"
uvm_fatal_regex   = "UVM_FATAL(?! \: )"
viv_fatal_error   = "FATAL_ERROR\:"
mdc_fatal_errors  = ["FATAL_ERROR\:", "=F:"]

uvm_gen_dir = re.sub("results.py", "", os.path.realpath(__file__)) + ".."
relative_path_to_template = uvm_gen_dir + "/templates/"

html_report_template_path = relative_path_to_template + "regression_results.html.j2"


class RegressionResults:
    """Regression results model"""

    def __init__(self, passed, duration, num_failed_tests, num_passed_tests, html_report_path, xml_report_path):
        self.passed           = passed
        self.duration         = duration
        self.num_failed_tests = num_failed_tests
        self.num_passed_tests = num_passed_tests
        self.pct_passed       = self.num_passed_tests / (self.num_passed_tests + self.num_failed_tests) * 100
        self.html_report_path = html_report_path
        self.xml_report_path  = xml_report_path


def main(ip_str, filename="", is_regression=False, test_suite="", regression_name="", regression_timestamp=""):
    vendor, name = common.parse_dep(ip_str)
    if vendor == "":
        ip = cache.get_anon_ip(name, True)
    else:
        ip = cache.get_ip(vendor, name, True)
    snapshot = f"{ip.vendor}/{ip.name}"
    if is_regression:
        filename = "report"
    test_count = 0
    failure_count = 0
    total_duration = 0
    
    now = datetime.now()
    timestamp = now.strftime("%Y/%m/%d-%H:%M:%S")
    
    testsuites = ET.Element("testsuites")
    testsuites.set('id', timestamp)
    testsuites.set('name', snapshot)
    testsuite = ET.SubElement(testsuites, "testsuite")
    testsuite.set('id', timestamp)
    testsuite.set('name', "functional")
    
    suite_model = {}
    suite_model['id'] = timestamp
    suite_model['name'] = 'Functional'
    suite_model['tests'] = []
    results_model = {}
    results_model['testsuites'] = {}
    results_model['testsuites']['suites'] = []
    if is_regression:
        results_model['testsuites']['name'] = snapshot + " '" + regression_name + "' regression"
    else:
        results_model['testsuites']['name'] = snapshot
    results_model['testsuites']['timestamp'] = timestamp
    results_model['testsuites']['suites'].append(suite_model)
    
    common.dbg(f"Parsing results for '{snapshot}'")
    try:
        if snapshot in cfg.job_history:
            if 'simulation' in cfg.job_history[snapshot]:
                for sim in cfg.job_history[snapshot]['simulation']:
                    common.dbg("sim job history entry:\n" + str(sim))
                    if sim['type'] == "end":
                        if is_regression:
                            if not sim['is_regression']:
                                continue
                            if not sim["regression_name"] == regression_name:
                                continue
                            if not sim["regression_timestamp"] == regression_timestamp:
                                continue
                        
                        sim_log_path = sim['log_path']
                        
                        start = datetime.strptime(sim['timestamp_start'], "%Y/%m/%d-%H:%M:%S")
                        end   = datetime.strptime(sim['timestamp_end'  ], "%Y/%m/%d-%H:%M:%S")
                        duration = end - start
                        duration = divmod(duration.seconds, 60)[1]
                        total_duration = total_duration + duration
                        
                        testcase = ET.SubElement(testsuite, "testcase")
                        testcase.set('id', snapshot + "." + sim['test_name'])
                        testcase.set('name', sim['test_name'])
                        testcase.set('time', str(duration))
                        testcase.set('seed', str(sim['seed']))
                        
                        testcase_model = {}
                        suite_model['tests'].append(testcase_model)
                        testcase_model['name'] = sim['test_name']
                        testcase_model['seed'] = sim['seed']
                        testcase_model['time'] = duration
                        testcase_model['index'] = test_count
                        
                        args = ET.SubElement(testcase, "args")
                        testcase_model['args'] = []
                        if sim['args'] != None:
                            for arg in sim['args']:
                                arg_e = ET.SubElement(args, "arg")
                                arg_e.text = arg
                                testcase_model['args'].append(arg)
                        
                        passed = parse_sim_results(sim_log_path, testcase, testcase_model)
                        if passed == "failed" or passed == "inconclusive":
                            failure_count = failure_count + 1
                            testcase_model['passed'] = False
                        else:
                            testcase_model['passed'] = True
                        test_count = test_count + 1
    except Exception as e:
        common.fatal("Failed to parse history log: " + str(e))
    testsuites.set('tests', str(test_count))
    testsuites.set('failures', str(failure_count))
    testsuites.set('time', str(total_duration))
    testsuite.set('tests', str(test_count))
    testsuite.set('failures', str(failure_count))
    testsuite.set('time', str(total_duration))
    tree = ET.ElementTree(testsuites)
    if is_regression:
        xml_file_path = cfg.regr_results_dir + "/" + ip.name + "_" + regression_name + "/" + regression_timestamp + "/" + filename + ".xml"
    else:
        xml_file_path = cfg.sim_dir + "/" + filename + ".xml"
    tree.write(xml_file_path)
    common.dbg(f"Wrote {xml_file_path}")
    
    suite_model['num_tests'] = test_count
    if test_count == 0:
        common.fatal("Did not find any simulation results to parse")
    
    suite_model['failures'] = failure_count
    suite_model['passing'] = test_count - failure_count
    suite_model['time'] = total_duration
    results_model['testsuites']['failures'] = failure_count
    if failure_count > 0:
        results_model['testsuites']['passed'] = False
    else:
        results_model['testsuites']['passed'] = True
    fin = open(html_report_template_path, "r")
    template_data = fin.read()
    html_report_template = Template(template_data)
    html_report_contents = html_report_template.render(testsuites=results_model['testsuites'])
    
    try:
        if is_regression:
            html_file_path = cfg.regr_results_dir + "/" + ip.name + "_" + regression_name + "/" + regression_timestamp + "/" + filename + ".html"
        else:
            html_file_path = cfg.sim_dir + "/" + filename + ".html"
        with open(html_file_path,'w') as htmlfile:
            htmlfile.write(html_report_contents)
        htmlfile.close()
        common.dbg(f"Wrote {html_file_path}")
    except Exception as e:
        common.fatal("Failed to write html report to disk:" + str(e))
    
    results_obj = RegressionResults(results_model['testsuites']['passed'], total_duration, failure_count, suite_model['passing'], html_file_path, xml_file_path)
    return results_obj


def parse_sim_results(sim_log_path, testcase, testcase_model):
    test_result = "passed"
    num_warnings=0
    num_errors = 0
    num_fatals=0
    for i, line in enumerate(open(sim_log_path)):
        matches = re.search(uvm_warning_regex, line)
        if matches:
            num_warnings = num_warnings + 1
        matches = re.search(uvm_error_regex, line)
        if matches:
            failure = ET.SubElement(testcase, "failure")
            failure.set("message", line)
            failure.set("type", "ERROR")
            test_result = "failed"
            num_errors = num_errors + 1
        matches = re.search(uvm_fatal_regex, line)
        if matches:
            failure = ET.SubElement(testcase, "failure")
            failure.set("message", line)
            failure.set("type", "FATAL")
            test_result = "failed"
            num_fatals = num_errors + 1
        matches = re.search(viv_fatal_error, line)
        if matches:
            failure = ET.SubElement(testcase, "failure")
            failure.set("message", line)
            failure.set("type", "FATAL")
            test_result = "failed"
            num_fatals = num_errors + 1
        
    
    testcase.set("warnings", str(num_warnings))
    testcase.set("errors", str(num_errors))
    testcase.set("fatals", str(num_fatals))
    testcase_model['num_warnings'] = num_warnings
    testcase_model['num_errors'] = num_errors
    testcase_model['num_fatals'] = num_fatals
    testcase_model['conclusion'] = test_result
    return test_result
