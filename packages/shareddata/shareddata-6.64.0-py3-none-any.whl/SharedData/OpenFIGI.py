import requests
import os
import json

class OpenFIGI:
    """
    Client for interacting with the OpenFIGI API to map third-party security identifiers to FIGIs.
    
    This class provides methods to create mapping jobs, validate them against allowed values,
    submit mapping requests to the OpenFIGI API, and manage the retrieval and caching of valid
    mapping values used for validation.
    
    Attributes:
        api_key (str): API key for authenticating with the OpenFIGI API. If not provided, attempts to read from the environment variable 'OPENFIGI_API_KEY'.
        base_url (str): Base URL for the OpenFIGI API endpoints.
        headers (dict): HTTP headers including content type and optional API key for requests.
        mapping_values (dict): Cached valid values for various mapping keys used to validate mapping jobs.
    
    Methods:
        create_mapping_job(...): Constructs a dictionary representing a single mapping job with required and optional parameters.
        map_identifiers(mapping_jobs): Sends a list of mapping jobs to the OpenFIGI API and returns the mapping results.
        validate_mapping_job(job): Validates a mapping job's fields against the cached valid mapping values.
        get_mapping_values(key): Retrieves the list of valid values for a given mapping key from the OpenFIGI API.
        save_mapping_values_to_json(json_file): Fetches all relevant mapping values
    """
    def __init__(self, api_key=None):
        """
        Initialize the client with an optional API key for accessing the OpenFIGI API.
        
        If no API key is provided, attempts to retrieve it from the environment variable 'OPENFIGI_API_KEY'.
        Sets the base URL and default headers for API requests.
        If an API key is available, adds it to the request headers.
        Loads mapping values by calling the `load_mapping_values` method during initialization.
        """
        self.api_key = api_key or os.getenv('OPENFIGI_API_KEY')
        self.base_url = 'https://api.openfigi.com/v3'
        self.headers = {'Content-Type': 'application/json'}
        if self.api_key:
            self.headers['X-OPENFIGI-APIKEY'] = self.api_key

        # Load mapping values at startup
        self.mapping_values = self.load_mapping_values()

    def create_mapping_job(self, id_type, id_value, 
                           exch_code=None, mic_code=None, currency=None, market_sec_des=None, 
                           security_type=None, security_type2=None, include_unlisted_equities=False, 
                           option_type=None, strike=None, contract_size=None, coupon=None, 
                           expiration=None, maturity=None, state_code=None):
        """
        '''
        Create a mapping job dictionary for the /v3/mapping endpoint.
        
        Args:
            id_type (str): Type of third-party identifier.
            id_value (str or int): The value for the third-party identifier.
            exch_code (str, optional): Exchange code of the desired instrument.
            mic_code (str, optional): Market identification code.
            currency (str, optional): Currency of the desired instrument.
            market_sec_des (str, optional): Market sector description.
            security_type (str, optional): Security type.
            security_type2 (str, optional): Alternative security type.
            include_unlisted_equities (bool, optional): Include unlisted equities.
            option_type (str, optional): Option type (Call or Put).
            strike (list, optional): Strike price interval [a, b].
            contract_size (list, optional): Contract size interval [a, b].
            coupon (list, optional): Coupon interval [a, b].
            expiration (list, optional): Expiration date interval [a, b].
            maturity (list, optional): Maturity date interval [a, b].
            state_code (str, optional): State code.
        
        Returns:
            dict: A dictionary representing a mapping job with provided parameters.
        """
        job = {
            'idType': id_type,
            'idValue': id_value
        }

        # Add optional parameters if provided
        if exch_code is not None:
            job['exchCode'] = exch_code
        if mic_code is not None:
            job['micCode'] = mic_code
        if currency is not None:
            job['currency'] = currency
        if market_sec_des is not None:
            job['marketSecDes'] = market_sec_des
        if security_type is not None:
            job['securityType'] = security_type
        if security_type2 is not None:
            job['securityType2'] = security_type2
        if include_unlisted_equities:
            job['includeUnlistedEquities'] = include_unlisted_equities
        if option_type is not None:
            job['optionType'] = option_type
        if strike is not None:
            job['strike'] = strike
        if contract_size is not None:
            job['contractSize'] = contract_size
        if coupon is not None:
            job['coupon'] = coupon
        if expiration is not None:
            job['expiration'] = expiration
        if maturity is not None:
            job['maturity'] = maturity
        if state_code is not None:
            job['stateCode'] = state_code

        return job

    def map_identifiers(self, mapping_jobs):
        """
        Send a batch of mapping jobs to the API to convert third-party identifiers into FIGIs.
        
        Each mapping job in the input list should be a dictionary specifying the identifiers to map.
        The method validates each job before sending the request.
        
        Args:
            mapping_jobs (list): A list of dictionaries, each representing a mapping job containing identifiers to be mapped.
        
        Returns:
            list: A list of mapping results returned by the API, each corresponding to an input mapping job.
        
        Raises:
            requests.exceptions.HTTPError: If the HTTP request to the mapping endpoint fails.
        """
        # Validate mapping jobs
        for job in mapping_jobs:
            self.validate_mapping_job(job)

        url = f"{self.base_url}/mapping"
        response = requests.post(url, json=mapping_jobs, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def validate_mapping_job(self, job):
        """
        Validate a mapping job by ensuring each value in the job dictionary is within the allowed values defined in self.mapping_values.
        
        Args:
            job (dict): A dictionary representing the mapping job to validate, where keys correspond to mapping keys and values are the values to validate.
        
        Raises:
            ValueError: If any value in the job is not present in the corresponding list of valid values in self.mapping_values.
        """
        for key in job:
            if key in self.mapping_values:
                if job[key] not in self.mapping_values[key]:
                    raise ValueError(f"Invalid value '{job[key]}' for key '{key}'. Valid values are: {self.mapping_values[key]}")        

    def get_mapping_values(self, key):
        """
        Retrieve the list of mapping values associated with the specified key from a remote service.
        
        Args:
            key (str): The key for which to fetch the mapping values.
        
        Returns:
            list: The list of mapping values if available; otherwise, an empty list.
        
        Raises:
            Exception: If the response contains an error message.
        
        Notes:
            If the response contains a warning, it will be printed to the console and an empty list will be returned.
        """
        url = f"{self.base_url}/mapping/values/{key}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        if 'values' in data:
            return data['values']
        elif 'error' in data:
            raise Exception(data['error'])
        elif 'warning' in data:
            print("Warning:", data['warning'])
            return []
        return []

    def save_mapping_values_to_json(self, json_file='openfigi_mapping_values.json'):
        """
        Save specific mapping values retrieved from the API to a JSON file.
        
        This method fetches mapping values for predefined keys from the API, handles any exceptions during retrieval,
        and writes the collected data to a specified JSON file. It also prints progress messages throughout the process.
        
        Args:
            json_file (str): The filename where the mapping values will be saved. Defaults to 'openfigi_mapping_values.json'.
        
        Returns:
            dict: A dictionary containing the mapping values retrieved from the API.
        """
        keys = ['idType', 'exchCode', 'micCode', 'currency', 'marketSecDes',
                'securityType', 'securityType2', 'stateCode']
        
        mapping_values = {}
        print("Starting the process to save mapping values.")
        for key in keys:
            try:
                print(f"Fetching mapping values for key: {key}")
                mapping_values[key] = self.get_mapping_values(key)
                print(f"Successfully retrieved values for key: {key}")
            except Exception as e:
                print(f"Error retrieving values for key {key}: {e}")
        
        print(f"Saving mapping values to {json_file}...")
        with open(json_file, 'w') as f:
            json.dump(mapping_values, f, indent=4)
        print("Mapping values successfully saved to JSON file.")
        
        return mapping_values

    def load_mapping_values(self, json_file='openfigi_mapping_values.json'):
        """
        Load mapping values from a JSON file. If the specified file does not exist, generate and save the mapping values to the file before loading.
        
        Args:
            json_file (str): The path to the JSON file containing the mapping values. Defaults to 'openfigi_mapping_values.json'.
        
        Returns:
            dict: A dictionary containing the loaded mapping values.
        """
        if not os.path.exists(json_file):
            return self.save_mapping_values_to_json(json_file)
        
        # print(f"Loading mapping values from {json_file}...")
        with open(json_file, 'r') as f:
            return json.load(f)
