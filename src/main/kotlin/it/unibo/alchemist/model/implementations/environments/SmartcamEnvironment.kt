package it.unibo.alchemist.model.implementations.environments

import it.unibo.alchemist.loader.export.NodeMovementTracker
import it.unibo.alchemist.model.implementations.positions.Euclidean2DPosition
import it.unibo.alchemist.model.interfaces.Molecule
import it.unibo.alchemist.model.interfaces.Node
import it.unibo.alchemist.model.interfaces.environments.HasBoundaries
import it.unibo.alchemist.model.interfaces.environments.RectangularBoundaries
import it.unibo.alchemist.model.interfaces.geometry.GeometricShape
import kotlin.math.abs

/**
 * A bounded [Rectangular2DEnvironment] with support for tracking movements
 */
class SmartcamEnvironment<T> (
    /**
     * The environment's width limits the positions of the nodes inside a rectangle [width * height] centered in (0,0)
     */
    width: Double,
    /**
     * The environment's height limits the positions of the nodes inside a rectangle [width * height] centered in (0,0)
     */
    height: Double,
    private val filterCamera: Molecule
) : Continuous2DEnvironment<T>(), HasBoundaries, NodeMovementTracker {
    private var cameraMovements = 0.0
    private var objectMovements = 0.0

    override val boundaries = RectangularBoundaries(width, height)

    override fun moveNodeToPosition(node: Node<T>, newpos: Euclidean2DPosition) {
        val realLastPos = getPosition(node)
        super.moveNodeToPosition(node, newpos)
        val realNewPos = getPosition(node)
        realLastPos?.also { lastp ->
            realNewPos?.also { newp ->
                val distance = lastp.getDistanceTo(newp)
                if (node.contains(filterCamera)) {
                    cameraMovements += distance
                } else {
                    objectMovements += distance
                }
            }
        }
    }

    override fun queryCameraMovementsSinceLastQuery(): Double {
        val result = cameraMovements
        cameraMovements = 0.0
        return result
    }

    override fun queryObjectMovementsSinceLastQuery(): Double {
        val result = objectMovements
        objectMovements = 0.0
        return result
    }

    override fun nodeShouldBeAdded(node: Node<T>, position: Euclidean2DPosition) =
        isWithinBoundaries(position, node.shape) && super.nodeShouldBeAdded(node, position)

    override fun canNodeFitPosition(node: Node<T>, position: Euclidean2DPosition) =
        isWithinBoundaries(position, node.shape) && super.canNodeFitPosition(node, position)

    private fun isWithinBoundaries(pos: Euclidean2DPosition, shape: GeometricShape<*, *>) =
        abs(pos.x) + shape.diameter / 2 < boundaries.width / 2 && abs(pos.y) + shape.diameter / 2 < boundaries.height / 2
}