#!/usr/bin/env python3

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

# rgx_tot = r'^.*(\d+).\s*Uebungsblatt,\s*Aufgabe\s*(\d+)*.*#\n#\s*\((\d+)\s*Pkt\.\)'

#
# global regexs to find stuff
#
rgx_lsg =   r'^(.*?)# *\+ *(\d+(?:\.\d+)?)?(\s*(?:inoff\.?)?\s*ZP)?(.*)?(?=\n)$' # points in the solutions
rgx_pts =   r'^(.*?)# *!!! *([\+\-]+\d+(?:\.\d+)?)?(\s*(?:inoff\.?)?\s*ZP)?(.*)?(?=\n)$' # points in submission added or substracted
rgx_tot = r'^.*(\d+).\s*Uebungsblatt,\s*(?:freiw\.?)?\s*Aufgabe\s*(\d+)*.*#\n#\s*\((\d+)\s*Pkt\.?(?:.*?(\d+)\s*Zusatzpkt\.?)?\)'

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

rgx_tot_can_find = """
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

def get_py_code(ipynb_file):
    # https://stackoverflow.com/questions/37797709/convert-json-ipython-notebook-ipynb-to-py-file
    # jupyter nbconvert --to script 'my-notebook.ipynb'

    # does this allow for wrap_text: 80 instead of 100 default?
    # jupyter nbconvert --PythonExporter.filters.wrap_text=80  --to script ./solutions/Lsg_01.ipynb

    # https://stackoverflow.com/questions/89228/how-do-i-execute-a-program-or-call-a-system-command
    # subprocess.call("jupyter nbconvert --stdout --to script " + myfile, shell=True) # elder method

    # https://stackoverflow.com/questions/41171791/how-to-suppress-or-capture-the-output-of-subprocess-run
    # a = subprocess.run("jupyter nbconvert --stdout --to script './solutions/Lsg_02.ipynb'", shell=True, capture_output=True, text=True)
    
    # cmd1 = "jupyter nbconvert --stdout --to script '{filename}'".format(filename=ipynb_file)
    # a = subprocess.run(cmd1, shell=True, stdout=subprocess.PIPE, text=True)

    ipynb_file = "\'" + ipynb_file + "\'"
    # cmd_lst = ['jupyter', 'nbconvert', '--stdout', '--to script', ipynb_file]
    # cmd_lst = ['bash']
    # cmd_lst = ['bash', '-c', '"jupyter', 'nbconvert', '--stdout', '--to script', ipynb_file, '"']
    cmd_lst = ['bash', '-c -l', '"jupyter', 'nbconvert', '--stdout', '--to script', ipynb_file, '"'] # -c -l needed for vscode build task
    # cmd = 'bash -c \"jupyter nbconvert --stdout --to script {filename}\"'.format(filename=ipynb_file)
    cmd = ' '.join(cmd_lst)
    
    # a = subprocess.run(' '.join(cmd_lst), shell=True)
    print("Executing:\n" + cmd + "\n\n")
    a = subprocess.run(
        cmd, 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.DEVNULL, # get rid of "I want IPython, even though it works without"
        text=True
    )
    return a.stdout

# with open(file=myfile,  mode="r") as f:
#     text = f.read()

# text = """from sympy import diff, symbols         # +1
# a, b, x = symbols("a b x")              # +0.5
# # sympy.core.function.diff(..)          # +1 inoff. ZP
# foo = bar + 2    # +2 inoff. ZP something else"""

def get_sheet_data(text : str, regex : str = rgx_tot) -> list:
    res = re.findall(regex, text, re.MULTILINE)
    # print(res)
    sheet_data_dict = {
        'sheet'     : int(res[0][0]),
        'exercise'  : int(res[0][1]),
        'points'    : int(res[0][2]),
        'bonus'     : int(res[0][3]) if res[0][3] != '' else 0
        }
    return sheet_data_dict

