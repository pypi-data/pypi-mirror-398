from math import exp


class BoltzmannAcceptance:
    """
    The BoltzmannEnergy class models energy difference transitions using the Boltzmann
    distribution, often applied in fields like statistical mechanics and optimization.

    This class helps calculate the probability of transitioning between states.
    Through a callable interface, it computes values based on energy state differences,
    a provided temperature, and the Boltzmann constant. It aids in understanding
    systems governed by thermodynamics or simulated annealing processes.

    Attributes:
        boltzmann_constant (float): The Boltzmann constant used in the energy calculation.
    """
    def __init__(self, boltzmann_constant: float = 1.0):
        self._boltzmann_constant = boltzmann_constant

    def __call__(self, current_value: float, new_value: float, temperature: float) -> float:
        if temperature == 0.0:
            return 0.0
        return exp(-(new_value - current_value) / (self._boltzmann_constant * temperature))


