from  rag_react_agent import ReActRAGAgent
from langchain.schema import AgentAction

from LLMResponse import Response

class TestLLM ():
            
    def __init__(self):
         # initialize agent
         self.react_agent = ReActRAGAgent()
         self.initialized = self.react_agent.initialize()
         self.agent = self.react_agent.agent_executor
         
         print(f"initialized : {self.initialized} and agent object type {type(self.agent)}")


    def run_query(self, query : str):
        result_object= self.agent.query(query)

        # call llm agent's query method to get response

        #extract intent, response and tool called.

        intermediate_steps = result_object.get("intermediate_steps", [])
        tool_used = None
        tool_input = None
        tool_output_raw = None

        for step in intermediate_steps:
            if isinstance(step[0], AgentAction):
                tool_used = step[0].tool
                tool_input = step[0].tool_input
            tool_output_raw = step[1]  # typically a stringified JSON

        answer = result_object.get("output", "No response generated.")
        print(f"Tool used : {tool_used} \n Tool_input")

        response = Response(intent = tool_used,tool_used = tool_used, tool_input = tool_input,
                             tool_output = tool_output_raw, final_response = answer)

        return response


if __name__ == "__main__":
    test_llm = TestLLM()

    # get user query from console : TODO

    print("execute test queries....")
    query1 = "Can I cancel my flight just 2 hours before departure?"
    actual_response1 = test_llm.run_query(query1)
    expected_response1 = Response(intent = "rag_tool", tool_used="rag_tool", 
                                  response = "Let me check the cancellation policy for close departure timings.")
    
    print(actual_response1.compare(expected_response1))




