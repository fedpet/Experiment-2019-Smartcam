package it.unibo.alchemist.loader.export

import it.unibo.alchemist.model.interfaces.*
import it.unibo.alchemist.model.interfaces.Time


interface NodeMovementTracker {
    fun queryCameraMovementsSinceLastQuery(): Double
    fun queryObjectMovementsSinceLastQuery(): Double
}

/**
 * Exports distance traveled by both cameras and objects. It is precise.
 */
class DistanceTraveled : Extractor {
    companion object {
        private val NAMES = listOf("CamDist", "ObjDist")
    }

    override fun extractData(environment: Environment<*, *>, r: Reaction<*>?, time: Time?, step: Long): DoubleArray {
        return if (environment is NodeMovementTracker) {
            doubleArrayOf(environment.queryCameraMovementsSinceLastQuery(), environment.queryObjectMovementsSinceLastQuery())
        } else {
            throw IllegalArgumentException("DistanceTraveled only works with environments implementing NodeMovementTracker")
        }
    }

    override fun getNames() = NAMES
}