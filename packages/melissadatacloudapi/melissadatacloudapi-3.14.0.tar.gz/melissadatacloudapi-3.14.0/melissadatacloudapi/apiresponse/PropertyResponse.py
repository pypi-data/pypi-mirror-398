from .ResponseBase import ResponseBase

class PropertyResponse(ResponseBase):

    def __init__(self, version="", transmission_results="", total_records="", records=None):
        self.version = version
        self.transmission_results = transmission_results
        self.total_records = total_records
        self.records = records if records is not None else []

    @classmethod
    def populate_from_dict(cls, data: dict):
        cls.data = data
        records = [PropertyRecord.from_dict(record) for record in data.get("Records", [])]
        return cls(
            version=data.get("Version", ""),
            transmission_results=data.get("TransmissionResults", ""),
            total_records=data.get("TotalRecords", ""),
            records=records
        )
    
    # Setters
    def set_version(self, version):
        self.version = version

    def set_transmission_results(self, transmission_results):
        self.transmission_results = transmission_results

    def set_total_records(self, total_records):
        self.total_records = total_records

    # Getters
    def get_version(self):
        return self.version or ""

    def get_transmission_results(self):
        return self.transmission_results or ""
    
    def get_total_records(self):
        return self.total_records or ""
    

class PropertyRecord:
    def __init__( self, doc_info=None, tx_def_info=None, tx_amt_info=None, primary_grantor=None, primary_grantee=None, title_comp_info=None, 
                  mortgage1=None, record_id="", results="", parcel=None, legal=None, property_address=None, parsed_property_address=None, 
                  primary_owner=None, owner_address=None, last_deed_owner_info=None, current_deed=None, tax=None, property_use_info=None, 
                  sale_info=None, property_size=None, pool=None, int_struct_info=None, int_room_info=None, int_amentities=None, ext_struct_info=None, 
                  ext_amentities=None, ext_buildings=None, utilities=None, parking=None, yard_garden_info=None, estimated_value=None, shape=None, 
                  mak="", base_mak="", fips="", apn="", property_city="", property_state="", property_zip="", property_plus4=""
                ):
        # For LookupDeeds endpoint
        self.doc_info = doc_info
        self.tx_def_info = tx_def_info
        self.tx_amt_info = tx_amt_info
        self.primary_grantor = primary_grantor
        self.primary_grantee = primary_grantee
        self.title_comp_info = title_comp_info
        self.mortgage1 = mortgage1
        
        # For LookupPropertyEndpoint
        self.record_id = record_id
        self.results = results
        self.parcel = parcel
        self.legal = legal
        self.property_address = property_address
        self.parsed_property_address = parsed_property_address
        self.primary_owner = primary_owner
        self.owner_address = owner_address
        self.last_deed_owner_info = last_deed_owner_info
        self.current_deed = current_deed
        self.tax = tax
        self.property_use_info = property_use_info
        self.sale_info = sale_info
        self.property_size = property_size
        self.pool = pool
        self.int_struct_info = int_struct_info
        self.int_room_info = int_room_info
        self.int_amentities = int_amentities
        self.ext_struct_info = ext_struct_info
        self.ext_amentities = ext_amentities
        self.ext_buildings = ext_buildings
        self.utilities = utilities
        self.parking = parking
        self.yard_garden_info = yard_garden_info
        self.estimated_value = estimated_value
        self.shape = shape
        
        # For Lookup HomesByOwner endpoint
        self.mak = mak
        self.base_mak = base_mak
        self.fips = fips
        self.apn = apn
        self.property_city = property_city
        self.property_state = property_state
        self.property_zip = property_zip
        self.property_plus4 = property_plus4
        

    @classmethod
    def from_dict(cls, data):
        cls.data = data
        return cls(
            doc_info=PropertyDocInfo.from_dict(data.get("DocInfo")) if data.get("DocInfo") else None,
            tx_def_info=PropertyTxDefInfo.from_dict(data.get("TxDefInfo")) if data.get("TxDefInfo") else None,
            tx_amt_info=PropertyTxAmtInfo.from_dict(data.get("TxAmtInfo")) if data.get("TxAmtInfo") else None,
            primary_grantor=PropertyPrimaryGrantor.from_dict(data.get("PrimaryGrantor")) if data.get("PrimaryGrantor") else None,
            primary_grantee=PropertyPrimaryGrantee.from_dict(data.get("PrimaryGrantee")) if data.get("PrimaryGrantee") else None,
            title_comp_info=PropertyTitleCompInfo.from_dict(data.get("TitleCompInfo")) if data.get("TitleCompInfo") else None,
            mortgage1=PropertyMortgage1.from_dict(data.get("Mortgage1")) if data.get("Mortgage1") else None,
            record_id=data.get("RecordID", ""),
            results=data.get("Results", ""),
            parcel=PropertyParcel.from_dict(data.get("Parcel")) if data.get("Parcel") else None,
            legal=PropertyLegal.from_dict(data.get("Legal")) if data.get("Legal") else None,
            property_address=data.get("PropertyAddress"),
            parsed_property_address=PropertyParsedPropertyAddress.from_dict(data.get("ParsedPropertyAddress")) if data.get("ParsedPropertyAddress") else None,
            primary_owner=PropertyPrimaryOwner.from_dict(data.get("PrimaryOwner")) if data.get("PrimaryOwner") else None,
            owner_address=PropertyOwnerAddress.from_dict(data.get("OwnerAddress")) if data.get("OwnerAddress") else None,
            last_deed_owner_info=PropertyLastDeedOwnerInfo.from_dict(data.get("LastDeedOwnerInfo")) if data.get("LastDeedOwnerInfo") else None,
            current_deed=PropertyCurrentDeed.from_dict(data.get("CurrentDeed")) if data.get("CurrentDeed") else None,
            tax=PropertyTax.from_dict(data.get("Tax")) if data.get("Tax") else None,
            property_use_info=PropertyUseInfo.from_dict(data.get("PropertyUseInfo")) if data.get("PropertyUseInfo") else None,
            sale_info=PropertySaleInfo.from_dict(data.get("SaleInfo")) if data.get("SaleInfo") else None,
            property_size=PropertySize.from_dict(data.get("PropertySize")) if data.get("PropertySize") else None,
            pool=PropertyPool.from_dict(data.get("Pool")) if data.get("Pool") else None,
            int_struct_info=PropertyIntRoomInfo.from_dict(data.get("IntStructInfo")) if data.get("IntStructInfo") else None,
            int_room_info=PropertyIntRoomInfo.from_dict(data.get("IntRoomInfo")) if data.get("IntRoomInfo") else None,
            int_amentities=PropertyIntAmentities.from_dict(data.get("IntAmentities")) if data.get("IntAmentities") else None,
            ext_struct_info=PropertyExtStructInfo.from_dict(data.get("ExtStructInfo")) if data.get("ExtStructInfo") else None,
            ext_amentities=PropertyExtAmentities.from_dict(data.get("ExtAmentities")) if data.get("ExtAmentities") else None,
            ext_buildings=PropertyExtBuildings.from_dict(data.get("ExtBuildings")) if data.get("ExtBuildings") else None,
            utilities=PropertyUtilities.from_dict(data.get("Utilities")) if data.get("Utilities") else None,
            parking=PropertyParking.from_dict(data.get("Parking")) if data.get("Parking") else None,
            yard_garden_info=PropertyYardGardenInfo.from_dict(data.get("YardGardenInfo")) if data.get("YardGardenInfo") else None,
            estimated_value=PropertyEstimatedValue.from_dict(data.get("EstimatedValue")) if data.get("EstimatedValue") else None,
            shape=PropertyShape.from_dict(data.get("Shape")) if data.get("Shape") else None,
            mak=data.get("MAK", ""),
            base_mak=data.get("BaseMAK", ""),
            fips=data.get("FIPS", ""),
            apn=data.get("APN", ""),
            property_city=data.get("PropertyCity", ""),
            property_state=data.get("PropertyState", ""),
            property_zip=data.get("PropertyZip", ""),
            property_plus4=data.get("PropertyPlus4", "")
        )


    # Setters
    def set_record_id(self, record_id):
        self.record_id = record_id

    def set_results(self, results):
        self.results = results

    def set_mak(self, mak):
        self.mak = mak

    def set_base_mak(self, base_mak):
        self.base_mak = base_mak

    def set_fips(self, fips):
        self.fips = fips

    def set_apn(self, apn):
        self.apn = apn

    def set_property_address(self, property_address):
        self.property_address = property_address

    def set_property_city(self, property_city):
        self.property_city = property_city

    def set_property_state(self, property_state):
        self.property_state = property_state

    def set_property_zip(self, property_zip):
        self.property_zip = property_zip

    def set_property_plus4(self, property_plus4):
        self.property_plus4 = property_plus4

    # Getters
    def get_record_id(self):
        return self.record_id or ""

    def get_results(self):
        return self.results or ""

    def get_mak(self):
        return self.mak or ""

    def get_base_mak(self):
        return self.base_mak or ""

    def get_fips(self):
        return self.fips or ""

    def get_apn(self):
        return self.apn or ""

    def get_property_address(self):
        return self.property_address if isinstance(self.property_address, str) else ""

    def get_property_city(self):
        return self.property_city or ""

    def get_property_state(self):
        return self.property_state or ""

    def get_property_zip(self):
        return self.property_zip or ""

    def get_property_plus4(self):
        return self.property_plus4 or ""


class PropertyDocInfo:
    def __init__(
        self,
        type_code="",
        instrument_number="",
        book="",
        page="",
        instrument_date="",
        recording_date=""
    ):
        self.type_code = type_code
        self.instrument_number = instrument_number
        self.book = book
        self.page = page
        self.instrument_date = instrument_date
        self.recording_date = recording_date

    @classmethod
    def from_dict(cls, data):
        return cls(
            type_code=data.get("TypeCode", ""),
            instrument_number=data.get("InstrumentNumber", ""),
            book=data.get("Book", ""),
            page=data.get("Page", ""),
            instrument_date=data.get("InstrumentDate", ""),
            recording_date=data.get("RecordingDate", "")
        )

    # Setters
    def set_type_code(self, type_code):
        self.type_code = type_code

    def set_instrument_number(self, instrument_number):
        self.instrument_number = instrument_number

    def set_book(self, book):
        self.book = book

    def set_page(self, page):
        self.page = page

    def set_instrument_date(self, instrument_date):
        self.instrument_date = instrument_date

    def set_recording_date(self, recording_date):
        self.recording_date = recording_date

    # Getters
    def get_type_code(self):
        return self.type_code or ""

    def get_instrument_number(self):
        return self.instrument_number or ""

    def get_book(self):
        return self.book or ""

    def get_page(self):
        return self.page or ""

    def get_instrument_date(self):
        return self.instrument_date or ""

    def get_recording_date(self):
        return self.recording_date or ""


class PropertyTxDefInfo:
    def __init__(
        self,
        transaction_type="",
        foreclosure_auction_sale="",
        transfer_info_distress_circumstance_code="",
        quitcalim_flag="",
        transfer_info_multi_parcel_flag="",
        arms_length_flag="",
        partial_interest=""
    ):
        self.transaction_type = transaction_type
        self.foreclosure_auction_sale = foreclosure_auction_sale
        self.transfer_info_distress_circumstance_code = transfer_info_distress_circumstance_code
        self.quitcalim_flag = quitcalim_flag
        self.transfer_info_multi_parcel_flag = transfer_info_multi_parcel_flag
        self.arms_length_flag = arms_length_flag
        self.partial_interest = partial_interest

    @classmethod
    def from_dict(cls, data):
        return cls(
            transaction_type=data.get("TransactionType", ""),
            foreclosure_auction_sale=data.get("ForeclosureAuctionSale", ""),
            transfer_info_distress_circumstance_code=data.get("TransferInfoDistressCircumstanceCode", ""),
            quitcalim_flag=data.get("QuitcalimFlag", ""),
            transfer_info_multi_parcel_flag=data.get("TransferInfoMultiParcelFlag", ""),
            arms_length_flag=data.get("ArmsLengthFlag", ""),
            partial_interest=data.get("PartialInterest", "")
        )

    # Setters
    def set_transaction_type(self, transaction_type):
        self.transaction_type = transaction_type

    def set_foreclosure_auction_sale(self, foreclosure_auction_sale):
        self.foreclosure_auction_sale = foreclosure_auction_sale

    def set_transfer_info_distress_circumstance_code(self, code):
        self.transfer_info_distress_circumstance_code = code

    def set_quitcalim_flag(self, quitcalim_flag):
        self.quitcalim_flag = quitcalim_flag

    def set_transfer_info_multi_parcel_flag(self, flag):
        self.transfer_info_multi_parcel_flag = flag

    def set_arms_length_flag(self, arms_length_flag):
        self.arms_length_flag = arms_length_flag

    def set_partial_interest(self, partial_interest):
        self.partial_interest = partial_interest

    # Getters
    def get_transaction_type(self):
        return self.transaction_type or ""

    def get_foreclosure_auction_sale(self):
        return self.foreclosure_auction_sale or ""

    def get_transfer_info_distress_circumstance_code(self):
        return self.transfer_info_distress_circumstance_code or ""

    def get_quitcalim_flag(self):
        return self.quitcalim_flag or ""

    def get_transfer_info_multi_parcel_flag(self):
        return self.transfer_info_multi_parcel_flag or ""

    def get_arms_length_flag(self):
        return self.arms_length_flag or ""

    def get_partial_interest(self):
        return self.partial_interest or ""


