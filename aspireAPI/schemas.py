from ninja import Schema


class ErrorSchema(Schema):
    """
    Pydantic representation of Error
    Can be extended to include more fields
    """

    message: str
