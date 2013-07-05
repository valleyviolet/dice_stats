#!/usr/bin/env python
"""
The purpose of this program is to generate simple statistics from files
containing dice roll data.

Copyright Eva Schiffer 2013

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import re
import sys

from optparse import OptionParser
from glob     import iglob

import numpy as numpy
from scipy.stats import chisquare

def _read_die_file (file_path) :
    """ load roll information from a file
    given a file containing roll information for a die,
    load the file and bin the rolls
    
    returns a string with basic dice description info and a
    dictionary keyed on the rolls (the value is the number of
    times it was rolled)
    """
    
    die_desc   = ""
    die_rolls  = { }
    
    file_temp  = open(file_path, 'r')
    first_line = True
    
    for line in file_temp :
        if first_line :
            die_desc   = line
            first_line = False
        else :
            line = int(line)
            # this has the flaw that if a number is never rolled it won't be
            # present in the dictionary at all... FUTURE, fix this edge case
            die_rolls[line] = die_rolls[line] + 1 if line in die_rolls else 1
    
    return die_desc, die_rolls

def _sort_all_apropriate_files (path, type_suffix_str=".txt") :
    """given a path, get a list of files at that path with acceptable suffixes
    
    if path is a directory all files in the directory will be examined
    if a glob pattern is given all files matching that pattern will be
    considered as possible candidates
    
    return a list of all acceptable file paths
    """
    
    path = os.path.abspath(path)
    
    file_paths = [ ]
    
    # if this is a directory, we need to look at everything in it
    if os.path.isdir(path) :
        path = os.path.join(path, "*" + type_suffix_str)
    
    # look through all the possible paths and find acceptable ones
    for poss_path in iglob(path) :
        if ((os.path.isfile(poss_path) and
            (os.path.splitext(poss_path)[-1] == type_suffix_str))) :
            #print ("path is acceptable")
            file_paths.append(poss_path)
        else :
            #print ("path rejected; will not be used")
            pass
    
    return file_paths

def _calculate_chi_squared (desc_rolls_tuples) :
    """
    given tuples with the description of the die and the observed rolls,
    calculate the chi squared values and make them into a dictionary
    indexed on the descriptions
    
    return a result dictionary where result[desc_string] = (chi_sq_stat, p_value)
    """
    
    results = { }
    
    for desc_str, obs_roll_array in desc_rolls_tuples :
        
        # we aren't providing expected values because we expect the sides
        # of the die to be rolled with equal frequency,
        # and that's the default for the scipy version of chi squared;
        # scipy's chi squared method also calculates the degrees of
        # freedom based on the length of our array, which works in this case
        chi_sq_stat, p_value = chisquare(numpy.array(obs_roll_array))
        results[desc_str]    = (chi_sq_stat, p_value)
    
    return results

def main () :
    usage = """
%prog [options] 
run "%prog help" to list commands
examples:

python -m dice_stats basic  -i ./path/to/filename.txt
python -m dice_stats chi_sq -i ./path/to/filename.txt

"""
    
    parser = OptionParser()
    
    parser.add_option("-i", "--input", default="./*.txt",
                      dest="input", 
                      help="the file(s) to analyze; " +
                           "if a directory is given all .txt " +
                           "files in that directory will be opened")
    parser.add_option("-o", "--outDir", default="./out",
                      dest="outDirectory", 
                      help="the directory where output text stats " +
                      "and images should go (TODO, program doesn't produce output to files yet)")
    parser.add_option('-v', '--version', dest='version',
                      action="store_true", default=False, help="display the program version")
    
    (options, args) = parser.parse_args()
    
    # display the version
    if options.version :
        # a super budget way to handle this, but having a version history is cool!
        print ("dice_stats v.0.1 \n")

    # set up the commands dictionary
    commands = {}
    prior = None
    prior = dict(locals())
    
    
    def basic ( ) :
        """ show basic analysis of the dice data
        
        basic analysis loads die roll data and displays simple
        textual information about the rolls, including overall
        counts, average value rolled, and a crappy ASCII histogram.
        """
        
        die_file_paths = _sort_all_apropriate_files(options.input)
        
        for die_file_path in die_file_paths :
            
            print
            #print ("loading die information from file: " + die_file_path)
            die_description, die_roll_dict = _read_die_file (die_file_path)
            
            print ("data for die with description: " + die_description.strip())
            
            print 
            
            print ("raw roll data:")
            for roll_value in sorted(die_roll_dict.keys()) :
                print ("rolled \t" + str(roll_value) + "\t on the die \t"
                       + str(die_roll_dict[roll_value]) + "\t time(s)")
            
            print 
            
            print ("simple roll histogram:")
            for roll_value in sorted(die_roll_dict.keys()) :
                bar_text = "*" * die_roll_dict[roll_value]
                print (str(roll_value) + "\t" + bar_text)
                
            print 
            
            side_val   = numpy.array(die_roll_dict.keys( ),   dtype=numpy.float)
            rolls      = numpy.array(die_roll_dict.values( ), dtype=numpy.float)
            num_rolls  = float(numpy.sum(rolls))
            avg_result = numpy.sum(rolls * side_val) / num_rolls
            
            print ("average roll: " + str(avg_result))
            
            print ("------------")
            
    
    def chi_sq ( ) :
        """ run a chi squared analysis of a die's rolls
        
        the chi squared analysis runs a standard chi squared
        analysis on each die file separately, comparing the
        die's rolls to an expected result of a perfectly fair die
        """
        
        # get the list of all files
        die_file_paths = _sort_all_apropriate_files(options.input)
        temp_tuples    = [ ]
        
        # open the files and arrange the info into tuples
        for die_file_path in die_file_paths :
            
            #print
            #print ("loading die information from file: " + die_file_path)
            die_description, die_roll_dict = _read_die_file (die_file_path)
            temp_tuples.append((die_description, die_roll_dict.values()))
        
        # analyze the info from each file with a chi squared test
        chi_sq_results = _calculate_chi_squared(temp_tuples)
        
        # display the results
        print ("-----")
        for desc_text in sorted(chi_sq_results.keys()) :
            
            (chi_sq_stat, p_value) = chi_sq_results[desc_text]
            print ("analysis of die:  " + desc_text.strip())
            print ("chi squared stat: " + str(chi_sq_stat))
            print ("p value:          " + str(p_value))
            print ("-----")
    
    def help(command=None):
        """print help for a specific command or list of commands
        e.g. help swap
        """
        if command is None: 
            # print first line of docstring
            for cmd in commands:
                ds = commands[cmd].__doc__.split('\n')[0]
                print "%-16s %s" % (cmd,ds)
        else:
            print commands[command].__doc__
    
    # all the local public functions are included, collect them up
    commands.update(dict(x for x in locals().items() if x[0] not in prior))    
    
    # if what the user asked for is not one of our existing functions, print the help
    if (not args) or (args[0] not in commands): 
        parser.print_help()
        help()
        return 1
    else:
        # call the function the user named, given the arguments from the command line  
        locals()[args[0]](*args[1:])

    return 0

if __name__ == "__main__":
    main()