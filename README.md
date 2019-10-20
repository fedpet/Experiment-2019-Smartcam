# Experiment-2019-Smartcam
I'm sorry, the code is a mess but finishing my thesis in time took the priority.

Run `gradlew build` to compile.

`gradlew showcase_ff_linpro_from_center`  and `gradlew showcase_ff_linpro_generic`
 to run the simulations shown during the presentation.

## TODO
- Clean the mess
  - ZigZagMove2 should be fixed in newer versions of Alchemist, if not then make a pr
  - Same for LevyWalk
  - InitHeading should be removed, the initial heading should become a constructor parameter of Node
  - AbstractConfigurableMoveNodeWithAccurateEuclideanDestination will then become useless and already included in Alchemist
  - Make pr to Alchemist with the fixed version of ZigZagRandomTarget2, RandomTarget, and ChangeTargetOnCollision. Make tests, remove them from here
  - CameraTargetAssignmentProblem (aka LinPro) handles the "fair" variant with.... commented code...
  - tests
  - ProtelisUtils is unreadable
- Improve performance of LinPro during simulations
  - ~~CachedCameraTargetAssignmentProblem doesn't work because cameras are not synchronized, find another method~~
  - The optimal solution for a round could probably be also the optimal solution for the next one, or a feasible one
  - If the set of targets and cameras didn't change from the previous round, the previous optimal solution could be assumed to still be the optimal one. This is an approximation.
  - There exists faster algorithms than the simplex method to solve transportation problems. Hint: Kramer's theorem using determinants of the submatrixes of the coefficients' one?
