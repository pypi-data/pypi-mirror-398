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

from tabulate import tabulate
import numpy as np
from IPython.display import display, HTML

from ._is_notebook import is_notebook

class BenchmarkTimer:
    """
    A class to time and manage benchmark results organized in "sections" and "measurements".

    Example
    -------

        .. code-block:: python

            from iactsim.utils import BenchmarkTimer
            import random
            import time

            class Foo():
                def __init__(self):
                    self.timer = BenchmarkTimer()
                    self.timer.add_section('foo1')
                    self.timer.add_section('foo2')

                def foo1(self):
                    t0 = time.time()
                    time.sleep(random.randint(0,50)/1000.)
                    t1 = time.time()
                    time.sleep(random.randint(0,5)/1000.)
                    t2 = time.time()
                    self.timer.add_entry('foo1', 'First', t1-t0)
                    self.timer.add_entry('foo1', 'Second', t2-t1)

                def foo2(self):
                    t0 = time.time()
                    time.sleep(random.randint(0,30)/1000.)
                    t1 = time.time()
                    self.timer.add_entry('foo2', 'foo2', t1-t0)
            
            foo = Foo()
            for i in range(100):
                foo.foo1()
                foo.foo2()
            foo.timer.print_results()
    
    """

    def __init__(self):
        """
        Initializes the BenchmarkTimer with an empty results dictionary.
        """
        self.results = {}  # {section_name: {measure_name: [times]}}
        self.active = True

    def add_section(self, section_name: str):
        """
        Adds a new section (e.g., a method name) to the results.

        Parameters
        ----------
        section_name : str
            The name of the section to add.
        """
        if section_name not in self.results:
            self.results[section_name] = {}

    def add_entry(self, section_name: str, measure_name: str, elapsed_time: float):
        """
        Adds a timing entry for a specific measure within a section.

        Parameters
        ----------
        section_name : str
            The name of the section.
        measure_name : str
            The name of the measurement within the section.
        elapsed_time : float
            The elapsed time in seconds.
        """
        if section_name not in self.results:
            raise(ValueError(f"Section {section_name} not found."))
        # Ensure measure exists
        if measure_name not in self.results[section_name]:
            self.results[section_name][measure_name] = []
        self.results[section_name][measure_name].append(elapsed_time)

    def get_results(self) -> dict:
        """
        Returns the raw results dictionary.

        Returns
        -------
        dict
            The results dictionary, structured as:
            {section_name: {measure_name: [time1, time2, ...]}}
        """
        return self.results

    def _calculate_totals(self):
        """
        Calculates and adds 'total_time' for each section.
        The 'total_time' will have an entry for each iteration, summing
        the times of all other measures *for that iteration*.
        """
        for section_name, section_data in self.results.items():
            # Find the maximum number of iterations
            max_iterations = 0
            for measure_name, times in section_data.items():
                if measure_name != "total_time":
                    max_iterations = max(max_iterations, len(times))

            # Initialize the total_time list
            if "total_time" not in self.results[section_name]:
                self.results[section_name]["total_time"] = []

            # Iterate through each iteration
            for i in range(max_iterations):
                total_time_for_iteration = 0
                # Sum the times for all measures in this iteration
                for measure_name, times in section_data.items():
                    if measure_name != "total_time" and i < len(times):
                        total_time_for_iteration += times[i]

                # Add/update the total time for this iteration
                if i < len(self.results[section_name]["total_time"]):
                  self.results[section_name]["total_time"][i] = total_time_for_iteration
                else:
                  self.results[section_name]["total_time"].append(total_time_for_iteration)

    def _prepare_data(self, compute_total: bool) -> list[list]:
        """
        Prepares the data for printing (calculates stats and overall total).

        Returns
        -------
        list[list]
            A list of lists, where each inner list represents a row
            in the table, ready for formatting.
        """
        self._calculate_totals()
        data = []

        for section_name, section_data in self.results.items():
            for measure_name, times in section_data.items():
                n_calls = len(times)
                if n_calls > 0:
                    times_np = np.array(times) * 1000  # Convert to milliseconds
                    min_time = np.min(times_np)
                    max_time = np.max(times_np)
                    mean_time = np.mean(times_np)
                    median_time = np.median(times_np)
                    stdev_time = np.std(times_np) if len(times_np) > 1 else 0.0
                else:
                    times_np = 0
                    min_time = 0
                    max_time = 0
                    mean_time = 0
                    median_time = 0
                    stdev_time = 0
                data.append([
                    section_name,
                    measure_name,
                    "{}".format(n_calls),
                    "{:.3f}".format(mean_time),
                    "{:.3f}".format(median_time),
                    "{:.3f}".format(stdev_time),
                    "{:.3f}".format(min_time),
                    "{:.3f}".format(max_time),
                ])

        # Calculate overall total (sum of all section totals) if every part is called n times
        # number_of_calls = [len(self.results[section]['total_time']) for section in self.results.keys()]
        # if len(set(number_of_calls)) == 1 and compute_total:
        #     totals = np.asarray([self.results[section]['total_time'] for section in self.results.keys()]).sum(axis=0) * 1000
        #     min_time = np.min(totals)
        #     max_time = np.max(totals)
        #     mean_time = np.mean(totals)
        #     median_time = np.median(totals)
        #     stdev_time = np.std(totals) if len(totals) > 1 else 0.0

            # data.append([]) # add an empty row
            # data.append([
            #     "Total",
            #     "",
            #     "{:.3f}".format(min_time),
            #     "{:.3f}".format(max_time),
            #     "{:.3f}".format(mean_time),
            #     "{:.3f}".format(median_time),
            #     "{:.3f}".format(stdev_time)
            # ])

        return data

    def _build_html_table(self, data: list[list]) -> str:
        """
        Builds the HTML table string for Jupyter Notebooks.  Internal method.

        Parameters
        ----------
        data : list[list]
            The prepared data (list of rows).

        Returns
        -------
        str
            The complete HTML table as a string.
        """
        headers = ["Section", "Measure", "N calls", "Mean (ms)", "Median (ms)", "Stdev (ms)", "Min (ms)", "Max (ms)"]
        html_output = "<table>\n"
        html_output += "<tr>" + "".join(f"<th>{header}</th>" for header in headers) + "</tr>\n"

        for row_data in data:
            if not row_data:  # Check for empty row
                html_output += "<tr>" + "".join("<td></td>" for _ in headers) + "</tr>\n" #empty row
            else:
                measure_name = row_data[1]
                # Apply bold formatting to total_time
                if measure_name == "total_time" or row_data[0] == "Total":
                    row_data = [f"<b>{x}</b>" for x in row_data]
                html_output += "<tr>" + "".join(f"<td>{value}</td>" for value in row_data) + "</tr>\n"


        html_output += "</table>"
        return html_output

    def _print_console_table(self, data: list[list], return_str=False):
        """
        Prints the formatted table to the console. Internal method.

        Parameters
        ----------
        data : list[list]
            The prepared data (list of rows).
        """
        headers = ["Section", "Measure", "N calls", "Mean (ms)", "Median (ms)", "Stdev (ms)", "Min (ms)", "Max (ms)"]

        formatted_data = []
        for row in data:
            if not row:
                formatted_data.append([""] * len(headers)) #empty row
            elif row[1] == "total_time" and not return_str:  #bold in console
                formatted_row = [f"\033[1m{x}\033[0m" for x in row]
                formatted_data.append(formatted_row)
            else:
                formatted_data.append(row)
        
        table = tabulate(formatted_data, headers=headers, tablefmt="grid")

        if return_str:
            return table
        else:
            print(table)


    def print_results(self, title: str = None, show_total: bool = True, return_str: bool = False):
        """
        Prints the timings, handling both notebook and console output.

        Parameters
        ----------
        title : str, optional
            An optional title to display above the table.
        show_total : bool, optional
            Add a last row with the sum of all sections.
        """
        if not self.active:
            return
        
        data = self._prepare_data(compute_total=show_total)

        if is_notebook() and not return_str:
            if title is not None:
                display(HTML(f'<h2>{title}</h2>'))
            html_table = self._build_html_table(data)
            display(HTML(html_table))
        else:
            if title is not None and not return_str:
                print(title.center(80))
            return self._print_console_table(data, return_str=return_str)

    def clear(self):
        """Resets the timer, keeping sections and measures, but clearing samples."""
        for section_data in self.results.values():
            for measure_name in section_data:
                section_data[measure_name] = []