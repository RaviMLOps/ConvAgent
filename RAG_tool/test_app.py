from  rag_react_agent import ReActRAGAgent
from langchain.schema import AgentAction

from RequestResponse import Response

class TestLLM ():
            
    def __init__(self):
         # initialize agent
         self.react_agent = ReActRAGAgent()
         self.initialized = self.react_agent.initialize()
         self.agent = self.react_agent.agent_executor
         
         print(f"initialized : {self.initialized} and agent object type {type(self.agent)}")


    def run_query(self, query : str):
        result_object= self.react_agent.query(query)
        print(f"type of result_object {type(result_object)}")
        # call llm agent's query method to get response
        response = None
        tool_used = None
        tool_input = None
        tool_output_raw = None
        #extract intent, response and tool called.
        if isinstance(result_object, dict):
            answer = result_object.get("output", "No response generated.")
            intermediate_steps = result_object.get("intermediate_steps", [])
            print(f"intermediate steps : {intermediate_steps}")
            for step in intermediate_steps:
                if isinstance(step[0], AgentAction):
                    tool_used = step[0].tool
                    tool_input = step[0].tool_input
                tool_output_raw = step[1]  # typically a stringified JSON

            print(f"tool_used : {tool_used} and tool_input :{tool_input} and tool_output_raw : {tool_output_raw}")   

        elif isinstance(result_object, str):
            answer = result_object
        else:
            return f"New type object: {type(result_object)}"

        # answer = result_object.get("output", "No response generated.")
        # print(f"Tool used : {tool_used} \n Tool_input")
        print()
        response = Response(intent = tool_used,tool_used = tool_used, tool_input = tool_input,
                          tool_output = tool_output_raw, final_response = answer)

        # return response
        return response


if __name__ == "__main__":
    #test_llm = TestLLM()

    # get user query from console : TODO

    print("execute test queries....")
    query1 = "Can I cancel my flight just 2 hours before departure?"
    #actual_response1 = test_llm.run_query(query1)
    tool_used = "rag_query"
    tool_input = query1
    tool_output_raw = "hello i am mdhu"
    final_response =  "hello i am madhu"
    response = Response(intent = tool_used,tool_used = tool_used, tool_input = tool_input,
                          tool_output = tool_output_raw, final_response = final_response)
    print(response)
    expected_response1 = Response(intent = "rag_query", tool_used="rag_query",
                                  tool_input = "",
                                  tool_output = "",
                                  final_response = "Let me check the cancellation policy for close departure timings.")
    
    print(response.compare(expected_response1))