class PropertyTxAmtInfo:
    def __init__(
        self,
        transfer_amount="",
        transfer_amount_info_accuracy="",
        transfer_tax_total="",
        transfer_tax_county=""
    ):
        self.transfer_amount = transfer_amount
        self.transfer_amount_info_accuracy = transfer_amount_info_accuracy
        self.transfer_tax_total = transfer_tax_total
        self.transfer_tax_county = transfer_tax_county

    @classmethod
    def from_dict(cls, data):
        return cls(
            transfer_amount=data.get("TransferAmount", ""),
            transfer_amount_info_accuracy=data.get("TransferAmountInfoAccuracy", ""),
            transfer_tax_total=data.get("TransferTaxTotal", ""),
            transfer_tax_county=data.get("TransferTaxCounty", "")
        )

    # Setters
    def set_transfer_amount(self, transfer_amount):
        self.transfer_amount = transfer_amount

    def set_transfer_amount_info_accuracy(self, transfer_amount_info_accuracy):
        self.transfer_amount_info_accuracy = transfer_amount_info_accuracy

    def set_transfer_tax_total(self, transfer_tax_total):
        self.transfer_tax_total = transfer_tax_total

    def set_transfer_tax_county(self, transfer_tax_county):
        self.transfer_tax_county = transfer_tax_county

    # Getters
    def get_transfer_amount(self):
        return self.transfer_amount or ""

    def get_transfer_amount_info_accuracy(self):
        return self.transfer_amount_info_accuracy or ""

    def get_transfer_tax_total(self):
        return self.transfer_tax_total or ""

    def get_transfer_tax_county(self):
        return self.transfer_tax_county or ""


class PropertyPrimaryGrantor:
    def __init__(
        self,
        name1_full="",
        name1_first="",
        name1_middle="",
        name1_last="",
        name1_suffix="",
        name1_class_type="",
        name1_legal_type="",
        name2_full="",
        name2_first="",
        name2_middle="",
        name2_last="",
        name2_suffix="",
        name2_class_type="",
        name2_legal_type=""
    ):
        self.name1_full = name1_full
        self.name1_first = name1_first
        self.name1_middle = name1_middle
        self.name1_last = name1_last
        self.name1_suffix = name1_suffix
        self.name1_class_type = name1_class_type
        self.name1_legal_type = name1_legal_type
        self.name2_full = name2_full
        self.name2_first = name2_first
        self.name2_middle = name2_middle
        self.name2_last = name2_last
        self.name2_suffix = name2_suffix
        self.name2_class_type = name2_class_type
        self.name2_legal_type = name2_legal_type

    @classmethod
    def from_dict(cls, data):
        return cls(
            name1_full=data.get("Name1Full", ""),
            name1_first=data.get("Name1First", ""),
            name1_middle=data.get("Name1Middle", ""),
            name1_last=data.get("Name1Last", ""),
            name1_suffix=data.get("Name1Suffix", ""),
            name1_class_type=data.get("Name1ClassType", ""),
            name1_legal_type=data.get("Name1LegalType", ""),
            name2_full=data.get("Name2Full", ""),
            name2_first=data.get("Name2First", ""),
            name2_middle=data.get("Name2Middle", ""),
            name2_last=data.get("Name2Last", ""),
            name2_suffix=data.get("Name2Suffix", ""),
            name2_class_type=data.get("Name2ClassType", ""),
            name2_legal_type=data.get("Name2LegalType", "")
        )

    # Setters
    def set_name1_full(self, name1_full):
        self.name1_full = name1_full

    def set_name1_first(self, name1_first):
        self.name1_first = name1_first

    def set_name1_middle(self, name1_middle):
        self.name1_middle = name1_middle

    def set_name1_last(self, name1_last):
        self.name1_last = name1_last

    def set_name1_suffix(self, name1_suffix):
        self.name1_suffix = name1_suffix

    def set_name1_class_type(self, name1_class_type):
        self.name1_class_type = name1_class_type

    def set_name1_legal_type(self, name1_legal_type):
        self.name1_legal_type = name1_legal_type

    def set_name2_full(self, name2_full):
        self.name2_full = name2_full

    def set_name2_first(self, name2_first):
        self.name2_first = name2_first

    def set_name2_middle(self, name2_middle):
        self.name2_middle = name2_middle

    def set_name2_last(self, name2_last):
        self.name2_last = name2_last

    def set_name2_suffix(self, name2_suffix):
        self.name2_suffix = name2_suffix

    def set_name2_class_type(self, name2_class_type):
        self.name2_class_type = name2_class_type

    def set_name2_legal_type(self, name2_legal_type):
        self.name2_legal_type = name2_legal_type

    # Getters
    def get_name1_full(self):
        return self.name1_full or ""

    def get_name1_first(self):
        return self.name1_first or ""

    def get_name1_middle(self):
        return self.name1_middle or ""

    def get_name1_last(self):
        return self.name1_last or ""

    def get_name1_suffix(self):
        return self.name1_suffix or ""

    def get_name1_class_type(self):
        return self.name1_class_type or ""

    def get_name1_legal_type(self):
        return self.name1_legal_type or ""

    def get_name2_full(self):
        return self.name2_full or ""

    def get_name2_first(self):
        return self.name2_first or ""

    def get_name2_middle(self):
        return self.name2_middle or ""

    def get_name2_last(self):
        return self.name2_last or ""

    def get_name2_suffix(self):
        return self.name2_suffix or ""

    def get_name2_class_type(self):
        return self.name2_class_type or ""

    def get_name2_legal_type(self):
        return self.name2_legal_type or ""


class PropertyPrimaryGrantee:
    def __init__(
        self,
        name1_full="",
        name1_first="",
        name1_middle="",
        name1_last="",
        name1_suffix="",
        name1_class_type="",
        name1_legal_type="",
        name2_full="",
        name2_first="",
        name2_middle="",
        name2_last="",
        name2_suffix="",
        name2_class_type=""
    ):
        self.name1_full = name1_full
        self.name1_first = name1_first
        self.name1_middle = name1_middle
        self.name1_last = name1_last
        self.name1_suffix = name1_suffix
        self.name1_class_type = name1_class_type
        self.name1_legal_type = name1_legal_type
        self.name2_full = name2_full
        self.name2_first = name2_first
        self.name2_middle = name2_middle
        self.name2_last = name2_last
        self.name2_suffix = name2_suffix
        self.name2_class_type = name2_class_type

    @classmethod
    def from_dict(cls, data):
        return cls(
            name1_full=data.get("Name1Full", ""),
            name1_first=data.get("Name1First", ""),
            name1_middle=data.get("Name1Middle", ""),
            name1_last=data.get("Name1Last", ""),
            name1_suffix=data.get("Name1Suffix", ""),
            name1_class_type=data.get("Name1ClassType", ""),
            name1_legal_type=data.get("Name1LegalType", ""),
            name2_full=data.get("Name2Full", ""),
            name2_first=data.get("Name2First", ""),
            name2_middle=data.get("Name2Middle", ""),
            name2_last=data.get("Name2Last", ""),
            name2_suffix=data.get("Name2Suffix", ""),
            name2_class_type=data.get("Name2ClassType", "")
        )

    # Setters
    def set_name1_full(self, name1_full):
        self.name1_full = name1_full

    def set_name1_first(self, name1_first):
        self.name1_first = name1_first

    def set_name1_middle(self, name1_middle):
        self.name1_middle = name1_middle

    def set_name1_last(self, name1_last):
        self.name1_last = name1_last

    def set_name1_suffix(self, name1_suffix):
        self.name1_suffix = name1_suffix

    def set_name1_class_type(self, name1_class_type):
        self.name1_class_type = name1_class_type

    def set_name1_legal_type(self, name1_legal_type):
        self.name1_legal_type = name1_legal_type

    def set_name2_full(self, name2_full):
        self.name2_full = name2_full

    def set_name2_first(self, name2_first):
        self.name2_first = name2_first

    def set_name2_middle(self, name2_middle):
        self.name2_middle = name2_middle

    def set_name2_last(self, name2_last):
        self.name2_last = name2_last

    def set_name2_suffix(self, name2_suffix):
        self.name2_suffix = name2_suffix

    def set_name2_class_type(self, name2_class_type):
        self.name2_class_type = name2_class_type

    # Getters
    def get_name1_full(self):
        return self.name1_full or ""

    def get_name1_first(self):
        return self.name1_first or ""

    def get_name1_middle(self):
        return self.name1_middle or ""

    def get_name1_last(self):
        return self.name1_last or ""

    def get_name1_suffix(self):
        return self.name1_suffix or ""

    def get_name1_class_type(self):
        return self.name1_class_type or ""

    def get_name1_legal_type(self):
        return self.name1_legal_type or ""

    def get_name2_full(self):
        return self.name2_full or ""

    def get_name2_first(self):
        return self.name2_first or ""

    def get_name2_middle(self):
        return self.name2_middle or ""

    def get_name2_last(self):
        return self.name2_last or ""

    def get_name2_suffix(self):
        return self.name2_suffix or ""

    def get_name2_class_type(self):
        return self.name2_class_type or ""


class PropertyTitleCompInfo:
    def __init__(
        self,
        standardized_name="",
        title_company_raw=""
    ):
        self.standardized_name = standardized_name
        self.title_company_raw = title_company_raw

    @classmethod
    def from_dict(cls, data):
        return cls(
            standardized_name=data.get("StandardizedName", ""),
            title_company_raw=data.get("TitleCompanyRaw", "")
        )

    # Setters
    def set_standardized_name(self, standardized_name):
        self.standardized_name = standardized_name

    def set_title_company_raw(self, title_company_raw):
        self.title_company_raw = title_company_raw

    # Getters
    def get_standardized_name(self):
        return self.standardized_name or ""

    def get_title_company_raw(self):
        return self.title_company_raw or ""


class PropertyMortgage1:
    def __init__(
        self,
        doc_number_formatted="",
        instrument_number="",
        book="",
        page="",
        recording_date="",
        type_="",
        amount="",
        lender_full_name="",
        lender_first_name="",
        lender_last_name="",
        lender_type="",
        is_lender_seller="",
        term_date="",
        prepayment_penalty_flag="",
        prepayment_term="",
        interest_rate_type="",
        interest_rate="",
        interest_type_initial="",
        interest_margin="",
        interest_rate_max="",
        adjustable_rate_index="",
        interest_only_flag="",
        interest_only_period="",
        adjustable_rate_rider_flag="",
        interest_type_change_date="",
        min_interest_rate_first_change="",
        max_interest_rate_first_change="",
        interest_change_freq=""
    ):
        self.doc_number_formatted = doc_number_formatted
        self.instrument_number = instrument_number
        self.book = book
        self.page = page
        self.recording_date = recording_date
        self.type = type_
        self.amount = amount
        self.lender_full_name = lender_full_name
        self.lender_first_name = lender_first_name
        self.lender_last_name = lender_last_name
        self.lender_type = lender_type
        self.is_lender_seller = is_lender_seller
        self.term_date = term_date
        self.prepayment_penalty_flag = prepayment_penalty_flag
        self.prepayment_term = prepayment_term
        self.interest_rate_type = interest_rate_type
        self.interest_rate = interest_rate
        self.interest_type_initial = interest_type_initial
        self.interest_margin = interest_margin
        self.interest_rate_max = interest_rate_max
        self.adjustable_rate_index = adjustable_rate_index
        self.interest_only_flag = interest_only_flag
        self.interest_only_period = interest_only_period
        self.adjustable_rate_rider_flag = adjustable_rate_rider_flag
        self.interest_type_change_date = interest_type_change_date
        self.min_interest_rate_first_change = min_interest_rate_first_change
        self.max_interest_rate_first_change = max_interest_rate_first_change
        self.interest_change_freq = interest_change_freq

    @classmethod
    def from_dict(cls, data):
        return cls(
            doc_number_formatted=data.get("DocNumberFormatted", ""),
            instrument_number=data.get("InstrumentNumber", ""),
            book=data.get("Book", ""),
            page=data.get("Page", ""),
            recording_date=data.get("RecordingDate", ""),
            type_=data.get("Type", ""),
            amount=data.get("Amount", ""),
            lender_full_name=data.get("LenderFullName", ""),
            lender_first_name=data.get("LenderFirstName", ""),
            lender_last_name=data.get("LenderLastName", ""),
            lender_type=data.get("LenderType", ""),
            is_lender_seller=data.get("IsLenderSeller", ""),
            term_date=data.get("TermDate", ""),
            prepayment_penalty_flag=data.get("PrepaymentPenaltyFlag", ""),
            prepayment_term=data.get("PrepaymentTerm", ""),
            interest_rate_type=data.get("InterestRateType", ""),
            interest_rate=data.get("InterestRate", ""),
            interest_type_initial=data.get("InterestTypeInitial", ""),
            interest_margin=data.get("InterestMargin", ""),
            interest_rate_max=data.get("InterestRateMax", ""),
            adjustable_rate_index=data.get("AdjustableRateIndex", ""),
            interest_only_flag=data.get("InterestOnlyFlag", ""),
            interest_only_period=data.get("InterestOnlyPeriod", ""),
            adjustable_rate_rider_flag=data.get("AdjustableRateRiderFlag", ""),
            interest_type_change_date=data.get("InterestTypeChangeDate", ""),
            min_interest_rate_first_change=data.get("MinInterestRateFirstChange", ""),
            max_interest_rate_first_change=data.get("MaxInterestRateFirstChange", ""),
            interest_change_freq=data.get("InterestChangeFreq", "")
        )

    # Setters
    def set_doc_number_formatted(self, doc_number_formatted):
        self.doc_number_formatted = doc_number_formatted

    def set_instrument_number(self, instrument_number):
        self.instrument_number = instrument_number

    def set_book(self, book):
        self.book = book

    def set_page(self, page):
        self.page = page

    def set_recording_date(self, recording_date):
        self.recording_date = recording_date

    def set_type(self, type_):
        self.type = type_

    def set_amount(self, amount):
        self.amount = amount

    def set_lender_full_name(self, lender_full_name):
        self.lender_full_name = lender_full_name

    def set_lender_first_name(self, lender_first_name):
        self.lender_first_name = lender_first_name

    def set_lender_last_name(self, lender_last_name):
        self.lender_last_name = lender_last_name

    def set_lender_type(self, lender_type):
        self.lender_type = lender_type

    def set_is_lender_seller(self, is_lender_seller):
        self.is_lender_seller = is_lender_seller

    def set_term_date(self, term_date):
        self.term_date = term_date

    def set_prepayment_penalty_flag(self, prepayment_penalty_flag):
        self.prepayment_penalty_flag = prepayment_penalty_flag

    def set_prepayment_term(self, prepayment_term):
        self.prepayment_term = prepayment_term

    def set_interest_rate_type(self, interest_rate_type):
        self.interest_rate_type = interest_rate_type

    def set_interest_rate(self, interest_rate):
        self.interest_rate = interest_rate

    def set_interest_type_initial(self, interest_type_initial):
        self.interest_type_initial = interest_type_initial

    def set_interest_margin(self, interest_margin):
        self.interest_margin = interest_margin

    def set_interest_rate_max(self, interest_rate_max):
        self.interest_rate_max = interest_rate_max

    def set_adjustable_rate_index(self, adjustable_rate_index):
        self.adjustable_rate_index = adjustable_rate_index

    def set_interest_only_flag(self, interest_only_flag):
        self.interest_only_flag = interest_only_flag

    def set_interest_only_period(self, interest_only_period):
        self.interest_only_period = interest_only_period

    def set_adjustable_rate_rider_flag(self, adjustable_rate_rider_flag):
        self.adjustable_rate_rider_flag = adjustable_rate_rider_flag

    def set_interest_type_change_date(self, interest_type_change_date):
        self.interest_type_change_date = interest_type_change_date

    def set_min_interest_rate_first_change(self, min_interest_rate_first_change):
        self.min_interest_rate_first_change = min_interest_rate_first_change

    def set_max_interest_rate_first_change(self, max_interest_rate_first_change):
        self.max_interest_rate_first_change = max_interest_rate_first_change

    def set_interest_change_freq(self, interest_change_freq):
        self.interest_change_freq = interest_change_freq

    # Getters
    def get_doc_number_formatted(self):
        return self.doc_number_formatted or ""

    def get_instrument_number(self):
        return self.instrument_number or ""

    def get_book(self):
        return self.book or ""

    def get_page(self):
        return self.page or ""

    def get_recording_date(self):
        return self.recording_date or ""

    def get_type(self):
        return self.type or ""

    def get_amount(self):
        return self.amount or ""

    def get_lender_full_name(self):
        return self.lender_full_name or ""

    def get_lender_first_name(self):
        return self.lender_first_name or ""

    def get_lender_last_name(self):
        return self.lender_last_name or ""

    def get_lender_type(self):
        return self.lender_type or ""

    def get_is_lender_seller(self):
        return self.is_lender_seller or ""

    def get_term_date(self):
        return self.term_date or ""

    def get_prepayment_penalty_flag(self):
        return self.prepayment_penalty_flag or ""

    def get_prepayment_term(self):
        return self.prepayment_term or ""

    def get_interest_rate_type(self):
        return self.interest_rate_type or ""

    def get_interest_rate(self):
        return self.interest_rate or ""

    def get_interest_type_initial(self):
        return self.interest_type_initial or ""

    def get_interest_margin(self):
        return self.interest_margin or ""

    def get_interest_rate_max(self):
        return self.interest_rate_max or ""

    def get_adjustable_rate_index(self):
        return self.adjustable_rate_index or ""

    def get_interest_only_flag(self):
        return self.interest_only_flag or ""

    def get_interest_only_period(self):
        return self.interest_only_period or ""

    def get_adjustable_rate_rider_flag(self):
        return self.adjustable_rate_rider_flag or ""

    def get_interest_type_change_date(self):
        return self.interest_type_change_date or ""

    def get_min_interest_rate_first_change(self):
        return self.min_interest_rate_first_change or ""

    def get_max_interest_rate_first_change(self):
        return self.max_interest_rate_first_change or ""

    def get_interest_change_freq(self):
        return self.interest_change_freq or ""


