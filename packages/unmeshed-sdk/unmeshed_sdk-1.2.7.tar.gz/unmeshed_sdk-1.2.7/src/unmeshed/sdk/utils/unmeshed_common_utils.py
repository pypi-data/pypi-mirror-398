import hashlib

class UnmeshedCommonUtils:
    @staticmethod
    def create_secure_hash(_input: str) -> str:
        try:
            hash_object = hashlib.sha256()
            hash_object.update(_input.encode('utf-8'))
            return hash_object.hexdigest()
        except Exception as e:
            raise Exception('Error creating hash') from e
