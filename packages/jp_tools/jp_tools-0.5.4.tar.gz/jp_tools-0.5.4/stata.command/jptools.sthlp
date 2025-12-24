{smcl}
{* *! version 1.0 10nov2025}{...}
{title:jptools}

{phang}
{bf:jptools} — Download a file from a URL using Python

{title:Syntax}

{p 8 15 2}
{cmd:jptools} , {opt url(string)} {opt file(string)}

{synoptset 20 tabbed}{...}
{synopthdr}
{synoptline}
{synopt:{opt url(string)}}The full URL of the file to download{p_end}
{synopt:{opt file(string)}}The local file path (including filename) to save the downloaded file{p_end}
{synoptline}

{title:Description}

{pstd}
{cmd:jptools} downloads a file from a specified {cmd:url} and saves it locally as {cmd:file}.
This command uses Python integration in Stata to call a Python function defined inside the ado file.
The Python function relies on the module {cmd:jp_tools.download} to handle the download process.

{pstd}
You must have Python properly configured in Stata (via {cmd:set python_exec}) and have the 
{cmd:jp_tools} module installed and available in your Python environment.

{title:Options}

{phang}
{opt url(string)} — The web address (URL) of the file to download.

{phang}
{opt file(string)} — The local destination path and filename to save the downloaded file.

{title:Examples}

{phang}{cmd:. jptools, url("https://example.com/data.csv") file("data.csv")}
{p_end}
{phang}{cmd:. jptools, url("https://raw.githubusercontent.com/user/repo/main/data.csv") file("C:\data\data.csv")}
{p_end}

{title:Remarks}

{pstd}
The {cmd:jptools} command delegates the actual downloading to a Python function defined within the ado file.
This approach allows for more flexible and powerful file-handling via Python libraries.

{pstd}
Ensure that the Python module {cmd:jp_tools} is available and importable from your configured Python environment.

{title:Author}

{phang}Alejandro Ouslan{p_end}
{phang}University of Puerto Rico, Mayaguez [alejandro.ouslan@upr.edu]{p_end}

{title:Also see}

{psee}
{help python integration:[R] python} — Using Python in Stata{p_end}
