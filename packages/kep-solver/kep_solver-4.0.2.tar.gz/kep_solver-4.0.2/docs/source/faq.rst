**************************
Frequently asked questions
**************************

How can I set a timeout when solving models?

  The :func:`kep_solver.model.Model.solve` and :func:`kep_solver.programme.Programme.solve_single` functions both support a parameter called `solvingOptions`, which is a :class:`kep_solver.solving.SolvingOptions` object.
  This object supports, amongst other things, assigning a particular PuLP solver, and in this manner a timeout can be applied as follows:
  ::

        from pulp import apis
        time_limited_solver = apis.COIN_CMD(timeLimit=60)
        options = SolvingOptions(solver=time_limited_solver)
        model.solve(solvingOptions=options)

  Note that PuLP supports `many other solvers <https://coin-or.github.io/pulp/technical/solvers.html>`_ that you can try, but some of them may not be available.
