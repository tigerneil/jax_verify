# coding=utf-8
# Copyright 2020 The jax_verify Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Methods for solving relaxation generated by relaxation.py.

This file mainly calls out to relaxation.RelaxationSolvers defined in other
files, and provides a higher-level interface than using relaxation.py directly.
"""

from jax_verify.src import bound_propagation
from jax_verify.src import cvxpy_relaxation_solver
from jax_verify.src import relaxation


def solve_planet_relaxation(
    logits_fn, initial_bounds, boundprop_transform,
    objective, objective_bias, index,
    solver=cvxpy_relaxation_solver.CvxpySolver):
  """Solves the "Planet" (Ehlers 17) or "triangle" relaxation.

  The general approach is to use jax_verify to generate constraints, which can
  then be passed to generic solvers. Note that using CVXPY will incur a large
  overhead when defining the LP, because we define all constraints element-wise,
  to avoid representing convolutional layers as a single matrix multiplication,
  which would be inefficient. In CVXPY, defining large numbers of constraints is
  slow.

  Args:
    logits_fn: Mapping from inputs (batch_size x input_size) -> (batch_size,
      num_classes)
    initial_bounds: `IntervalBound` with initial bounds on inputs,
      with lower and upper bounds of dimension (batch_size x input_size).
    boundprop_transform: bound_propagation.BoundTransform instance, such as
      `jax_verify.ibp_transform`. Used to pre-compute interval bounds for
      intermediate activations used in defining the Planet relaxation.
    objective: Objective to optimize, given as an array of coefficients to be
      applied to the output of logits_fn defining the objective to minimize
    objective_bias: Bias to add to objective
    index: Index in the batch for which to solve the relaxation
    solver: A relaxation.RelaxationSolver, which specifies the backend to solve
      the resulting LP.
  Returns:
    val: The optimal value from the relaxation
    status: The status of the relaxation solver
  """
  relaxation_transform = relaxation.RelaxationTransform(boundprop_transform)
  variable, graph = bound_propagation.bound_propagation(
      relaxation_transform, logits_fn, initial_bounds)
  value, status = relaxation.solve_relaxation(
      solver, objective, objective_bias, variable, graph.env,
      index=index, time_limit=None)
  return value, status