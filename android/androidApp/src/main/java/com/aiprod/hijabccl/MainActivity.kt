package com.aiprod.hijabccl

import android.annotation.SuppressLint
import android.app.Activity
import android.content.pm.ApplicationInfo
import android.content.ContentValues
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.util.Base64
import android.webkit.CookieManager
import android.webkit.JavascriptInterface
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.webkit.WebViewAssetLoader
import androidx.webkit.WebViewClientCompat
import java.io.File

class MainActivity : ComponentActivity() {

    companion object {
        private const val APP_HOST = "appassets.androidplatform.net"
        private const val START_URL = "https://$APP_HOST/assets/index.html"
        private const val DOWNLOAD_BRIDGE = "NativeDownloads"
    }

    private lateinit var webView: WebView
    private var fileChooserCallback: ValueCallback<Array<Uri>>? = null

    private val fileChooserLauncher =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
            val callback = fileChooserCallback ?: return@registerForActivityResult
            val uris = if (result.resultCode == Activity.RESULT_OK) {
                WebChromeClient.FileChooserParams.parseResult(result.resultCode, result.data)
            } else {
                null
            }
            callback.onReceiveValue(uris)
            fileChooserCallback = null
        }

    @SuppressLint("SetJavaScriptEnabled", "AddJavascriptInterface")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        webView = WebView(this)
        setContentView(webView)

        CookieManager.getInstance().setAcceptCookie(false)
        WebView.setWebContentsDebuggingEnabled((applicationInfo.flags and ApplicationInfo.FLAG_DEBUGGABLE) != 0)

        with(webView.settings) {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            allowContentAccess = true
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            setSupportMultipleWindows(false)
            mediaPlaybackRequiresUserGesture = true
        }

        val assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler(
                "/assets/",
                WebViewAssetLoader.AssetsPathHandler(this)
            )
            .build()

        webView.addJavascriptInterface(DownloadBridge(), DOWNLOAD_BRIDGE)

        webView.webViewClient = object : WebViewClientCompat() {
            override fun shouldInterceptRequest(
                view: WebView,
                request: WebResourceRequest
            ): WebResourceResponse? = assetLoader.shouldInterceptRequest(request.url)

            @Deprecated("Deprecated in Java")
            override fun shouldInterceptRequest(
                view: WebView,
                url: String
            ): WebResourceResponse? = assetLoader.shouldInterceptRequest(Uri.parse(url))

            override fun shouldOverrideUrlLoading(
                view: WebView,
                request: WebResourceRequest
            ): Boolean = !isTrustedAppAsset(request.url)

            @Deprecated("Deprecated in Java")
            override fun shouldOverrideUrlLoading(
                view: WebView,
                url: String
            ): Boolean = !isTrustedAppAsset(Uri.parse(url))

            override fun onPageFinished(view: WebView, url: String) {
                super.onPageFinished(view, url)
                if (isTrustedAppAsset(Uri.parse(url))) {
                    installBlobDownloadInterceptor()
                }
            }
        }

        webView.webChromeClient = object : WebChromeClient() {
            override fun onShowFileChooser(
                webView: WebView,
                filePathCallback: ValueCallback<Array<Uri>>,
                fileChooserParams: FileChooserParams
            ): Boolean {
                fileChooserCallback?.onReceiveValue(null)
                fileChooserCallback = filePathCallback

                return try {
                    val intent = fileChooserParams.createIntent().apply {
                        addCategory(Intent.CATEGORY_OPENABLE)
                    }
                    fileChooserLauncher.launch(intent)
                    true
                } catch (_: Exception) {
                    fileChooserCallback?.onReceiveValue(null)
                    fileChooserCallback = null
                    false
                }
            }
        }

        onBackPressedDispatcher.addCallback(
            this,
            object : OnBackPressedCallback(true) {
                override fun handleOnBackPressed() {
                    if (!webView.canGoBack()) {
                        finish()
                        return
                    }

                    val beforeUrl = webView.url
                    webView.goBack()

                    // The HTML candidate re-arms its history guard synchronously when
                    // it consumes Back for an internal state. If it does not re-arm,
                    // we are at the app root and the first physical Back should exit.
                    webView.postDelayed({
                        if (!isFinishing && !webView.canGoBack() && webView.url == beforeUrl) {
                            finish()
                        }
                    }, 250L)
                }
            }
        )

        if (savedInstanceState == null) {
            webView.loadUrl(START_URL)
        } else {
            webView.restoreState(savedInstanceState)
        }
    }

    override fun onSaveInstanceState(outState: Bundle) {
        webView.saveState(outState)
        super.onSaveInstanceState(outState)
    }

    override fun onDestroy() {
        fileChooserCallback?.onReceiveValue(null)
        fileChooserCallback = null
        webView.removeJavascriptInterface(DOWNLOAD_BRIDGE)
        webView.stopLoading()
        webView.destroy()
        super.onDestroy()
    }

    private fun isTrustedAppAsset(uri: Uri): Boolean {
        return uri.scheme == "https" &&
            uri.host == APP_HOST &&
            (uri.path ?: "").startsWith("/assets/")
    }

    private fun installBlobDownloadInterceptor() {
        val script = """
            (function () {
              if (window.__mhcclNativeDownloadInstalled) return;
              window.__mhcclNativeDownloadInstalled = true;

              document.addEventListener('click', function (event) {
                const target = event.target;
                const anchor = target && target.closest ? target.closest('a[download]') : null;
                if (!anchor || !anchor.href || !anchor.href.startsWith('blob:')) return;

                event.preventDefault();
                const name = String(anchor.download || 'mhccl-export');
                fetch(anchor.href)
                  .then(function (response) { return response.blob(); })
                  .then(function (blob) {
                    const reader = new FileReader();
                    reader.onloadend = function () {
                      if (typeof reader.result === 'string') {
                        NativeDownloads.save(name, String(blob.type || ''), reader.result);
                      }
                    };
                    reader.readAsDataURL(blob);
                  })
                  .catch(function () {});
              }, true);
            })();
        """.trimIndent()

        webView.evaluateJavascript(script, null)
    }

    private inner class DownloadBridge {
        @JavascriptInterface
        fun save(fileName: String, mimeType: String, dataUrl: String) {
            if (!dataUrl.startsWith("data:") || !dataUrl.contains(";base64,")) {
                return
            }

            val safeName = sanitizeFileName(fileName)
            val encoded = dataUrl.substringAfter(";base64,", "")
            val bytes = runCatching {
                Base64.decode(encoded, Base64.DEFAULT)
            }.getOrNull() ?: return

            runOnUiThread {
                val saved = runCatching {
                    saveToDownloads(safeName, mimeType.ifBlank { "application/octet-stream" }, bytes)
                }.getOrDefault(false)

                Toast.makeText(
                    this@MainActivity,
                    if (saved) R.string.export_saved else R.string.export_failed,
                    Toast.LENGTH_SHORT
                ).show()
            }
        }
    }

    private fun sanitizeFileName(input: String): String {
        val cleaned = input
            .replace(Regex("""[^A-Za-z0-9._-]"""), "_")
            .trim('.', '_')
            .take(120)
        return cleaned.ifBlank { "mhccl-export" }
    }

    private fun saveToDownloads(name: String, mimeType: String, bytes: ByteArray): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val values = ContentValues().apply {
                put(MediaStore.Downloads.DISPLAY_NAME, name)
                put(MediaStore.Downloads.MIME_TYPE, mimeType)
                put(MediaStore.Downloads.IS_PENDING, 1)
            }

            val uri = contentResolver.insert(
                MediaStore.Downloads.EXTERNAL_CONTENT_URI,
                values
            ) ?: return false

            try {
                contentResolver.openOutputStream(uri)?.use { output ->
                    output.write(bytes)
                } ?: return false

                values.clear()
                values.put(MediaStore.Downloads.IS_PENDING, 0)
                contentResolver.update(uri, values, null, null)
                true
            } catch (error: Exception) {
                contentResolver.delete(uri, null, null)
                false
            }
        } else {
            val dir = getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS) ?: return false
            val file = File(dir, name)
            runCatching {
                file.outputStream().use { it.write(bytes) }
            }.isSuccess
        }
    }
}
