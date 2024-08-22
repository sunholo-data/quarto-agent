from sunholo.genai import GenAIFunctionProcessor
from sunholo.utils import ConfigManager
from sunholo.gcs.add_file import add_file_to_gcs

from my_log import log

import subprocess
import os
import json
import traceback
import time
import shutil

class QuartoProcessor(GenAIFunctionProcessor):

    def upload_to_gcs(self, folder:str):
        log.info(f"Uploading {folder=}")
        vector_name = self.config.vector_name

        output_urls = []
        # Iterate through all files in the directory and upload them
        for root, _, files in os.walk(folder):
            for file in files:
                filename = os.path.join(root, file)

                # Create a relative path for the bucket
                relative_path = os.path.relpath(filename, folder)
                bucket_filepath = f"quarto/{vector_name}/{folder}/{relative_path}"

                file_url = add_file_to_gcs(filename,
                                           vector_name=vector_name,
                                           metadata={"type": "quarto"},
                                           bucket_filepath=bucket_filepath)
        
                log.info(f"Uploaded {filename} to {file_url=}")
                output_urls.append(file_url)

        return output_urls
        
    def construct_tools(self) -> dict:
        #tools = self.config.vacConfig("tools")
        #if not tools:
        #    vac_name = self.config.vector_name
        #    raise ValueError(f"No config.vac.{vac_name}.tools found")
        #quarto_config = tools.get("quarto")

        def write_to_file(text: str, file_path: str = "renders/temp.py", append: bool=False) -> str:
            """
            Writes the given text content to a specified file for use in Quarto renders. 
            Do not use backticks (```) to the start of the text - this is text that will write directly to the file, not within markdown.
            This function will only write .py, .r files. Do not attempt to write other types of files with this function.
            Will only accept up to 4000 characters of text each time to avoid overflow issues. 
            Use the same file_path argument and call the function again to append additional text to the file.

            Args:
                text (str): The text content to write to the file.
                file_path (str): The path to the file where the markdown will be written. 
                                Default is "renders/temp.py".
                append (bool): Whether you want to append to the existing file.  If False (default) then it will overwrite the existing file.
            Returns:
                str: The path to the file where the text was written.
            Raises:
                ValueError: If the file extension is not .py or .r.
                ValueError: If the text exceeds 4000 characters.
            """
            try:
                # Validate the file extension
                if not file_path.endswith(('.py', '.r')):
                    raise ValueError("This function only supports writing to .py and .r files.")

                # Ensure the text does not exceed 4000 characters
                if len(text) > 4000:
                    raise ValueError("Text exceeds the 4000 character limit. Shorten text and then call this function again with same file_name to append the text to the file.")

                # Ensure the directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # Ensure \n gets rendered correctly
                text = text.encode('utf-8').decode('unicode_escape')

                mode = 'a' if append else 'w'
                
                # Write or append the content to the file
                with open(file_path, mode, encoding='utf-8') as file:  
                    file.write(text)
                
                # Log the successful write operation
                print(f"Text successfully written to {file_path}")
                return file_path

            except Exception as e:
                print(f"Error writing content to file: {str(e)}")
                raise

        def render_and_upload_quarto(markdown_filename: str = "", format: str='html') -> dict:
            """
            Render and upload a Quarto markdown document to Google Cloud Storage.

            This function expects a filename location of valid Quarto markdown. 
            The encoded markdown will be rendered using Quarto. 
            The resulting output file will be uploaded to a Google Cloud Storage (GCS) bucket.
            The markdown must be quarto formatted to work with quarto.
            The markdown will be supplied to the quarto_cmd() function and execute `quarto render temp.qmd --to={format} --output={filename}`
            If successfully rendered, the output file will then be uploaded to a GCS bucket
            
            Args:
                markdown_filename (str): The location of the markdown file to render. If not provided, a demo markdown file will be used.
                format (str): The format to render the markdown file into - default is 'html'.
            Returns:
                dict: A dictionary with the result of the rendering process, including:
                    - "status": "success" or "error" depending on the outcome.
                    - "gcs_url": The URL of the uploaded file (if successful).
                    - "stdout": The standard output from the Quarto rendering process.
                    - "stderr": The standard error output from the Quarto rendering process.
                    - "message": An error message if the rendering or upload failed.
            """

            if not markdown_filename:
                markdown_filename = 'tools/demo.qmd'

            try:               
                # Create a timestamped directory
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                temp_dir = os.path.join("renders", timestamp)
                os.makedirs(temp_dir, exist_ok=True)

                # Copy the markdown file to the timestamped directory
                new_markdown_filename = os.path.join(temp_dir, os.path.basename(markdown_filename))
                shutil.copy(markdown_filename, new_markdown_filename)

                # Render the markdown file using Quarto from the new directory
                output_filename = f'output.{format}'
                render_command = f"render {os.path.basename(new_markdown_filename)} --to={format} --output={output_filename}"
                result = quarto_command(render_command, cwd=temp_dir)
                result = json.loads(result)
                log.info(f"{result=}")

                # Check if there was an error during rendering
                if result["status"] == "error":
                    return json.dumps({
                        "status": "error",
                        "stdout": result["stdout"],
                        "stderr": result["stderr"],
                        "message": "Quarto rendering failed."
                    })
                
                # Upload the rendered file to Google Cloud Storage
                upload_to_gcs = self.upload_to_gcs(temp_dir)
                
                return json.dumps({
                    "status": "success",
                    "gcs_urls": upload_to_gcs,
                    "stdout": result["stdout"],
                    "stderr": result["stderr"]
                })
            
            except Exception as e:
                error_message = f"Error in render_and_upload_quarto: {str(e)}"
                traceback_details = traceback.format_exc()
                error_and_traceback = f"ERROR: {error_message} {traceback_details}"
                log.warning(error_and_traceback)
                return json.dumps({
                    "status": "error",
                    "message": error_and_traceback,
                })
        
        def decide_to_go_on(go_on: bool, chat_summary: str) -> dict:
            """
            Examine the chat history.  If the answer to the user's question has been answered, then go_on=False.
            If the chat history indicates the answer is still being looked for, then go_on=True.
            If there is no chat history, then go_on=True.
            If there is an error that can't be corrected or solved by you, then go_on=False.
            If there is an error but you think you can solve it by correcting your function arguments (such as an incorrect source), then go_on=True
            If you want to ask the user a question or for some more feedback, then go_on=False.
            When calling, please also add a chat summary of why you think the function should  be called to end.
            
            Args:
                go_on: boolean Whether to continue searching for an answer
                chat_summary: string A brief explanation on why go_on is TRUE or FALSE
            
            Returns:
                boolean: True to carry on, False to continue
            """
            return {"go_on": go_on, "chat_summary": chat_summary}
        
        def quarto_command(cmd: str, cwd: str = None) -> dict:
            """
            Run a Quarto command in the terminal and capture the output.
            Do not run commands starting with 'quarto' e.g. 'quarto preview' - instead use 'preview'.
            The 'quarto' command will be prefixed to your cmd.
            
            Args:
                cmd (str): The command to execute with Quarto (e.g., 'check', 'render <file>').
                cwd (str): The working directory in which to run the command. Default is None, 
                   which means the command runs in the current working directory.        
            Returns:
                dict: A dictionary containing 'stdout' and 'stderr' from the command execution.
                    If the command is successful (return code 0), 'status' will be 'success',
                    even if there is content in 'stderr'.
            """
            try:
                result = subprocess.run(
                            ["quarto"] + cmd.split(), 
                            capture_output=True, 
                            text=True, 
                            cwd=cwd
                        )
                log.info(f"{result.stdout=}")
                log.info(f"{result.stderr=}")

                if result.returncode == 0:
                    # Command was successful
                    return json.dumps({
                        "status": "success",
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    })
                else:
                    # Command failed
                    return json.dumps({
                        "status": "error",
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "message": f"Quarto command '{cmd}' failed with return code {result.returncode}",
                        "returncode": result.returncode
                    })
                
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "stdout": "",
                    "stderr": f"Error running Quarto command '{cmd}': {str(e)}"
                })
        
        def quarto_version() -> str:
            """
            Reports back the version of Quarto available and what is installed on the server.
            If the result starts with "OK:" then quarto is successfully installed.
            There may be other dependencies thought that are not installed such as R or Jupyter.
            
            Returns:
                str: The version information of Quarto, as returned by the 'quarto check' command.
            """
            result = quarto_command("check")
            result = json.loads(result)

            if result["status"] == "success":
                return f"OK: {result['stderr']}"
            return result["stdout"]

        def install_pip_package(package_name: str) -> dict:
            """
            Install a pip package in the local environment.
            
            Args:
                package_name (str): The name of the pip package to install.
            
            Returns:
                dict: A dictionary containing 'stdout' and 'stderr' from the command execution.
            """
            try:
                result = subprocess.run(["pip", "install", package_name], capture_output=True, text=True)

                log.info(f"Installing package {package_name}")
                log.info(f"{result.stdout=}")
                log.info(f"{result.stderr=}")

                return json.dumps({
                    "stdout": result.stdout,
                    "stderr": result.stderr
                })
            
            except Exception as e:
                return json.dumps({
                    "stdout": "",
                    "stderr": f"Error installing pip package '{package_name}': {str(e)}"
                })

        def install_r_package(package_name: str) -> dict:
            """
            Install an R package in the local environment.
            
            Args:
                package_name (str): The name of the R package to install.
            
            Returns:
                dict: A dictionary containing 'stdout' and 'stderr' from the command execution.
            """
            try:
                # Construct the R command to install the package
                r_command = f"install.packages('{package_name}', repos='https://cloud.r-project.org/')"
                
                # Run the R command
                result = subprocess.run(["R", "-e", r_command], capture_output=True, text=True)

                log.info(f"Installing R package {package_name}")
                log.info(f"{result.stdout=}")
                log.info(f"{result.stderr=}")

                return json.dumps({
                    "stdout": result.stdout,
                    "stderr": result.stderr
                })
            
            except Exception as e:
                return json.dumps({
                    "stdout": "",
                    "stderr": f"Error installing R package '{package_name}': {str(e)}"
                    })

        return {
            "render_and_upload_quarto": render_and_upload_quarto,
            "quarto_command": quarto_command,
            "quarto_version": quarto_version,
            "decide_to_go_on": decide_to_go_on,
            "install_pip_package": install_pip_package,
            "install_r_package": install_r_package,
            "write_to_file": write_to_file,
        }

