import java.security.MessageDigest

plugins {
    id("com.android.application")
}

val canonicalPrototype = rootProject.projectDir.resolve("../prototype/index.html")
val canonicalPrototypeDir = rootProject.projectDir.resolve("../prototype")
val expectedPrototypeSha = providers.gradleProperty("mhccl.prototype.sha256").get()

android {
    namespace = "com.aiprod.hijabccl"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.aiprod.hijabccl"
        minSdk = 24
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0-test"
    }

    buildTypes {
        debug {
            applicationIdSuffix = ".test"
            versionNameSuffix = "-debug"
        }
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    sourceSets {
        getByName("main") {
            assets.srcDir(canonicalPrototypeDir)
        }
    }
}

dependencies {
    implementation("androidx.activity:activity-ktx:1.13.0")
    implementation("androidx.webkit:webkit:1.17.1")
}

tasks.register("verifyPrototypeSha") {
    group = "verification"
    description = "Fails if the Android app is not packaging the canonical tested HTML candidate."
    inputs.file(canonicalPrototype)

    doLast {
        check(canonicalPrototype.isFile) {
            "Canonical prototype missing: ${canonicalPrototype.absolutePath}"
        }
        val digest = MessageDigest.getInstance("SHA-256")
            .digest(canonicalPrototype.readBytes())
            .joinToString("") { "%02x".format(it) }

        check(digest == expectedPrototypeSha) {
            "Prototype SHA mismatch. Expected $expectedPrototypeSha, got $digest"
        }
        println("Canonical prototype SHA verified: $digest")
    }
}

tasks.named("preBuild").configure {
    dependsOn("verifyPrototypeSha")
}
