package it.unibo.alchemist.loader.variables

import com.google.common.collect.Streams
import java.util.stream.Stream

class ListOf<T : java.io.Serializable>(
    private val default: T,
    private vararg val values: T
) : PrintableVariable<T>() {
    override fun getDefault() = default

    override fun stream(): Stream<T> = Streams.concat(Stream.of(default), Stream.of(*values))
}