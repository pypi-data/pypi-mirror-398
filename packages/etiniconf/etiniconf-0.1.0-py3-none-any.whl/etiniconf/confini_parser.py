import configparser

class ConfiniError(Exception):    
    """A general error related to configuration."""
    
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
    
    def __str__(self):
        return self.message

class SectionNotFoundError(ConfiniError):
    """Raised when a section is not found in the configuration."""
    
    def __init__(self, section):
        self.section = section
        message = f"No section: {section}"
        super().__init__(message)

class OptionNotFoundError(ConfiniError):
    """Raised when an option is not found in the configuration."""
    
    def __init__(self, section, option):
        self.section = section
        self.option = option
        message = f"No option '{option}' in section: {section}"
        super().__init__(message)

class ConfiniResult:
    """Used to unify the return of success and failure"""
    
    def __init__(self, value=None, error=None):
        self.value = value
        self.error = error
        self.is_success = error is None
    
    def __bool__(self):
        return self.is_success
    
    @classmethod
    def success(cls, value):
        return cls(value=value)
    
    @classmethod
    def failure(cls, error):
        return cls(error=error)

class SectionProxy:
    """Used to support attributes/dictionaries"""
    
    def __init__(self, manager, section):
        self._manager = manager
        self._section = section
    
    def __getattr__(self, option):
        """Support the access method of conf.section.option"""
        return self._manager.get_value(self._section, option)
    
    def __getitem__(self, option):
        """Support the access method of conf.section['option']"""
        return self._manager.get_value(self._section, option)

class ConfiniParserFactory:
    """Used to create configuration managers with different error - handling strategies"""
    
    @staticmethod
    def create_with_exception_strategy(filepath):
        """Create a configuration manager that uses the exception - handling strategy"""
        return ConfiniParser(filepath, error_strategy="exception")
    
    @staticmethod
    def create_with_result_strategy(filepath):
        """Create a configuration manager using the result object strategy"""
        return ConfiniParser(filepath, error_strategy="result")
    
    @staticmethod
    def create_with_silent_strategy(filepath):
        """Create a configuration manager that uses the silent handling strategy"""
        return ConfiniParser(filepath, error_strategy="silent")

class ConfiniParser():
    def __init__(self, filepath, error_strategy="exception"):
        self.filepath = filepath
        self.config = configparser.ConfigParser()
        self.config.read(filepath)
        self.error_strategy = error_strategy

    def _handle_error(self, error):
        """Handle errors according to the strategy"""
        if self.error_strategy == "exception":
            raise error
        elif self.error_strategy == "result":
            return ConfiniResult.failure(error)
        elif self.error_strategy == "silent":
            return None
        else:
            raise ValueError(f"Unknown error strategy: {self.error_strategy}")

    def get_value(self, section, option):
        if not self.config.has_section(section):
            return self._handle_error(SectionNotFoundError(section))
        
        if not self.config.has_option(section, option):
            return self._handle_error(OptionNotFoundError(section, option))
        
        value = self.config.get(section, option)
        return ConfiniResult.success(value) if self.error_strategy == "result" else value

    def set_value(self, section, option, value):
        """If the section does not exist, create it first."""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, value)
        with open(self.filepath, 'w') as configfile:
            self.config.write(configfile)

    def add_section(self, section):
        if not self.config.has_section(section):
            self.config.add_section(section)
            with open(self.filepath, 'w') as configfile:
                self.config.write(configfile)

    def remove_section(self, section):
        if self.config.has_section(section):
            self.config.remove_section(section)
            with open(self.filepath, 'w') as configfile:
                self.config.write(configfile)

    def get_sections(self):
        sections = self.config.sections()
        return ConfiniResult.success(sections) if self.error_strategy == "result" else sections

    def get_options(self, section):
        if not self.config.has_section(section):
            return self._handle_error(SectionNotFoundError(section))
        
        options = self.config.options(section)
        return ConfiniResult.success(options) if self.error_strategy == "result" else options
    
    def get_options_items(self, section):
        if not self.config.has_section(section):
            return self._handle_error(SectionNotFoundError(section))
        
        items = self.config.items(section)
        return ConfiniResult.success(items) if self.error_strategy == "result" else items

    def __getattr__(self, section):
        """Support the access method of conf.section.option"""
        if section in self.config.sections():
            return SectionProxy(self, section)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{section}'")

    def __getitem__(self, section):
        """Support the access method of conf['section']['option']"""
        if self.config.has_section(section):
            return SectionProxy(self, section)
        raise SectionNotFoundError(section)

    def __contains__(self, section):
        """Support 'section' in conf operation"""
        return self.config.has_section(section)
    