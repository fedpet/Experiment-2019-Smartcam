package it.unibo.smartcamexperiment.test

import io.kotlintest.shouldBe
import io.kotlintest.shouldNotBe
import io.kotlintest.specs.StringSpec
import it.unibo.alchemist.model.implementations.environments.Continuous2DEnvironment
import it.unibo.alchemist.model.implementations.linkingrules.NoLinks
import it.unibo.alchemist.model.implementations.nodes.ProtelisNode
import it.unibo.alchemist.model.implementations.positions.Euclidean2DPosition
import it.unibo.alchemist.model.smartcam.VisibleNodeImpl
import it.unibo.smartcamexperiment.CameraAdapter

class TestLinproCacheability : StringSpec({
    "VisibleNode equals by ID" { // must compare only by ID to make cached linpro works
        val env = Continuous2DEnvironment<Any>()
        env.linkingRule = NoLinks()
        val node1 = ProtelisNode(env)
        env.addNode(node1, env.makePosition(1.0, 1.0))
        val node2 = ProtelisNode(env)
        env.addNode(node2, env.makePosition(20.0, 20.0))
        val visible1 = VisibleNodeImpl<Any, Euclidean2DPosition>(node1, env.getPosition(node1))
        val visible2 = VisibleNodeImpl<Any, Euclidean2DPosition>(node2, env.getPosition(node2))
        visible1 shouldNotBe visible2
        val visible1copy = VisibleNodeImpl<Any, Euclidean2DPosition>(node1, env.getPosition(node1))
        visible1 shouldBe visible1copy
        val visible1copyDifferentPos = VisibleNodeImpl<Any, Euclidean2DPosition>(node1, env.makePosition(2.0, 2.0))
        visible1 shouldBe visible1copyDifferentPos
        visible1copy shouldBe visible1copyDifferentPos
    }
    "CameraAdapter equals by ID" { // must compare only by ID to make cached linpro works
        val env = Continuous2DEnvironment<Any>()
        env.linkingRule = NoLinks()
        val node1 = ProtelisNode(env)
        env.addNode(node1, env.makePosition(1.0, 1.0))
        val node2 = ProtelisNode(env)
        env.addNode(node2, env.makePosition(20.0, 20.0))
        val cam1 = CameraAdapter(node1, env.getPosition(node1))
        val cam2 = CameraAdapter(node2, env.getPosition(node2))
        cam1 shouldNotBe cam2
        val cam1copy = CameraAdapter(node1, env.getPosition(node1))
        cam1 shouldBe cam1copy
        val cam1copyDifferentPos = CameraAdapter(node1, env.makePosition(2.0, 2.0))
        cam1 shouldBe cam1copyDifferentPos // must compare only by ID to make cached linpro works
        cam1copy shouldBe cam1copyDifferentPos
    }
})