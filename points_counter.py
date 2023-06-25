#!/usr/bin/env python3
'''

      Project: hiwi_ss23
         File: points_counter.py
 File Created: 08.05.2023
       Author: jangtze (yangntze+github@gmail.com)
-----
Last Modified: 18.06.2023 15:00:59
  Modified By: jangtze (yangntze+github@gmail.com)
-----
    Copyright: 2023 jangtze

'''

# https://stackoverflow.com/questions/27494758/how-do-i-make-a-python-script-executable

# calling the script 
# import shlex          # https://docs.python.org/3/library/__main__.html
# import getopt         # https://www.tutorialspoint.com/python/python_command_line_arguments.htm
# ... better with argparse

import os
import sys
import argparse         # https://docs.python.org/3/library/argparse.html # cmd line call
import textwrap         # https://docs.python.org/3/library/textwrap.html # for help text
import re               # main script part
import subprocess       # main script part

# TODO: use classes to bundle
# TODO: split by cells and process ipynb directly, put cell / linenumbers into dicts in the returned list of dicitonaries
# TODO: emplace points comment in file (option)
# TODO: change language to option not boolean flag (we can't have several languages)

#
# regex Versions
#
# regex = r"(?m)^.*?#\s*\+\s*\d+(\.\d+)?(\s*inoff\.\s*ZP)?\b.*?$"
# regex = r'^(.*# \+\s*\d+(\.\d+)?(?:\s*inoff\.\s*ZP)?)$'
# regex = r'^(.*# \+\s*\d+(?:\.\d+)?(?:\s*inoff\.\s*ZP)?)$'
# regex = r'^(.*#\s*\+\s*(\d+(?:\.\d+)?)?(\s*inoff\.\s*ZP)?)$'
# regex = r'^((.*)#\s*\+\s*(\d+(?:\.\d+)?)?(\s*inoff\.\s*ZP)?)$'

# rgx_lsg =   r'^(.*#\s*\+\s*(\d+(?:\.\d+)?)?(\s*inoff\.\s*ZP)?(?:.*)?)$'
# rgx_lsg =   r'^(.*?)#\s*\+\s*(\d+(?:\.\d+)?)?(\s*(?:inoff\.?)?\s*ZP)?(?:.*)?$'

# rgx_pts =   r'^(.*#\s*\+\s*([\+\-]?\d+(?:\.\d+)?)?(\s*(?:inoff\.)?\s*ZP)?(?:.*)?)$'
# rgx_pts =   r'^(.*((?:#\s*[\+\-]+)\d+(?:\.\d+)?)(\s*(?:inoff\.)?\s*ZP)?(?:.*)?)$'

# rgx_sht = r'^.*(\d+).\s*Uebungsblatt,\s*Aufgabe\s*(\d+)*.*#\n#\s*\((\d+)\s*Pkt\.\)'
# rgx_sht = r'^.*(\d+).\s*Uebungsblatt,\s*(?:freiw\.?)?\s*Aufgabe\s*(\d+)*.*#\n#\s*\((\d+)\s*Pkt\.?(?:.*?(\d+)\s*Zusatzpkt\.?)?\)'

#
# global regexs to find stuff
#
# TODO: named captures may improve generality and expandability of regex later
line_of_code        = r'^(.*?)'
py_comment          = r'#'
cpp_comment         = r'//'
lsg_point_comment   = r' *\+ *(\d+(?:\.\d+)?)?(\s*(?:inoff\.?)?\s*ZP)?(.*)?(?=\n)$'
cor_point_comment   = r' *!!! *([\+\-]+\d+(?:\.\d+)?)?(\s*(?:inoff\.?)?\s*ZP)?(.*)?(?=\n)$'