def get_quarto(config:ConfigManager, processor:QuartoProcessor):

    tools = config.vacConfig('tools')

    if tools and tools.get('quarto'):
        model_name = None
        if config.vacConfig('llm') != "vertex":
            model_name = 'gemini-1.5-flash'
        model = processor.get_model(
            system_instruction=(
                    "You are a helpful Quarto agent that helps users create and render Quarto documents. "
                    "When you think the answer has been given to the satisfaction of the user, or you think no answer is possible, or you need user confirmation or input, you MUST use the decide_to_go_on(go_on=False) function"
                    "When you want to ask the question to the user, mark the go_on=False in the function"
                    "You must use the render_and_upload_quarto() function to render Quarto functions and upload them to the pre-configured bucket.  Do not try to use your own bucket"
                    "DO NOT use .qmd files as there are issues parsing markdown - always write .py and .r files with the appropriate Quarto metadata instead."
                    '''These are instructions on how to annotate .py files for Quarto:
Script rendering for Jupyter makes use of the percent format that is supported by several other tools including Spyder, VS Code, PyCharm, and Jupytext.
In the percent format:
	•	Markdown cells are delimited by # %% [markdown], and can include content as single line comments (#) or multi-line strings (""").
	•	Code cells are delimited by # %%.
There are also Quarto-specific additions:
	•	The script must start with a markdown cell that includes a YAML header block (including the usual --- YAML delimiters).
	•	You can add code cell options in the usual way with #| comments.
For example, here is a Python script that includes both markdown and code cells (you can click on the numbers on the right for further details):
script.py
# %% [markdown]
# ---
# title: Palmer Penguins
# author: Norah Jones
# date: 3/12/23
# ---

# %%
#| echo: false
import pandas as pd
df = pd.read_csv("palmer-penguins.csv")

# %% [markdown]
"""
## Exploring the data

See @fig-bill-sizes for an exploration of bill sizes by species.
"""

# %% 
#| label: fig-bill-sizes
#| fig-cap: Bill Sizes by Species
                                          
import matplotlib.pyplot as plt           
import seaborn as sns

g = sns.FacetGrid(df, hue="species", height=3, aspect=3.5/1.5)
g.map(plt.scatter, "bill_length_mm", "bill_depth_mm").add_legend()

Generating Markdown
Jupyter scripts are especially convenient when most of your document consists of code that dynamically generates markdown. You can write markdown from Python using functions in the IPython.display module. For example:
# %%
#| echo: false
radius = 10
from IPython.display import Markdown
Markdown(f"The _radius_ of the circle is **{radius}**.")

Note that dynamically generated markdown will still be enclosed in the standard Quarto output divs. If you want to remove all of Quarto’s default output enclosures use the output: asis option. For example:
# %%
#| echo: false
#| output: asis
radius = 10
from IPython.display import Markdown
Markdown(f"The _radius_ of the circle is **{radius}**.")

Raw Cells
You can include raw cells (e.g. HTML or LaTeX) within scripts using the # %% [raw] cell delimiter along with a format attribute, for example:
# %% [raw] format="html"
"""
<iframe width="560" height="315" src="https://www.youtube.com/embed/lJIrF4YjHfQ?si=aP7PxA1Pz8IIoQUX"></iframe>
"""                          
'''),
            model_name=model_name
        )

        if model:
            return model

    log.error("Error initializing quarto model")    
    return None