def points_finder(text : str, regex : str = rgx_lsg) -> list:

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
        print("Error: no matches!")
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

        res_dict_lst.append(dict({
            'pos' : next(i+1 for i in range(len(line_num)) if line_num[i]>m.start(0)) , 
            'match' : m , 
            'pts' : points , 
            'bonus' : zp_bool , 
            'code' : code_str , 
            'comment' : cmmt_str , 
            'line' : line_str
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
        #     points_sum += float(points)

    # print(
    #     "Punkte: {0:3}, Bonuspunkte: {1:3}".format(points_sum, bonusp_sum)
    # )

    # print("Found {0} entries".format(num_mtc))
    return res_dict_lst

def get_points(match_dict_lst : list) -> dict:

    points_sum = 0
    bonusp_sum = 0

    for match_dct in match_dict_lst:
        if match_dct['bonus']:
            # print('bonus')
            # print(bonusp_sum, match_dct['pts'])
            bonusp_sum += match_dct['pts']
            # print(bonusp_sum )
        else:
            points_sum += match_dct['pts']

    res = {}
    res.update({'points_sum' : points_sum, 'bonus_sum' : bonusp_sum})
    return res

def print_found_points(match_dict_lst : list):

    for match_dct in match_dict_lst:
        # print(
        #         match_dct['pos'], 
        #         match_dct['code'] if match_dct['code'] != '' else match_dct['comment'],
        #         # match_dct['code'] if match_dct['code']
        #         # match_dct['code'] if match_dct['code'] != '' else '#' + match_dct['comment'] \
        #         # if '#' not in match_dct['code'] else match_dct['line'],
        #         match_dct['pts'],
        #         "ZP" if match_dct['bonus'] else ""
        #     )
        print(
            '{2: 2.1f} {3:2} {0:>4}: {1:80} '.format(
                match_dct['pos'], 
                '#' + match_dct['comment'] if match_dct['code'] == '' else match_dct['line'] if '# ' in match_dct['code'] else match_dct['code'],
                match_dct['pts'],
                "ZP" if match_dct['bonus'] else ""
            )
        )

def print_found_total(match_dict_lst : list):
    totals = get_points(match_dict_lst)
    print(
        "Punkte: {0:3}, Bonuspunkte: {1:3}".format(totals['points_sum'], totals['bonus_sum'])
    )

def print_sheet_data(sh_dat_dict : dict):
    # print('Blattdaten')
    print(
        "Blatt \t{0:02d} \tAufgabe \t  {1:02d} \nPunkte:\t{2:02d} \tBonuspunkte (ZP): {3:2d}\n".format(
        sh_dat_dict['sheet'], 
        sh_dat_dict['exercise'], 
        sh_dat_dict['points'],
        sh_dat_dict['bonus']
        )
    )


# https://docs.python.org/3/library/__main__.html
def main():
    # print('sys.argv: \t', sys.argv)
    print(
        'script:',
        '\n    filename: ',   os.path.basename(os.path.realpath(__file__)),
        '\n    location: ',   os.path.dirname(os.path.realpath(__file__)),
        '\n     calldir: ',   os.getcwd(),
        )

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

                ./points_counter.py filename

            """), '  '),
        epilog=textwrap.dedent("""\
            ... enjoy and give feedback to yangntze+ptscnt@gmail.com \n\n
            """),
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
    
    args = parser.parse_args()
    # parser.parse_args(
    #     ['submissions/Mathem. am Computer (SoSe 23)-Aufgabe 01-1211043/Isabel Hirschmann_2725676_assignsubmission_file_/feedback_jz_I_Hirschmann_Bl_01_Aufg_01.ipynb']
    #     )
    print(args)

    print(os.path.isfile(args.filename))
    print(args.filename.endswith('.ipynb'))
    print(os.path.basename(args.filename))
    print(os.path.abspath(args.filename))
    print(os.path.realpath(os.getcwd()))

    # base_path = "/Users/ztzmjn/Documents/Studium/Mathe/sonstiges/hiwi/SS23/py_kurs/"
    # # file_name = "/solutions/Lsg_01.ipynb"
    # # file_name = "submissions/Mathem. am Computer (SoSe 23)-Aufgabe 02-1211044/Conrad Kühn_2725690_assignsubmission_file_/Aufg_02_ConradKuehn.ipynb"
    # file_name = "submissions/Mathem. am Computer (SoSe 23)-Aufgabe 01-1211043/Isabel Hirschmann_2725676_assignsubmission_file_/feedback_jz_I_Hirschmann_Bl_01_Aufg_01.ipynb"
    # # file_name = "exercises/Aufg_04.ipynb"
    # myfile = base_path + file_name

    base_path = "/Users/ztzmjn/Documents/Studium/Mathe/sonstiges/hiwi/SS23/py_kurs/"

    text = get_py_code(myfile)
    print("\n --- --- --- --- --- --- ---   --- --- --- --- --- --- ---   --- --- --- --- --- --- --- \n")
    print(text[300:400])
    # sdd = get_sheet_data(text)
    # print_sheet_data(sdd)


    # rg_found = points_finder(text, regex = rgx_lsg)
    # print_found_points(rg_found)

    rg_found = points_finder(text, regex = rgx_pts)
    # print(rg_found[0])
    print_found_points(rg_found)

    # for i in range(len(rg_found)):
    # for i in [1]:
    #     print('\n________')                 # ________
    #     print(rg_found[i][0].group(0))      # # !!! +1 ZP für Nutzung des einzelnen Imports und Aufruf über "sympy."
    #     print(rg_found[i][0].group(1))      #  code vor dem "#"
    #     print(rg_found[i][0].group(2))      # +1
    #     print(rg_found[i][0].group(3))      #  ZP
    #     print(rg_found[i][0].group(4))      #  für Nutzung des einzelnen Imports und Aufruf über "sympy."

    return 0

if __name__ == '__main__':
    sys.exit(main())