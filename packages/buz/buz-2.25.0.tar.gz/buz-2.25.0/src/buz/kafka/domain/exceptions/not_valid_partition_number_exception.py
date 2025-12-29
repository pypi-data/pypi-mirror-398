class NotValidPartitionNumberException(Exception):
    def __init__(
        self,
        *,
        partition_number: int,
        min_partition_number: int,
    ) -> None:
        super().__init__(
            f'"{partition_number}" is not a valid partition number, the minimum partition number is "{min_partition_number}"'
        )
