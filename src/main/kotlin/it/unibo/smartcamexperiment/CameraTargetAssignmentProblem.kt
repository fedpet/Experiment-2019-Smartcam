package it.unibo.smartcamexperiment

/**
 * NOTE: Apache's SimplexSolver is extremely slow for big problems. may need to rewrite this using a better implementation
 * e.g. https://github.com/WinVector/WVLPSolver
 * AND/OR Let fewer nodes solve it.
 *
 * Given a list of sources (cameras) and a list of destinations (targets), decides which camera gets which target.
 * @param <S> source type
 * @param <D> destination type
 */
interface CameraTargetAssignmentProblem<S, D> {

    /**
     * Given a list of sources and a list of destinations, decides which source gets which destination.
     * @param sources all possible sources
     * @param destinations all possible destinations
     * @param maxSourcesPerDestination maximum number of sources for each destination
     * @param cost a function calculating the cost for a source to reach the given destination.
     * @return a map from sources to destinations
     */
    fun solve(sources: List<S>, destinations: List<D>, maxSourcesPerDestination: Int, cost: (source: S, destination: D) -> Double): Map<S, D>
}