class PropertyParcel:
    def __init__(
        self,
        fips_code="",
        county="",
        unformatted_apn="",
        formatted_apn="",
        account_number="",
        map_book="",
        map_page="",
        minor_civil_division_name=""
    ):
        self.fips_code = fips_code
        self.county = county
        self.unformatted_apn = unformatted_apn
        self.formatted_apn = formatted_apn
        self.account_number = account_number
        self.map_book = map_book
        self.map_page = map_page
        self.minor_civil_division_name = minor_civil_division_name

    @classmethod
    def from_dict(cls, data):
        return cls(
            fips_code=data.get("FIPSCode", ""),
            county=data.get("County", ""),
            unformatted_apn=data.get("UnformattedAPN", ""),
            formatted_apn=data.get("FormattedAPN", ""),
            account_number=data.get("AccountNumber", ""),
            map_book=data.get("MapBook", ""),
            map_page=data.get("MapPage", ""),
            minor_civil_division_name=data.get("MinorCivilDivisionName", "")
        )

    # Setters
    def set_fips_code(self, fips_code):
        self.fips_code = fips_code

    def set_county(self, county):
        self.county = county

    def set_unformatted_apn(self, unformatted_apn):
        self.unformatted_apn = unformatted_apn

    def set_formatted_apn(self, formatted_apn):
        self.formatted_apn = formatted_apn

    def set_account_number(self, account_number):
        self.account_number = account_number

    def set_map_book(self, map_book):
        self.map_book = map_book

    def set_map_page(self, map_page):
        self.map_page = map_page

    def set_minor_civil_division_name(self, minor_civil_division_name):
        self.minor_civil_division_name = minor_civil_division_name

    # Getters
    def get_fips_code(self):
        return self.fips_code or ""

    def get_county(self):
        return self.county or ""

    def get_unformatted_apn(self):
        return self.unformatted_apn or ""

    def get_formatted_apn(self):
        return self.formatted_apn or ""

    def get_account_number(self):
        return self.account_number or ""

    def get_map_book(self):
        return self.map_book or ""

    def get_map_page(self):
        return self.map_page or ""

    def get_minor_civil_division_name(self):
        return self.minor_civil_division_name or ""


class PropertyLegal:
    def __init__(
        self,
        legal_description="",
        range_="",
        township="",
        section="",
        quarter="",
        quarter_quarter="",
        subdivision="",
        phase="",
        tract_number="",
        block1="",
        lot_number1="",
        lot_number2="",
        lot_number3="",
        unit=""
    ):
        self.legal_description = legal_description
        self.range = range_
        self.township = township
        self.section = section
        self.quarter = quarter
        self.quarter_quarter = quarter_quarter
        self.subdivision = subdivision
        self.phase = phase
        self.tract_number = tract_number
        self.block1 = block1
        self.lot_number1 = lot_number1
        self.lot_number2 = lot_number2
        self.lot_number3 = lot_number3
        self.unit = unit

    @classmethod
    def from_dict(cls, data):
        return cls(
            legal_description=data.get("LegalDescription", ""),
            range_=data.get("Range", ""),
            township=data.get("Township", ""),
            section=data.get("Section", ""),
            quarter=data.get("Quarter", ""),
            quarter_quarter=data.get("QuarterQuarter", ""),
            subdivision=data.get("Subdivision", ""),
            phase=data.get("Phase", ""),
            tract_number=data.get("TractNumber", ""),
            block1=data.get("Block1", ""),
            lot_number1=data.get("LotNumber1", ""),
            lot_number2=data.get("LotNumber2", ""),
            lot_number3=data.get("LotNumber3", ""),
            unit=data.get("Unit", "")
        )

    # Setters
    def set_legal_description(self, legal_description):
        self.legal_description = legal_description

    def set_range(self, range_):
        self.range = range_

    def set_township(self, township):
        self.township = township

    def set_section(self, section):
        self.section = section

    def set_quarter(self, quarter):
        self.quarter = quarter

    def set_quarter_quarter(self, quarter_quarter):
        self.quarter_quarter = quarter_quarter

    def set_subdivision(self, subdivision):
        self.subdivision = subdivision

    def set_phase(self, phase):
        self.phase = phase

    def set_tract_number(self, tract_number):
        self.tract_number = tract_number

    def set_block1(self, block1):
        self.block1 = block1

    def set_lot_number1(self, lot_number1):
        self.lot_number1 = lot_number1

    def set_lot_number2(self, lot_number2):
        self.lot_number2 = lot_number2

    def set_lot_number3(self, lot_number3):
        self.lot_number3 = lot_number3

    def set_unit(self, unit):
        self.unit = unit

    # Getters
    def get_legal_description(self):
        return self.legal_description or ""

    def get_range(self):
        return self.range or ""

    def get_township(self):
        return self.township or ""

    def get_section(self):
        return self.section or ""

    def get_quarter(self):
        return self.quarter or ""

    def get_quarter_quarter(self):
        return self.quarter_quarter or ""

    def get_subdivision(self):
        return self.subdivision or ""

    def get_phase(self):
        return self.phase or ""

    def get_tract_number(self):
        return self.tract_number or ""

    def get_block1(self):
        return self.block1 or ""

    def get_lot_number1(self):
        return self.lot_number1 or ""

    def get_lot_number2(self):
        return self.lot_number2 or ""

    def get_lot_number3(self):
        return self.lot_number3 or ""

    def get_unit(self):
        return self.unit or ""


class PropertyAddress:
    def __init__(
        self,
        address="",
        city="",
        state="",
        zip_="",
        address_key="",
        mak="",
        base_mak="",
        latitude="",
        longitude="",
        carrier_route="",
        privacy_info=""
    ):
        self.address = address
        self.city = city
        self.state = state
        self.zip = zip_
        self.address_key = address_key
        self.mak = mak
        self.base_mak = base_mak
        self.latitude = latitude
        self.longitude = longitude
        self.carrier_route = carrier_route
        self.privacy_info = privacy_info

    @classmethod
    def from_dict(cls, data):
        return cls(
            address=data.get("Address", ""),
            city=data.get("City", ""),
            state=data.get("State", ""),
            zip_=data.get("Zip", ""),
            address_key=data.get("AddressKey", ""),
            mak=data.get("MAK", ""),
            base_mak=data.get("BaseMAK", ""),
            latitude=data.get("Latitude", ""),
            longitude=data.get("Longitude", ""),
            carrier_route=data.get("CarrierRoute", ""),
            privacy_info=data.get("PrivacyInfo", "")
        )

    # Setters
    def set_address(self, address):
        self.address = address

    def set_city(self, city):
        self.city = city

    def set_state(self, state):
        self.state = state

    def set_zip(self, zip_):
        self.zip = zip_

    def set_address_key(self, address_key):
        self.address_key = address_key

    def set_mak(self, mak):
        self.mak = mak

    def set_base_mak(self, base_mak):
        self.base_mak = base_mak

    def set_latitude(self, latitude):
        self.latitude = latitude

    def set_longitude(self, longitude):
        self.longitude = longitude

    def set_carrier_route(self, carrier_route):
        self.carrier_route = carrier_route

    def set_privacy_info(self, privacy_info):
        self.privacy_info = privacy_info

    # Getters
    def get_address(self):
        return self.address or ""

    def get_city(self):
        return self.city or ""

    def get_state(self):
        return self.state or ""

    def get_zip(self):
        return self.zip or ""

    def get_address_key(self):
        return self.address_key or ""

    def get_mak(self):
        return self.mak or ""

    def get_base_mak(self):
        return self.base_mak or ""

    def get_latitude(self):
        return self.latitude or ""

    def get_longitude(self):
        return self.longitude or ""

    def get_carrier_route(self):
        return self.carrier_route or ""

    def get_privacy_info(self):
        return self.privacy_info or ""


class PropertyParsedPropertyAddress:
    def __init__(
        self,
        range_="",
        pre_directional="",
        street_name="",
        suffix="",
        post_directional="",
        suite_name="",
        suite_range=""
    ):
        self.range = range_
        self.pre_directional = pre_directional
        self.street_name = street_name
        self.suffix = suffix
        self.post_directional = post_directional
        self.suite_name = suite_name
        self.suite_range = suite_range

    @classmethod
    def from_dict(cls, data):
        return cls(
            range_=data.get("Range", ""),
            pre_directional=data.get("PreDirectional", ""),
            street_name=data.get("StreetName", ""),
            suffix=data.get("Suffix", ""),
            post_directional=data.get("PostDirectional", ""),
            suite_name=data.get("SuiteName", ""),
            suite_range=data.get("SuiteRange", "")
        )

    # Setters
    def set_range(self, range_):
        self.range = range_

    def set_pre_directional(self, pre_directional):
        self.pre_directional = pre_directional

    def set_street_name(self, street_name):
        self.street_name = street_name

    def set_suffix(self, suffix):
        self.suffix = suffix

    def set_post_directional(self, post_directional):
        self.post_directional = post_directional

    def set_suite_name(self, suite_name):
        self.suite_name = suite_name

    def set_suite_range(self, suite_range):
        self.suite_range = suite_range

    # Getters
    def get_range(self):
        return self.range or ""

    def get_pre_directional(self):
        return self.pre_directional or ""

    def get_street_name(self):
        return self.street_name or ""

    def get_suffix(self):
        return self.suffix or ""

    def get_post_directional(self):
        return self.post_directional or ""

    def get_suite_name(self):
        return self.suite_name or ""

    def get_suite_range(self):
        return self.suite_range or ""


