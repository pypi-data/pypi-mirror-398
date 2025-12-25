from pyroll.core import RollPass, Hook
from pyroll.karman_force_torque.karman_solver import KarmanSolver

RollPass.karman_solution = Hook[KarmanSolver]()
"""Solution values of von-Karman ODE"""


@RollPass.karman_solution
def karman_solution(self: RollPass):
    return KarmanSolver(roll_pass=self)


@RollPass.InProfile.velocity
def profile_entry_velocity(self: RollPass.InProfile):

    return self.roll_pass.karman_solution.entry_velocity


@RollPass.OutProfile.velocity
def velocity(self: RollPass.OutProfile):
    return self.roll_pass.karman_solution.exit_velocity


@RollPass.roll_force
def roll_force(self: RollPass):
    return (self.karman_solution.roll_force_per_unit_width * self.roll.contact_area) / self.roll.contact_length


@RollPass.Roll.neutral_point
def neutral_point(self: RollPass.Roll):
    return self.roll_pass.karman_solution.neutral_plane_position


@RollPass.Roll.roll_torque
def roll_torque(self: RollPass.Roll):
    return (
            self.roll_pass.karman_solution.roll_torque_per_unit_width * self.roll_pass.contact_area) / self.contact_length
