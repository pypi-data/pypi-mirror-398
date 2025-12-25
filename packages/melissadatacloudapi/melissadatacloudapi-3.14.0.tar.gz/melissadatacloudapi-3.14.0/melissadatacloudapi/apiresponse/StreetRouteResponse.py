from .ResponseBase import ResponseBase

class StreetRouteResponse(ResponseBase):
    def __init__(self, version="", units="", transmission_reference="", transmission_result="", total_records="", 
                 record_id="", results="", travel_time="", total_driving_distance="", records=None):
        self.version = version,
        self.units = units,
        self.transmission_reference = transmission_reference
        self.transmission_result = transmission_result
        self.total_records = total_records,
        self.record_id = record_id,
        self.results = results,
        self.travel_time = travel_time,
        self.total_driving_distance = total_driving_distance,
        self.records = records if records is not None else []

    @classmethod
    def populate_from_dict(cls, data: dict):
        cls.data = data
        return cls(
            version=data.get("Version", ""),
            units=data.get("Units", ""),
            transmission_reference=data.get("TransmissionReference", ""),
            transmission_result=data.get("TransmissionResult", ""),
            total_records=data.get("TotalRecords", ""),
            record_id=data.get("RecordID", ""),
            results=data.get("Results", ""),
            travel_time=data.get("TravelTime", ""),
            total_driving_distance=data.get("TotalDrivingDistance", ""),
            records=[StreetRouteRecord.from_dict(record) for record in data.get("Records", [])]
        )
    
    # Setters
    def set_version(self, version):
        self.version = version

    def set_units(self, units):
        self.units = units

    def set_transmission_reference(self, transmission_reference):
        self.transmission_reference = transmission_reference

    def set_transmission_result(self, transmission_result):
        self.transmission_result = transmission_result

    def set_total_records(self, total_records):
        self.total_records = total_records

    def set_record_id(self, record_id):
        self.record_id = record_id

    def set_results(self, results):
        self.results = results

    def set_travel_time(self, travel_time):
        self.travel_time = travel_time

    def set_total_driving_distance(self, total_driving_distance):
        self.total_driving_distance = total_driving_distance
    
    # Getters
    def get_version(self):
        return self.version or ""

    def get_units(self):
        return self.units or ""

    def get_transmission_reference(self):
        return self.transmission_reference or ""

    def get_transmission_result(self):
        return self.transmission_result or ""

    def get_total_records(self):
        return self.total_records or ""

    def get_record_id(self):
        return self.record_id or ""

    def get_results(self):
        return self.results or ""

    def get_travel_time(self):
        return self.travel_time or ""

    def get_total_driving_distance(self):
        return self.total_driving_distance or ""
        
class StreetRouteRecord(ResponseBase):
    def __init__(self, record_id="", results="", travel_time="", total_driving_distance=""):
        self.record_id = record_id
        self.results = results
        self.travel_time = travel_time
        self.total_driving_distance = total_driving_distance

    @classmethod
    def from_dict(cls, data):
        return cls(
            record_id=data.get("RecordID", ""),
            results=data.get("Results", ""),
            travel_time=data.get("TravelTime", ""),
            total_driving_distance=data.get("TotalDrivingDistance", "")
        )
    
    # Setters
    def set_record_id(self, record_id):
        self.record_id = record_id

    def set_results(self, results):
        self.results = results

    def set_travel_time(self, travel_time):
        self.travel_time = travel_time

    def set_total_driving_distance(self, total_driving_distance):
        self.total_driving_distance = total_driving_distance

    # Getters
    def get_record_id(self):
        return self.record_id or ""

    def get_results(self):
        return self.results or ""

    def get_travel_time(self):
        return self.travel_time or ""

    def get_total_driving_distance(self):
        return self.total_driving_distance or ""




