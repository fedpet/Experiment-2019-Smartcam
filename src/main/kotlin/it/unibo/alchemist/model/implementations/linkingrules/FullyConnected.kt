package it.unibo.alchemist.model.implementations.linkingrules

import it.unibo.alchemist.model.implementations.neighborhoods.Neighborhoods
import it.unibo.alchemist.model.interfaces.*

class FullyConnected<T, P: Position<P>> : LinkingRule<T, P> {
    override fun computeNeighborhood(center: Node<T>, env: Environment<T, P>) =
        Neighborhoods.make(env, center, env.nodes.minusElement(center))

    override fun isLocallyConsistent() = true
}