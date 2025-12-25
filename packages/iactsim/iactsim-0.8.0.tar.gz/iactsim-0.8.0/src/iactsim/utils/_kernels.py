# Copyright (C) 2024- Davide Mollica <davide.mollica@inaf.it>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of iactsim.
#
# iactsim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iactsim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with iactsim.  If not, see <https://www.gnu.org/licenses/>.

import re
from functools import wraps
import textwrap

def wrap_cupy_rawkernel(raw_kernel, docstring):
    """
    Generates wrapper function for a CuPy RawKernel.
    The wrapper allows you to provide a custom docstring.

    Parameters
    ----------
        raw_kernel: cupy.RawKernel
            The cupy.RawKernel object to wrap.
        docstring: str
            A custom docstring for the wrapped kernel.

    Returns
    -------
        A Python function that wraps the CuPy RawKernel.
    """

    @wraps(raw_kernel)  # Preserve original kernel's metadata
    def wrapper(*args, **kwargs):
        raw_kernel(*args, **kwargs)

    wrapper.__doc__ = docstring

    return wrapper

def clean(string):
    string_clean = re.sub(r"^ \* ?", "", string, flags=re.MULTILINE).strip()
    if string_clean.startswith("*"):
        string_clean = string_clean[1:]
    return string_clean

