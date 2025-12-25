class BaseVectorDistance:
    def __init__(self, left: str | list[float], right: str | list[float]) -> None:
        self.left = left
        self.right = right


class L2Distance(BaseVectorDistance):
    pass


class CosineDistance(BaseVectorDistance):
    pass


class InnerProduct(BaseVectorDistance):
    pass


class L1Distance(BaseVectorDistance):
    pass
