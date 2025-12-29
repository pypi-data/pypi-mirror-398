from properties_defs.property_address import PropertyAddress


class UnderContractTask:
    def __init__(self, address: str, gid: str):
        self.address: PropertyAddress = PropertyAddress.from_full_address(address)
        self.gid: str = gid



