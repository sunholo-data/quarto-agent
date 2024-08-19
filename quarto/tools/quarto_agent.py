from sunholo.genai import GenAIFunctionProcessor
from sunholo.utils import ConfigManager
from sunholo.gcs.add_file import add_file_to_gcs

from my_log import log

import subprocess
import os

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
        tools = self.config.vacConfig("tools")
        quarto_config = tools.get("quarto")
        
        def decide_to_go_on(go_on: bool):
            """
            Examine the chat history.  If the answer to the user's question has been answered, then go_on=False.
            If the chat history indicates the answer is still being looked for, then go_on=True.
            If there is no chat history, then go_on=True.
            If there is an error that can't be corrected or solved by you, then go_on=False.
            If there is an error but you think you can solve it by correcting your function arguments (such as an incorrect source), then go_on=True
            If you want to ask the user a question or for some more feedback, then go_on=False.
            
            Args:
                go_on: boolean Whether to continue searching or fetching from the AlloyDB database
            
            Returns:
                boolean: True to carry on, False to continue
            """
            return go_on
        
        def quarto_command(cmd:str) -> str:
            """
            Run a quarto command - will prefix the command with 'quarto' and run in the terminal

            Args: str: command to execute with quarto e.g. quarto 'cmd'

            Returns:
                str: The result of the command
            """
            try:
                result = subprocess.run(["quarto", cmd], capture_output=True, text=True)
                return result.stdout
            except Exception as e:
                return f"Error checking running Quarto cmd {cmd}: {str(e)}"
        
        def quarto_version() -> str:
            """
            Reports back what version of Quarto is available and what is installed on the server.

            Args: None

            Returns:
                str: Text about the version, the result of "quarto check" terminal command
            """
            try:
                result = subprocess.run(["quarto", "check"], capture_output=True, text=True)
                return result.stdout
            except Exception as e:
                return f"Error checking Quarto version: {str(e)}"

        def quarto_render(markdown_content: str, output_format: str = "html", output_filename: str = "output.html") -> dict:
            """
            Render a Quarto markdown document and upload the rendered output to a Google Cloud Storage bucket.
            
            Args:
                markdown_content (str): The Quarto markdown content to render.
                output_format (str): The desired output format (e.g., "html", "pdf"). Default is "html".
                output_filename (str): The filename for the rendered output. Default is "output.html".
            
            Returns:
                dict: A dictionary with the result of the rendering process, including the URL of the uploaded file.
            """
            try:
                # Write markdown content to a temporary file
                markdown_filename = "temp.qmd"
                with open(markdown_filename, 'w') as f:
                    f.write(markdown_content)
                
                # Render the markdown file using Quarto
                render_command = ["quarto", "render", markdown_filename, f"--to={output_format}", f"--output={output_filename}"]
                subprocess.run(render_command, check=True)

                # Upload the rendered file to Google Cloud Storage
                upload_to_gcs = self.upload_to_gcs(output_filename, file_type=output_format)
                
                return {"status": "success", "gcs_url": upload_to_gcs}
            
            except subprocess.CalledProcessError as e:
                return {"status": "error", "message": f"Error during Quarto rendering: {str(e)}"}
            except Exception as e:
                return {"status": "error", "message": f"General error: {str(e)}"}


        return {
            "quarto_render": quarto_render,
            "quarto_command": quarto_command,
            "quarto_version": quarto_version,
            "decide_to_go_on": decide_to_go_on
        }

def quarto_content(question: str, chat_history=[]) -> str:
    prompt_config = ConfigManager("quarto")
    alloydb_template = prompt_config.promptConfig("quarto_template")
    
    conversation_text = ""
    for human, ai in chat_history:
        conversation_text += f"Human: {human}\nAI: {ai}\n"

    return alloydb_template.format(the_question=question, chat_history=conversation_text[-10000:])


def get_quarto(config:ConfigManager, processor:QuartoProcessor):

    tools = config.vacConfig('tools')

    if tools and tools.get('quarto'):
        model_name = None
        if config.vacConfig('llm') != "vertex":
            model_name = 'gemini-1.5-flash'
        alloydb_model = processor.get_model(
            system_instruction=(
                    "You are a helpful Quarto agent that helps users create and render Quarto documents. "
                    "When you think the answer has been given to the satisfaction of the user, or you think no answer is possible, or you need user confirmation or input, you MUST use the decide_to_go_on(go_on=False) function"
                    "When you want to ask the question to the user, mark the go_on=False in the function"
                ),
            model_name=model_name
        )

        if alloydb_model:
            return alloydb_model

    log.error("Error initializing quarto model")    
    return None