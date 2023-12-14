class Setting:
    def default(self) -> None:
        for key in self.__dict__.keys():
            if issubclass(type(self.__dict__[key]), Setting):
                self.__dict__[key].default()
