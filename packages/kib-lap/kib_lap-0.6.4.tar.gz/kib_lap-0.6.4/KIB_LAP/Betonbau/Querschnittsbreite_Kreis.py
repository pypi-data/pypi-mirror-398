import numpy as np
import matplotlib.pyplot as plt

class CircleSection:
    def __init__(self, radius):
        """
        Initializes the circle with the given radius.
        
        Parameters:
        radius (float): Radius of the circle.
        """
        self.radius = radius

    def calculate_section_width_at_height(self, height):
        """
        Calculates the width of the circle section at a specific height (y-value).
        
        Parameters:
        height (float): The y-value at which to calculate the section width.
        
        Returns:
        float: Width of the circle section at the specified height.
        """
        if abs(height) > self.radius:
            return 0.0
        return 2 * np.sqrt(self.radius**2 - height**2)

    def plot(self, height=None):
        """
        Plots the circle and optionally a horizontal line at the specified height.
        
        Parameters:
        height (float, optional): The y-value at which to plot a horizontal line.
        """
        theta = np.linspace(0, 2 * np.pi, 100)
        x = self.radius * np.cos(theta)
        y = self.radius * np.sin(theta)

        plt.figure()
        plt.plot(x, y, 'b-', label='Circle')
        plt.fill(x, y, 'b', alpha=0.3)
        if height is not None:
            plt.axhline(y=height, color='g', linestyle='--', label=f'Height = {height}')
            section_width = self.calculate_section_width_at_height(height)
            plt.plot([-section_width / 2, section_width / 2], [height, height], 'r-', linewidth=2, label=f'Section Width = {section_width:.2f}')
        plt.legend()
        plt.xlabel('x')
        plt.ylabel('y')
        plt.title('Circle and Section Width at Specific Height')
        plt.axis('equal')
        plt.show()

# Example usage
radius = 1.0
circle = CircleSection(radius)

# Define the height at which to calculate the section width
height = -0.5
section_width = circle.calculate_section_width_at_height(height)
print(f"Section width at height {height} is: {section_width}")

# Plot the circle and the horizontal line
circle.plot(height)