def convert_doxygen_to_numpy(cuda_source, function_name):
    """
    Converts Doxygen-style documentation within the given source code to NumPy-style docstrings.

    Parameters
    ----------
        cuda_source: str
            The source code.
        function_name: str
            The name of the function.

    Returns
    -------
        docstring: str 
            The NumPy-style docstring or None if not found.
    """

    # Find all functions with docstring
    function_pattern = re.compile(
        r"/\*\*\s*\n\s*\*\s*@brief\s*(.*?)\n(.*?)\*/\s*(__global__|__device__)\s+.*?\s+(\w+)\s*\(",
        re.DOTALL,
    )

    # Cicly over all functions
    for match in function_pattern.finditer(cuda_source):

        # Look for the specified function
        current_function_name = match.group(4)
        if current_function_name != function_name:
            continue
        
        is_global = match.group(3) == '__global__'

        # Isolate the function source code
        start = match.start()

        # Find the *correct* closing parenthesis for the parameter list
        open_paren_index = match.end()  # start after the opening parenthesis
        brace_count = 1
        cur_pos = open_paren_index
        while brace_count > 0 and cur_pos < len(cuda_source):
            if cuda_source[cur_pos] == '(':
                brace_count += 1
            elif cuda_source[cur_pos] == ')':
                brace_count -= 1
            cur_pos += 1

        end = cur_pos  # end after the closing parenthesis
        function_source = cuda_source[start:end]

        # Remove comments
        function_source = re.sub(r'//.*', '', function_source)
        
        param_string_start = [m.start() for m in re.finditer(r'\(',function_source)][-1]+1
        param_string_end = [m.start() for m in re.finditer(r'\)',function_source)][-1]
        param_types_str = function_source[param_string_start:param_string_end].strip()
        param_types_str = re.sub(r"[\n\t ]+", " ", param_types_str)
        
        # Parse parameter types and names
        param_types_dict = {}
        if param_types_str:
          params = [p.strip() for p in param_types_str.split(",") if p.strip()]
          for param in params:
            param = re.sub(r'//.*', '', param).strip()
            if not param:
                continue
            
            parts = param.rsplit(" ", 1)
            if len(parts) == 2:
              param_type, param_name = parts[0].strip(), parts[1].strip()
              param_type = param_type.replace(' *', '*').replace(' &', '&')
              if param_name.startswith('*') or param_name.startswith('&'):
                param_type += param_name[0]
                param_name = param_name[1:]

              param_types_dict[param_name] = param_type
            elif len(parts) == 1:
              param_types_dict[parts[0]] = "Unknown"

        # Isolate function description removing all doxygen directives
        brief = match.group(1).strip()
        detailed = match.group(2).strip()

        # Isolate parameter names
        param_pattern = re.compile(r"@param\s+(\w+)\s+((?:(?!@param|@warning|@note|@return|@returns|@see|@code|@details).)+)", re.DOTALL)
        params = param_pattern.findall(detailed)

        # Handle doxygen directives
        warnings = re.findall(r'@warning\s+((?:(?!@param|@warning|@note|@return|@returns|@see|@code|@details).)+)', detailed, re.DOTALL)
        notes = re.findall(r'@note\s+((?:(?!@param|@warning|@note|@return|@returns|@see|@code|@details).)+)', detailed, re.DOTALL)
        returns = re.findall(r'@return(?:s)?\s+((?:(?!@param|@warning|@note|@return|@returns|@see|@code|@details).)+)', detailed, re.DOTALL)
        see_also = re.findall(r'@see\s+((?:(?!@param|@warning|@note|@return|@returns|@see|@code|@details).)+)', detailed, re.DOTALL)
        code_blocks = re.findall(r'@code(?:cpp)?\s*([\s\S]*?)\s*@endcode', detailed)
        details = re.findall(r'@details\s+((?:(?!@param|@warning|@note|@return|@returns|@see|@code|@details).)+)', detailed, re.DOTALL)

        # Clean description
        detailed_clean = re.sub(r"@param\s+\w+\s+(?:(?!@param|@warning|@note|@return|@returns|@see|@code|@details).)+", "", detailed, flags=re.DOTALL).replace('*', '').strip()
        detailed_clean = re.sub(r'@warning\s+((?:(?!@param|@warning|@note|@return|@returns|@see|@code|@details).)+)',"",detailed_clean, flags=re.DOTALL).strip()
        detailed_clean = re.sub(r'@note\s+((?:(?!@param|@warning|@note|@return|@returns|@see|@code|@details).)+)',"",detailed_clean, flags=re.DOTALL).strip()
        detailed_clean = re.sub(r'@return(?:s)?\s+((?:(?!@param|@warning|@note|@return|@returns|@see|@code|@details).)+)',"",detailed_clean, flags=re.DOTALL).strip()
        detailed_clean = re.sub(r'@see\s+((?:(?!@param|@warning|@note|@return|@returns|@see|@code|@details).)+)',"",detailed_clean, flags=re.DOTALL).strip()
        detailed_clean = re.sub(r'@code(?:cpp)?\s*([\s\S]*?)\s*@endcode',"",detailed_clean, flags=re.DOTALL).strip()
        detailed_clean = re.sub(r'@details\s+((?:(?!@param|@warning|@note|@return|@returns|@see|@code|@details).)+)',"",detailed_clean, flags=re.DOTALL).strip()
        detailed_clean = re.sub(r'\s+', ' ', detailed_clean).strip()

        # Clean brief description
        brief = re.sub(r'\s+', ' ', brief).strip()
        
        # Write docstring
        numpy_docstring = f"{brief.replace('*', '').strip()}\n\n"
        numpy_docstring += f"{detailed_clean}\n\n"

        if details:
            # numpy_docstring += "\n\n---------\n\n"
            details[0] = details[0]
            for detail_text in details:
                detail_text_clean = clean(detail_text)
                numpy_docstring += f"{textwrap.dedent(detail_text_clean.strip())}\n\n"

        if params:
            numpy_docstring += "Parameters\n----------\n"
            for param_name, param_desc in params:
                param_type = param_types_dict.get(param_name, "Unknown")
                param_desc_clean = clean(param_desc)#param_desc.replace('*', '').strip()
                param_desc_clean = param_desc_clean.replace('\n', ' ').strip()
                param_desc_clean = re.sub(r'\s+', ' ', param_desc_clean).strip()
                numpy_docstring += f"{param_name} : {param_type}\n    {param_desc_clean}\n"

        if returns:
            numpy_docstring += "\nReturns\n-------\n"
            for ret_desc in returns:
                # ret_desc_clean = ret_desc.replace('*', '').strip()
                ret_desc_clean = clean(ret_desc)
                numpy_docstring += f"{ret_desc_clean}\n"
        
        if warnings:
            numpy_docstring += "\nWarnings\n--------\n"
            for warning in warnings:
                warning_clean = clean(warning)
                # warning_clean = warning.replace('*', '').strip()
                numpy_docstring += f"{warning_clean}\n"
        
        if notes:
            numpy_docstring += "\nNotes\n-----\n"
            for note_text in notes:
                note_text_clean = clean(note_text)#note_text.replace('*','').strip()
                numpy_docstring += f"{note_text_clean}\n"
        
        if see_also:
            numpy_docstring += "\nSee Also\n--------\n"
            for see in see_also:
                see_clean = clean(see)#see.replace('*', '').strip()
                numpy_docstring += f"{see_clean}\n"
        
        if code_blocks:
            numpy_docstring += "\nExamples\n--------\n"
            for code_text in code_blocks:
                clean_code_text = clean(code_text)#code_text.replace('*', '')
                numpy_docstring += ".. code-block:: cpp\n\n    "
                numpy_docstring += ''.join([line+'\n' for line in clean_code_text.split('\n ')])
                numpy_docstring += "\n"
        
        if is_global:
            numpy_docstring += "\nAttention\n---------\n"
            numpy_docstring += "This is a wrapped CuPy `RawKernel` object,\n"
            numpy_docstring += "you can launch it as follows:\n\n"
            numpy_docstring += ".. code-block:: python\n\n"
            numpy_docstring += "   blocks = ...  # Number of blocks\n"
            numpy_docstring += "   threads = ...  # Number of threads per block\n"
            numpy_docstring += "   shared_memory = ...  # Dynamic shared memory buffer size (if needed)\n"
            numpy_docstring += f"   args = (...)  # Provide the arguments\n"
            numpy_docstring += "   kernel(grid, block, args, shared_mem=shared_memory)\n\n"
            numpy_docstring += "If you are new to CuPy, please see the CuPy `documentation`_.\n\n"
            numpy_docstring += ".. _documentation: https://cupy.dev/\n"

        return numpy_docstring

    return None


def get_kernel(module, kernel_name):
    """Get kernel wrapper.

    Parameters
    ----------
    module : cupy.RawModule
        A CuPy rawModule
    kernel_name : str
        Name of the kernel to retrieve and wrap.
    
    Return
    ------
        Wrapper to the RawKernel with a NumPy-style docstring.
    """
    docstring = convert_doxygen_to_numpy(module.code, kernel_name)
    return wrap_cupy_rawkernel(module.get_function(kernel_name), docstring)