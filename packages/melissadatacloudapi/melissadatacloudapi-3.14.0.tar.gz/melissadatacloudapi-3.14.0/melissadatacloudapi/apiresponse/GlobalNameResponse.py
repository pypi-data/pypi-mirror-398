from .ResponseBase import ResponseBase

class GlobalNameResponse(ResponseBase):
    def __init__(self, version="", transmission_reference="", transmission_results="", total_records="", records=None):
        self.version = version
        self.transmission_reference = transmission_reference
        self.transmission_results = transmission_results
        self.total_records = total_records
        self.records = records if records is not None else []

    @classmethod
    def populate_from_dict(cls, data: dict):
        records = [GlobalNameRecord.from_dict(record) for record in data.get("Records", [])]
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

class GlobalNameRecord(ResponseBase):
    def __init__(self, record_id="", results="", company="", name_prefix="", name_first="", name_middle="",
                 name_last="", name_suffix="", name_nickname="", name_prof_title="", gender="", name_prefix2="",
                 name_first2="", name_middle2="", name_last2="", name_suffix2="", name_nickname2="",
                 name_prof_title2="", gender2="", salutation="", extras=""):
        self.record_id = record_id
        self.results = results
        self.company = company
        self.name_prefix = name_prefix
        self.name_first = name_first
        self.name_middle = name_middle
        self.name_last = name_last
        self.name_suffix = name_suffix
        self.name_nickname = name_nickname
        self.name_prof_title = name_prof_title
        self.gender = gender
        self.name_prefix2 = name_prefix2
        self.name_first2 = name_first2
        self.name_middle2 = name_middle2
        self.name_last2 = name_last2
        self.name_suffix2 = name_suffix2
        self.name_nickname2 = name_nickname2
        self.name_prof_title2 = name_prof_title2
        self.gender2 = gender2
        self.salutation = salutation
        self.extras = extras

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            record_id=data.get("RecordID", ""),
            results=data.get("Results", ""),
            company=data.get("Company", ""),
            name_prefix=data.get("NamePrefix", ""),
            name_first=data.get("NameFirst", ""),
            name_middle=data.get("NameMiddle", ""),
            name_last=data.get("NameLast", ""),
            name_suffix=data.get("NameSuffix", ""),
            name_nickname=data.get("NameNickname", ""),
            name_prof_title=data.get("NameProfTitle", ""),
            gender=data.get("Gender", ""),
            name_prefix2=data.get("NamePrefix2", ""),
            name_first2=data.get("NameFirst2", ""),
            name_middle2=data.get("NameMiddle2", ""),
            name_last2=data.get("NameLast2", ""),
            name_suffix2=data.get("NameSuffix2", ""),
            name_nickname2=data.get("NameNickname2", ""),
            name_prof_title2=data.get("NameProfTitle2", ""),
            gender2=data.get("Gender2", ""),
            salutation=data.get("Salutation", ""),
            extras=data.get("Extras", "")
        )

    # Setters
    def set_record_id(self, record_id):
        self.record_id = record_id

    def set_results(self, results):
        self.results = results

    def set_company(self, company):
        self.company = company

    def set_name_prefix(self, name_prefix):
        self.name_prefix = name_prefix

    def set_name_first(self, name_first):
        self.name_first = name_first

    def set_name_middle(self, name_middle):
        self.name_middle = name_middle

    def set_name_last(self, name_last):
        self.name_last = name_last

    def set_name_suffix(self, name_suffix):
        self.name_suffix = name_suffix

    def set_name_nickname(self, name_nickname):
        self.name_nickname = name_nickname

    def set_name_prof_title(self, name_prof_title):
        self.name_prof_title = name_prof_title

    def set_gender(self, gender):
        self.gender = gender

    def set_name_prefix2(self, name_prefix2):
        self.name_prefix2 = name_prefix2

    def set_name_first2(self, name_first2):
        self.name_first2 = name_first2

    def set_name_middle2(self, name_middle2):
        self.name_middle2 = name_middle2

    def set_name_last2(self, name_last2):
        self.name_last2 = name_last2

    def set_name_suffix2(self, name_suffix2):
        self.name_suffix2 = name_suffix2

    def set_name_nickname2(self, name_nickname2):
        self.name_nickname2 = name_nickname2

    def set_name_prof_title2(self, name_prof_title2):
        self.name_prof_title2 = name_prof_title2

    def set_gender2(self, gender2):
        self.gender2 = gender2

    def set_salutation(self, salutation):
        self.salutation = salutation

    def set_extras(self, extras):
        self.extras = extras

    # Getters
    def get_record_id(self):
        return self.record_id or ""

    def get_results(self):
        return self.results or ""

    def get_company(self):
        return self.company or ""

    def get_name_prefix(self):
        return self.name_prefix or ""

    def get_name_first(self):
        return self.name_first or ""

    def get_name_middle(self):
        return self.name_middle or ""

    def get_name_last(self):
        return self.name_last or ""

    def get_name_suffix(self):
        return self.name_suffix or ""

    def get_name_nickname(self):
        return self.name_nickname or ""

    def get_name_prof_title(self):
        return self.name_prof_title or ""

    def get_gender(self):
        return self.gender or ""

    def get_name_prefix2(self):
        return self.name_prefix2 or ""

    def get_name_first2(self):
        return self.name_first2 or ""

    def get_name_middle2(self):
        return self.name_middle2 or ""

    def get_name_last2(self):
        return self.name_last2 or ""

    def get_name_suffix2(self):
        return self.name_suffix2 or ""

    def get_name_nickname2(self):
        return self.name_nickname2 or ""

    def get_name_prof_title2(self):
        return self.name_prof_title2 or ""

    def get_gender2(self):
        return self.gender2 or ""

    def get_salutation(self):
        return self.salutation or ""

    def get_extras(self):
        return self.extras or ""
