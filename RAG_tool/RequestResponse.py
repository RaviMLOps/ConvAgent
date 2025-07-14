from  pydantic import BaseModel
from typing import Optional


class Response(BaseModel):
    intent : Optional[str]
    tool_used : Optional[str]
    tool_input:Optional[str]
    tool_output:Optional[str]
    final_response : Optional[str]

    
    # def __init__(self, **kwargs):
    #     self.intent = kwargs.get("intent")
    #     self.tool_used = kwargs.get("tool_used")
    #     self.tool_input = kwargs.get("tool_input")
    #     self.tool_output = kwargs.get("tool_output")
    #     self.final_response = kwargs.get("final_response")

    def compare(self, other_object : "Response"):
        # write logic to compare both objects.

        if self.intent == other_object.intent:
            print("the intent is same")

        compare_result = {"intent_comparision":self.intent == other_object.intent,
                          "tool_used comparision":self.tool_used == other_object.tool_used,
                          }

        return compare_result

class QnA(BaseModel):
    query : str
    answer : Response

    def __init__(self, query):
        self.query = query
        self.answergit  = None

    def set_response(self, answer:Response):
        self.answer = answer