# py / ipynb
rgx_lsg     = line_of_code + py_comment + lsg_point_comment # points in the solutions
rgx_pts     = line_of_code + py_comment + cor_point_comment # points in submission added or substracted
rgx_sht     = r'^.*(?P<sheet>\d+).\s*Uebungsblatt,\s*(?:freiw\.?)?\s*Aufgabe\s*(?P<exercise>\d+ ?(?:[a-zA-Z])?\)?) *#\n#\s*(?:\d\.\s*Vorgabe[A-Za-z#.,:\s\n]*)?(?:\(?(?P<points>\d+(?=\s*Pkt|\s*Punkte))\s*(?:Pkt\.|Punkte)?)?\)?(?:(?:.*?)(?P<bonus>\d+(?=.*Zu))\s*(?:Zusatzpkt\.?|Zusatzpunkte)?)?\)?'
# before sheet 03:
# ^.*(?P<sheet>\d+).\s*Uebungsblatt,\s*(?:freiw\.?)?\s*Aufgabe\s*(?P<exercise>\d+ ?(?:[a-zA-Z])?\)?) *#\n#\s*(?:\d\.\s*Vorgabe[A-Za-z#.,:\s\n]*)?(?:\(?(?P<points>\d+)(?=\s*Pkt|\s*Punkte)\s*(?:Pkt\.?)?(?:Punkte)?\)?)?(?:.*?(?P<bonus>\d+)\s*Zusatzpkt\.?)?
# then ...
# ^.*(?P<sheet>\d+).\s*Uebungsblatt,\s*(?:freiw\.?)?\s*Aufgabe\s*(?P<exercise>\d+ ?(?:[a-zA-Z])?\)?) *#\n#\s*(?:\d\.\s*Vorgabe[A-Za-z#.,:\s\n]*)?(?:\(?(?P<points>\d+)(?=\s*Pkt|\s*Punkte)\s*(?:Pkt\.?)?(?:Punkte)?)?(?:.*?)?(?:(?P<bonus>\d+)\s*(?:.*?Zusatzpkt\.?.*?|.*?Zusatzpunkte.*?)?)\)?
# ^.*(?P<sheet>\d+).\s*Uebungsblatt,\s*(?:freiw\.?)?\s*Aufgabe\s*(?P<exercise>\d+ ?(?:[a-zA-Z])?\)?) *#\n#\s*(?:\d\.\s*Vorgabe[A-Za-z#.,:\s\n]*)?(?:\(?(?P<points>\d+)(?=\s*Pkt|\s*Punkte)\s*(?:Pkt\.|Punkte)?)?\)?(?:.*?)?(?:(?P<bonus>\d+)\s*(?:.*?Zusatzpkt\.??.*?|.*?Zusatzpunkte.*?)?)?\)?
# ^.*(?P<sheet>\d+).\s*Uebungsblatt,\s*(?:freiw\.?)?\s*Aufgabe\s*(?P<exercise>\d+ ?(?:[a-zA-Z])?\)?) *#\n#\s*(?:\d\.\s*Vorgabe[A-Za-z#.,:\s\n]*)?(?:\(?(?P<points>\d+)\s*(?:Pkt\.|Punkte)?)?\)?(?:.*?)(?:(?P<bonus>\d+)\s*(?:Zusatzpkt\.?|Zusatzpunkte)?)\)?
# ^.*(?P<sheet>\d+).\s*Uebungsblatt,\s*(?:freiw\.?)?\s*Aufgabe\s*(?P<exercise>\d+ ?(?:[a-zA-Z])?\)?) *#\n#\s*(?:\d\.\s*Vorgabe[A-Za-z#.,:\s\n]*)?(?:\(?(?P<points>\d+(?=\s*Pkt|\s*Punkte))\s*(?:Pkt\.|Punkte)?)?\)?(?:(?:.*?)(?P<bonus>\d+(?=.*Zu))\s*(?:Zusatzpkt\.?|Zusatzpunkte)?)?\)?

# cpp
rgx_lsg_cpp = line_of_code + re.escape(cpp_comment) + lsg_point_comment # points in the solutions
rgx_pts_cpp = line_of_code + re.escape(cpp_comment) + cor_point_comment # points in submission added or substracted
rgx_sht_cpp = r'^\/\*[\s]*(?:insges\.)? (?:\(?(?P<points>\d+)\s*(?:Pkt\.?)?(?:Punkte)?\)?)?(?:.*?(?P<bonus>\d+)\s*(Zusatzpkt\.?|inoff\.? ZP))?'

rgx_lsg_can_find = """
from sympy import diff, symbols         # +1
a, b, x = symbols("a b x")              # -0.5 some comment
# sympy.core.function.diff(..)          # +1 inoff. ZP
sympy.core.function.diff(..)            # -0.2 inoff ZP comment
"""

rgx_pts_can_find="""
from sympy import diff, symbols         # !!! +1
a, b, x = symbols("a b x")              # !!! -0.5 some comment
# sympy.core.function.diff(..)          # !!! +1 inoff. ZP
sympy.core.function.diff(..)            # !!! -0.2 inoff ZP comment
"""

