from sunholo.genai import GenAIFunctionProcessor
from sunholo.utils import ConfigManager
from sunholo.gcs.add_file import add_file_to_gcs

from my_log import log

import subprocess
import os
import json
import traceback

class QuartoProcessor(GenAIFunctionProcessor):

    def upload_to_gcs(self, filename, file_type):
        log.info(f"Uploading {filename=} of {file_type=}")
        vector_name = self.config.vector_name

        file_url = add_file_to_gcs(filename, 
                                vector_name=vector_name,
                                metadata={"type": "quarto",
                                          "file_type": file_type},
                                bucket_filepath=f"quarto/{file_type}/{os.path.basename(filename)}")
        
        log.info(f"Uploaded to {file_url=}")

        return file_url
        
    def construct_tools(self) -> dict:
        #tools = self.config.vacConfig("tools")
        #if not tools:
        #    vac_name = self.config.vector_name
        #    raise ValueError(f"No config.vac.{vac_name}.tools found")
        #quarto_config = tools.get("quarto")

        def render_and_upload_quarto(markdown: str = "") -> dict:
            """
            A string of markdown is supplied to the markdown argument.
            The markdown must be quarto formatted to work with quarto.
            The markdown will be supplied to the quarto_cmd() function and execute `quarto render temp.qmd --to={format} --output={filename}`
            If successfully rendered, the output file will then be uploaded to a GCS bucket
            
            Args:
                markdown (str): The Quarto markdown content to render. If not provided, a demo markdown string will be used.
            
            Returns:
                dict: A dictionary with the result of the rendering process, including the URL of the uploaded file.
            """


            if not markdown:
                with open('tools/demo.qmd', 'r') as f:
                    markdown = f.read()
            
            try:
                # Write markdown content to a temporary file
                markdown_filename = "renders/temp.qmd"
                with open(markdown_filename, 'w') as f:
                    f.write(markdown)
                
                # Render the markdown file using Quarto
                format='html'
                filename='output.html'
                render_command = f"render {markdown_filename} --to={format} --output={filename}"
                result = quarto_command(render_command)
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
                upload_to_gcs = self.upload_to_gcs(filename, file_type=format)
                
                return json.dumps({
                    "status": "success",
                    "gcs_url": upload_to_gcs,
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
        
        def quarto_command(cmd: str) -> dict:
            """
            Run a Quarto command in the terminal and capture the output.
            Do not run commands starting with 'quarto' e.g. 'quarto preview' - instead use 'preview'.
            The 'quarto' command will be prefixed to your cmd.
            
            Args:
                cmd (str): The command to execute with Quarto (e.g., 'check', 'render <file>').
            
            Returns:
                dict: A dictionary containing 'stdout' and 'stderr' from the command execution.
                    If the command is successful (return code 0), 'status' will be 'success',
                    even if there is content in 'stderr'.
            """
            try:
                result = subprocess.run(["quarto"] + cmd.split(), capture_output=True, text=True)

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
            if result["stderr"]:
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
                ),
            model_name=model_name
        )

        if model:
            return model

    log.error("Error initializing quarto model")    
    return None