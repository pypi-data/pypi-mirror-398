import datetime

class DateTimeTool:
    def __init__(self):
        """Initialize the Date Time tool."""
        self.description = "A tool for getting the current date and time. You can specify 'date', 'time', or 'datetime' as input to get the respective information."

    def run(self, query_type="date"):
        now = datetime.datetime.now()
        if query_type == "date":
            return now.strftime("%d-%m-%Y")
        elif query_type == "time":
            return now.strftime("%H:%M:%S")
        elif query_type == "datetime":
            return now.strftime("%d-%m-%Y %H:%M:%S")