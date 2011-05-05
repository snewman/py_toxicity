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
                    cmd = 'java -jar checkstyle-all-4.4.jar -f xml -c metrics.xml -o ' + output_file + ' -r ' + source_dir
                    print "Running ", cmd
                    retcode = call(cmd, shell=True)
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
                                                return toxicity_score(match.group(1), match.group(2))
                                               
                logging.warning("Unknown violation type " + msg)
                return 0.0

def name_of_violation(msg):
    for rule in CHECKSTYLE_RULES.items():
         match = re.match(rule[1], msg)
         if match:
             return rule[0]

    return "Unknown"
                                    
def main(argv):
                timestamp = str(time.time())
                checkstyle_output = 'analysis' + timestamp + '.xml'
                src_dir = argv[0]
               
                #Needed because checkstyle 5.3 picks up non-java files when invoked from the command-line
                #copy_java_tree(src_dir, temp_dir)
                run_checkstyle(src_dir, checkstyle_output)
               
                dom = parse(checkstyle_output)
                violations = set()
                file_scores = {}
                
                for file in dom.getElementsByTagName('file'):
                    errors = file.getElementsByTagName('error')
                               
                    if len(errors) > 0:
                        #Need to convert to maps to pull into a table...
                        file = file.getAttribute("name")

                        for error in errors:
                            message = error.getAttribute('message')
                            score = score_of_violation(message)
                            violation = name_of_violation(message)
                            violations.add(violation)

                            if not file_scores.has_key(file):
                                file_scores[file] = {}

                            if file_scores[file].has_key(violation):
                                file_scores[file][violation] = file_scores[file][violation] + score
                            else:
                                file_scores[file][violation] = score
                            

                print "File name",violations
                
                for file, scores in file_scores.iteritems():
                    score_line = file
                    for violation in violations:
                      score_line = score_line + ',' + str(scores.get(violation, 0.0))
                        
                    print score_line
                    #    print file, ",", scores
               
if __name__ == "__main__":
    main(sys.argv[1:])
