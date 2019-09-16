package it.unibo.alchemist.model.implementations.actions

import it.unibo.alchemist.model.implementations.movestrategies.ZigZagRandomTarget2
import it.unibo.alchemist.model.implementations.movestrategies.speed.GloballyConstantSpeed
import it.unibo.alchemist.model.implementations.positions.Euclidean2DPosition
import it.unibo.alchemist.model.implementations.routes.PolygonalChain
import it.unibo.alchemist.model.interfaces.Environment
import it.unibo.alchemist.model.interfaces.Node
import it.unibo.alchemist.model.interfaces.Reaction
import it.unibo.alchemist.model.interfaces.movestrategies.RoutingStrategy
import org.apache.commons.math3.random.RandomGenerator

/**
 * NOTE: same as ZigZagMove but without the bug affecting Alchemist 9.0.0
 * Moves toward a randomly chosen direction for up to distance meters, then chooses another one and so on.
 * @param <T> concentration type
 * @param env environment containing the node
 * @param node the node to move
 * @param reaction the reaction containing this action
 * @param rng random number generator to use for the decisions
 * @param distance the distance to travel before picking another one
 * @param speed the speed
 */
class ZigZagMove2<T>(
    node: Node<T>,
    reaction: Reaction<T>,
    private val env: Environment<T, Euclidean2DPosition>,
    private val rng: RandomGenerator,
    private val distance: Double,
    private val speed: Double
) : AbstractConfigurableMoveNodeWithAccurateEuclideanDestination<T>(
    env,
    node,
    RoutingStrategy { p1, p2 -> PolygonalChain<Euclidean2DPosition>(listOf(p1, p2)) },
    ZigZagRandomTarget2<T>(node, env, rng, distance),
    GloballyConstantSpeed(reaction, speed)
) {
    override fun cloneAction(n: Node<T>, r: Reaction<T>) =
        ZigZagMove2(n, r, env, rng, distance, speed)
}