class PropertyPrimaryOwner:
    def __init__(
        self,
        name1_full="",
        name1_first="",
        name1_middle="",
        name1_last="",
        name1_suffix="",
        trust_flag="",
        company_flag="",
        name2_full="",
        name2_first="",
        name2_middle="",
        name2_last="",
        name2_suffix="",
        vesting_type=""
    ):
        self.name1_full = name1_full
        self.name1_first = name1_first
        self.name1_middle = name1_middle
        self.name1_last = name1_last
        self.name1_suffix = name1_suffix
        self.trust_flag = trust_flag
        self.company_flag = company_flag
        self.name2_full = name2_full
        self.name2_first = name2_first
        self.name2_middle = name2_middle
        self.name2_last = name2_last
        self.name2_suffix = name2_suffix
        self.vesting_type = vesting_type

    @classmethod
    def from_dict(cls, data):
        return cls(
            name1_full=data.get("Name1Full", ""),
            name1_first=data.get("Name1First", ""),
            name1_middle=data.get("Name1Middle", ""),
            name1_last=data.get("Name1Last", ""),
            name1_suffix=data.get("Name1Suffix", ""),
            trust_flag=data.get("TrustFlag", ""),
            company_flag=data.get("CompanyFlag", ""),
            name2_full=data.get("Name2Full", ""),
            name2_first=data.get("Name2First", ""),
            name2_middle=data.get("Name2Middle", ""),
            name2_last=data.get("Name2Last", ""),
            name2_suffix=data.get("Name2Suffix", ""),
            vesting_type=data.get("VestingType", "")
        )

    # Setters
    def set_name1_full(self, name1_full):
        self.name1_full = name1_full

    def set_name1_first(self, name1_first):
        self.name1_first = name1_first

    def set_name1_middle(self, name1_middle):
        self.name1_middle = name1_middle

    def set_name1_last(self, name1_last):
        self.name1_last = name1_last

    def set_name1_suffix(self, name1_suffix):
        self.name1_suffix = name1_suffix

    def set_trust_flag(self, trust_flag):
        self.trust_flag = trust_flag

    def set_company_flag(self, company_flag):
        self.company_flag = company_flag

    def set_name2_full(self, name2_full):
        self.name2_full = name2_full

    def set_name2_first(self, name2_first):
        self.name2_first = name2_first

    def set_name2_middle(self, name2_middle):
        self.name2_middle = name2_middle

    def set_name2_last(self, name2_last):
        self.name2_last = name2_last

    def set_name2_suffix(self, name2_suffix):
        self.name2_suffix = name2_suffix

    def set_vesting_type(self, vesting_type):
        self.vesting_type = vesting_type

    # Getters
    def get_name1_full(self):
        return self.name1_full or ""

    def get_name1_first(self):
        return self.name1_first or ""

    def get_name1_middle(self):
        return self.name1_middle or ""

    def get_name1_last(self):
        return self.name1_last or ""

    def get_name1_suffix(self):
        return self.name1_suffix or ""

    def get_trust_flag(self):
        return self.trust_flag or ""

    def get_company_flag(self):
        return self.company_flag or ""

    def get_name2_full(self):
        return self.name2_full or ""

    def get_name2_first(self):
        return self.name2_first or ""

    def get_name2_middle(self):
        return self.name2_middle or ""

    def get_name2_last(self):
        return self.name2_last or ""

    def get_name2_suffix(self):
        return self.name2_suffix or ""

    def get_vesting_type(self):
        return self.vesting_type or ""


class PropertyOwnerAddress:
    def __init__(
        self,
        address="",
        city="",
        state="",
        zip_="",
        carrier_route="",
        mak="",
        base_mak="",
        format_info="",
        privacy_info=""
    ):
        self.address = address
        self.city = city
        self.state = state
        self.zip = zip_
        self.carrier_route = carrier_route
        self.mak = mak
        self.base_mak = base_mak
        self.format_info = format_info
        self.privacy_info = privacy_info

    @classmethod
    def from_dict(cls, data):
        return cls(
            address=data.get("Address", ""),
            city=data.get("City", ""),
            state=data.get("State", ""),
            zip_=data.get("Zip", ""),
            carrier_route=data.get("CarrierRoute", ""),
            mak=data.get("MAK", ""),
            base_mak=data.get("BaseMAK", ""),
            format_info=data.get("FormatInfo", ""),
            privacy_info=data.get("PrivacyInfo", "")
        )

    # Setters
    def set_address(self, address):
        self.address = address

    def set_city(self, city):
        self.city = city

    def set_state(self, state):
        self.state = state

    def set_zip(self, zip_):
        self.zip = zip_

    def set_carrier_route(self, carrier_route):
        self.carrier_route = carrier_route

    def set_mak(self, mak):
        self.mak = mak

    def set_base_mak(self, base_mak):
        self.base_mak = base_mak

    def set_format_info(self, format_info):
        self.format_info = format_info

    def set_privacy_info(self, privacy_info):
        self.privacy_info = privacy_info

    # Getters
    def get_address(self):
        return self.address or ""

    def get_city(self):
        return self.city or ""

    def get_state(self):
        return self.state or ""

    def get_zip(self):
        return self.zip or ""

    def get_carrier_route(self):
        return self.carrier_route or ""

    def get_mak(self):
        return self.mak or ""

    def get_base_mak(self):
        return self.base_mak or ""

    def get_format_info(self):
        return self.format_info or ""

    def get_privacy_info(self):
        return self.privacy_info or ""


class PropertyLastDeedOwnerInfo:
    def __init__(
        self,
        name1_full="",
        name1_first="",
        name1_middle="",
        name1_last="",
        name1_suffix="",
        name2_full="",
        name2_first="",
        name2_middle="",
        name2_last="",
        name2_suffix=""
    ):
        self.name1_full = name1_full
        self.name1_first = name1_first
        self.name1_middle = name1_middle
        self.name1_last = name1_last
        self.name1_suffix = name1_suffix
        self.name2_full = name2_full
        self.name2_first = name2_first
        self.name2_middle = name2_middle
        self.name2_last = name2_last
        self.name2_suffix = name2_suffix

    @classmethod
    def from_dict(cls, data):
        return cls(
            name1_full=data.get("Name1Full", ""),
            name1_first=data.get("Name1First", ""),
            name1_middle=data.get("Name1Middle", ""),
            name1_last=data.get("Name1Last", ""),
            name1_suffix=data.get("Name1Suffix", ""),
            name2_full=data.get("Name2Full", ""),
            name2_first=data.get("Name2First", ""),
            name2_middle=data.get("Name2Middle", ""),
            name2_last=data.get("Name2Last", ""),
            name2_suffix=data.get("Name2Suffix", "")
        )

    # Setters
    def set_name1_full(self, name1_full):
        self.name1_full = name1_full

    def set_name1_first(self, name1_first):
        self.name1_first = name1_first

    def set_name1_middle(self, name1_middle):
        self.name1_middle = name1_middle

    def set_name1_last(self, name1_last):
        self.name1_last = name1_last

    def set_name1_suffix(self, name1_suffix):
        self.name1_suffix = name1_suffix

    def set_name2_full(self, name2_full):
        self.name2_full = name2_full

    def set_name2_first(self, name2_first):
        self.name2_first = name2_first

    def set_name2_middle(self, name2_middle):
        self.name2_middle = name2_middle

    def set_name2_last(self, name2_last):
        self.name2_last = name2_last

    def set_name2_suffix(self, name2_suffix):
        self.name2_suffix = name2_suffix

    # Getters
    def get_name1_full(self):
        return self.name1_full or ""

    def get_name1_first(self):
        return self.name1_first or ""

    def get_name1_middle(self):
        return self.name1_middle or ""

    def get_name1_last(self):
        return self.name1_last or ""

    def get_name1_suffix(self):
        return self.name1_suffix or ""

    def get_name2_full(self):
        return self.name2_full or ""

    def get_name2_first(self):
        return self.name2_first or ""

    def get_name2_middle(self):
        return self.name2_middle or ""

    def get_name2_last(self):
        return self.name2_last or ""

    def get_name2_suffix(self):
        return self.name2_suffix or ""


class PropertyCurrentDeed:
    def __init__(
        self,
        mortgage_amount="",
        mortgage_date="",
        mortgage_loan_type_code="",
        mortgage_due_date="",
        lender_name="",
        second_mortgage_amount=""
    ):
        self.mortgage_amount = mortgage_amount
        self.mortgage_date = mortgage_date
        self.mortgage_loan_type_code = mortgage_loan_type_code
        self.mortgage_due_date = mortgage_due_date
        self.lender_name = lender_name
        self.second_mortgage_amount = second_mortgage_amount

    @classmethod
    def from_dict(cls, data):
        return cls(
            mortgage_amount=data.get("MortgageAmount", ""),
            mortgage_date=data.get("MortgageDate", ""),
            mortgage_loan_type_code=data.get("MortgageLoanTypeCode", ""),
            mortgage_due_date=data.get("MortgageDueDate", ""),
            lender_name=data.get("LenderName", ""),
            second_mortgage_amount=data.get("SecondMortgageAmount", "")
        )

    # Setters
    def set_mortgage_amount(self, mortgage_amount):
        self.mortgage_amount = mortgage_amount

    def set_mortgage_date(self, mortgage_date):
        self.mortgage_date = mortgage_date

    def set_mortgage_loan_type_code(self, mortgage_loan_type_code):
        self.mortgage_loan_type_code = mortgage_loan_type_code

    def set_mortgage_due_date(self, mortgage_due_date):
        self.mortgage_due_date = mortgage_due_date

    def set_lender_name(self, lender_name):
        self.lender_name = lender_name

    def set_second_mortgage_amount(self, second_mortgage_amount):
        self.second_mortgage_amount = second_mortgage_amount

    # Getters
    def get_mortgage_amount(self):
        return self.mortgage_amount or ""

    def get_mortgage_date(self):
        return self.mortgage_date or ""

    def get_mortgage_loan_type_code(self):
        return self.mortgage_loan_type_code or ""

    def get_mortgage_due_date(self):
        return self.mortgage_due_date or ""

    def get_lender_name(self):
        return self.lender_name or ""

    def get_second_mortgage_amount(self):
        return self.second_mortgage_amount or ""


class PropertyTax:
    def __init__(
        self, year_assessed="", assessed_value_total="", assessed_value_improvements="", assessed_value_land="", 
        assessed_improvements_perc="", market_value_year="", market_value_total="", market_value_improvements="", 
        market_value_land="", market_improvements_perc="", tax_fiscal_year="", tax_rate_area="", tax_billed_amount="", 
        tax_delinquent_year="", last_tax_roll_update="", assr_last_updated="", tax_exemption_homeowner="", 
        tax_exemption_disabled="", tax_exemption_senior="", tax_exemption_veteran="", tax_exemption_widow="", 
        tax_exemption_additional=""
    ):
        self.year_assessed = year_assessed
        self.assessed_value_total = assessed_value_total
        self.assessed_value_improvements = assessed_value_improvements
        self.assessed_value_land = assessed_value_land
        self.assessed_improvements_perc = assessed_improvements_perc
        self.market_value_year = market_value_year
        self.market_value_total = market_value_total
        self.market_value_improvements = market_value_improvements
        self.market_value_land = market_value_land
        self.market_improvements_perc = market_improvements_perc
        self.tax_fiscal_year = tax_fiscal_year
        self.tax_rate_area = tax_rate_area
        self.tax_billed_amount = tax_billed_amount
        self.tax_delinquent_year = tax_delinquent_year
        self.last_tax_roll_update = last_tax_roll_update
        self.assr_last_updated = assr_last_updated
        self.tax_exemption_homeowner = tax_exemption_homeowner
        self.tax_exemption_disabled = tax_exemption_disabled
        self.tax_exemption_senior = tax_exemption_senior
        self.tax_exemption_veteran = tax_exemption_veteran
        self.tax_exemption_widow = tax_exemption_widow
        self.tax_exemption_additional = tax_exemption_additional

    @classmethod
    def from_dict(cls, data):
        return cls(
            year_assessed=data.get("YearAssessed", ""),
            assessed_value_total=data.get("AssessedValueTotal", ""),
            assessed_value_improvements=data.get("AssessedValueImprovements", ""),
            assessed_value_land=data.get("AssessedValueLand", ""),
            assessed_improvements_perc=data.get("AssessedImprovementsPerc", ""),
            market_value_year=data.get("MarketValueYear", ""),
            market_value_total=data.get("MarketValueTotal", ""),
            market_value_improvements=data.get("MarketValueImprovements", ""),
            market_value_land=data.get("MarketValueLand", ""),
            market_improvements_perc=data.get("MarketImprovementsPerc", ""),
            tax_fiscal_year=data.get("TaxFiscalYear", ""),
            tax_rate_area=data.get("TaxRateArea", ""),
            tax_billed_amount=data.get("TaxBilledAmount", ""),
            tax_delinquent_year=data.get("TaxDelinquentYear", ""),
            last_tax_roll_update=data.get("LastTaxRollUpdate", ""),
            assr_last_updated=data.get("AssrLastUpdated", ""),
            tax_exemption_homeowner=data.get("TaxExemptionHomeowner", ""),
            tax_exemption_disabled=data.get("TaxExemptionDisabled", ""),
            tax_exemption_senior=data.get("TaxExemptionSenior", ""),
            tax_exemption_veteran=data.get("TaxExemptionVeteran", ""),
            tax_exemption_widow=data.get("TaxExemptionWidow", ""),
            tax_exemption_additional=data.get("TaxExemptionAdditional", "")
        )

    # Setters
    def set_year_assessed(self, year_assessed):
        self.year_assessed = year_assessed

    def set_assessed_value_total(self, assessed_value_total):
        self.assessed_value_total = assessed_value_total

    def set_assessed_value_improvements(self, assessed_value_improvements):
        self.assessed_value_improvements = assessed_value_improvements

    def set_assessed_value_land(self, assessed_value_land):
        self.assessed_value_land = assessed_value_land

    def set_assessed_improvements_perc(self, assessed_improvements_perc):
        self.assessed_improvements_perc = assessed_improvements_perc

    def set_market_value_year(self, market_value_year):
        self.market_value_year = market_value_year

    def set_market_value_total(self, market_value_total):
        self.market_value_total = market_value_total

    def set_market_value_improvements(self, market_value_improvements):
        self.market_value_improvements = market_value_improvements

    def set_market_value_land(self, market_value_land):
        self.market_value_land = market_value_land

    def set_market_improvements_perc(self, market_improvements_perc):
        self.market_improvements_perc = market_improvements_perc

    def set_tax_fiscal_year(self, tax_fiscal_year):
        self.tax_fiscal_year = tax_fiscal_year

    def set_tax_rate_area(self, tax_rate_area):
        self.tax_rate_area = tax_rate_area

    def set_tax_billed_amount(self, tax_billed_amount):
        self.tax_billed_amount = tax_billed_amount

    def set_tax_delinquent_year(self, tax_delinquent_year):
        self.tax_delinquent_year = tax_delinquent_year

    def set_last_tax_roll_update(self, last_tax_roll_update):
        self.last_tax_roll_update = last_tax_roll_update

    def set_assr_last_updated(self, assr_last_updated):
        self.assr_last_updated = assr_last_updated

    def set_tax_exemption_homeowner(self, tax_exemption_homeowner):
        self.tax_exemption_homeowner = tax_exemption_homeowner

    def set_tax_exemption_disabled(self, tax_exemption_disabled):
        self.tax_exemption_disabled = tax_exemption_disabled

    def set_tax_exemption_senior(self, tax_exemption_senior):
        self.tax_exemption_senior = tax_exemption_senior

    def set_tax_exemption_veteran(self, tax_exemption_veteran):
        self.tax_exemption_veteran = tax_exemption_veteran

    def set_tax_exemption_widow(self, tax_exemption_widow):
        self.tax_exemption_widow = tax_exemption_widow

    def set_tax_exemption_additional(self, tax_exemption_additional):
        self.tax_exemption_additional = tax_exemption_additional

    # Getters
    def get_year_assessed(self):
        return self.year_assessed or ""

    def get_assessed_value_total(self):
        return self.assessed_value_total or ""

    def get_assessed_value_improvements(self):
        return self.assessed_value_improvements or ""

    def get_assessed_value_land(self):
        return self.assessed_value_land or ""

    def get_assessed_improvements_perc(self):
        return self.assessed_improvements_perc or ""

    def get_market_value_year(self):
        return self.market_value_year or ""

    def get_market_value_total(self):
        return self.market_value_total or ""

    def get_market_value_improvements(self):
        return self.market_value_improvements or ""

    def get_market_value_land(self):
        return self.market_value_land or ""

    def get_market_improvements_perc(self):
        return self.market_improvements_perc or ""

    def get_tax_fiscal_year(self):
        return self.tax_fiscal_year or ""

    def get_tax_rate_area(self):
        return self.tax_rate_area or ""

    def get_tax_billed_amount(self):
        return self.tax_billed_amount or ""

    def get_tax_delinquent_year(self):
        return self.tax_delinquent_year or ""

    def get_last_tax_roll_update(self):
        return self.last_tax_roll_update or ""

    def get_assr_last_updated(self):
        return self.assr_last_updated or ""

    def get_tax_exemption_homeowner(self):
        return self.tax_exemption_homeowner or ""

    def get_tax_exemption_disabled(self):
        return self.tax_exemption_disabled or ""

    def get_tax_exemption_senior(self):
        return self.tax_exemption_senior or ""

    def get_tax_exemption_veteran(self):
        return self.tax_exemption_veteran or ""

    def get_tax_exemption_widow(self):
        return self.tax_exemption_widow or ""

    def get_tax_exemption_additional(self):
        return self.tax_exemption_additional or ""


