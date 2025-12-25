from django.db.models import TextChoices

class ExecutionStatus(TextChoices):
    PENDING = "PENDING", "Pending"
    IN_DRAFT = "IN_DRAFT", "In Draft"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"
    REJECTED = "REJECTED", "Rejected"
    FAILED = "FAILED", "Failed"
    UNKNOWN = "UNKNOWN", "Unknown"



class ExecutionInstruction(TextChoices):

    MARKET_ON_CLOSE = "MARKET_ON_CLOSE", "Market On Close" # no parameter
    GUARANTEED_MARKET_ON_CLOSE = "GUARANTEED_MARKET_ON_CLOSE", "Guaranteed Market On Close" # no parameter
    GUARANTEED_MARKET_ON_OPEN  = "GUARANTEED_MARKET_ON_OPEN", "Guaranteed Market On Open" # no parameter
    GPW_MARKET_ON_CLOSE = "GPW_MARKET_ON_CLOSE", "GPW Market On Close" # no parameter
    MARKET_ON_OPEN = "MARKET_ON_OPEN", "Market On Open" # no parameter
    IN_LINE_WITH_VOLUME = "IN_LINE_WITH_VOLUME", "In Line With Volume" # 1 parameter "Percentage"
    LIMIT_ORDER = "LIMIT_ORDER", "Limit Order" # 2 parameters "limit and cutoff"
    VWAP = "VWAP", "VWAP" # 2 parameters
    TWAP = "TWAP", "TWAP" # 2 paramters



class RoutingException(Exception):
    def __init__(self, errors):
        # messages: a list of strings
        super().__init__()  # You can pass a summary to the base Exception
        self.errors = errors

    def __str__(self):
        return str(self.errors)
