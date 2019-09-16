package it.unibo.alchemist.loader.export

import it.unibo.alchemist.loader.variables.ListOf
import it.unibo.alchemist.model.interfaces.*
import it.unibo.alchemist.model.interfaces.Time
import it.unibo.alchemist.model.interfaces.environments.BoundariesVisitor
import it.unibo.alchemist.model.interfaces.environments.HasBoundaries
import it.unibo.alchemist.model.interfaces.environments.RectangularBoundaries
import kotlin.math.max

/**
 * Hack to log progress % to the console
 */
class LogProgress<P : Position<P>>(
    private val visionMolecule: Molecule,
    private val targetMolecule: Molecule
    ) : Extractor {
    companion object  {
        private val EXPORT = DoubleArray(0)
        private val NAMES = emptyList<String>()
        private const val PRINT_EACH_MILLISECONDS = 10000.0
    }

    private var printed = false
    private var lastPrintTime = System.currentTimeMillis()

    override fun extractData(environment: Environment<*, *>, r: Reaction<*>?, time: Time?, step: Long): DoubleArray {
        @Suppress("UNCHECKED_CAST") val env = environment as Environment<*, P>
        require(env is HasBoundaries)
        if (!printed) {
            val nodes = env.nodes
            var width = 0.0
            var height = 0.0
            env.boundaries.accept(object : BoundariesVisitor {
                override fun visit(rectangularBoundaries: RectangularBoundaries) {
                    width = rectangularBoundaries.height
                    height = rectangularBoundaries.width
                }
            })
            val numCameras = nodes.filter { it.isCamera() }.count()
            val numObjects = nodes.size - numCameras
            println()
            println()
            println("EnvSize=$width x $height, Objects=$numObjects, Cameras=$numCameras, Ratio=${numCameras / max(1, numObjects)}")
            println()
            printed = true
        }
        val nowTime = System.currentTimeMillis()
        if(!environment.simulation.finalTime.isInfinite && nowTime - lastPrintTime > PRINT_EACH_MILLISECONDS){
            val simTime = environment.simulation.time.toDouble()
            val end = environment.simulation.finalTime.toDouble()
            println("%.1f%%".format(simTime / max(0.1, end) * 100))
            lastPrintTime = nowTime
        }
        return EXPORT
    }

    override fun getNames() = NAMES

    private fun Node<*>.isTarget() = contains(targetMolecule)

    private fun Node<*>.isCamera() = contains(visionMolecule)
}