rgx_sht_can_find = """
#########################################
#   Mathematik am Computer (SoSe 2023)  #
#                                       #
#  2. Uebungsblatt, freiw. Aufgabe 04   #
#        (21 Pkt., 13 Zusatzpkt.)       #
#     Abgabetermin: vgl. eLearning      #
#                                       #
#########################################
"""

# file_name = "Lsg_01.ipynb" 
# ... currently unsupported
# -> would need processing of the cells 
# -> they come in lists of line_strs starting and ending with quotes""
# -> would give the advantage of having cell numbers where something happened

def get_py_code(ipynb_file : str) -> str:
    # https://stackoverflow.com/questions/37797709/convert-json-ipython-notebook-ipynb-to-py-file
    # jupyter nbconvert --to script 'my-notebook.ipynb'

    # does this allow for wrap_text: 80 instead of 100 default?
    # jupyter nbconvert --PythonExporter.filters.wrap_text=80  --to script ./solutions/Lsg_01.ipynb

    # https://stackoverflow.com/questions/41171791/how-to-suppress-or-capture-the-output-of-subprocess-run
    # a = subprocess.run("jupyter nbconvert --stdout --to script './solutions/Lsg_02.ipynb'", shell=True, capture_output=True, text=True)
    
    ipynb_file = "\'" + ipynb_file + "\'"
    # cmd_lst = ['jupyter', 'nbconvert', '--stdout', '--to script', ipynb_file]
    # cmd_lst = ['bash']
    # cmd_lst = ['bash', '-c', '"jupyter', 'nbconvert', '--stdout', '--to script', ipynb_file, '"']
    cmd_lst = ['bash', '-c -l', '"jupyter', 'nbconvert', '--stdout', '--to script', ipynb_file, '"']
    # -c -l needed for vscode build task
    # cmd = 'bash -c \"jupyter nbconvert --stdout --to script {filename}\"'.format(filename=ipynb_file)
    cmd = ' '.join(cmd_lst)
    
    print(
        "Executing:\n" 
        + cmd 
        # + "\n"
    )
    a = subprocess.run(
        cmd, 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.DEVNULL, # get rid of "I want IPython, even though it works without"
        text=True
    )
    
    # print(a)

    if a.stdout == '':
        print('Error: Got no text from jupyter nbconvert!')

    return a.stdout

def get_sheet_data(text : str, regex : str = rgx_sht) -> list:
    cmpldrgx=re.compile(regex, re.MULTILINE)
    res = re.findall(cmpldrgx, text)
    
    # print(res, cmpldrgx.groups, cmpldrgx.pattern, cmpldrgx.groupindex)

    sheet_data_dict = {
        'sheet'     : 0,
        'exercise'  : 'N/A',
        'points'    : 0.0,
        'bonus'     : 0.0
    }

    # former way by indices 
    # -> now checking by type and placing with key 
    # -> checking key would be better ... is better if empty match checked
    # {
    #     'sheet'     : int(res[0][0]) if res[0][0] != '' else 0,
    #     'exercise'  : str.strip(res[0][1]),
    #     'points'    : int(res[0][2]) if res[0][2] != '' else 0,
    #     'bonus'     : int(res[0][3]) if res[0][3] != '' else 0
    #     }
    if len(res) == 0:
        return sheet_data_dict
    
    for key in cmpldrgx.groupindex.keys():
        # print(
        #     key,
        #     cmpldrgx.groupindex[key]-1,
        #     res[0][cmpldrgx.groupindex[key]-1]
        #     )
        # who programmed this ?!? index not from 0 
        # ... maybe they had capture of everything in 0 once?

        m = res[0][cmpldrgx.groupindex[key]-1]

        # https://stackoverflow.com/questions/354038/how-do-i-check-if-a-string-represents-a-number-float-or-int
        # if m.replace('-','',1).isdigit() :
        #     m = int(m)
        # elif m.replace('.','',1).replace('-','',1).isdigit():
        #     m = float(m)
        # elif m.strip() == '':
        #     continue
        # else:
        #     m = m.strip()

        if m == '':
            continue

        if key=='sheet' :
            m = int(m)
        elif key=='points' or key=='bonus':
            m = float(m)
        elif key=='exercise':
            m = m.strip()
        else:
            pass
            
        sheet_data_dict.update([(
            key, 
            m
            )])
    
    # print(sheet_data_dict)

    return sheet_data_dict

