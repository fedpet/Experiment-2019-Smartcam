package it.unibo.alchemist.model.implementations.actions

import it.unibo.alchemist.model.interfaces.Context
import it.unibo.alchemist.model.interfaces.Node
import it.unibo.alchemist.model.interfaces.Reaction
import it.unibo.alchemist.model.interfaces.environments.EuclideanPhysics2DEnvironment
import it.unibo.smartcamexperiment.randomAngle
import org.apache.commons.math3.random.RandomGenerator
import kotlin.math.cos
import kotlin.math.sin

/**
 * Sets heading once, and then removes itself.
 * Should be part of node initialization via construtor parameter?
 */
class InitHeading @JvmOverloads constructor(
    node: Node<Any>,
    private val reaction: Reaction<Any>,
    private val env: EuclideanPhysics2DEnvironment<Any>,
    private val rng: RandomGenerator,
    private val initialAngle: Double = rng.randomAngle()
) : AbstractAction<Any>(node) {
    //private var executed = false

    init {
        execute()
    }

    override fun cloneAction(n: Node<Any>, r: Reaction<Any>) = InitHeading(n, r, env, rng, initialAngle)

    override fun execute() {
        //require(!executed)
        reaction.actions = reaction.actions.minusElement(this)
        env.setHeading(node, env.makePosition(cos(initialAngle), sin(initialAngle)))
        //executed = true
    }

    override fun getContext() = Context.LOCAL
}