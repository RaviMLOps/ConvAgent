from  pydantic import BaseModel

class Response(BaseModel):
    intent : str
    tool_used : str
    tool_input:str
    tool_output:str
    final_response : str

    def __init__(self, **kwargs):
        if "intent" in kwargs:
            self.intent = kwargs["intent"]
        if "tool_used" in kwargs:
            self.intent = kwargs["tool_used"]
        if "tool_input" in kwargs:
            self.intent = kwargs["tool_input"]
        if "tool_output" in kwargs:
            self.intent = kwargs["tool_output"]
        if "final_response" in kwargs:
            self.intent = kwargs["final_response"]

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
