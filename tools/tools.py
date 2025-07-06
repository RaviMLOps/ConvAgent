

class Tools:
    def book_flight(Customer_Name,From_City,To_City,Travel_date):
        #book_flight_to_db(Customer_Name,From_City,To_City)
        print(f"The book flight tool is called here....{Customer_Name}, {From_City},{To_City},{Travel_date}")

        #TODO make Book_flight API call

        return {"booked":"OK"}

    def cancel_flight(PNR,Lastname):
        #book_flight_to_db(Customer_Name,From_City,To_City)
        print(f"The cancel flight tool is called here....{PNR}, {Lastname}")


         #TODO make cancel_flight  API call
        return {"cancelled":"OK"}

    def check_availability(From_City,To_City,Travel_date):
        #book_flight_to_db(Customer_Name,From_City,To_City)
        print(f"The check_availability tool is called here....{Travel_date}, {From_City},{To_City}")

         #TODO make check availability  API call

        return {"check_availability ":"OK"}

    def booking_status(PNR,Lastname):
        #book_flight_to_db(Customer_Name,From_City,To_City)
        print(f"The booking_status tool is called here....{PNR}, {Lastname}")

        #TODO make booking status API call

        return {"booking_status ":"OK"}


    def refund_status(PNR,Lastname):
        #book_flight_to_db(Customer_Name,From_City,To_City)
        print(f"The Refund status tool is called here....{PNR}, {Lastname}")

        #TODO make refund status API call

        return {"booking_status ":"OK"}

    def RAG_tool(Customer_Name,From_City,To_City):
        #book_flight_to_db(Customer_Name,From_City,To_City)
        print(f"The RAG_tool tool is called here....{Customer_Name}, {From_City},{To_City}")

        #TODO Make RAG Tool call for this specific usecase

        return {"RAG_tool ":"OK"}


class Tools_description:

    def __init__(self):
        self.book_flight_json = {
            
        "name": "book_flight",
        "description": "Use this tool to book a flight for a user who has provided required parameters",
        "parameters": {
            "type": "object",
            "properties": {
                "Customer_Name": {
                    "type": "string",
                    "description": "This is the name of this user or traveller"
                },
                "From_City": {
                    "type": "string",
                    "description": "This is the source city from where the flight takes off"
                },
                "To_City": {
                    "type": "string",
                    "description":  "This is the destination city to where the flight lands "
                },
                "Travel_date": {
                    "type": "string",
                    "description":  "This is the destination city to where the flight lands "
                }

            },
            "required": ["Customer_Name","From_City","To_City"],
            "additionalProperties": False
        }}

        self.cancel_flight_json = {
        "name": "cancel_flight",
        "description": "Use this tool to cancel a flight. ",
        "parameters": {
            "type": "object",
            "properties": {
                "PNR": {
                    "type": "string",
                    "description": "This is the PNR details of the booking"
                },
                "Lastname": {
                    "type": "string",
                    "description": "Lastname of the traveller or user"
                }

            },
            "required": ["PNR","Lastname"],
            "additionalProperties": False
        }},

        self.check_availability = {
        "name": "check_availability",
        "description": "Use this tool check the availability of the flight ",
        "parameters": {
            "type": "object",
            "properties": {
                "From_City": {
                    "type": "string",
                    "description": "This is the source city from where the flight takes off"
                },
                "To_City": {
                    "type": "string",
                    "description":  "This is the destination city to where the flight lands "
                },
                "Travel_date": {
                    "type": "string",
                    "description":  "This is the destination city to where the flight lands "
                }

            },
            "required": ["From_City","To_City","Travel_date"],
            "additionalProperties": False
        }}

        self.booking_status = {
        "name": "booking_status",
        "description": "Use this tool check the status of the bookings ",
        "parameters": {
            "type": "object",
            "properties": {
                "PNR": {
                    "type": "string",
                    "description": "This is the PNR details of the booking"
                },
                "Lastname": {
                    "type": "string",
                    "description": "Lastname of the traveller or user"
                }

            },
            "required": ["PNR","Lastname"],
            "additionalProperties": False
        }}

        self.refund_staus = {
        "name": "refund_staus",
        "description": "Use this tool check the refund status of flight",
        "parameters": {
            "type": "object",
            "properties": {
                "PNR": {
                    "type": "string",
                    "description": "This is the PNR details of the booking"
                },
                "Lastname": {
                    "type": "string",
                    "description": "Lastname of the traveller or user"
                }

            },
            "required": ["PNR","Lastname"],
            "additionalProperties": False
        }}

    def get_tools_descriptions(self):
        print(f"========={self.cancel_flight_json}")
        return [self.book_flight_json,
                              self.check_availability,self.refund_staus, self.booking_status]
