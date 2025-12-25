from abc import ABC
from typing import List, TypeVar, Generic
from .RecordRequests import *

TRecord = TypeVar('TRecord')

class PostRequestBase(ABC, Generic[TRecord]):
    def __init__(self, records: List[TRecord], transmission_reference, options):
        self.transmission_reference = transmission_reference
        self.options = options
        self.records = records

class BusinessCoderPostRequest(PostRequestBase[BusinessCoderRecordRequest]):
    def __init__(self, records: List[BusinessCoderRecordRequest], id, t=None, opt=None, cols=None):
        super().__init__(records, t, opt)
        self.id = id
        self.cols = cols
        self.opt = opt
        self.t = t


    def to_dict(self):
        return {
            "T": self.t,
            "Opt": self.opt,
            "Records": [BusinessCoderRecordRequest.to_dict(record) for record in self.records],           
            "Id": self.id,
            "Cols": self.cols
        }

class GlobalAddressVerificationPostRequest(PostRequestBase[GlobalAddressVerificationRecordRequest]):
    def __init__(self, records: List[GlobalAddressVerificationRecordRequest], customer_id, transmission_reference=None, options=None):
        super().__init__(records, transmission_reference, options)
        self.customer_id = customer_id

    def to_dict(self):
        return {
            "TransmissionReference": self.transmission_reference,
            "Options": self.options,
            "Records": [GlobalAddressVerificationRecordRequest.to_dict(record) for record in self.records],           
            "CustomerId": self.customer_id
        }

class GlobalEmailPostRequest(PostRequestBase[GlobalEmailRecordRequest]):
    def __init__(self, records: List[GlobalEmailRecordRequest], customer_id, transmission_reference=None, options=None):
        super().__init__(records, transmission_reference, options)
        self.customer_id = customer_id

    def to_dict(self):
        return {
            "TransmissionReference": self.transmission_reference,
            "Options": self.options,
            "Records": [GlobalEmailRecordRequest.to_dict(record) for record in self.records],           
            "CustomerId": self.customer_id
        }
    
class GlobalIPPostRequest(PostRequestBase[GlobalIPRecordRequest]):
    def __init__(self, records: List[GlobalIPRecordRequest], customer_id, transmission_reference=None, options=None):   
        super().__init__(records, transmission_reference, options)
        self.customer_id = customer_id

    def to_dict(self):
        return {
            "TransmissionReference": self.transmission_reference,
            "Options": self.options,
            "Records": [GlobalIPRecordRequest.to_dict(record) for record in self.records],           
            "CustomerId": self.customer_id
        }

    
class GlobalNamePostRequest(PostRequestBase[GlobalNameRecordRequest]):
    def __init__(self, records: List[GlobalNameRecordRequest], customer_id, transmission_reference=None, options=None):   
        super().__init__(records, transmission_reference, options)
        self.customer_id = customer_id

    def to_dict(self):
        return {
            "TransmissionReference": self.transmission_reference,
            "Options": self.options,
            "Records": [GlobalNameRecordRequest.to_dict(record) for record in self.records],
            "CustomerId": self.customer_id
        }
    
class GlobalPhonePostRequest(PostRequestBase[GlobalPhoneRecordRequest]):
    def __init__(self, records: List[GlobalPhoneRecordRequest], customer_id, transmission_reference=None, options=None):   
        super().__init__(records, transmission_reference, options)
        self.customer_id = customer_id

    def to_dict(self):
        return {
            "TransmissionReference": self.transmission_reference,
            "Options": self.options,
            "Records": [GlobalPhoneRecordRequest.to_dict(record) for record in self.records],
            "CustomerId": self.customer_id
        }
    
class PersonatorConsumerPostRequest(PostRequestBase[PersonatorConsumerRecordRequest]):
    def __init__(self, records: List[PersonatorConsumerRecordRequest], customer_id, transmission_reference=None, options=None):   
        super().__init__(records, transmission_reference, options)
        self.customer_id = customer_id

    def to_dict(self):
        return {
            "TransmissionReference": self.transmission_reference,
            "Options": self.options,
            "Records": [PersonatorConsumerRecordRequest.to_dict(record) for record in self.records],
            "CustomerId": self.customer_id
        }
    
class PropertyPostRequest(PostRequestBase[PropertyRecordRequest]):
    def __init__(
        self, customer_id, records: List[PropertyRecordRequest], transmission_reference=None, options=None,
        columns="", total_records="", apn="", fips="", free_form="", property_mak="", owner_mak=""
    ):
        super().__init__(records, transmission_reference, options)

        self.customer_id = customer_id
        self.columns = columns
        self.total_records = total_records
        self.apn = apn
        self.fips = fips
        self.free_form = free_form
        self.property_mak = property_mak
        self.owner_mak = owner_mak

    def to_dict(self):
        return {
            "Records": [PropertyRecordRequest.to_dict(record) for record in self.records],
            "CustomerId": self.customer_id,
            "Columns": self.columns,
            "TotalRecords": self.total_records,
            "APN": self.apn,
            "FIPS": self.fips,
            "FreeForm": self.free_form,
            "PropertyMAK": self.property_mak,
            "OwnerMAK": self.owner_mak
        }
    

class SmartMoverPostRequest(PostRequestBase[SmartMoverRecordRequest]):
    def __init__(self, records: List[SmartMoverRecordRequest], customer_id, transmission_reference=None, options=None, job_id=None, 
                 paf_id=None, execution_id=None, actions=None, columns=None, opt_smart_mover_list_name=None):
        super().__init__(records, transmission_reference, options)
        self.customer_id = customer_id
        self.job_id = job_id
        self.paf_id = paf_id
        self.execution_id = execution_id
        self.actions = actions
        self.columns = columns
        self.opt_smart_mover_list_name = opt_smart_mover_list_name


    def to_dict(self):
        return {
            "Records": [SmartMoverRecordRequest.to_dict(record) for record in self.records],
            "CustomerID": self.customer_id,
            "TransmissionReference": self.transmission_reference,
            "Options": self.options,
            "JobID": self.job_id,
            "PafID": self.paf_id,
            "ExecutionID": self.execution_id,
            "Actions": self.actions,
            "Columns": self.columns,
            "OptSmartMoverListName": self.opt_smart_mover_list_name
        }

class SSNNameMatchPostRequest(PostRequestBase[SSNNameMatchRecordRequest]):
    def __init__(self, records: List[SSNNameMatchRecordRequest], customer_id, transmission_reference=None, options=None):
        super().__init__(records, transmission_reference, options)
        self.customer_id = customer_id

    def to_dict(self):
        return {
            "TransmissionReference": self.transmission_reference,
            "Options": self.options,
            "Records": [SSNNameMatchRecordRequest.to_dict(record) for record in self.records],           
            "CustomerId": self.customer_id
        }

class StreetRoutePostRequest(PostRequestBase[StreetRouteRecordRequest]):
    def __init__(self, records: List[StreetRouteRecordRequest], customer_id, transmission_reference=None, options=None):
        super().__init__(records, transmission_reference, options)
        self.customer_id = customer_id

    def to_dict(self):
        return {
            "TransmissionReference": self.transmission_reference,
            "Options": self.options,
            "Records": [StreetRouteRecordRequest.to_dict(record) for record in self.records],           
            "CustomerId": self.customer_id
        }




