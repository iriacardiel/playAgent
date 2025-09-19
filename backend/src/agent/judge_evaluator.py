# from langgraph import Node
from agent.state import AgentState
from agent.prompts import get_judge_prompt

class JudgeNode():
    def __init__(self, state: AgentState):
        # judge_type could be 'user_input' or 'llm_output' or any custom type
        pass
        
    def run(self):
        # TODO ver si la distinción se hace aquí o a nivel del grafo
        is_safe = self.judge_content(self.input_text)
        return self.judge_node(is_safe)
        
    def judge_content(input_text: str) -> bool:
        """Returns True if content is safe, False if it violates rules."""
        prompt = [SystemMessage(content=get_judge_prompt()), input_text]
        response = llm.invoke(prompt)
        return response.strip().upper() == "SAFE"


    def judge_node(self, input_text):
        if self.judge_content(input_text):
            return input_text
        else:
            return "⚠️ Content blocked due to safety concerns."
        
    # # LLM Assistant Node
    # def LLM_node(self, state: AgentState):
    #     """LLM Assistant Node - Handles LLM interactions."""
    #     messages_list = self.filtermessages( 20, state["messages"])

    #     # Apply custom filtering
    #     llm_input = [
    #         SystemMessage(content=get_system_prompt(state.get("short_term_memories", []), cdu = "main")),
    #     ] + messages_list

    #     with open("./src/logs/llm_input.txt", "w") as f:
    #         f.write("Empty" if not llm_input else "\n" + "\n".join(
    #             f"{'DORI' if isinstance(m, AIMessage) else 'User' if isinstance(m, HumanMessage) else 'System' if isinstance(m, SystemMessage) else 'Tool'} - {m.content}"
    #             for m in llm_input
    #         ))
                
    #     # Call LLM
    #     ai_message = self.llm_with_tools.invoke(llm_input)

    #     # Token count (through LangChain AIMessage)
    #     log_token_usage(ai_message, messages_list)
        
    #     return {"messages": [ai_message]}
