package it.unibo.smartcamexperiment.test

import io.kotlintest.fail
import io.kotlintest.shouldBe
import io.kotlintest.specs.FreeSpec
import it.unibo.smartcamexperiment.CameraTargetAssignmentProblem
import it.unibo.smartcamexperiment.linpro.SCPLinpro
import it.unibo.smartcamexperiment.linpro.ApacheLinpro
import scpsolver.lpsolver.SolverFactory

class TestCameraTargetAssignmentProblem : FreeSpec() {
    init {
        val solvers = mutableListOf<() -> CameraTargetAssignmentProblem<String, String>>(
            ::ApacheLinpro
        )
        if (SCPLinpro.isAvailable()) {
            solvers.add(::SCPLinpro)
        }
        solvers.forEach {
            val solver = it()
            solver.javaClass.simpleName - {
                "No sources nor destinations" {
                    solver.solve(emptyMap(), 1) shouldBe emptyMap<String, String>()
                }
                "No sources" {
                    solver.solve(emptyList(), listOf("da", "db"), 1, false,
                        zeroCost()
                    ) shouldBe emptyMap<String, String>()
                }
                "No destinations" {
                    solver.solve(listOf("sa", "sb"), emptyList(), 1, false,
                        zeroCost()
                    ) shouldBe emptyMap<String, String>()
                }
                "Zero maxSourcesPerDestination" {
                    solver.solve(listOf("sa", "sb"), listOf("da", "db"), 0, false,
                        zeroCost()
                    ) shouldBe emptyMap<String, String>()
                }
                "Simple and balanced problem" {
                    val data = mapOf(
                        Pair("sa", "da") to 1.0,
                        Pair("sa", "db") to 10.0,
                        Pair("sb", "da") to 10.0,
                        Pair("sb", "db") to 1.0
                    )
                    solver.solve(data, 1) shouldBe mapOf(
                        "sa" to "da",
                        "sb" to "db"
                    )
                }
                "More sources than destinations, 1 source per destination" {
                    val data = mapOf(
                        Pair("sa", "da") to 1.0,
                        Pair("sb", "da") to 2.0,
                        Pair("sc", "da") to 3.0,
                        Pair("sd", "da") to 3.0,
                        Pair("sa", "db") to 2.0,
                        Pair("sb", "db") to 1.0,
                        Pair("sc", "db") to 3.0,
                        Pair("sd", "db") to 3.0
                    )
                    solver.solve(data, 1) shouldBe mapOf(
                        "sa" to "da",
                        "sb" to "db"
                    )
                }
                "More sources than destinations, 2 sources per destination" {
                    val data = mapOf(
                        Pair("sa", "da") to 1.0,
                        Pair("sb", "da") to 20.0,
                        Pair("sc", "da") to 100.0,
                        Pair("sa", "db") to 0.0,
                        Pair("sb", "db") to 1.0,
                        Pair("sc", "db") to 3.0,
                        Pair("sd", "da") to 300.0,
                        Pair("sd", "db") to 3.0,
                        Pair("se", "da") to 100.0,
                        Pair("se", "db") to 100.0
                    )
                    solver.solve(data, 2) shouldBe mapOf(
                        "sa" to "da",
                        "sb" to "da",
                        "sc" to "db",
                        "sd" to "db"
                    )
                }
                "More destinations than sources, 1 source per destination" {
                    val data = mapOf(
                        Pair("sa", "da") to 100.0,
                        Pair("sa", "db") to 100.0,
                        Pair("sa", "dc") to 1.0,
                        Pair("sa", "dd") to 100.0,
                        Pair("sb", "da") to 100.0,
                        Pair("sb", "db") to 100.0,
                        Pair("sb", "dc") to 1.0,
                        Pair("sb", "dd") to 10.0
                    )
                    solver.solve(data, 1) shouldBe mapOf(
                        "sa" to "dc",
                        "sb" to "dd"
                    )
                }
            }
        }
    }
}

private fun zeroCost() = { _:String, _:String -> 0.0 }

private fun <S, D> CameraTargetAssignmentProblem<S, D>.solve(data: Map<Pair<S, D>, Double>, maxSourcesPerDestination: Int) =
    solve(
        data.keys.map { it.first }.distinct(),
        data.keys.map { it.second }.distinct(),
        maxSourcesPerDestination,
        false)
    {
        src, dst -> data.getOrElse(Pair(src, dst)) {
            fail("No cost defined from $src to $dst")
        }
    }