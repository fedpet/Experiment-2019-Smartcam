package it.unibo.smartcamexperiment.linpro

import org.apache.commons.math3.optim.linear.*
import org.apache.commons.math3.optim.nonlinear.scalar.GoalType

class ApacheLinpro<S, D> : AbstractLinpro<S, D>() {
    override fun solveLPProblem(builder: LPProblemBuilder.() -> Unit): DoubleArray {
        val settings = object :
            LPProblemBuilder {
            var objectiveFunction = LinearObjectiveFunction(DoubleArray(0), 0.0)
            var objective =
                LPProblemBuilder.GOAL.MINIMIZE
            val constraints = mutableListOf<LinearConstraint>()
            var nonNegative = false
            override fun setObjectiveFunction(coefficients: DoubleArray, goal: LPProblemBuilder.GOAL) {
                objectiveFunction = LinearObjectiveFunction(coefficients, 0.0)
                objective = goal
            }
            override fun addSmallerThanEqualsConstraint(coefficients: DoubleArray, value: Double) {
                constraints.add(LinearConstraint(coefficients, Relationship.LEQ, value))
            }
            override fun addBiggerThanEqualsConstraint(coefficients: DoubleArray, value: Double) {
                constraints.add(LinearConstraint(coefficients, Relationship.GEQ, value))
            }
            override fun addEqualsConstraint(coefficients: DoubleArray, value: Double) {
                constraints.add(LinearConstraint(coefficients, Relationship.EQ, value))
            }
            override fun addNonNegativityConstraint() {
                nonNegative = true
            }
        }.apply(builder)
        return SimplexSolver().optimize(
            settings.objectiveFunction,
            LinearConstraintSet(settings.constraints),
            if (settings.objective == LPProblemBuilder.GOAL.MINIMIZE) GoalType.MINIMIZE else GoalType.MAXIMIZE,
            NonNegativeConstraint(settings.nonNegative)
        ).first
    }

}