package it.unibo.smartcamexperiment.linpro

import org.danilopianini.util.LinkedListSet

/**
 * Basic cache which takes into account only the last input.
 * Note: it does not take into consideration the cost function!
 * See [CameraTargetAssignmentProblem] for a description of the parameters.
 */
class LinproCache<S, D> {
    private var lastInput = Input<S, D>(emptySet(), emptySet(), 0, false) { _, _ -> 0.0 }
    private var lastResult = emptyMap<S, D>()

    /**
     * Get the cached result, or compute a new one if it is not present.
     * The first parameters are those of [CameraTargetAssignmentProblem].
     * @param calculate is the function which is called to calculate the correct result, in case the cache misses
     */
    fun get(sources: List<S>,
            destinations: List<D>,
            maxSourcesPerDestination: Int,
            fair: Boolean,
            cost: (source: S, destination: D) -> Double,
            calculate: (sources: List<S>,
                        destinations: List<D>,
                        maxSourcesPerDestination: Int,
                        fair: Boolean,
                        cost: (source: S, destination: D) -> Double) -> Map<S, D>
    ): Map<S, D> {
        val destsSet = LinkedListSet(destinations)
        val newInput = Input(sources.toSet(), destsSet, maxSourcesPerDestination, fair, cost)
        return if (lastInput != newInput) {
            lastInput = newInput
            lastResult = calculate(sources, destinations, maxSourcesPerDestination, fair, cost)
            lastResult
        } else {
            // return updated positions
            lastResult.mapValues { entry -> destsSet[destsSet.indexOf(entry.value)] }
        }
    }

    private class Input<S, D>(
        private val sources: Set<S>,
        private val destinations: Set<D>,
        private val maxSourcesPerDestination: Int,
        private val fair: Boolean,
        cost: (source: S, destination: D) -> Double) {

        override fun equals(other: Any?): Boolean {
            if (this === other) return true
            if (javaClass != other?.javaClass) return false
            other as Input<*, *>
            if (sources != other.sources) return false
            if (destinations != other.destinations) return false
            if (maxSourcesPerDestination != other.maxSourcesPerDestination) return false
            if (fair != other.fair) return false
            return true
        }

        override fun hashCode(): Int {
            var result = sources.hashCode()
            result = 31 * result + destinations.hashCode()
            result = 31 * result + maxSourcesPerDestination
            result = 31 * result + fair.hashCode()
            return result
        }
    }
}