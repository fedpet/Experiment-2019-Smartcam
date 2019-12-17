package it.unibo.alchemist.loader.export

import it.unibo.alchemist.model.interfaces.Environment
import it.unibo.alchemist.model.interfaces.Molecule
import it.unibo.alchemist.model.interfaces.Node
import it.unibo.alchemist.model.interfaces.Position
import it.unibo.alchemist.model.interfaces.Reaction
import it.unibo.alchemist.model.interfaces.Time
import it.unibo.alchemist.model.interfaces.VisibleNode
import it.unibo.smartcamexperiment.toBoolean
import java.util.*
import kotlin.math.max

/**
 * Exports the percentage of targets covered by at least 1 camera, up to [maxCamerasPerTarget].
 * For instance if [maxCamerasPerTarget] is 2 then it exports 1-coverage and 2-coverage percentages.
 * It exports NaN if there are no targets
 * A target is any [Node] containing [targetMolecule].
 * A camera is any [Node] containing [visionMolecule].
 * [visionMolecule] is expected to contain a collection of [VisibleNode].
 */
class CamerasKCoverage<P : Position<P>>(
    private val visionMolecule: Molecule,
    private val targetMolecule: Molecule,
    private val maxCamerasPerTarget: Int
) : Extractor {
    init {
        require(maxCamerasPerTarget > 0)
    }
    private val names = maxCamerasPerTarget.downTo(1).map { "$it-coverage" }
    private val resultWithNoTargets = DoubleArray(maxCamerasPerTarget) { Double.NaN }

    override fun extractData(environment: Environment<*, *>, r: Reaction<*>?, time: Time?, step: Long): DoubleArray {
        @Suppress("UNCHECKED_CAST") val env = environment as Environment<*, P>
        val nodes: List<Node<*>> = env.nodes
        val numTargets = nodes.filter { it.isTarget() }.count()
        return if (numTargets <= 0) resultWithNoTargets else nodes
            .filter { it.isCamera() }
            .flatMap { it.getVisibleTargets() } // all visible targets
            .groupingBy { it.node.id } // group by camera
            .eachCount() // count #cameras for each target
            .values
            .groupingBy { it } // group by #cameras (k coverage)
            .eachCount() // count #targets for each k-coverage
            .let { map ->
                val k = max(map.keys.max() ?: maxCamerasPerTarget, maxCamerasPerTarget)
                DoubleArray(k) { map.getOrDefault(k - it, 0).toDouble() }
                    .also { values -> // add (k+n)cov to k-cov. so that 1-cov includes 2-cov and 3-cov etc..
                        (1 until k).forEach { idx -> values[idx] += values[idx - 1] }
                    }
            }
            .takeLast(maxCamerasPerTarget) // make sure to only output k values and forget k+n coverages
            .map { it / numTargets } // percentages
            .toDoubleArray()
    }

    override fun getNames() = names

    private fun Node<*>.isTarget() = contains(targetMolecule) && getConcentration(targetMolecule).toBoolean()

    private fun Node<*>.isCamera() = contains(visionMolecule)

    private fun Node<*>.getVisibleTargets() =
        with(getConcentration(visionMolecule)) {
            require(this is List<*>) { "Expected a List but got $this of type ${this::class}" }
            if (!isEmpty()) {
                get(0)?.also {
                    require(it is VisibleNode<*, *>) {
                        "Expected a List<VisibleNode> but got List<${it::class}> = $this"
                    }
                }
            }
            @Suppress("UNCHECKED_CAST")
            (this as Iterable<VisibleNode<*, *>>).filter { it.node.isTarget() }
        }
}