class PropertyUseInfo:
    def __init__(
        self,
        year_built="",
        year_built_effective="",
        zoned_code_local="",
        property_use_muni="",
        property_use_group="",
        property_use_standardized=""
    ):
        self.year_built = year_built
        self.year_built_effective = year_built_effective
        self.zoned_code_local = zoned_code_local
        self.property_use_muni = property_use_muni
        self.property_use_group = property_use_group
        self.property_use_standardized = property_use_standardized

    @classmethod
    def from_dict(cls, data):
        return cls(
            year_built=data.get("YearBuilt", ""),
            year_built_effective=data.get("YearBuiltEffective", ""),
            zoned_code_local=data.get("ZonedCodeLocal", ""),
            property_use_muni=data.get("PropertyUseMuni", ""),
            property_use_group=data.get("PropertyUseGroup", ""),
            property_use_standardized=data.get("PropertyUseStandardized", "")
        )

    # Setters
    def set_year_built(self, year_built):
        self.year_built = year_built

    def set_year_built_effective(self, year_built_effective):
        self.year_built_effective = year_built_effective

    def set_zoned_code_local(self, zoned_code_local):
        self.zoned_code_local = zoned_code_local

    def set_property_use_muni(self, property_use_muni):
        self.property_use_muni = property_use_muni

    def set_property_use_group(self, property_use_group):
        self.property_use_group = property_use_group

    def set_property_use_standardized(self, property_use_standardized):
        self.property_use_standardized = property_use_standardized

    # Getters
    def get_year_built(self):
        return self.year_built or ""

    def get_year_built_effective(self):
        return self.year_built_effective or ""

    def get_zoned_code_local(self):
        return self.zoned_code_local or ""

    def get_property_use_muni(self):
        return self.property_use_muni or ""

    def get_property_use_group(self):
        return self.property_use_group or ""

    def get_property_use_standardized(self):
        return self.property_use_standardized or ""


class PropertySaleInfo:
    def __init__(
        self,
        assessor_last_sale_date="",
        assessor_last_sale_amount="",
        assessor_prior_sale_date="",
        assessor_prior_sale_amount="",
        last_ownership_transfer_date="",
        last_ownership_transfer_document_number="",
        deed_last_sale_document_book="",
        deed_last_sale_document_page="",
        deed_last_document_number="",
        deed_last_sale_date="",
        deed_last_sale_price=""
    ):
        self.assessor_last_sale_date = assessor_last_sale_date
        self.assessor_last_sale_amount = assessor_last_sale_amount
        self.assessor_prior_sale_date = assessor_prior_sale_date
        self.assessor_prior_sale_amount = assessor_prior_sale_amount
        self.last_ownership_transfer_date = last_ownership_transfer_date
        self.last_ownership_transfer_document_number = last_ownership_transfer_document_number
        self.deed_last_sale_document_book = deed_last_sale_document_book
        self.deed_last_sale_document_page = deed_last_sale_document_page
        self.deed_last_document_number = deed_last_document_number
        self.deed_last_sale_date = deed_last_sale_date
        self.deed_last_sale_price = deed_last_sale_price

    @classmethod
    def from_dict(cls, data):
        return cls(
            assessor_last_sale_date=data.get("AssessorLastSaleDate", ""),
            assessor_last_sale_amount=data.get("AssessorLastSaleAmount", ""),
            assessor_prior_sale_date=data.get("AssessorPriorSaleDate", ""),
            assessor_prior_sale_amount=data.get("AssessorPriorSaleAmount", ""),
            last_ownership_transfer_date=data.get("LastOwnershipTransferDate", ""),
            last_ownership_transfer_document_number=data.get("LastOwnershipTransferDocumentNumber", ""),
            deed_last_sale_document_book=data.get("DeedLastSaleDocumentBook", ""),
            deed_last_sale_document_page=data.get("DeedLastSaleDocumentPage", ""),
            deed_last_document_number=data.get("DeedLastDocumentNumber", ""),
            deed_last_sale_date=data.get("DeedLastSaleDate", ""),
            deed_last_sale_price=data.get("DeedLastSalePrice", "")
        )

    # Setters
    def set_assessor_last_sale_date(self, assessor_last_sale_date):
        self.assessor_last_sale_date = assessor_last_sale_date

    def set_assessor_last_sale_amount(self, assessor_last_sale_amount):
        self.assessor_last_sale_amount = assessor_last_sale_amount

    def set_assessor_prior_sale_date(self, assessor_prior_sale_date):
        self.assessor_prior_sale_date = assessor_prior_sale_date

    def set_assessor_prior_sale_amount(self, assessor_prior_sale_amount):
        self.assessor_prior_sale_amount = assessor_prior_sale_amount

    def set_last_ownership_transfer_date(self, last_ownership_transfer_date):
        self.last_ownership_transfer_date = last_ownership_transfer_date

    def set_last_ownership_transfer_document_number(self, last_ownership_transfer_document_number):
        self.last_ownership_transfer_document_number = last_ownership_transfer_document_number

    def set_deed_last_sale_document_book(self, deed_last_sale_document_book):
        self.deed_last_sale_document_book = deed_last_sale_document_book

    def set_deed_last_sale_document_page(self, deed_last_sale_document_page):
        self.deed_last_sale_document_page = deed_last_sale_document_page

    def set_deed_last_document_number(self, deed_last_document_number):
        self.deed_last_document_number = deed_last_document_number

    def set_deed_last_sale_date(self, deed_last_sale_date):
        self.deed_last_sale_date = deed_last_sale_date

    def set_deed_last_sale_price(self, deed_last_sale_price):
        self.deed_last_sale_price = deed_last_sale_price

    # Getters
    def get_assessor_last_sale_date(self):
        return self.assessor_last_sale_date or ""

    def get_assessor_last_sale_amount(self):
        return self.assessor_last_sale_amount or ""

    def get_assessor_prior_sale_date(self):
        return self.assessor_prior_sale_date or ""

    def get_assessor_prior_sale_amount(self):
        return self.assessor_prior_sale_amount or ""

    def get_last_ownership_transfer_date(self):
        return self.last_ownership_transfer_date or ""

    def get_last_ownership_transfer_document_number(self):
        return self.last_ownership_transfer_document_number or ""

    def get_deed_last_sale_document_book(self):
        return self.deed_last_sale_document_book or ""

    def get_deed_last_sale_document_page(self):
        return self.deed_last_sale_document_page or ""

    def get_deed_last_document_number(self):
        return self.deed_last_document_number or ""

    def get_deed_last_sale_date(self):
        return self.deed_last_sale_date or ""
    
    def get_deed_last_sale_price(self):
        return self.deed_last_sale_price or ""


class PropertySize:
    def __init__(
        self,
        area_building="",
        area_1st_floor="",
        area_2nd_floor="",
        area_upper_floors="",
        area_lot_acres="",
        area_lot_sf="",
        lot_depth="",
        lot_width="",
        attic_area="",
        attic_flag="",
        basement_area="",
        basement_area_finished="",
        basement_area_unfinished="",
        parking_garage="",
        parking_garage_area="",
        parking_carport="",
        parking_carport_area=""
    ):
        self.area_building = area_building
        self.area_1st_floor = area_1st_floor
        self.area_2nd_floor = area_2nd_floor
        self.area_upper_floors = area_upper_floors
        self.area_lot_acres = area_lot_acres
        self.area_lot_sf = area_lot_sf
        self.lot_depth = lot_depth
        self.lot_width = lot_width
        self.attic_area = attic_area
        self.attic_flag = attic_flag
        self.basement_area = basement_area
        self.basement_area_finished = basement_area_finished
        self.basement_area_unfinished = basement_area_unfinished
        self.parking_garage = parking_garage
        self.parking_garage_area = parking_garage_area
        self.parking_carport = parking_carport
        self.parking_carport_area = parking_carport_area

    @classmethod
    def from_dict(cls, data):
        return cls(
            area_building=data.get("AreaBuilding", ""),
            area_1st_floor=data.get("Area1stFloor", ""),
            area_2nd_floor=data.get("Area2ndFloor", ""),
            area_upper_floors=data.get("AreaUpperFloors", ""),
            area_lot_acres=data.get("AreaLotAcres", ""),
            area_lot_sf=data.get("AreaLotSF", ""),
            lot_depth=data.get("LotDepth", ""),
            lot_width=data.get("LotWidth", ""),
            attic_area=data.get("AtticArea", ""),
            attic_flag=data.get("AtticFlag", ""),
            basement_area=data.get("BasementArea", ""),
            basement_area_finished=data.get("BasementAreaFinished", ""),
            basement_area_unfinished=data.get("BasementAreaUnfinished", ""),
            parking_garage=data.get("ParkingGarage", ""),
            parking_garage_area=data.get("ParkingGarageArea", ""),
            parking_carport=data.get("ParkingCarport", ""),
            parking_carport_area=data.get("ParkingCarportArea", "")
        )

    # Setters
    def set_area_building(self, area_building):
        self.area_building = area_building

    def set_area_1st_floor(self, area_1st_floor):
        self.area_1st_floor = area_1st_floor

    def set_area_2nd_floor(self, area_2nd_floor):
        self.area_2nd_floor = area_2nd_floor

    def set_area_upper_floors(self, area_upper_floors):
        self.area_upper_floors = area_upper_floors

    def set_area_lot_acres(self, area_lot_acres):
        self.area_lot_acres = area_lot_acres

    def set_area_lot_sf(self, area_lot_sf):
        self.area_lot_sf = area_lot_sf

    def set_lot_depth(self, lot_depth):
        self.lot_depth = lot_depth

    def set_lot_width(self, lot_width):
        self.lot_width = lot_width

    def set_attic_area(self, attic_area):
        self.attic_area = attic_area

    def set_attic_flag(self, attic_flag):
        self.attic_flag = attic_flag

    def set_basement_area(self, basement_area):
        self.basement_area = basement_area

    def set_basement_area_finished(self, basement_area_finished):
        self.basement_area_finished = basement_area_finished

    def set_basement_area_unfinished(self, basement_area_unfinished):
        self.basement_area_unfinished = basement_area_unfinished

    def set_parking_garage(self, parking_garage):
        self.parking_garage = parking_garage

    def set_parking_garage_area(self, parking_garage_area):
        self.parking_garage_area = parking_garage_area

    def set_parking_carport(self, parking_carport):
        self.parking_carport = parking_carport

    def set_parking_carport_area(self, parking_carport_area):
        self.parking_carport_area = parking_carport_area

    # Getters
    def get_area_building(self):
        return self.area_building or ""

    def get_area_1st_floor(self):
        return self.area_1st_floor or ""

    def get_area_2nd_floor(self):
        return self.area_2nd_floor or ""

    def get_area_upper_floors(self):
        return self.area_upper_floors or ""

    def get_area_lot_acres(self):
        return self.area_lot_acres or ""

    def get_area_lot_sf(self):
        return self.area_lot_sf or ""

    def get_lot_depth(self):
        return self.lot_depth or ""

    def get_lot_width(self):
        return self.lot_width or ""

    def get_attic_area(self):
        return self.attic_area or ""

    def get_attic_flag(self):
        return self.attic_flag or ""

    def get_basement_area(self):
        return self.basement_area or ""

    def get_basement_area_finished(self):
        return self.basement_area_finished or ""

    def get_basement_area_unfinished(self):
        return self.basement_area_unfinished or ""

    def get_parking_garage(self):
        return self.parking_garage or ""

    def get_parking_garage_area(self):
        return self.parking_garage_area or ""

    def get_parking_carport(self):
        return self.parking_carport or ""

    def get_parking_carport_area(self):
        return self.parking_carport_area or ""


