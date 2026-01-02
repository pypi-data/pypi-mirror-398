import os
import logging
import random
import string
import re
import ibm_aigov_facts_client.factsheet as modelfacts
from base64 import b64decode,b64encode
from io import BytesIO
from IPython import get_ipython
from IPython.core import magic_arguments
from IPython.core.magic import (Magics, cell_magic, magics_class)
from IPython.display import display
from IPython.utils.capture import capture_output
from ibm_aigov_facts_client.utils.constants import *


_logger = logging.getLogger(__name__) 

# 3 length suffix
def randStr(chars = string.ascii_lowercase + string.digits, N=3):
	return ''.join(random.choice(chars) for _ in range(N))


def get_file_path(filename):
    
    current_directory = os.getcwd()
    final_directory = os.path.join(current_directory, CELL_FACTS_TMP_DIR)
    if not os.path.exists(final_directory):
        os.makedirs(final_directory)

    file_path = os.path.join(final_directory, filename)
    return file_path

def remove_tag(html, tag_name):
    new_html = html.replace("\n", '')
    regex_string = f'<{tag_name}[^>]*>\s*.*\s*<\/{tag_name}>'
    regex = re.compile(rf'{regex_string}', re.IGNORECASE | re.MULTILINE)
    # replace the matching patterns with an empty string
    new_html = re.sub(regex, '', new_html)
    return new_html


@magics_class
class CellFactsMagic(Magics):
    _fname=None

    @cell_magic
    @magic_arguments.magic_arguments()

    @magic_arguments.argument(
        "--printmsgonly",
        "-po",
        action='store_true',
        help=("Defines whether to capture print messages only"),
    )

    @magic_arguments.argument(
        "--capturecode",
        "-cc",
        action='store_true',
        help=("Defines whether to capture cell codes"),
    )

    def capture_cell_facts(self, line, cell):
        args = magic_arguments.parse_argstring(CellFactsMagic.capture_cell_facts, line)
        stdout_only = args.printmsgonly
        cap_codes=args.capturecode
        
        fmt='''<div class="card"><img src="data:image/png;base64,{}"/><br>\n'''
        txt='''<pre> {} </pre> <br>\n'''
        t='''<p> {} </p> <br>\n'''
        tmp=[]
        
        CellFactsMagic._fname="Captured_Cell_Output_{}.html".format(randStr())
        output_filepath= get_file_path(CellFactsMagic._fname)

        with capture_output(stdout=True, stderr=False, display=True) as io:
            get_ipython().run_cell(cell)
        io()
        
        if stdout_only:
            with capture_output(stdout=True, stderr=False, display=True) as result:
                #self.shell.run_cell(cell)
                get_ipython().run_cell(cell)
                with open(output_filepath, 'w+') as fd:
                    if result.stdout is not None:
                        message=result.stdout
                        fmt_data="<br />".join(message.split("\n"))
                        if cap_codes:
                            fmt_cell="<br />".join(cell.split("\n"))
                            fd.write(t.format(fmt_cell))
                        fd.write(t.format(fmt_data))  
        else:
            with capture_output(stdout=False, stderr=False, display=True) as result:
                #self.shell.run_cell(cell)
                get_ipython().run_cell(cell)
                if result.outputs:
                    for output in result.outputs:
                        data = output.data
                        tmp.append(data)

            with open(output_filepath, 'w+') as fd:
                if cap_codes:
                    fmt_cell="<br />".join(cell.split("\n"))
                    fd.write(t.format(fmt_cell))

                for i in tmp:
                    if 'image/png' in i:
                        png_bytes = i['image/png']
                        if isinstance(png_bytes, str):
                            png_bytes = b64decode(png_bytes)
                        assert isinstance(png_bytes, bytes)
                        bytes_io = BytesIO(png_bytes)
                        encoded_string = b64encode(bytes_io.getvalue()).decode()
                        img_str=fmt.format(encoded_string)
                        fd.write(img_str)

                    elif 'text/plain' in i and not 'text/html' in i:
                        txt_data = i['text/plain']
                        fd.write(txt.format(txt_data))
                    
                    elif 'text/plain' in i and 'text/html' in i:
                        tbl_data = i['text/html']
                        # removes style tag and it's content
                        tmp_data = remove_tag(tbl_data,"style")
                        fd.write(tmp_data)
                 
                    else:
                        fmt_data="<br />".join(i.split("\n"))
                        fd.write(t.format(fmt_data))

        _logger.info("Saved cell facts under: ")    
        return output_filepath                