class ValidatorNotFountError(Exception):
    def __init__(self, validator_name:str):
        super().__init__(f"Validator {validator_name} not found")

class EmptyValidatorNameError(Exception):
    def __init__(self, validator_name:str):
        super().__init__(f"Empty validator name")