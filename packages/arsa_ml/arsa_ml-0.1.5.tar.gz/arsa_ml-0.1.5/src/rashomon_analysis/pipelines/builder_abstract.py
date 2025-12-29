from abc import ABC, abstractmethod

class Builder(ABC):

    '''
        Abstract class asserting that all pipeline classes have implemented methods such as:
        preview_rashomon(), set_epsilon() and build()
    '''

    @abstractmethod
    def preview_rashomon(self):
        '''
            Method for printing all trained models and their scores (leaderboard) and the Rashomon Set size plot
            to help the user choose the right epsilon parameter value.
        '''
        pass

    @abstractmethod
    def set_epsilon(self):
        '''
            setting epsilon parameter value. Needs to be completed before the build() method.
        '''
        pass

    @abstractmethod
    def build(self):
        '''
            Core method for performing all pipeline steps. Has to assert that all parameters including epsilon have been specified.
        '''
        pass

    @abstractmethod
    def dashboard_close(self):
        '''
            Method closing all stramlit processes.
        '''
        pass