from amsdal_data.transactions.decorators import async_transaction, transaction

@transaction
def rollback_to_timestamp(timestamp: float) -> None:
    """
    Rollback the data to the given timestamp
    Args:
        timestamp (float): The timestamp to rollback the data to.
    Returns:
        None
    """
@transaction
def rollback_transaction(transaction_id: str) -> None:
    """
    Rollback the data to the point in time before the given transaction
    Args:
        transaction_id (str): The transaction ID to rollback the data to.
    Returns:
        None
    """
@async_transaction
async def async_rollback_to_timestamp(timestamp: float) -> None:
    """
    Rollback the data to the given timestamp
    Args:
        timestamp (float): The timestamp to rollback the data to.
    Returns:
        None
    """
@async_transaction
async def async_rollback_transaction(transaction_id: str) -> None:
    """
    Rollback the data to the point in time before the given transaction
    Args:
        transaction_id (str): The transaction ID to rollback the data to.
    Returns:
        None
    """