def remarks_finder(text : str, regex : str = rgx_lsg) -> list:

    # TODO: split by cells and process ipynb directly, put cell / linenumbers into 
    # dicts in the returned list of dicitonaries maybe call this finder for each cell and handle cells outside

    # print(text)
    # print()

    # res = re.findall(regex, text, re.MULTILINE)
    # print(res)
    # print(res[0][1].strip(), sep='\n\n')
    # print(*[(match[0], match[1].strip(), match[2], bool(match[3])) for match in res], sep='\n\n')

    # https://stackoverflow.com/questions/16673778/python-regex-match-in-multiline-but-still-want-to-get-the-line-number
    end='.*\n'
    line_num=[]
    for m in re.finditer(end, text):
        line_num.append(m.end())

    # cmpldrgx=re.compile(regex, re.MULTILINE|re.DOTALL)
    cmpldrgx=re.compile(regex, re.MULTILINE)

    if re.search(cmpldrgx, text) is None:
        print("Error: no matches for remarks!")
        return []
    
    matches = re.finditer(cmpldrgx, text)

    res_dict_lst = []
    # # [dict()]*len(matches) # consumes matches generator
    for m in matches:
        line_str    = m.group(0)
        code_str    = m.group(1).strip()
        cmmt_str    = m.group(4).strip()
        try:
            points  = float(m.group(2))
        except(TypeError):
            points  = 0
        zp_val      = m.group(3)
        zp_bool     = isinstance(zp_val, str) and 'ZP' in zp_val
        zp_secret   = isinstance(zp_val, str) and 'ZP' in zp_val and "inoff" in zp_val

        res_dict_lst.append(dict({
            'pos'       : next(i+1 for i in range(len(line_num)) if line_num[i]>m.start(0)) , 
            'match'     : m , 
            'points'    : points , 
            'bonus'     : zp_bool , 
            'secret'    : zp_secret , 
            'bonus_str' : zp_val,
            'code'      : code_str , 
            'comment'   : cmmt_str , 
            'line'      : line_str
        }))
    
    # # debugging
    # reslst = list(matches)
    # for match in reslst:
    #     # print(
    #     #     'linenum: %d, %s' %(
    #     #         next( i for i in range(len(line)) if line[i]>m.start(1) ), 
    #     #         m.group(1)
    #     #     ))
    #     line_str    = match.group(0)
    #     code_str    = match.group(1).strip()
    #     points      = float(match.group(2))
    #     zp_val      = match.group(3)
    #     zp_bool     = isinstance(zp_val, str) and "ZP" in zp_val
    #     # zp_str      = "ZP" if zp_bool else ""
    #     comment     = match.group(4)

    #     print(
    #             line_str,           ",\t",
    #             code_str,           ",\t",
    #             points,             ",\t",
    #             zp_val,             ",\t",
    #             comment,            "\n"
    #     )
        # if zp_bool:
        #     bonusp_sum += float(points)
        # else:
        #     point_sum += float(points)

    # print(
    #     "Punkte: {0:3}, Bonuspunkte: {1:3}".format(point_sum, bonusp_sum)
    # )

    # print("Found {0} entries".format(num_mtc))
    return res_dict_lst

def get_points(match_dict_lst : list) -> dict:

    point_sum = 0
    bonusp_sum = 0
    secret_sum = 0

    for match_dct in match_dict_lst:
        if match_dct['bonus'] :
            if match_dct['secret'] :
                secret_sum += match_dct['points']
            else:
                # print('bonus')
                # print(bonusp_sum, match_dct['points'])
                bonusp_sum += match_dct['points']
                # print(bonusp_sum )
        else:
            point_sum += match_dct['points']

    res = {}
    res.update({
        'point_sum'     : point_sum, 
        'bonus_sum'     : bonusp_sum, 
        'inoff_sum'     : secret_sum
        })
    return res

