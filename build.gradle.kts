import org.jetbrains.kotlin.gradle.tasks.KotlinCompile
import java.io.ByteArrayOutputStream

plugins {
    java
    kotlin("jvm") version "1.3.50"
    //id("com.github.ManifestClasspath") version "0.1.0-RELEASE" // shortens command length for windows
    //id("ua.eshepelyuk.ManifestClasspath") version "1.0.0" // shortens command length for windows
}

group = "it.unibo.alchemist"
version = "1.0-SNAPSHOT"

repositories {
    mavenCentral()
    maven("https://dl.bintray.com/alchemist-simulator/Alchemist/")
    maven("https://dl.bintray.com/protelis/Protelis/")
    jcenter()
}

dependencies {
    implementation("it.unibo.alchemist:alchemist:9.0.0")
    implementation("it.unibo.alchemist:alchemist-implementationbase:9.0.0")
    implementation("it.unibo.alchemist:alchemist-interfaces:9.0.0")
    implementation("it.unibo.alchemist:alchemist-smartcam:9.0.0")
    implementation("it.unibo.alchemist:alchemist-loading:9.0.0")
    implementation("com.yundom:kache:1.0.5")
    implementation(kotlin("stdlib-jdk8"))
}

configure<JavaPluginConvention> {
    sourceCompatibility = JavaVersion.VERSION_1_8
}
tasks.withType<KotlinCompile> {
    kotlinOptions.jvmTarget = "1.8"
}

sourceSets.main.get().resources.setSrcDirs(listOf("src/main/resources", "src/main/protelis"))

task("allSimulations") {
    doLast {
        println("Done.")
    }
}
fun makeTest(
    file: String,
    name: String = file,
    effects: String? = "smartcam.aes",
    sampling: Double = 1.0,
    time: Double = Double.POSITIVE_INFINITY,
    vars: Set<String> = setOf(),
    maxHeap: Long? = null,
    taskSize: Int = 1024,
    threads: Int? = null,
    debug: Boolean = false
) {
    val heap: Long = maxHeap ?: if (System.getProperty("os.name").toLowerCase().contains("linux")) {
        ByteArrayOutputStream().use { output ->
            exec {
                executable = "bash"
                args = listOf("-c", "cat /proc/meminfo | grep MemAvailable | grep -o '[0-9]*'")
                standardOutput = output
            }
            output.toString().trim().toLong() / 1024
        }.also { println("Detected ${it}MB RAM available.") }  * 9 / 10
    } else {
        // Guess 16GB RAM of which 2 used by the OS
        14 * 1024L
    }
    val threadCount = threads ?: maxOf(1, minOf(Runtime.getRuntime().availableProcessors(), heap.toInt() / taskSize ))
    println("Running on $threadCount threads")
    task<JavaExec>(name) {
        //dependsOn("build")
        if (System.getProperty("os.name").toLowerCase().contains("windows")) {
            // pass classpath in environment's variable to avoid errors such as "command line too long"
            environment("CLASSPATH", sourceSets["main"].runtimeClasspath.asPath)
        } else {
            classpath = sourceSets["main"].runtimeClasspath
            classpath("src/main/protelis")
        }
        main = "it.unibo.alchemist.Alchemist"
        maxHeapSize = "${heap}m"
        if (debug) {
            jvmArgs("-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=1044")
        }
        File("data").mkdirs()
        args(
            "-y", "src/main/resources/${file}.yml",
            "-t", "$time",
            "-p", threadCount,
            "-i", "$sampling"
        )
        if (effects != null) {
            args("-g", "effects/${effects}")
        }
        if (vars.isNotEmpty()) {
            args("-b") // background
            args("-var", *vars.toTypedArray())
            args("-e", "data/${name}")
            tasks {
                "allSimulations" {
                    dependsOn(name)
                }
            }
        } else {
            args("-e", name)
        }
    }
}


makeTest("testperf", name="testperf")
makeTest("forcefields", name="ff")
makeTest("fully_connected", name="launchGUI")
makeTest("fully_connected", time = 2000.0, vars = setOf("Seed", "Algorithm", "HumansCamerasRatio"))
makeTest("limited_connection_range", time = 2000.0, vars = setOf("Seed", "Algorithm", "ConnectionRange"))
defaultTasks("allSimulations")