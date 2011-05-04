import glob
import sys
import os
import time
from shutil import copytree
from subprocess import call
from xml.dom.minidom import parse
import re
import logging
 
def java_only(path, names):
                print "In path ", path
                return [file for file in names if not os.path.isdir(path + '/' + file) and not file.endswith('.java')]
 
def copy_java_tree(path, dest):
                copytree(path, dest, ignore=java_only)
 
def run_checkstyle(source_dir, output_file):
                try:
                                retcode = call('java -jar checkstyle-5.3-all.jar -f xml -c metrics.xml -o ' + output_file + ' -r ' + source_dir, shell=True)
                                if retcode < 0:
                                                print >>sys.stderr, "Child was terminated by signal", -retcode
                                else:
                                                print >>sys.stderr, "Child returned", retcode
                except OSError, e:
                                print >>sys.stderr, "Execution failed:", e
 
def toxicity_score(actual, allowed):
                return float(actual) / float(allowed)
               
CHECKSTYLE_RULES = {
                "Method Length": r"Method length is (\d+) lines \(max allowed is (\d+)\).",
                "Class Data Abstraction Coupling": r"Class Data Abstraction Coupling is (\d+) \(max allowed is (\d+)\)",
                "Class Fan-Out Complexity": r"Class Fan-Out Complexity is (\d+) \(max allowed is (\d+)\)",
                "Cyclomatic Complexity": r"Cyclomatic Complexity is (\d+) \(max allowed is (\d+)\)",
                "Anonymous inner class length": r"Anonymous inner class length is (\d+) lines \(max allowed is (\d+)\)",
                "Nested if-else depth": r"Nested if-else depth is (\d+) \(max allowed is (\d+)\)",
                "Boolean expression complexity": r"Boolean expression complexity is (\d+) \(max allowed is (\d+)\)",
                "File length": r"File length is (\d+) lines \(max allowed is (\d+)\)", # - tricky - does date formatting for thounsands
}
               
# Returns a pair of rule_name, score
def score_of_violation(msg):
                # Two cases we cannot handle out of the box (without adding custom Checkstyle handlers):
                # Parameter length - does not report the actual params
                # switch statement without a default clause - perhaps just sum the occcurances?
               
                for rule in CHECKSTYLE_RULES.items():
                                match = re.match(rule[1], msg)
                                if match:
                                                return (rule[0], toxicity_score(match.group(1), match.group(2)))
                                               
                logging.warning("Unknown violation type " + msg)
                return ("Unknown", 1.0)
 
def main(argv):
                timestamp = str(time.time())
                temp_dir = 'c:/temp/glp-analysis-' + timestamp
                checktyle_output = 'analysis' + timestamp + '.xml'
               
                #Needed because checkstyle 5.3 picks up non-java files when invoked from the command-line
                #copy_java_tree('c:/GLPWorkspace/glp_workspace/ITT/mainline/CLP', temp_dir)
                #run_checkstyle(source_dir, checktyle_output)
               
                dom = parse('analysis1290598710.22.xml')
                violators = []
                for file in dom.getElementsByTagName('file'):
                                errors = file.getElementsByTagName('error')
                               
                                if len(errors) > 0:
                                                scores = {}
                                                #Need to convert to maps to pull into a table..
                                                scores = map(lambda error:  score_of_violation(error.getAttribute('message')), errors)
                                                print "Scores for ", file.getAttribute("name"), scores
 
                for violator in violators:
                                print(violator)
               
if __name__ == "__main__":
    main(sys.argv[1:])