def print_found_remarks(match_dict_lst : list, comment_symbol=py_comment):

    # TODO: add functionality for cell number with line-number (inside cell)

    for match_dct in match_dict_lst:
        # print(
        #         match_dct['pos'], 
        #         match_dct['code'] if match_dct['code'] != '' else match_dct['comment'],
        #         # match_dct['code'] if match_dct['code']
        #         # match_dct['code'] if match_dct['code'] != '' else '#' + match_dct['comment'] \
        #         # if '#' not in match_dct['code'] else match_dct['line'],
        #         match_dct['points'],
        #         "ZP" if match_dct['bonus'] else ""
        #     )
                # comment_symbol + match_dct['comment'] if match_dct['code'] == '' else match_dct['line'] if ((comment_symbol+' ') in match_dct['code']) else match_dct['code'],
                # match_dct['points'],

        # print(match_dct['code'], '|', match_dct['comment'])

        info = ''
        bonus_str = "" if not match_dct['bonus'] else "ZP" if not match_dct['secret'] else "iZP"
        if (    match_dct['code']   == '' 
            or  comment_symbol      == match_dct['code'].strip() # if the 'code' isa a line with two comment symbols
            ) and not match_dct['comment'] == '':
            # points = '+' + str(match_dct['points']) if match_dct['points']>0 else str(match_dct['points']) + bonus_str
            info = (comment_symbol 
                    # + ' ' + points # do I want points with the comment string?
                    + ' ' + match_dct['comment'].strip()
                    )
        # elif match_dct['comment'] == '' and (comment_symbol+' ') in match_dct['code']:
        elif match_dct['comment'] == '' and not match_dct['code'] == '' and not match_dct['code'].startswith(comment_symbol):
            info = match_dct['code'].strip()
        else:
            info = match_dct['line'].strip()
        print(
            '{2: 2.1f} {3:>3} {0:>4}: {1:80} '.format(
                match_dct['pos'], 
                info,
                match_dct['points'],
                bonus_str
            )
        )

def print_found_total(match_dict_lst : list, is_sol=False):
    totals = get_points(match_dict_lst)
    print("Found points from remarks in this file:")
    if not is_sol:
        print(
            # "Punkte: {0:3}  \t Bonuspunkte (ZP): {1:2}".format(totals['point_sum'], totals['bonus_sum'])
            "Points:  {0:3.1f}  \t Bonus Points (ZP):  {1:2.1f}".format(totals['point_sum'], totals['bonus_sum']+totals['inoff_sum'])
        )
    else:
        print(
            # "Punkte: {0:3}  \t Bonuspunkte (ZP): {1:2}".format(totals['point_sum'], totals['bonus_sum'])
            "Points:  {0:3.1f}  \t Bonus Points (ZP):  {1:2.1f} \t Secret Bonus (inoff. ZP):  {2:2.1f}".format(totals['point_sum'], totals['bonus_sum'], totals['inoff_sum'])
        )


def print_sheet_data(sh_dat_dict : dict):
    if( sh_dat_dict['sheet'] == 0 and
        sh_dat_dict['exercise'] == 'N/A' and
        sh_dat_dict['points'] == 0.0 and
        sh_dat_dict['bonus'] == 0.0):
        return
    print('Extracted Sheet Data')
    # print('Blattdaten')
    print(
        # "Blatt \t {0:02d} \t Aufgabe \t  {1:>3} \nPunkte:\t {2:02d} \t Bonuspunkte (ZP): {3:2d}".format(
        "Sheet \t {0:02d} \t Exercise \t  {1:>6} \nPoints:\t {2:02.1f} \t Bonus Points (ZP):  {3:2.1f}".format(
        sh_dat_dict['sheet'], 
        sh_dat_dict['exercise'], 
        sh_dat_dict['points'],
        sh_dat_dict['bonus']
        )
    )

