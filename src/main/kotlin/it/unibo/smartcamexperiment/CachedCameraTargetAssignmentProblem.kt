package it.unibo.smartcamexperiment

import com.yundom.kache.Builder
import com.yundom.kache.Kache
import com.yundom.kache.config.LRU
import it.unibo.alchemist.model.implementations.positions.Euclidean2DPosition
import it.unibo.alchemist.model.interfaces.VisibleNode

/*
 * Tried every possible hack I could imagine.
 * It does not work, the cameras are simply solving different problems with different inputs even when they are fully connected.
 * They quickly get completely desynchronized and the hit ratio goes to zero.
 * A different solution is needed
 */

class CachedCameraTargetAssignmentProblem : CameraTargetAssignmentProblem<CameraAdapter, VisibleNode<*, Euclidean2DPosition>>() {

    companion object {
        private const val DOUBLE_EPS = 9
        private val CACHE: Kache<CacheInput<String, Euclidean2DPosition>, Map<String, Euclidean2DPosition>> = Builder.build {
            policy = LRU
            capacity = 5*1024
        }
    }

    private data class CacheInput<S, D>(
        val sources: List<S>,
        val destinations: List<D>,
        val maxSourcesPerDestination: Int,
        val cost: (source: S, destination: D) -> Double
    ) {
        private val costMap = mapOf<Pair<S, D>, Double>(
            *sources.flatMap { s ->
                destinations.map { d ->
                    Pair(s, d) to cost.invoke(s, d)
                }
            }.toTypedArray()
        )

        override fun equals(other: Any?): Boolean {
            if (this === other) return true
            if (javaClass != other?.javaClass) return false
            other as CacheInput<*, *>
            if (maxSourcesPerDestination != other.maxSourcesPerDestination) return false
            if(costMap.entries != other.costMap.entries) {
                //println("diff entries")
                return false
            }
            for(k in costMap.keys) {
                val oth = other.costMap[k]
                val t = costMap[k]
                if(oth == null || t == null || kotlin.math.abs(oth - t) > DOUBLE_EPS) {
                    //println("diff cost")
                    return false
                }
            }
            return true
        }

        override fun hashCode(): Int {
            //var result = costMap.hashCode()
            //result = 31 * result + maxSourcesPerDestination
            return costMap.entries.hashCode()//result
        }
    }

    private var x = 0
    private var hits = 0
    private var calls = 0
    override fun solve(sources: List<CameraAdapter>, destinations: List<VisibleNode<*, Euclidean2DPosition>>, maxSourcesPerDestination: Int, cost: (source: CameraAdapter, destination: VisibleNode<*, Euclidean2DPosition>) -> Double): Map<CameraAdapter, VisibleNode<*, Euclidean2DPosition>> {
        val input = CacheInput(sources.map { it.uid }, destinations.map { it.position }, maxSourcesPerDestination) {
            s, d -> sources.first { it.uid == s }.position.getDistanceTo(d)
        }
        val output = CACHE.get(input)
        calls++
        x++
        if(x > 1000) {
            println("hits=$hits, calls=$calls, ratio=${(hits.toDouble() / calls * 100).toInt()}")
            x = 0
            hits = 0
            calls = 0
        }
        return if(output == null) {
            val result = super.solve(sources, destinations, maxSourcesPerDestination, cost)
            CACHE.put(input, result.mapKeys { it.key.uid }.mapValues { it.value.position })
            result
        } else {
            hits++
            output.mapKeys { sources.first { s -> it.key == s.uid} }.mapValues { destinations.first { d -> d.position == it.value } }
        }
    }
}