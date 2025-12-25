from .ResponseBase import ResponseBase

class SSNNameMatchResponse(ResponseBase):
    def __init__(self, version="", transmission_reference="", transmission_results="", total_records="", records=None):
        self.version = version
        self.transmission_reference = transmission_reference
        self.transmission_results = transmission_results
        self.total_records = total_records
        self.records = records if records is not None else []

    @classmethod
    def populate_from_dict(cls, data: dict):
        cls.data = data
        records = [SSNNameMatchRecord.from_dict(record) for record in data.get("Records", [])]
        return cls(
            version=data.get("Version", ""),
            transmission_reference=data.get("TransmissionReference", ""),
            transmission_results=data.get("TransmissionResults", ""),
            total_records = data.get("TotalRecords", ""),
            records=records
        )
    
    # Setters
    def set_version(self, version):
        self.version = version

    def set_transmission_reference(self, transmission_reference):
        self.transmission_reference = transmission_reference

    def set_transmission_results(self, transmission_results):
        self.transmission_results = transmission_results

    def set_total_records(self, total_records):
        self.total_records = total_records

    # Getters
    def get_version(self):
        return self.version or ""

    def get_transmission_reference(self):
        return self.transmission_reference or ""

    def get_transmission_results(self):
        return self.transmission_results or ""

    def get_total_records(self):
        return self.total_records or ""
    

class SSNNameMatchRecord:
    def __init__(
        self,
        record_id="",
        ssn="",
        issuing_state="",
        results="",
        results_from_data_source="",
    ):
        self.record_id = record_id
        self.ssn = ssn
        self.issuing_state = issuing_state
        self.results = results
        self.results_from_data_source = results_from_data_source

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            record_id=data.get("RecordID", ""),
            ssn=data.get("SSN", ""),
            issuing_state=data.get("IssuingState", ""),
            results=data.get("Results", ""),
            results_from_data_source=data.get("ResultsFromDataSource", ""),
        )
    
    # Setters
    def set_record_id(self, record_id):
        self._record_id = record_id

    def set_ssn(self, ssn):
        self._ssn = ssn

    def set_issuing_state(self, issuing_state):
        self._issuing_state = issuing_state

    def set_results(self, results):
        self._results = results

    def set_results_from_data_source(self, results_from_data_source):
        self.results_from_data_source = results_from_data_source

    # Getters
    def get_record_id(self):
        return self.record_id or ""

    def get_ssn(self):
        return self.ssn or ""

    def get_issuing_state(self):
        return self.issuing_state or ""

    def get_results(self):
        return self.results or ""

    def get_results_from_data_source(self):
        return self.results_from_data_source or ""






