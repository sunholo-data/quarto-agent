
from sunholo.utils import ConfigManager
from sunholo.vertex import (
    init_genai,
)

from tools.quarto_agent import get_quarto, QuartoProcessor

from my_log import log

init_genai()

# kwargs supports - image_uri, mime
def vac_stream(question: str, vector_name:str, chat_history=[], callback=None, **kwargs):
    
    config=ConfigManager(vector_name)
    processor = QuartoProcessor(config)

    orchestrator = get_quarto(config, processor)
    if not orchestrator:
        msg = f"No quarto model could be configured for {vector_name}"
        log.error(msg)
        callback.on_llm_end(response=msg)
        return {"answer": msg}

    chat = orchestrator.start_chat()

    guardrail = 0
    guardrail_max = kwargs.get('max_steps', 10)
    big_text = ""
    usage_metadata = None
    functions_called = []

    while guardrail < guardrail_max:

        conversation_text = ""
        for human, ai in chat_history:
            conversation_text += f"Human: {human}\nAI: {ai}\n"
        content = (
            "A user has asked a question related to Quarto. Here is what has happened so far: "
            f"<chat_history>{conversation_text}</chat_history> "
            f"Please help the user with their question:<user_input>{question}</user_input> "
            )

        log.info(f"# Loop [{guardrail}] - {content=}")
        response = chat.send_message([content], stream=True)
        this_text = "" # reset for this loop
        
        for chunk in response:
            try:
                token = ""
                log.debug(f"[{guardrail}] {chunk=}")
                # Check if 'text' is an attribute of chunk and if it's a string
                if hasattr(chunk, 'text') and isinstance(chunk.text, str):
                    token = chunk.text
                else:
                    log.info(f"skipping {chunk}")

                callback.on_llm_new_token(token=token)
                big_text += token
                this_text += token
                
                if not usage_metadata:
                    chunk_metadata = chunk.usage_metadata
                    usage_metadata = {
                        "prompt_token_count": chunk_metadata.prompt_token_count,
                        "candidates_token_count": chunk_metadata.candidates_token_count,
                        "total_token_count": chunk_metadata.total_token_count,
                    }

            except ValueError as err:
                callback.on_llm_new_token(token=f"{str(err)} for {chunk=}")
        
        # change response to one with executed functions
        executed_responses = processor.process_funcs(response)
        log.info(f"[{guardrail}] {executed_responses=}")

        token = ""
        for executed_response in executed_responses:
            fn = executed_response.function_response.name
            fn_args = executed_response.function_response.response["args"]
            fn_result = executed_response.function_response.response["result"]
            log.info(f"{fn=}({fn_args}) {fn_result}]")

            if fn == "decide_to_go_on":
                token = f"\n\nSTOPPING: {fn_result.get('chat_summary')}"
            else:
                token = f"# {fn}({fn_args}) result:\n{fn_result}"

            callback.on_llm_new_token(token=token)
            big_text += token
            this_text += token

        if this_text:
            chat_history.append(("<waiting for ai>", this_text))
            log.info(f"[{guardrail}] Updated chat_history: {chat_history}")

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


