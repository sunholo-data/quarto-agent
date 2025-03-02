from sunholo.utils import ConfigManager
from sunholo.vertex import init_genai
from sunholo.gcs import get_bytes_from_gcs

from tools.quarto_agent import get_quarto, QuartoProcessor

import mimetypes
import tempfile

from my_log import log

import google.generativeai as genai
import json

init_genai()

# kwargs supports - image_uri, mime
def vac_stream(question: str, vector_name:str, chat_history=[], callback=None, **kwargs):
    
    config = ConfigManager(vector_name)
    processor = QuartoProcessor(config)

    orchestrator = get_quarto(config, processor)
    if not orchestrator:
        msg = f"No quarto model could be configured for {vector_name}"
        log.error(msg)
        callback.on_llm_end(response=msg)
        return {"answer": msg}
    
    downloaded_file = None
    mime_type = None
    if 'image_uri' in kwargs:
        image_uri = kwargs['image_uri']
        mime_type = kwargs['mime']

        log.info(f"Found {image_uri} - downloading...")
        file_bytes = get_bytes_from_gcs(image_uri)
        extension = mimetypes.guess_extension(mime_type)
        if image_uri.endswith(".qmd") or image_uri.endswith(".md"):
            extension = ".qmd"

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=extension, dir="renders")
        downloaded_file = temp_file.name
        
        with open(downloaded_file, 'wb') as f:
            f.write(file_bytes)
        
        log.info(f"Created {downloaded_file} from {image_uri}")
    
    content = [f"Please help the user with their question:<user_input>{question}</user_input>"] 
               
    if downloaded_file:
        content.append(f"A local file is available to work with located at: {downloaded_file}")
        try:
            downloaded_content = genai.upload_file(downloaded_file)
            log.info(f"{downloaded_content=}")
            content.append(downloaded_content)
        except Exception as e:
            log.warning(f"Could not upload {downloaded_file=} via genai.upload_file() - {str(e)}")

    chat = orchestrator.start_chat()

    guardrail = 0
    guardrail_max = kwargs.get('max_steps', 10)
    big_text = ""
    usage_metadata = {
                        "prompt_token_count": 0,
                        "candidates_token_count": 0,
                        "total_token_count": 0,
                    }
    functions_called = []

    while guardrail < guardrail_max:

        callback.on_llm_new_token(
            token=f"\n----Loop [{guardrail}] Start------\n"
            )

        log.info(f"# Loop [{guardrail}] - {content=}")
        this_text = "" # reset for this loop
        response = []

        try:
            callback.on_llm_new_token(token="\n= Calling Agent\n")
            response = chat.send_message(content, stream=True)
            
        except Exception as e:
            msg = f"Error sending {content} to model: {str(e)}"
            log.info(msg)
            callback.on_llm_new_token(token=msg)
            break

        loop_metadata = response.usage_metadata
        if loop_metadata:
            usage_metadata = {
                "prompt_token_count": usage_metadata["prompt_token_count"] + (loop_metadata.prompt_token_count or 0),
                "candidates_token_count": usage_metadata["candidates_token_count"] + (loop_metadata.candidates_token_count or 0),
                "total_token_count": usage_metadata["total_token_count"] + (loop_metadata.total_token_count or 0),
            }
            callback.on_llm_new_token(token=(
                "\n-- Agent response\n" 
                f"prompt_token_count: [{loop_metadata.prompt_token_count}]/[{usage_metadata["prompt_token_count"]}] "
                f"candidates_token_count: [{loop_metadata.candidates_token_count}]/[{usage_metadata["candidates_token_count"]}] "
                f"total_token_count: [{loop_metadata.total_token_count}]/[{usage_metadata["total_token_count"]}] \n"
                ))
        loop_metadata = None
    
        for chunk in response:
            if not chunk:
                continue

            log.debug(f"[{guardrail}] {chunk=}")
            try:
                # Check if 'text' is an attribute of chunk and if it's a string
                if hasattr(chunk, 'text') and isinstance(chunk.text, str):
                    token = chunk.text
                    callback.on_llm_new_token(token=token)
                    big_text += token
                    this_text += token
                else:
                    log.info(f"skipping {chunk}")
                
            except ValueError as err:
                callback.on_llm_new_token(token=f"{str(err)} for {chunk=}")
        
        # change response to one with executed functions
        executed_responses = processor.process_funcs(response)
        log.info(f"[{guardrail}] {executed_responses=}")

        if executed_responses:  
            callback.on_llm_new_token(token="\nAgent function execution:\n")
            for executed_response in executed_responses:
                token = ""
                fn = executed_response.function_response.name
                fn_args = executed_response.function_response.response["args"]
                fn_result = executed_response.function_response.response["result"]
                log.info(f"{fn=}({fn_args}) {fn_result}]")

                try:
                    fn_result_json = json.loads(fn_result)
                except Exception:
                    log.warning(f"{fn_result} was not json decoded")
                    fn_result_json=None

                if fn == "decide_to_go_on":
                    token = f"\n\n{'STOPPING' if not fn_result.get('go_on') else 'CONTINUE'}: {fn_result.get('chat_summary')}"
                else:
                    token = f"--- function call: {fn}({fn_args}) ---"
                    if fn_result_json:
                        if fn_result_json.get('stdout'):
                            # ensures \n gets rendered correctly
                            text = fn_result_json.get('stdout').encode('utf-8').decode('unicode_escape')
                            token += text
                        if fn_result_json.get('stderr'):
                            text = fn_result_json.get('stdout').encode('utf-8').decode('unicode_escape')
                            token += text
                        if not fn_result_json.get('stdout') and fn_result_json.get('stderr'):
                            token += f" - result:\n{fn_result}\n"
                    else:
                        token += f" - result:\n{fn_result}\n"
                
                big_text += token
                this_text += token
                callback.on_llm_new_token(token=token)
        else:
            token = "\nNo function executions where found\n"
            callback.on_llm_new_token(token=token)
            big_text += token
            this_text += token

        if this_text:
            content.append(f"Agent: {this_text}")    
            log.info(f"[{guardrail}] Updated content:\n{this_text}")
        else:
            log.warning(f"[{guardrail}] No content created this loop")
            content.append(f"Agent: No response was found for loop [{guardrail}]")

        callback.on_llm_new_token(
            token=f"\n----Loop [{guardrail}] End------\n{usage_metadata}\n----------------------"
            )

        go_on_check = processor.check_function_result("decide_to_go_on", {"go_on":False})
        if go_on_check:
            log.info("Breaking agent loop")
            break
        
        guardrail += 1
        if guardrail > guardrail_max:
            log.warning("Guardrail kicked in, more than 10 loops")
            break

    callback.on_llm_end(response=big_text)
    log.info(f"orchestrator.response: {big_text}")

    metadata = {
        "question:": question,
        "chat_history": chat_history,
        "usage_metadata": usage_metadata,
        "functions_called": functions_called
    }

    return {"answer": big_text or "No answer was given", "metadata": metadata}


def vac(question: str, vector_name: str, chat_history=[], **kwargs):
    # Create a callback that does nothing for streaming if you don't want intermediate outputs
    class NoOpCallback:
        def on_llm_new_token(self, token):
            pass
        def on_llm_end(self, response):
            pass

    # Use the NoOpCallback for non-streaming behavior
    callback = NoOpCallback()

    # Pass all arguments to vac_stream and use the final return
    result = vac_stream(
        question=question, 
        vector_name=vector_name, 
        chat_history=chat_history, 
        callback=callback, 
        **kwargs
    )

    return result