class PropertyPool:
    def __init__(
        self,
        pool="",
        pool_area="",
        sauna_flag=""
    ):
        self.pool = pool
        self.pool_area = pool_area
        self.sauna_flag = sauna_flag

    @classmethod
    def from_dict(cls, data):
        return cls(
            pool=data.get("Pool", ""),
            pool_area=data.get("PoolArea", ""),
            sauna_flag=data.get("SaunaFlag", "")
        )

    # Setters
    def set_pool(self, pool):
        self.pool = pool

    def set_pool_area(self, pool_area):
        self.pool_area = pool_area

    def set_sauna_flag(self, sauna_flag):
        self.sauna_flag = sauna_flag

    # Getters
    def get_pool(self):
        return self.pool or ""

    def get_pool_area(self):
        return self.pool_area or ""

    def get_sauna_flag(self):
        return self.sauna_flag or ""


class PropertyIntStructInfo:
    def __init__(
        self,
        foundation="",
        construction="",
        interior_structure="",
        plumbing_fixtures_count="",
        construction_fire_resistance_class="",
        safety_fire_sprinklers_flag="",
        flooring_material_primary=""
    ):
        self.foundation = foundation
        self.construction = construction
        self.interior_structure = interior_structure
        self.plumbing_fixtures_count = plumbing_fixtures_count
        self.construction_fire_resistance_class = construction_fire_resistance_class
        self.safety_fire_sprinklers_flag = safety_fire_sprinklers_flag
        self.flooring_material_primary = flooring_material_primary

    @classmethod
    def from_dict(cls, data):
        return cls(
            foundation=data.get("Foundation", ""),
            construction=data.get("Construction", ""),
            interior_structure=data.get("InteriorStructure", ""),
            plumbing_fixtures_count=data.get("PlumbingFixturesCount", ""),
            construction_fire_resistance_class=data.get("ConstructionFireResistanceClass", ""),
            safety_fire_sprinklers_flag=data.get("SafetyFireSprinklersFlag", ""),
            flooring_material_primary=data.get("FlooringMaterialPrimary", "")
        )

    # Setters
    def set_foundation(self, foundation):
        self.foundation = foundation

    def set_construction(self, construction):
        self.construction = construction

    def set_interior_structure(self, interior_structure):
        self.interior_structure = interior_structure

    def set_plumbing_fixtures_count(self, plumbing_fixtures_count):
        self.plumbing_fixtures_count = plumbing_fixtures_count

    def set_construction_fire_resistance_class(self, construction_fire_resistance_class):
        self.construction_fire_resistance_class = construction_fire_resistance_class

    def set_safety_fire_sprinklers_flag(self, safety_fire_sprinklers_flag):
        self.safety_fire_sprinklers_flag = safety_fire_sprinklers_flag

    def set_flooring_material_primary(self, flooring_material_primary):
        self.flooring_material_primary = flooring_material_primary

    # Getters
    def get_foundation(self):
        return self.foundation or ""

    def get_construction(self):
        return self.construction or ""

    def get_interior_structure(self):
        return self.interior_structure or ""

    def get_plumbing_fixtures_count(self):
        return self.plumbing_fixtures_count or ""

    def get_construction_fire_resistance_class(self):
        return self.construction_fire_resistance_class or ""

    def get_safety_fire_sprinklers_flag(self):
        return self.safety_fire_sprinklers_flag or ""

    def get_flooring_material_primary(self):
        return self.flooring_material_primary or ""


class PropertyIntRoomInfo:
    def __init__(
        self,
        bath_count="",
        bath_partial_count="",
        bedrooms_count="",
        rooms_count="",
        stories_count="",
        units_count="",
        bonus_room_flag="",
        breakfast_nook_flag="",
        cellar_flag="",
        exercise_flag="",
        family_code="",
        game_flag="",
        great_flag="",
        hobby_flag="",
        laundry_flag="",
        media_flag="",
        mud_flag="",
        office_area="",
        office_flag="",
        safe_room_flag="",
        sitting_flag="",
        storm_flag="",
        study_flag="",
        sunroom_flag="",
        utility_area="",
        utility_code=""
    ):
        self.bath_count = bath_count
        self.bath_partial_count = bath_partial_count
        self.bedrooms_count = bedrooms_count
        self.rooms_count = rooms_count
        self.stories_count = stories_count
        self.units_count = units_count
        self.bonus_room_flag = bonus_room_flag
        self.breakfast_nook_flag = breakfast_nook_flag
        self.cellar_flag = cellar_flag
        self.exercise_flag = exercise_flag
        self.family_code = family_code
        self.game_flag = game_flag
        self.great_flag = great_flag
        self.hobby_flag = hobby_flag
        self.laundry_flag = laundry_flag
        self.media_flag = media_flag
        self.mud_flag = mud_flag
        self.office_area = office_area
        self.office_flag = office_flag
        self.safe_room_flag = safe_room_flag
        self.sitting_flag = sitting_flag
        self.storm_flag = storm_flag
        self.study_flag = study_flag
        self.sunroom_flag = sunroom_flag
        self.utility_area = utility_area
        self.utility_code = utility_code

    @classmethod
    def from_dict(cls, data):
        return cls(
            bath_count=data.get("BathCount", ""),
            bath_partial_count=data.get("BathPartialCount", ""),
            bedrooms_count=data.get("BedroomsCount", ""),
            rooms_count=data.get("RoomsCount", ""),
            stories_count=data.get("StoriesCount", ""),
            units_count=data.get("UnitsCount", ""),
            bonus_room_flag=data.get("BonusRoomFlag", ""),
            breakfast_nook_flag=data.get("BreakfastNookFlag", ""),
            cellar_flag=data.get("CellarFlag", ""),
            exercise_flag=data.get("ExerciseFlag", ""),
            family_code=data.get("FamilyCode", ""),
            game_flag=data.get("GameFlag", ""),
            great_flag=data.get("GreatFlag", ""),
            hobby_flag=data.get("HobbyFlag", ""),
            laundry_flag=data.get("LaundryFlag", ""),
            media_flag=data.get("MediaFlag", ""),
            mud_flag=data.get("MudFlag", ""),
            office_area=data.get("OfficeArea", ""),
            office_flag=data.get("OfficeFlag", ""),
            safe_room_flag=data.get("SafeRoomFlag", ""),
            sitting_flag=data.get("SittingFlag", ""),
            storm_flag=data.get("StormFlag", ""),
            study_flag=data.get("StudyFlag", ""),
            sunroom_flag=data.get("SunroomFlag", ""),
            utility_area=data.get("UtilityArea", ""),
            utility_code=data.get("UtilityCode", "")
        )

    # Setters
    def set_bath_count(self, bath_count):
        self.bath_count = bath_count

    def set_bath_partial_count(self, bath_partial_count):
        self.bath_partial_count = bath_partial_count

    def set_bedrooms_count(self, bedrooms_count):
        self.bedrooms_count = bedrooms_count

    def set_rooms_count(self, rooms_count):
        self.rooms_count = rooms_count

    def set_stories_count(self, stories_count):
        self.stories_count = stories_count

    def set_units_count(self, units_count):
        self.units_count = units_count

    def set_bonus_room_flag(self, bonus_room_flag):
        self.bonus_room_flag = bonus_room_flag

    def set_breakfast_nook_flag(self, breakfast_nook_flag):
        self.breakfast_nook_flag = breakfast_nook_flag

    def set_cellar_flag(self, cellar_flag):
        self.cellar_flag = cellar_flag

    def set_exercise_flag(self, exercise_flag):
        self.exercise_flag = exercise_flag

    def set_family_code(self, family_code):
        self.family_code = family_code

    def set_game_flag(self, game_flag):
        self.game_flag = game_flag

    def set_great_flag(self, great_flag):
        self.great_flag = great_flag

    def set_hobby_flag(self, hobby_flag):
        self.hobby_flag = hobby_flag

    def set_laundry_flag(self, laundry_flag):
        self.laundry_flag = laundry_flag

    def set_media_flag(self, media_flag):
        self.media_flag = media_flag

    def set_mud_flag(self, mud_flag):
        self.mud_flag = mud_flag

    def set_office_area(self, office_area):
        self.office_area = office_area

    def set_office_flag(self, office_flag):
        self.office_flag = office_flag

    def set_safe_room_flag(self, safe_room_flag):
        self.safe_room_flag = safe_room_flag

    def set_sitting_flag(self, sitting_flag):
        self.sitting_flag = sitting_flag

    def set_storm_flag(self, storm_flag):
        self.storm_flag = storm_flag

    def set_study_flag(self, study_flag):
        self.study_flag = study_flag

    def set_sunroom_flag(self, sunroom_flag):
        self.sunroom_flag = sunroom_flag

    def set_utility_area(self, utility_area):
        self.utility_area = utility_area

    def set_utility_code(self, utility_code):
        self.utility_code = utility_code

    # Getters
    def get_bath_count(self):
        return self.bath_count or ""

    def get_bath_partial_count(self):
        return self.bath_partial_count or ""

    def get_bedrooms_count(self):
        return self.bedrooms_count or ""

    def get_rooms_count(self):
        return self.rooms_count or ""

    def get_stories_count(self):
        return self.stories_count or ""

    def get_units_count(self):
        return self.units_count or ""

    def get_bonus_room_flag(self):
        return self.bonus_room_flag or ""

    def get_breakfast_nook_flag(self):
        return self.breakfast_nook_flag or ""

    def get_cellar_flag(self):
        return self.cellar_flag or ""

    def get_exercise_flag(self):
        return self.exercise_flag or ""

    def get_family_code(self):
        return self.family_code or ""

    def get_game_flag(self):
        return self.game_flag or ""

    def get_great_flag(self):
        return self.great_flag or ""

    def get_hobby_flag(self):
        return self.hobby_flag or ""

    def get_laundry_flag(self):
        return self.laundry_flag or ""

    def get_media_flag(self):
        return self.media_flag or ""

    def get_mud_flag(self):
        return self.mud_flag or ""

    def get_office_area(self):
        return self.office_area or ""

    def get_office_flag(self):
        return self.office_flag or ""

    def get_safe_room_flag(self):
        return self.safe_room_flag or ""

    def get_sitting_flag(self):
        return self.sitting_flag or ""

    def get_storm_flag(self):
        return self.storm_flag or ""

    def get_study_flag(self):
        return self.study_flag or ""

    def get_sunroom_flag(self):
        return self.sunroom_flag or ""

    def get_utility_area(self):
        return self.utility_area or ""

    def get_utility_code(self):
        return self.utility_code or ""


class PropertyIntAmentities:
    def __init__(
        self,
        fireplace="",
        fireplace_count="",
        accessability_elevator_flag="",
        accessability_handicap_flag="",
        escalator_flag="",
        central_vacuum_flag="",
        intercom_flag="",
        sound_system_flag="",
        wet_bar_flag="",
        security_alarm_flag=""
    ):
        self.fireplace = fireplace
        self.fireplace_count = fireplace_count
        self.accessability_elevator_flag = accessability_elevator_flag
        self.accessability_handicap_flag = accessability_handicap_flag
        self.escalator_flag = escalator_flag
        self.central_vacuum_flag = central_vacuum_flag
        self.intercom_flag = intercom_flag
        self.sound_system_flag = sound_system_flag
        self.wet_bar_flag = wet_bar_flag
        self.security_alarm_flag = security_alarm_flag

    @classmethod
    def from_dict(cls, data):
        return cls(
            fireplace=data.get("Fireplace", ""),
            fireplace_count=data.get("FireplaceCount", ""),
            accessability_elevator_flag=data.get("AccessabilityElevatorFlag", ""),
            accessability_handicap_flag=data.get("AccessabilityHandicapFlag", ""),
            escalator_flag=data.get("EscalatorFlag", ""),
            central_vacuum_flag=data.get("CentralVacuumFlag", ""),
            intercom_flag=data.get("IntercomFlag", ""),
            sound_system_flag=data.get("SoundSystemFlag", ""),
            wet_bar_flag=data.get("WetBarFlag", ""),
            security_alarm_flag=data.get("SecurityAlarmFlag", "")
        )

    # Setters
    def set_fireplace(self, fireplace):
        self.fireplace = fireplace

    def set_fireplace_count(self, fireplace_count):
        self.fireplace_count = fireplace_count

    def set_accessability_elevator_flag(self, accessability_elevator_flag):
        self.accessability_elevator_flag = accessability_elevator_flag

    def set_accessability_handicap_flag(self, accessability_handicap_flag):
        self.accessability_handicap_flag = accessability_handicap_flag

    def set_escalator_flag(self, escalator_flag):
        self.escalator_flag = escalator_flag

    def set_central_vacuum_flag(self, central_vacuum_flag):
        self.central_vacuum_flag = central_vacuum_flag

    def set_intercom_flag(self, intercom_flag):
        self.intercom_flag = intercom_flag

    def set_sound_system_flag(self, sound_system_flag):
        self.sound_system_flag = sound_system_flag

    def set_wet_bar_flag(self, wet_bar_flag):
        self.wet_bar_flag = wet_bar_flag

    def set_security_alarm_flag(self, security_alarm_flag):
        self.security_alarm_flag = security_alarm_flag

    # Getters
    def get_fireplace(self):
        return self.fireplace or ""

    def get_fireplace_count(self):
        return self.fireplace_count or ""

    def get_accessability_elevator_flag(self):
        return self.accessability_elevator_flag or ""

    def get_accessability_handicap_flag(self):
        return self.accessability_handicap_flag or ""

    def get_escalator_flag(self):
        return self.escalator_flag or ""

    def get_central_vacuum_flag(self):
        return self.central_vacuum_flag or ""

    def get_intercom_flag(self):
        return self.intercom_flag or ""

    def get_sound_system_flag(self):
        return self.sound_system_flag or ""

    def get_wet_bar_flag(self):
        return self.wet_bar_flag or ""

    def get_security_alarm_flag(self):
        return self.security_alarm_flag or ""