def prepare_argv_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='points_counter.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description= \
            textwrap.dedent("""\
            Points Counter (points_counter.py)
            ----------------------------------
            """) \
            + textwrap.indent(textwrap.dedent('''\
            This script was written to help finding corrections for a student job 
            at UBT SS2023. It allows to search for patterns in currently only 
            Python code (it will convert ipynb to py to do so). So this regex:\n
            '''), '  ') \
            + textwrap.indent(rgx_pts, "\t") \
            + textwrap.indent(textwrap.dedent("""\n
            should find commented lines and points as in the following examples:\n
            """), '  ') \
            + textwrap.indent(rgx_pts_can_find, "\t") \
            + textwrap.dedent("""\nHow to run:""")
            + textwrap.indent(textwrap.dedent("""\n
            (compare: https://stackoverflow.com/questions/27494758/how-do-i-make-a-python-script-executable)
            Make it executable by
                chmod +x ./points_counter.py
            optionally add it to the PATH
                export PATH=/path/to/script:$PATH
            and then call it as 
                points_counter.py filename
            """), '  '),
        epilog=textwrap.dedent("""\
            ... enjoy and give feedback to yangntze+ptscnt@gmail.com
            """)+" \n",
        # usage='%(prog)s [options]'
        )
    parser.add_argument(
        'filename', 
        # type=str,
        help='file to be processed'
        )
    parser.add_argument(
        '-l', '--solution', '--sol',
        default=False,
        action='store_true',
        # type=bool,
        # nargs='?',
        # const='True',
        help='Indicates whether or not a solution is scanned.'
    )
    parser.add_argument(
        '-c', '--cplusplus', '--cpp', '--c++',
        default=False,
        action='store_true',
        help='Flag that indicates whether or not a cpp-file is scanned.'
    )
    parser.add_argument(
        '-j', '--jupyternotebook', '--ipynb', '--jupyter',
        default=True,
        action='store_true',
        help='Flag that indicates whether or not a JupyterNotebook-file is scanned.'
    )

    return parser

def check_file(args : argparse.Namespace) -> bool:

    # print(file_name_noext, " is a file: ", is_file, sep='')
    # print("*", file_type, " is a notebook: ", is_ipynb, sep='')
    # print(file_name)
    # print(base_path)
    # print(file_full_path)

    is_file         = os.path.isfile(args.filename)
    if(not is_file):
        print("Error: not a file!")
        return False

    file_endings    = ('.txt', '.ipynb', '.cpp', '.hpp', '.h', '.c' )
    is_format       = args.filename.endswith(file_endings)
    if not is_format:
        print("Error: Currently only files of type ", file_endings ," are supported!")
        return False
    
    return True

def process_ipynb(args : argparse.Namespace, verbose : bool =True) -> list:

    file_full_path  = os.path.abspath(args.filename)
    file_name       = os.path.basename(args.filename)
    # base_path       = os.path.dirname(file_full_path)
    file_name_noext = os.path.splitext(file_name)[0]
    # file_type       = os.path.splitext(file_name)[1]
    # is_file         = os.path.isfile(args.filename)

    # TODO: split by cells and process ipynb directly, put cell / linenumbers into dicts in the returned list of dicitonaries
    text = get_py_code(file_full_path)
    if verbose:
        print(" ---"*20)

    if args.solution == True:
        rg_found = remarks_finder(text, regex = rgx_lsg)
        if verbose:
            print(text[50:384])
            # print("\n\tSolution:")
    else:
        rg_found = remarks_finder(text, regex = rgx_pts)

    print_found_remarks(rg_found)
    print(file_name_noext)
    print_sheet_data(get_sheet_data(text))
    print_found_total(rg_found, is_sol=args.solution)

    return rg_found

def process_cpp(args : argparse.Namespace) -> list:

    file_full_path  = os.path.abspath(args.filename)
    file_name       = os.path.basename(args.filename)
    # base_path       = os.path.dirname(file_full_path)
    file_name_noext = os.path.splitext(file_name)[0]
    # file_type       = os.path.splitext(file_name)[1]
    # is_file         = os.path.isfile(args.filename)
    
    # text = ''
    with open(file=file_full_path,  mode="r") as f:
        text = f.read()
    print(" ---"*20)

    if args.solution == True:
        rg_found = remarks_finder(text, regex =rgx_lsg_cpp)
    else:
        rg_found = remarks_finder(text, regex =rgx_pts_cpp)

    print_found_remarks(rg_found, comment_symbol=cpp_comment)
    print(file_name_noext)
    print_sheet_data(get_sheet_data(text, regex=rgx_sht_cpp))
    print_found_total(rg_found, is_sol=args.solution)
        
    return rg_found



# https://docs.python.org/3/library/__main__.html
def main():
    # print('sys.argv: \t', sys.argv)
    print(
        'script:',
        '\n    filename: ',   os.path.basename(os.path.realpath(__file__)),
        '\n    location: ',   os.path.dirname(os.path.realpath(__file__)),
        '\n     calldir: ',   os.getcwd(),
        )

    parser = prepare_argv_parser()
    args = 0
    # https://stackoverflow.com/questions/4042452/display-help-message-with-python-argparse-when-script-is-called-without-any-argu
    try:
        # print("try")
        args = parser.parse_args()
    except SystemExit as err:
        if err.code == 2:
            # unknown argument or filename
            parser.error('... exiting')

    except:
        # other errors
        # print("except")
        # parser.print_help()
        # parser.print_usage()
        # print(parser._get_positional_kwargs())
        parser.error('... exiting')

    # debug
    # print(args)

    if not check_file(args):
        parser.print_help()
        return 1

    if args.jupyternotebook == True and args.cplusplus == False:
        rg_found = process_ipynb(args)

    if args.cplusplus == True:
        rg_found = process_cpp(args)

    else:
        rg_found = []
        

    return 0

if __name__ == '__main__':
    sys.exit(main())