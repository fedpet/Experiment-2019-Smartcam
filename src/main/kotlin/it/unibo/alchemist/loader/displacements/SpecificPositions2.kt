package it.unibo.alchemist.loader.displacements

import it.unibo.alchemist.model.interfaces.Environment
import it.unibo.alchemist.model.interfaces.Position

/**
 * Working version of [SpecificPositions] which doesn't work.
 * TODO: make pr
 */
class SpecificPositions2 (
    environment: Environment<*, *>,
    vararg positions: List<Number>
) : Displacement<Position<*>> {

    private val positions: List<Position<*>> = positions.map { environment.makePosition(*it.toTypedArray()) }

    override fun stream() = positions.stream()
}