class PropertyExtStructInfo:
    def __init__(
        self,
        structure_style="",
        exterior1_code="",
        roof_material="",
        roof_construction="",
        storm_shutter_flag="",
        overhead_door_flag=""
    ):
        self.structure_style = structure_style
        self.exterior1_code = exterior1_code
        self.roof_material = roof_material
        self.roof_construction = roof_construction
        self.storm_shutter_flag = storm_shutter_flag
        self.overhead_door_flag = overhead_door_flag

    @classmethod
    def from_dict(cls, data):
        return cls(
            structure_style=data.get("StructureStyle", ""),
            exterior1_code=data.get("Exterior1Code", ""),
            roof_material=data.get("RoofMaterial", ""),
            roof_construction=data.get("RoofConstruction", ""),
            storm_shutter_flag=data.get("StormShutterFlag", ""),
            overhead_door_flag=data.get("OverheadDoorFlag", "")
        )

    # Setters
    def set_structure_style(self, structure_style):
        self.structure_style = structure_style

    def set_exterior1_code(self, exterior1_code):
        self.exterior1_code = exterior1_code

    def set_roof_material(self, roof_material):
        self.roof_material = roof_material

    def set_roof_construction(self, roof_construction):
        self.roof_construction = roof_construction

    def set_storm_shutter_flag(self, storm_shutter_flag):
        self.storm_shutter_flag = storm_shutter_flag

    def set_overhead_door_flag(self, overhead_door_flag):
        self.overhead_door_flag = overhead_door_flag

    # Getters
    def get_structure_style(self):
        return self.structure_style or ""

    def get_exterior1_code(self):
        return self.exterior1_code or ""

    def get_roof_material(self):
        return self.roof_material or ""

    def get_roof_construction(self):
        return self.roof_construction or ""

    def get_storm_shutter_flag(self):
        return self.storm_shutter_flag or ""

    def get_overhead_door_flag(self):
        return self.overhead_door_flag or ""


class PropertyExtAmentities:
    def __init__(
        self,
        view_description="",
        porch_code="",
        porch_area="",
        patio_area="",
        deck_flag="",
        deck_area="",
        feature_balcony_flag="",
        balcony_area="",
        breezeway_flag=""
    ):
        self.view_description = view_description
        self.porch_code = porch_code
        self.porch_area = porch_area
        self.patio_area = patio_area
        self.deck_flag = deck_flag
        self.deck_area = deck_area
        self.feature_balcony_flag = feature_balcony_flag
        self.balcony_area = balcony_area
        self.breezeway_flag = breezeway_flag

    @classmethod
    def from_dict(cls, data):
        return cls(
            view_description=data.get("ViewDescription", ""),
            porch_code=data.get("PorchCode", ""),
            porch_area=data.get("PorchArea", ""),
            patio_area=data.get("PatioArea", ""),
            deck_flag=data.get("DeckFlag", ""),
            deck_area=data.get("DeckArea", ""),
            feature_balcony_flag=data.get("FeatureBalconyFlag", ""),
            balcony_area=data.get("BalconyArea", ""),
            breezeway_flag=data.get("BreezewayFlag", "")
        )

    # Setters
    def set_view_description(self, view_description):
        self.view_description = view_description

    def set_porch_code(self, porch_code):
        self.porch_code = porch_code

    def set_porch_area(self, porch_area):
        self.porch_area = porch_area

    def set_patio_area(self, patio_area):
        self.patio_area = patio_area

    def set_deck_flag(self, deck_flag):
        self.deck_flag = deck_flag

    def set_deck_area(self, deck_area):
        self.deck_area = deck_area

    def set_feature_balcony_flag(self, feature_balcony_flag):
        self.feature_balcony_flag = feature_balcony_flag

    def set_balcony_area(self, balcony_area):
        self.balcony_area = balcony_area

    def set_breezeway_flag(self, breezeway_flag):
        self.breezeway_flag = breezeway_flag

    # Getters
    def get_view_description(self):
        return self.view_description or ""

    def get_porch_code(self):
        return self.porch_code or ""

    def get_porch_area(self):
        return self.porch_area or ""

    def get_patio_area(self):
        return self.patio_area or ""

    def get_deck_flag(self):
        return self.deck_flag or ""

    def get_deck_area(self):
        return self.deck_area or ""

    def get_feature_balcony_flag(self):
        return self.feature_balcony_flag or ""

    def get_balcony_area(self):
        return self.balcony_area or ""

    def get_breezeway_flag(self):
        return self.breezeway_flag or ""


class PropertyExtBuildings:
    def __init__(
        self, buildings_count="", bath_house_area="", bath_house_flag="", boat_house_area="", boat_house_flag="", cabin_area="", 
        cabin_flag="", canopy_area="", canopy_flag="", gazebo_area="", gazebo_flag="", granary_area="", granary_flag="", 
        green_house_area="", green_house_flag="", guest_house_area="", guest_house_flag="", kennel_area="", kennel_flag="", 
        lean_to_area="", lean_to_flag="", loading_platform_area="", loading_platform_flag="", milk_house_area="", milk_house_flag="", 
        outdoor_kitchen_fireplace_flag="", pool_house_area="", pool_house_flag="", poultry_house_area="", poultry_house_flag="", 
        quonset_area="", quonset_flag="", shed_area="", shed_code="", silo_area="", silo_flag="", stable_area="", stable_flag="", 
        storage_building_area="", storage_building_flag="", utility_building_area="", utility_building_flag="", pole_structure_area="", 
        pole_structure_flag=""
    ):
        self.buildings_count = buildings_count
        self.bath_house_area = bath_house_area
        self.bath_house_flag = bath_house_flag
        self.boat_house_area = boat_house_area
        self.boat_house_flag = boat_house_flag
        self.cabin_area = cabin_area
        self.cabin_flag = cabin_flag
        self.canopy_area = canopy_area
        self.canopy_flag = canopy_flag
        self.gazebo_area = gazebo_area
        self.gazebo_flag = gazebo_flag
        self.granary_area = granary_area
        self.granary_flag = granary_flag
        self.green_house_area = green_house_area
        self.green_house_flag = green_house_flag
        self.guest_house_area = guest_house_area
        self.guest_house_flag = guest_house_flag
        self.kennel_area = kennel_area
        self.kennel_flag = kennel_flag
        self.lean_to_area = lean_to_area
        self.lean_to_flag = lean_to_flag
        self.loading_platform_area = loading_platform_area
        self.loading_platform_flag = loading_platform_flag
        self.milk_house_area = milk_house_area
        self.milk_house_flag = milk_house_flag
        self.outdoor_kitchen_fireplace_flag = outdoor_kitchen_fireplace_flag
        self.pool_house_area = pool_house_area
        self.pool_house_flag = pool_house_flag
        self.poultry_house_area = poultry_house_area
        self.poultry_house_flag = poultry_house_flag
        self.quonset_area = quonset_area
        self.quonset_flag = quonset_flag
        self.shed_area = shed_area
        self.shed_code = shed_code
        self.silo_area = silo_area
        self.silo_flag = silo_flag
        self.stable_area = stable_area
        self.stable_flag = stable_flag
        self.storage_building_area = storage_building_area
        self.storage_building_flag = storage_building_flag
        self.utility_building_area = utility_building_area
        self.utility_building_flag = utility_building_flag
        self.pole_structure_area = pole_structure_area
        self.pole_structure_flag = pole_structure_flag

    @classmethod
    def from_dict(cls, data):
        return cls(
            buildings_count=data.get("BuildingsCount", ""),
            bath_house_area=data.get("BathHouseArea", ""),
            bath_house_flag=data.get("BathHouseFlag", ""),
            boat_house_area=data.get("BoatHouseArea", ""),
            boat_house_flag=data.get("BoatHouseFlag", ""),
            cabin_area=data.get("CabinArea", ""),
            cabin_flag=data.get("CabinFlag", ""),
            canopy_area=data.get("CanopyArea", ""),
            canopy_flag=data.get("CanopyFlag", ""),
            gazebo_area=data.get("GazeboArea", ""),
            gazebo_flag=data.get("GazeboFlag", ""),
            granary_area=data.get("GranaryArea", ""),
            granary_flag=data.get("GranaryFlag", ""),
            green_house_area=data.get("GreenHouseArea", ""),
            green_house_flag=data.get("GreenHouseFlag", ""),
            guest_house_area=data.get("GuestHouseArea", ""),
            guest_house_flag=data.get("GuestHouseFlag", ""),
            kennel_area=data.get("KennelArea", ""),
            kennel_flag=data.get("KennelFlag", ""),
            lean_to_area=data.get("LeanToArea", ""),
            lean_to_flag=data.get("LeanToFlag", ""),
            loading_platform_area=data.get("LoadingPlatformArea", ""),
            loading_platform_flag=data.get("LoadingPlatformFlag", ""),
            milk_house_area=data.get("MilkHouseArea", ""),
            milk_house_flag=data.get("MilkHouseFlag", ""),
            outdoor_kitchen_fireplace_flag=data.get("OutdoorKitchenFireplaceFlag", ""),
            pool_house_area=data.get("PoolHouseArea", ""),
            pool_house_flag=data.get("PoolHouseFlag", ""),
            poultry_house_area=data.get("PoultryHouseArea", ""),
            poultry_house_flag=data.get("PoultryHouseFlag", ""),
            quonset_area=data.get("QuonsetArea", ""),
            quonset_flag=data.get("QuonsetFlag", ""),
            shed_area=data.get("ShedArea", ""),
            shed_code=data.get("ShedCode", ""),
            silo_area=data.get("SiloArea", ""),
            silo_flag=data.get("SiloFlag", ""),
            stable_area=data.get("StableArea", ""),
            stable_flag=data.get("StableFlag", ""),
            storage_building_area=data.get("StorageBuildingArea", ""),
            storage_building_flag=data.get("StorageBuildingFlag", ""),
            utility_building_area=data.get("UtilityBuildingArea", ""),
            utility_building_flag=data.get("UtilityBuildingFlag", ""),
            pole_structure_area=data.get("PoleStructureArea", ""),
            pole_structure_flag=data.get("PoleStructureFlag", "")
        )

    # Setters
    def set_buildings_count(self, buildings_count):
        self.buildings_count = buildings_count

    def set_bath_house_area(self, bath_house_area):
        self.bath_house_area = bath_house_area

    def set_bath_house_flag(self, bath_house_flag):
        self.bath_house_flag = bath_house_flag

    def set_boat_house_area(self, boat_house_area):
        self.boat_house_area = boat_house_area

    def set_boat_house_flag(self, boat_house_flag):
        self.boat_house_flag = boat_house_flag

    def set_cabin_area(self, cabin_area):
        self.cabin_area = cabin_area

    def set_cabin_flag(self, cabin_flag):
        self.cabin_flag = cabin_flag

    def set_canopy_area(self, canopy_area):
        self.canopy_area = canopy_area

    def set_canopy_flag(self, canopy_flag):
        self.canopy_flag = canopy_flag

    def set_gazebo_area(self, gazebo_area):
        self.gazebo_area = gazebo_area

    def set_gazebo_flag(self, gazebo_flag):
        self.gazebo_flag = gazebo_flag

    def set_granary_area(self, granary_area):
        self.granary_area = granary_area

    def set_granary_flag(self, granary_flag):
        self.granary_flag = granary_flag

    def set_green_house_area(self, green_house_area):
        self.green_house_area = green_house_area

    def set_green_house_flag(self, green_house_flag):
        self.green_house_flag = green_house_flag

    def set_guest_house_area(self, guest_house_area):
        self.guest_house_area = guest_house_area

    def set_guest_house_flag(self, guest_house_flag):
        self.guest_house_flag = guest_house_flag

    def set_kennel_area(self, kennel_area):
        self.kennel_area = kennel_area

    def set_kennel_flag(self, kennel_flag):
        self.kennel_flag = kennel_flag

    def set_lean_to_area(self, lean_to_area):
        self.lean_to_area = lean_to_area

    def set_lean_to_flag(self, lean_to_flag):
        self.lean_to_flag = lean_to_flag

    def set_loading_platform_area(self, loading_platform_area):
        self.loading_platform_area = loading_platform_area

    def set_loading_platform_flag(self, loading_platform_flag):
        self.loading_platform_flag = loading_platform_flag

    def set_milk_house_area(self, milk_house_area):
        self.milk_house_area = milk_house_area

    def set_milk_house_flag(self, milk_house_flag):
        self.milk_house_flag = milk_house_flag

    def set_outdoor_kitchen_fireplace_flag(self, outdoor_kitchen_fireplace_flag):
        self.outdoor_kitchen_fireplace_flag = outdoor_kitchen_fireplace_flag

    def set_pool_house_area(self, pool_house_area):
        self.pool_house_area = pool_house_area

    def set_pool_house_flag(self, pool_house_flag):
        self.pool_house_flag = pool_house_flag

    def set_poultry_house_area(self, poultry_house_area):
        self.poultry_house_area = poultry_house_area

    def set_poultry_house_flag(self, poultry_house_flag):
        self.poultry_house_flag = poultry_house_flag

    def set_quonset_area(self, quonset_area):
        self.quonset_area = quonset_area

    def set_quonset_flag(self, quonset_flag):
        self.quonset_flag = quonset_flag

    def set_shed_area(self, shed_area):
        self.shed_area = shed_area

    def set_shed_code(self, shed_code):
        self.shed_code = shed_code

    def set_silo_area(self, silo_area):
        self.silo_area = silo_area

    def set_silo_flag(self, silo_flag):
        self.silo_flag = silo_flag

    def set_stable_area(self, stable_area):
        self.stable_area = stable_area

    def set_stable_flag(self, stable_flag):
        self.stable_flag = stable_flag

    def set_storage_building_area(self, storage_building_area):
        self.storage_building_area = storage_building_area

    def set_storage_building_flag(self, storage_building_flag):
        self.storage_building_flag = storage_building_flag

    def set_utility_building_area(self, utility_building_area):
        self.utility_building_area = utility_building_area

    def set_utility_building_flag(self, utility_building_flag):
        self.utility_building_flag = utility_building_flag

    def set_pole_structure_area(self, pole_structure_area):
        self.pole_structure_area = pole_structure_area

    def set_pole_structure_flag(self, pole_structure_flag):
        self.pole_structure_flag = pole_structure_flag

    # Getters
    def get_buildings_count(self):
        return self.buildings_count or ""

    def get_bath_house_area(self):
        return self.bath_house_area or ""

    def get_bath_house_flag(self):
        return self.bath_house_flag or ""

    def get_boat_house_area(self):
        return self.boat_house_area or ""

    def get_boat_house_flag(self):
        return self.boat_house_flag or ""

    def get_cabin_area(self):
        return self.cabin_area or ""

    def get_cabin_flag(self):
        return self.cabin_flag or ""

    def get_canopy_area(self):
        return self.canopy_area or ""

    def get_canopy_flag(self):
        return self.canopy_flag or ""

    def get_gazebo_area(self):
        return self.gazebo_area or ""

    def get_gazebo_flag(self):
        return self.gazebo_flag or ""

    def get_granary_area(self):
        return self.granary_area or ""

    def get_granary_flag(self):
        return self.granary_flag or ""

    def get_green_house_area(self):
        return self.green_house_area or ""

    def get_green_house_flag(self):
        return self.green_house_flag or ""

    def get_guest_house_area(self):
        return self.guest_house_area or ""

    def get_guest_house_flag(self):
        return self.guest_house_flag or ""

    def get_kennel_area(self):
        return self.kennel_area or ""

    def get_kennel_flag(self):
        return self.kennel_flag or ""

    def get_lean_to_area(self):
        return self.lean_to_area or ""

    def get_lean_to_flag(self):
        return self.lean_to_flag or ""

    def get_loading_platform_area(self):
        return self.loading_platform_area or ""

    def get_loading_platform_flag(self):
        return self.loading_platform_flag or ""

    def get_milk_house_area(self):
        return self.milk_house_area or ""

    def get_milk_house_flag(self):
        return self.milk_house_flag or ""

    def get_outdoor_kitchen_fireplace_flag(self):
        return self.outdoor_kitchen_fireplace_flag or ""

    def get_pool_house_area(self):
        return self.pool_house_area or ""

    def get_pool_house_flag(self):
        return self.pool_house_flag or ""

    def get_poultry_house_area(self):
        return self.poultry_house_area or ""

    def get_poultry_house_flag(self):
        return self.poultry_house_flag or ""

    def get_quonset_area(self):
        return self.quonset_area or ""

    def get_quonset_flag(self):
        return self.quonset_flag or ""

    def get_shed_area(self):
        return self.shed_area or ""

    def get_shed_code(self):
        return self.shed_code or ""

    def get_silo_area(self):
        return self.silo_area or ""

    def get_silo_flag(self):
        return self.silo_flag or ""

    def get_stable_area(self):
        return self.stable_area or ""

    def get_stable_flag(self):
        return self.stable_flag or ""

    def get_storage_building_area(self):
        return self.storage_building_area or ""

    def get_storage_building_flag(self):
        return self.storage_building_flag or ""

    def get_utility_building_area(self):
        return self.utility_building_area or ""

    def get_utility_building_flag(self):
        return self.utility_building_flag or ""

    def get_pole_structure_area(self):
        return self.pole_structure_area or ""

    def get_pole_structure_flag(self):
        return self.pole_structure_flag or ""


