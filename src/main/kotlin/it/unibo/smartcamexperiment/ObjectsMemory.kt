package it.unibo.smartcamexperiment

import it.unibo.alchemist.model.interfaces.VisibleNode
import org.protelis.lang.datatype.DeviceUID
import org.protelis.lang.datatype.Tuple

private data class Record(
    val time: Double,
    val objects: List<VisibleNode<*,*>>
) {
    fun remove(node: VisibleNode<*, *>) =
        Record(time, objects.filter { it == node })
}

/*
 * Unfinished data structure to memorize targets sent by multiple cameras and go farther than 1 hop
 * It should include strategies to discard old packets based on time and distance
 */
class ObjectsMemory {
    private val camToObjMap: Map<DeviceUID, Record>
    private val objToCamMap: Map<VisibleNode<*,*>, DeviceUID>

    constructor() : this(mapOf<DeviceUID, Record>(), mapOf<VisibleNode<*,*>, DeviceUID>())

    private constructor(cto: Map<DeviceUID, Record>, otc: Map<VisibleNode<*,*>, DeviceUID>) {
        camToObjMap = cto
        objToCamMap = otc
    }

    fun insert(devId: DeviceUID, time: Double, objects: Tuple): ObjectsMemory {
        val newCamToObjMap = camToObjMap.toMutableMap()
        val newObjToCamMap = objToCamMap.toMutableMap()
        val targets = objects.toAnyTargets()

        val newTargets = mutableListOf<VisibleNode<*,*>>()
        targets.forEach { newObj ->
            newObjToCamMap[newObj]?.also { cam ->
                newCamToObjMap[cam]?.also { record ->
                    if (record.time < time) {
                        val newRecord = record.remove(newObj)
                        newObjToCamMap.remove(newObj)
                        if (newRecord.objects.isEmpty()) {
                            newCamToObjMap.remove(cam)
                        } else {
                            newCamToObjMap.replace(cam, newRecord)
                        }
                        newTargets.add(newObj)
                    }
                }
            }
        }

        val newRecord = Record(time, newTargets)
        newCamToObjMap.merge(devId, newRecord) { old, new ->
             if (old.time < new.time) {
                 old.objects.forEach { newObjToCamMap.remove(it) }
                 new.objects.forEach { newObjToCamMap[it] = devId }
                 new
             } else {
                 old
             }
        }

        return ObjectsMemory(newCamToObjMap, newObjToCamMap)
    }
}