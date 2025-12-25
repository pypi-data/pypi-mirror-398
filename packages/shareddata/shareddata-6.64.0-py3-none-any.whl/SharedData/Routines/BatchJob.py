# SharedData/Routines/BatchJob.py
import argparse
import base64
import bson

from SharedData.Logger import Logger

class BatchJob:
    """
    Represents a batch job initialized with command-line arguments.
    
    Parses command-line arguments to extract a required routine hash and optional BSON-encoded routine arguments.
    Decodes the BSON arguments if provided and stores them in the instance.
    Connects a Logger instance using the extracted hash and an optional user identifier.
    
    Attributes:
        hash (str): The routine hash extracted from command-line arguments.
        args (dict): The decoded routine arguments from BSON, or empty if none provided.
    
    Methods:
        parse_args(): Parses and returns command-line arguments for 'hash' and 'bson'.
        decode_bson(b64_arg): Decodes a base64-encoded BSON string into a dictionary.
    """
    def __init__(self, user=None,args=None):
        """
        Initializes the instance by parsing command-line arguments or using provided arguments, setting the hash attribute, decoding BSON data if available, and establishing a logger connection.
        
        Parameters:
            user (optional): An optional user identifier to associate with the logger connection.
            args (optional): A dictionary of arguments; if provided, parsing is skipped.
        
        Behavior:
        - If `args` is provided, sets `self.hash` and `self.args` directly from it.
        - Otherwise, parses command-line arguments using `parse_args()`.
        - Sets `self.hash` from parsed arguments.
        - If a BSON string is present in parsed arguments, decodes it and stores the result in `self.args`.
        - Connects the Logger with the hash and optional user information.
        """
        if args is not None:
            self.hash = args.get('hash', None)
            self.args = args
        else:
            _args = self.parse_args()        
            self.hash = _args.hash
            self.args = {}
            if _args.bson:
                self.args = self.decode_bson(_args.bson)                    
        Logger.connect(f'@{self.hash}', user=user)
    
    @staticmethod
    def parse_args():
        """
        Parses command-line arguments for routine configuration.
        
        Returns:
            argparse.Namespace: An object containing the parsed command-line arguments:
                - hash (str): Required. The routine hash.
                - bson (str or None): Optional. The routine arguments in BSON format. Defaults to None.
        """
        parser = argparse.ArgumentParser(description="routine configuration")
        parser.add_argument('--hash', required=True, help='routine hash')
        parser.add_argument('--bson', default=None, help='routine args')
        return parser.parse_args()

    @staticmethod
    def decode_bson(b64_arg):
        """
        Decode a base64-encoded BSON string into a Python dictionary.
        
        Args:
            b64_arg (str): A base64-encoded string representing BSON data.
        
        Returns:
            dict: The decoded BSON data as a Python dictionary. Returns an empty dictionary if the input is None or empty.
        """
        if not b64_arg:
            return {}
        bson_data = base64.b64decode(b64_arg)
        return bson.BSON(bson_data).decode()

# Example usage:    
# from SharedData.Logger import Logger
# from SharedData.Routines.BatchJob import BatchJob
# job = BatchJob()
# Logger.log.info(f'hash: {job.hash}')
# Logger.log.info(f'args: {job.args}')