class PropertyUtilities(ResponseBase):
    def __init__(self, hvac_cooling_detail="", hvac_heating_detail="", hvac_heating_fuel="", 
                 sewage_usage="", water_source="", mobile_home_hookup_flag=""):
        self.hvac_cooling_detail = hvac_cooling_detail
        self.hvac_heating_detail = hvac_heating_detail
        self.hvac_heating_fuel = hvac_heating_fuel
        self.sewage_usage = sewage_usage
        self.water_source = water_source
        self.mobile_home_hookup_flag = mobile_home_hookup_flag

    @classmethod
    def from_dict(cls, data):
        return cls(
            hvac_cooling_detail=data.get('HVACCoolingDetail', ""),
            hvac_heating_detail=data.get('HVACHeatingDetail', ""),
            hvac_heating_fuel=data.get('HVACHeatingFuel', ""),
            sewage_usage=data.get('SewageUsage', ""),
            water_source=data.get('WaterSource', ""),
            mobile_home_hookup_flag=data.get('MobileHomeHookupFlag', "")
        )

    # Setters
    def set_hvac_cooling_detail(self, hvac_cooling_detail):
        self.hvac_cooling_detail = hvac_cooling_detail

    def set_hvac_heating_detail(self, hvac_heating_detail):
        self.hvac_heating_detail = hvac_heating_detail

    def set_hvac_heating_fuel(self, hvac_heating_fuel):
        self.hvac_heating_fuel = hvac_heating_fuel

    def set_sewage_usage(self, sewage_usage):
        self.sewage_usage = sewage_usage

    def set_water_source(self, water_source):
        self.water_source = water_source

    def set_mobile_home_hookup_flag(self, mobile_home_hookup_flag):
        self.mobile_home_hookup_flag = mobile_home_hookup_flag

    # Getters
    def get_hvac_cooling_detail(self):
        return self.hvac_cooling_detail or ""

    def get_hvac_heating_detail(self):
        return self.hvac_heating_detail or ""

    def get_hvac_heating_fuel(self):
        return self.hvac_heating_fuel or ""

    def get_sewage_usage(self):
        return self.sewage_usage or ""

    def get_water_source(self):
        return self.water_source or ""

    def get_mobile_home_hookup_flag(self):
        return self.mobile_home_hookup_flag or ""


class PropertyParking(ResponseBase):
    def __init__(self, rv_parking_flag="", parking_space_count="", driveway_area="", driveway_material=""):
        self.rv_parking_flag = rv_parking_flag
        self.parking_space_count = parking_space_count
        self.driveway_area = driveway_area
        self.driveway_material = driveway_material

    @classmethod
    def from_dict(cls, data):
        return cls(
            rv_parking_flag=data.get('RVParkingFlag', ""),
            parking_space_count=data.get('ParkingSpaceCount', ""),
            driveway_area=data.get('DrivewayArea', ""),
            driveway_material=data.get('DrivewayMaterial', "")
        )

    # Setters
    def set_rv_parking_flag(self, rv_parking_flag):
        self.rv_parking_flag = rv_parking_flag

    def set_parking_space_count(self, parking_space_count):
        self.parking_space_count = parking_space_count

    def set_driveway_area(self, driveway_area):
        self.driveway_area = driveway_area

    def set_driveway_material(self, driveway_material):
        self.driveway_material = driveway_material

    # Getters
    def get_rv_parking_flag(self):
        return self.rv_parking_flag or ""

    def get_parking_space_count(self):
        return self.parking_space_count or ""

    def get_driveway_area(self):
        return self.driveway_area or ""

    def get_driveway_material(self):
        return self.driveway_material or ""


class PropertyYardGardenInfo(ResponseBase):
    def __init__(self, topography_code="", fence_code="", fence_area="", courtyard_flag="",
                 courtyard_area="", arbor_pergola_flag="", sprinklers_flag="", golf_course_green_flag="",
                 tennis_court_flag="", sports_court_flag="", arean_flag="", water_feature_flag="",
                 pond_flag="", boat_lift_flag=""):
        self.topography_code = topography_code
        self.fence_code = fence_code
        self.fence_area = fence_area
        self.courtyard_flag = courtyard_flag
        self.courtyard_area = courtyard_area
        self.arbor_pergola_flag = arbor_pergola_flag
        self.sprinklers_flag = sprinklers_flag
        self.golf_course_green_flag = golf_course_green_flag
        self.tennis_court_flag = tennis_court_flag
        self.sports_court_flag = sports_court_flag
        self.arean_flag = arean_flag
        self.water_feature_flag = water_feature_flag
        self.pond_flag = pond_flag
        self.boat_lift_flag = boat_lift_flag

    @classmethod
    def from_dict(cls, data):
        return cls(
            topography_code=data.get('TopographyCode', ""),
            fence_code=data.get('FenceCode', ""),
            fence_area=data.get('FenceArea', ""),
            courtyard_flag=data.get('CourtyardFlag', ""),
            courtyard_area=data.get('CourtyardArea', ""),
            arbor_pergola_flag=data.get('ArborPergolaFlag', ""),
            sprinklers_flag=data.get('SprinklersFlag', ""),
            golf_course_green_flag=data.get('GolfCourseGreenFlag', ""),
            tennis_court_flag=data.get('TennisCourtFlag', ""),
            sports_court_flag=data.get('SportsCourtFlag', ""),
            arean_flag=data.get('AreanFlag', ""),
            water_feature_flag=data.get('WaterFeatureFlag', ""),
            pond_flag=data.get('PondFlag', ""),
            boat_lift_flag=data.get('BoatLiftFlag', "")
        )

    # Setters
    def set_topography_code(self, topography_code):
        self.topography_code = topography_code

    def set_fence_code(self, fence_code):
        self.fence_code = fence_code

    def set_fence_area(self, fence_area):
        self.fence_area = fence_area

    def set_courtyard_flag(self, courtyard_flag):
        self.courtyard_flag = courtyard_flag

    def set_courtyard_area(self, courtyard_area):
        self.courtyard_area = courtyard_area

    def set_arbor_pergola_flag(self, arbor_pergola_flag):
        self.arbor_pergola_flag = arbor_pergola_flag

    def set_sprinklers_flag(self, sprinklers_flag):
        self.sprinklers_flag = sprinklers_flag

    def set_golf_course_green_flag(self, golf_course_green_flag):
        self.golf_course_green_flag = golf_course_green_flag

    def set_tennis_court_flag(self, tennis_court_flag):
        self.tennis_court_flag = tennis_court_flag

    def set_sports_court_flag(self, sports_court_flag):
        self.sports_court_flag = sports_court_flag

    def set_arean_flag(self, arean_flag):
        self.arean_flag = arean_flag

    def set_water_feature_flag(self, water_feature_flag):
        self.water_feature_flag = water_feature_flag

    def set_pond_flag(self, pond_flag):
        self.pond_flag = pond_flag

    def set_boat_lift_flag(self, boat_lift_flag):
        self.boat_lift_flag = boat_lift_flag

    # Getters
    def get_topography_code(self):
        return self.topography_code or ""

    def get_fence_code(self):
        return self.fence_code or ""

    def get_fence_area(self):
        return self.fence_area or ""

    def get_courtyard_flag(self):
        return self.courtyard_flag or ""

    def get_courtyard_area(self):
        return self.courtyard_area or ""

    def get_arbor_pergola_flag(self):
        return self.arbor_pergola_flag or ""

    def get_sprinklers_flag(self):
        return self.sprinklers_flag or ""

    def get_golf_course_green_flag(self):
        return self.golf_course_green_flag or ""

    def get_tennis_court_flag(self):
        return self.tennis_court_flag or ""

    def get_sports_court_flag(self):
        return self.sports_court_flag or ""

    def get_arean_flag(self):
        return self.arean_flag or ""

    def get_water_feature_flag(self):
        return self.water_feature_flag or ""

    def get_pond_flag(self):
        return self.pond_flag or ""

    def get_boat_lift_flag(self):
        return self.boat_lift_flag or ""


class PropertyEstimatedValue(ResponseBase):
    def __init__(self, estimated_value="", estimated_min_value="", estimated_max_value="", confidence_score="", valuation_date=""):
        self.estimated_value = estimated_value
        self.estimated_min_value = estimated_min_value
        self.estimated_max_value = estimated_max_value
        self.confidence_score = confidence_score
        self.valuation_date = valuation_date

    @classmethod
    def from_dict(cls, data):
        return cls(
            estimated_value=data.get('EstimatedValue', ""),
            estimated_min_value=data.get('EstimatedMinValue', ""),
            estimated_max_value=data.get('EstimatedMaxValue', ""),
            confidence_score=data.get('ConfidenceScore', ""),
            valuation_date=data.get('ValuationDate', "")
        )

    # Setters
    def set_estimated_value(self, estimated_value):
        self.estimated_value = estimated_value

    def set_estimated_min_value(self, estimated_min_value):
        self.estimated_min_value = estimated_min_value

    def set_estimated_max_value(self, estimated_max_value):
        self.estimated_max_value = estimated_max_value

    def set_confidence_score(self, confidence_score):
        self.confidence_score = confidence_score

    def set_valuation_date(self, valuation_date):
        self.valuation_date = valuation_date

    # Getters
    def get_estimated_value(self):
        return self.estimated_value or ""

    def get_estimated_min_value(self):
        return self.estimated_min_value or ""

    def get_estimated_max_value(self):
        return self.estimated_max_value or ""

    def get_confidence_score(self):
        return self.confidence_score or ""

    def get_valuation_date(self):
        return self.valuation_date or ""


class PropertyShape(ResponseBase):
    def __init__(self, well_known_text=""):
        self.well_known_text = well_known_text

    @classmethod
    def from_dict(cls, data):
        return cls(
            well_known_text=data.get('WellKnownText', "")
        )

    # Setter
    def set_well_known_text(self, well_known_text):
        self.well_known_text = well_known_text

    # Getter
    def get_well_known_text(self):
        return self.well_known_text or ""






