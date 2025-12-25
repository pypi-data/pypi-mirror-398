from abc import ABC, abstractmethod
import time

class SteppableSystem(ABC):
    """
    A system that can be stepped at a specific frequency.
    """

    def __init__(self):
        # Must be set by the subclass
        self.operating_frequency = None

        # Managed by SteppableSystem
        self.current_step = 0
        self.step_time = None
        self.next_step_start_time = None
        self.is_root_step = False

    def start(self, is_root_step: bool = False):
        if not hasattr(self, 'operating_frequency'):
            raise ValueError("operating_frequency must be set by the " + self.__class__.__name__)
        self.current_step = 0
        self.step_time = 1.0 / self.operating_frequency
        self.next_step_start_time = time.time()
        self.is_root_step = is_root_step
        
    def get_operating_frequency(self):
        return self.operating_frequency
    
    def step(self):
        self._before_step()
        self._step()
        self._after_step()
    
    def _before_step(self):
        self.next_step_start_time = self.next_step_start_time + self.step_time

    def _after_step(self):
        self.current_step += 1
        if self.is_root_step:
            end_time = time.time()
            # More accurate sleep at the cost of compute. Sleep has a 20%-30% error.
            if self.next_step_start_time - end_time > 0:
                time.sleep(self.next_step_start_time - end_time)
    
    def get_next_step_start_time(self):
        return self.next_step_start_time
    
    def on_abort(self):
        pass

    @abstractmethod
    def _step(self):
        pass
    