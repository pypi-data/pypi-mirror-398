class Config:
    def __init__(
            self,
            skip_property_return_annotation: bool,
    ):
        self.skip_property_return_annotation = skip_property_return_annotation


class DefaultConfig(Config):
    def __init__(
            self,
            skip_property_return_annotation: bool = False,
    ):

        super().__init__(
            skip_property_return_annotation=skip_property_return_annotation,
        )
